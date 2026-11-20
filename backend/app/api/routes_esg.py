from typing import List
from fastapi import APIRouter, Depends
from fastapi.responses import PlainTextResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.schemas import EsgLedgerEntry
from app.services.esg_ledger import get_esg_ledger, ledger_to_csv

router = APIRouter(prefix="/api/esg", tags=["ESG Audit"])


@router.get("/ledger", response_model=List[EsgLedgerEntry])
async def fetch_ledger(db: AsyncSession = Depends(get_db)):
    return await get_esg_ledger(db)


@router.get("/export/csv")
async def export_csv(db: AsyncSession = Depends(get_db)):
    entries = await get_esg_ledger(db)
    csv_text = ledger_to_csv(entries)
    return PlainTextResponse(
        content=csv_text,
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=gridpulse_esg_ledger.csv"},
    )
