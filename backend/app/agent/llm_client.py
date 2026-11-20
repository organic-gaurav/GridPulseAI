import json
import re
from openai import AsyncOpenAI
from app.config import settings
from app.models.schemas import ConstraintPatch


class LLMClient:
    """Provider-agnostic LLM wrapper with zero-key deterministic NLP fallback."""

    def __init__(self) -> None:
        self.api_key = settings.active_llm_key
        self.base_url = settings.llm_base_url or None
        if settings.groq_api_key and not self.base_url:
            self.base_url = "https://api.groq.com/openai/v1"
        elif settings.gemini_api_key and not self.base_url:
            self.base_url = "https://generativelanguage.googleapis.com/v1beta/openai/"

        self.client = (
            AsyncOpenAI(api_key=self.api_key, base_url=self.base_url) if self.api_key else None
        )

    async def compile_policy(self, message: str) -> ConstraintPatch:
        if self.client:
            try:
                resp = await self.client.chat.completions.create(
                    model=settings.llm_model,
                    response_format={"type": "json_object"},
                    messages=[
                        {
                            "role": "system",
                            "content": (
                                "You are GridPulse AI's Neuro-Symbolic Policy Compiler. "
                                "Convert the operator's natural-language request into a JSON object matching: "
                                '{"zone_temp_overrides": {"Zone A": {"t_min": 21.0, "t_max": 24.0}}, '
                                '"ev_target_overrides": {"EV-1": {"departure_hour": 16, "target_kwh": 45.0}}, '
                                '"battery_min_soc_pct": 25.0, "pareto_alpha": 0.2, "shed_deferrable": false, '
                                '"summary": "short explanation"}. Omit null fields.'
                            ),
                        },
                        {"role": "user", "content": message},
                    ],
                    temperature=0.1,
                )
                raw = resp.choices[0].message.content or "{}"
                return ConstraintPatch(**json.loads(raw))
            except Exception:
                pass

        return self._deterministic_parse(message)

    def _deterministic_parse(self, message: str) -> ConstraintPatch:
        msg = message.lower()
        patch = ConstraintPatch(summary=f"Parsed policy: {message}")

        # Carbon-first / Cost-first detection
        if any(k in msg for k in ["carbon", "green", "zero", "clean", "esg"]):
            patch.pareto_alpha = 0.1
            patch.summary = "Prioritize Carbon-Zero dispatch (alpha=0.10)"
        elif any(k in msg for k in ["cost", "cheap", "save money", "tariff", "bill"]):
            patch.pareto_alpha = 0.9
            patch.summary = "Prioritize Cost-First dispatch (alpha=0.90)"

        # Battery reserve floor
        soc_match = re.search(r"(\d{2})\s*%.*(battery|reserve|soc|backup)", msg) or re.search(
            r"(battery|reserve|soc|backup).*?(\d{2})\s*%", msg
        )
        if soc_match:
            val = int(next(g for g in soc_match.groups() if g and g.isdigit()))
            patch.battery_min_soc_pct = float(max(15, min(80, val)))
            patch.summary = f"Set BESS minimum reserve floor to {patch.battery_min_soc_pct}%"

        # Zone temperature overrides
        if "zone a" in msg or "office" in msg or "precool" in msg or "widen" in msg or "comfort" in msg:
            if "widen" in msg or "relax" in msg or "26" in msg:
                patch.zone_temp_overrides = {"Zone A": {"t_min": 20.0, "t_max": 26.0}}
                patch.summary = "Widen Zone A comfort band to 20.0–26.0°C"
            elif "precool" in msg or "cool" in msg:
                patch.zone_temp_overrides = {"Zone A": {"t_min": 19.5, "t_max": 23.0}}
                patch.summary = "Pre-cool Zone A (19.5–23.0°C)"
            else:
                patch.zone_temp_overrides = {"Zone A": {"t_min": 21.0, "t_max": 23.5}}
                patch.summary = "Lock Zone A temperature band to 21.0–23.5°C"

        # EV priority
        if "ev" in msg or "fleet" in msg or "charger" in msg or "van" in msg:
            dep_match = re.search(r"(\d{1,2})\s*(pm|am|:00)?", msg)
            dep_hr = 15
            if dep_match:
                hr = int(dep_match.group(1))
                if dep_match.group(2) == "pm" and hr < 12:
                    hr += 12
                dep_hr = max(10, min(22, hr))
            patch.ev_target_overrides = {"EV-1": {"departure_hour": dep_hr, "target_kwh": 55.0}}
            patch.summary = f"Prioritize EV-1 Fleet Van (55 kWh by {dep_hr:02d}:00)"

        # Shed deferrable
        if "shed" in msg or "pause batch" in msg or "curtail" in msg:
            patch.shed_deferrable = True
            patch.summary = "Shed non-critical deferrable batch loads"

        return patch


llm_client = LLMClient()
