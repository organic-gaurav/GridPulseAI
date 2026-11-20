import math
import time
from datetime import datetime, timezone
from typing import Dict, List, Tuple
import httpx

from app.config import settings


class ExternalFeedsService:
    """Fetches live 24h weather/solar irradiance and grid carbon intensity with 15-min TTL cache and synthetic fallback."""

    def __init__(self) -> None:
        self._cache_ttl = 900.0  # 15 minutes
        self._last_fetch_ts: float = 0.0
        self._cached_data: Dict | None = None

    async def get_24h_forecasts(self, force_refresh: bool = False) -> Dict:
        now = time.time()
        if not force_refresh and self._cached_data and (now - self._last_fetch_ts) < self._cache_ttl:
            return self._cached_data

        temps, irradiance, weather_src = await self._fetch_open_meteo()
        carbon, carbon_src = await self._fetch_carbon_intensity()

        self._cached_data = {
            "outdoor_temp_c": temps,
            "irradiance_wm2": irradiance,
            "carbon_intensity": carbon,
            "weather_source": weather_src,
            "carbon_source": carbon_src,
            "last_updated": datetime.now(timezone.utc).strftime("%H:%M:%S UTC"),
        }
        self._last_fetch_ts = now
        return self._cached_data

    async def _fetch_open_meteo(self) -> Tuple[List[float], List[float], str]:
        url = "https://api.open-meteo.com/v1/forecast"
        params = {
            "latitude": settings.latitude,
            "longitude": settings.longitude,
            "hourly": "temperature_2m,cloud_cover,shortwave_radiation",
            "forecast_days": 2,
            "timezone": "auto",
        }
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                resp = await client.get(url, params=params)
                resp.raise_for_status()
                data = resp.json()
                hourly = data.get("hourly", {})
                temps = [float(x) for x in hourly.get("temperature_2m", [])[:24]]
                rad = [float(x) for x in hourly.get("shortwave_radiation", [])[:24]]
                if len(temps) == 24 and len(rad) == 24:
                    return temps, rad, "Open-Meteo Live"
        except Exception:
            pass

        # Physics-informed synthetic fallback
        temps = [round(18.0 + 7.5 * math.sin((h - 9) * math.pi / 12), 1) for h in range(24)]
        rad = [round(max(0.0, 820.0 * math.sin((h - 6) * math.pi / 12)), 1) if 6 <= h <= 18 else 0.0 for h in range(24)]
        return temps, rad, "Synthetic Fallback"

    async def _fetch_carbon_intensity(self) -> Tuple[List[float], str]:
        if settings.carbon_provider == "electricity_maps" and settings.electricity_maps_api_key:
            try:
                url = f"https://api.electricitymaps.com/v4/carbon-intensity/forecast?zone={settings.electricity_maps_zone}"
                headers = {"auth-token": settings.electricity_maps_api_key}
                async with httpx.AsyncClient(timeout=5.0) as client:
                    resp = await client.get(url, headers=headers)
                    resp.raise_for_status()
                    data = resp.json()
                    forecast = data.get("forecast", [])[:24]
                    if len(forecast) == 24:
                        return [float(item["carbonIntensity"]) for item in forecast], f"Electricity Maps ({settings.electricity_maps_zone})"
            except Exception:
                pass

        # Default: Great Britain Carbon Intensity API (no key required)
        try:
            now_iso = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:00Z")
            url = f"https://api.carbonintensity.org.uk/intensity/{now_iso}/fw24h"
            async with httpx.AsyncClient(timeout=5.0) as client:
                resp = await client.get(url)
                resp.raise_for_status()
                data = resp.json().get("data", [])
                # UK API returns 30-min slots; sample every 2nd slot for 24 hours
                hourly_vals = []
                for i in range(0, min(len(data), 48), 2):
                    val = data[i].get("intensity", {}).get("forecast") or data[i].get("intensity", {}).get("actual") or 220
                    hourly_vals.append(float(val))
                if len(hourly_vals) == 24:
                    return hourly_vals, "UK Carbon Intensity Live"
        except Exception:
            pass

        # Realistic duck-curve carbon fallback (gCO2eq/kWh)
        fallback = [
            165, 155, 148, 145, 152, 175, 215, 245,
            230, 195, 160, 135, 120, 118, 130, 165,
            225, 290, 325, 310, 275, 235, 200, 180,
        ]
        return [float(x) for x in fallback], "Synthetic Fallback"


external_feeds = ExternalFeedsService()
