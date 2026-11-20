import asyncio
import logging
from collections import defaultdict, deque
from contextlib import asynccontextmanager
from time import monotonic
from typing import Deque, Dict, Set

from fastapi import Depends, FastAPI, Request, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api import routes_agent, routes_esg, routes_optimizer, routes_twin
from app.config import settings
from app.database import AsyncSessionLocal, init_db
from app.models.db_models import TelemetryRecord
from app.security import require_operator
from app.services.digital_twin import twin
from app.services.external_feeds import external_feeds

logger = logging.getLogger("gridpulse")
connected_clients: Set[WebSocket] = set()
_request_times: Dict[str, Deque[float]] = defaultdict(deque)
_RATE_LIMIT_PATHS = {
    "/api/auth/check",
    "/api/agent/policy",
    "/api/agent/decisions",
    "/api/optimizer/pareto",
    "/api/optimizer/solve",
    "/api/twin/clock",
    "/api/twin/chaos",
}
RATE_LIMIT_WINDOW_SECONDS = 60.0
RATE_LIMIT_MAX_REQUESTS = 30


async def broadcast_snapshot() -> None:
    if not connected_clients:
        return

    payload = twin.get_snapshot().model_dump_json()
    dead = []
    for websocket in tuple(connected_clients):
        try:
            await websocket.send_text(payload)
        except Exception:
            dead.append(websocket)

    for websocket in dead:
        connected_clients.discard(websocket)


async def simulation_loop() -> None:
    while True:
        await asyncio.sleep(twin.tick_seconds)
        if not twin.is_running:
            continue

        try:
            record = twin.step_hour()
            async with AsyncSessionLocal() as db:
                db.add(TelemetryRecord(**record))
                await db.commit()
            await broadcast_snapshot()
        except asyncio.CancelledError:
            raise
        except Exception:
            logger.exception("Simulation tick failed; the loop will retry next tick")


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    data = await external_feeds.get_24h_forecasts()
    twin.update_external_forecasts(data)
    task = asyncio.create_task(simulation_loop())
    try:
        yield
    finally:
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass
        for websocket in tuple(connected_clients):
            try:
                await websocket.close(code=1001, reason="Server shutting down")
            except Exception:
                pass
        connected_clients.clear()


app = FastAPI(
    title="GridPulse AI",
    version="1.1.0",
    lifespan=lifespan,
    docs_url=None if settings.environment == "production" else "/docs",
    redoc_url=None if settings.environment == "production" else "/redoc",
    openapi_url=None if settings.environment == "production" else "/openapi.json",
)

allowed_origins = [settings.frontend_origin.rstrip("/")]
if settings.environment != "production":
    allowed_origins.extend(["http://localhost:5173", "http://127.0.0.1:5173"])

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=False,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization"],
    max_age=600,
)


@app.middleware("http")
async def security_and_rate_limit(request: Request, call_next):
    path = request.url.path
    is_limited_path = path in _RATE_LIMIT_PATHS or path.startswith("/api/agent/decisions/")
    if (request.method == "POST" and is_limited_path) or (request.method == "GET" and path == "/api/auth/check"):
        remote = request.client.host if request.client else "unknown"
        now = monotonic()
        bucket = _request_times[remote]
        while bucket and now - bucket[0] > RATE_LIMIT_WINDOW_SECONDS:
            bucket.popleft()
        if len(bucket) >= RATE_LIMIT_MAX_REQUESTS:
            return JSONResponse(
                status_code=429,
                content={"detail": "Too many state-changing requests. Please retry shortly."},
                headers={"Retry-After": str(int(RATE_LIMIT_WINDOW_SECONDS))},
            )
        bucket.append(now)

    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
    if path.startswith("/api/"):
        response.headers["Cache-Control"] = "no-store"
    response.headers["Cross-Origin-Opener-Policy"] = "same-origin"
    if settings.environment == "production":
        response.headers["Strict-Transport-Security"] = "max-age=63072000; includeSubDomains"
    return response


app.include_router(routes_twin.router)
app.include_router(routes_optimizer.router)
app.include_router(routes_agent.router)
app.include_router(routes_esg.router)


@app.get("/")
async def root():
    return {
        "service": "GridPulse AI API",
        "status": "running",
        "health": "/api/health",
    }


@app.get("/api/health")
async def health():
    return {"status": "ok", "service": "GridPulse AI"}


@app.get("/api/auth/check", dependencies=[Depends(require_operator)])
async def check_operator_access():
    return {"authenticated": True}


@app.websocket("/ws/telemetry")
async def ws_telemetry(websocket: WebSocket):
    if len(connected_clients) >= 100:
        await websocket.close(code=1013, reason="Telemetry connection limit reached")
        return

    await websocket.accept()
    connected_clients.add(websocket)
    try:
        await websocket.send_text(twin.get_snapshot().model_dump_json())
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        pass
    finally:
        connected_clients.discard(websocket)
