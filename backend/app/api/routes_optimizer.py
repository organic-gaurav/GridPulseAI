from fastapi import APIRouter
from app.models.schemas import ParetoUpdateRequest, TwinSnapshot
from app.services.digital_twin import twin

router = APIRouter(prefix="/api/optimizer", tags=["Optimizer"])


@router.post("/pareto", response_model=TwinSnapshot)
async def update_pareto(req: ParetoUpdateRequest):
    twin.pareto_alpha = req.alpha
    twin.reoptimize()
    return twin.get_snapshot()


@router.post("/solve", response_model=TwinSnapshot)
async def force_solve():
    twin.reoptimize()
    return twin.get_snapshot()
