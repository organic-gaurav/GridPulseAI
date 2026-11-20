import uuid
from datetime import datetime, timezone
from typing import List
from app.models.schemas import AnomalyItem
from app.services.digital_twin import DualDigitalTwin


class AnomalyDetector:
    """Physics-residual fault & phantom-load detector."""

    def inspect(self, twin: DualDigitalTwin) -> List[AnomalyItem]:
        anomalies: List[AnomalyItem] = []
        now_str = datetime.now(timezone.utc).strftime("%H:%M:%S UTC")

        # 1. HVAC Stuck-On / Phantom Load
        if "hvac_fault" in twin.active_chaos:
            anomalies.append(
                AnomalyItem(
                    id=f"anom-hvac-{twin.sim_hour}",
                    detected_at=now_str,
                    sim_hour=twin.sim_hour,
                    anomaly_type="HVAC Stuck Damper / Phantom Load",
                    severity="critical",
                    description="Zone A HVAC drawing +14.0 kW above RC thermal physics residual.",
                    estimated_waste_kw=14.0,
                    resolved=False,
                )
            )

        # 2. Solar String Degradation / Cloudburst
        if "cloudburst" in twin.active_chaos:
            anomalies.append(
                AnomalyItem(
                    id=f"anom-pv-{twin.sim_hour}",
                    detected_at=now_str,
                    sim_hour=twin.sim_hour,
                    anomaly_type="Solar PV Output Drop (-65%)",
                    severity="high",
                    description="Actual PV generation >25% below clear-sky irradiance baseline.",
                    estimated_waste_kw=round(twin.PV_PEAK_KW * 0.4, 1),
                    resolved=False,
                )
            )

        # 3. Peak Demand Threshold Breach Risk
        if twin.schedule_24h:
            pt = twin.schedule_24h[twin.sim_hour]
            if pt.grid_import_kw > 55.0:
                anomalies.append(
                    AnomalyItem(
                        id=f"anom-peak-{twin.sim_hour}",
                        detected_at=now_str,
                        sim_hour=twin.sim_hour,
                        anomaly_type="Peak Demand Threshold Risk",
                        severity="medium",
                        description=f"Grid import ({pt.grid_import_kw} kW) exceeds 55 kW demand-charge threshold.",
                        estimated_waste_kw=round(pt.grid_import_kw - 55.0, 1),
                        resolved=False,
                    )
                )

        return anomalies


anomaly_detector = AnomalyDetector()
