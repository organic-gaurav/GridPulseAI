import csv
import io
from typing import List
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.db_models import TelemetryRecord
from app.models.schemas import EsgLedgerEntry


async def get_esg_ledger(db: AsyncSession) -> List[EsgLedgerEntry]:
    result = await db.execute(select(TelemetryRecord).order_by(TelemetryRecord.id.desc()).limit(48))
    rows = result.scalars().all()
    entries = []
    for r in reversed(rows):
        entries.append(
            EsgLedgerEntry(
                hour=r.sim_hour,
                opt_grid_kwh=round(r.opt_grid_kw, 2),
                base_grid_kwh=round(r.base_grid_kw, 2),
                pv_kwh=round(r.pv_kw, 2),
                opt_cost_usd=round(r.opt_cost_usd, 2),
                base_cost_usd=round(r.base_cost_usd, 2),
                cost_saved_usd=round(max(0.0, r.base_cost_usd - r.opt_cost_usd), 2),
                opt_carbon_kg=round(r.opt_carbon_kg, 2),
                base_carbon_kg=round(r.base_carbon_kg, 2),
                carbon_avoided_kg=round(max(0.0, r.base_carbon_kg - r.opt_carbon_kg), 2),
            )
        )
    return entries


def ledger_to_csv(entries: List[EsgLedgerEntry]) -> str:
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(
        [
            "Hour",
            "Optimized Grid (kWh)",
            "Baseline Grid (kWh)",
            "Solar PV (kWh)",
            "Optimized Cost ($)",
            "Baseline Cost ($)",
            "Cost Saved ($)",
            "Optimized Carbon (kg CO2eq)",
            "Baseline Carbon (kg CO2eq)",
            "Carbon Avoided (kg CO2eq)",
        ]
    )
    for e in entries:
        writer.writerow(
            [
                e.hour,
                e.opt_grid_kwh,
                e.base_grid_kwh,
                e.pv_kwh,
                e.opt_cost_usd,
                e.base_cost_usd,
                e.cost_saved_usd,
                e.opt_carbon_kg,
                e.base_carbon_kg,
                e.carbon_avoided_kg,
            ]
        )
    return output.getvalue()
