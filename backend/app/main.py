import asyncio
from contextlib import asynccontextmanager
from typing import Set

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

from app.api import routes_agent, routes_esg, routes_optimizer, routes_twin
from app.database import AsyncSessionLocal, init_db
from app.models.db_models import TelemetryRecord
from app.services.digital_twin import twin
from app.services.external_feeds import external_feeds

connected_clients: Set[WebSocket] = set()


async def broadcast_snapshot():
    if not connected_clients:
        return
    payload = twin.get_snapshot().model_dump_json()
    dead = []
    for ws in list(connected_clients):
        try:
            await ws.send_text(payload)
        except Exception:
            dead.append(ws)
    for ws in dead:
        connected_clients.discard(ws)


async def simulation_loop():
    while True:
        await asyncio.sleep(twin.tick_seconds)
        if twin.is_running:
            rec = twin.step_hour()
            async with AsyncSessionLocal() as db:
                db.add(TelemetryRecord(**rec))
                await db.commit()
            await broadcast_snapshot()


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    data = await external_feeds.get_24h_forecasts()
    twin.update_external_forecasts(data)
    task = asyncio.create_task(simulation_loop())
    yield
    task.cancel()


app = FastAPI(title="GridPulse AI", version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(routes_twin.router)
app.include_router(routes_optimizer.router)
app.include_router(routes_agent.router)
app.include_router(routes_esg.router)


@app.get("/api/health")
async def health():
    return {"status": "ok", "service": "GridPulse AI"}


@app.websocket("/ws/telemetry")
async def ws_telemetry(websocket: WebSocket):
    await websocket.accept()
    connected_clients.add(websocket)
    try:
        await websocket.send_text(twin.get_snapshot().model_dump_json())
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        connected_clients.discard(websocket)
    except Exception:
        connected_clients.discard(websocket)
