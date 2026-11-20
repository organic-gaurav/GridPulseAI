from datetime import datetime, timezone
from sqlalchemy import Boolean, DateTime, Float, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class TelemetryRecord(Base):
    __tablename__ = "telemetry_records"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    sim_hour: Mapped[int] = mapped_column(Integer, index=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))
    opt_grid_kw: Mapped[float] = mapped_column(Float)
    base_grid_kw: Mapped[float] = mapped_column(Float)
    pv_kw: Mapped[float] = mapped_column(Float)
    battery_soc_pct: Mapped[float] = mapped_column(Float)
    opt_cost_usd: Mapped[float] = mapped_column(Float)
    base_cost_usd: Mapped[float] = mapped_column(Float)
    opt_carbon_kg: Mapped[float] = mapped_column(Float)
    base_carbon_kg: Mapped[float] = mapped_column(Float)
    carbon_intensity: Mapped[float] = mapped_column(Float)
    tariff_usd_kwh: Mapped[float] = mapped_column(Float)


class AgentDecisionRecord(Base):
    __tablename__ = "agent_decisions"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))
    title: Mapped[str] = mapped_column(String(200))
    tier: Mapped[int] = mapped_column(Integer)  # 1 = Autonomous, 2 = HITL
    status: Mapped[str] = mapped_column(String(32), default="pending")  # executed, pending, approved, rejected
    rationale: Mapped[str] = mapped_column(Text)
    cost_impact_usd: Mapped[float] = mapped_column(Float, default=0.0)
    carbon_impact_kg: Mapped[float] = mapped_column(Float, default=0.0)
    comfort_impact: Mapped[str] = mapped_column(String(120), default="None")
    trace_json: Mapped[str] = mapped_column(Text, default="{}")
    patch_json: Mapped[str] = mapped_column(Text, default="{}")


class PolicyRecord(Base):
    __tablename__ = "policies"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))
    raw_text: Mapped[str] = mapped_column(Text)
    parsed_json: Mapped[str] = mapped_column(Text)
    active: Mapped[bool] = mapped_column(Boolean, default=True)


class AnomalyRecord(Base):
    __tablename__ = "anomalies"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    detected_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))
    sim_hour: Mapped[int] = mapped_column(Integer)
    anomaly_type: Mapped[str] = mapped_column(String(64))
    severity: Mapped[str] = mapped_column(String(32))
    description: Mapped[str] = mapped_column(Text)
    estimated_waste_kw: Mapped[float] = mapped_column(Float, default=0.0)
    resolved: Mapped[bool] = mapped_column(Boolean, default=False)
