from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.db_models import TelemetryRecord
from app.models.schemas import ChaosRequest, ClockControlRequest, TwinSnapshot
from app.services.digital_twin import twin
from app.services.external_feeds import external_feeds

router = APIRouter(prefix="/api/twin", tags=["Digital Twin"])


@router.get("/state", response_model=TwinSnapshot)
async def get_twin_state():
    return twin.get_snapshot()


@router.post("/clock", response_model=TwinSnapshot)
async def control_clock(req: ClockControlRequest, db: AsyncSession = Depends(get_db)):
    if req.tick_seconds is not None:
        twin.tick_seconds = req.tick_seconds
    if req.action == "play":
        twin.is_running = True
    elif req.action == "pause":
        twin.is_running = False
    elif req.action == "step":
        rec = twin.step_hour()
        db.add(TelemetryRecord(**rec))
        await db.commit()
    elif req.action == "reset":
        twin.reset()
        data = await external_feeds.get_24h_forecasts()
        twin.update_external_forecasts(data)
    return twin.get_snapshot()


@router.post("/chaos", response_model=TwinSnapshot)
async def inject_chaos(req: ChaosRequest):
    twin.inject_chaos(req.event)
    return twin.get_snapshot()
