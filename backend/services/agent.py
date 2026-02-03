import json
from typing import Optional

from openai import OpenAI

from backend.config import CalculationConfig, Settings, get_calculation_config
from backend.schemas.schemas import PropertyType, CalcBreakdown


class AIAnalystService:
    """AI calc analysis using OpenAI."""

    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._client: Optional[OpenAI] = None

    def _client_or_raise(self) -> OpenAI:
        if self._client is None:
            if not self._settings.openai_api_key:
                raise RuntimeError("OPENAI_API_KEY is required for AI Analyst")
            self._client = OpenAI(api_key=self._settings.openai_api_key)
        return self._client

    def generate_analysis(
        self,
        property_type: PropertyType,
        cpi_index: float,
        index_factor: float,
        calc: CalcBreakdown,
    ) -> str:
        """Return a short explanation of the calc (residential/commercial, CPI, comparison)."""
        client = self._client_or_raise()
        cfg: CalculationConfig = get_calculation_config()
        payload = {
            "property_type": property_type.value,
            "cpi_index_prev_year": cpi_index,
            "index_factor_vs_oct_2001": index_factor,
            "calc": calc.model_dump(),
        }
        system = cfg.agent_system_prompt
        user = (
            "Use the following structured data to explain the calc.\n\n"
            f"JSON data:\n{json.dumps(payload, indent=2)}\n\n"
            f"{cfg.agent_user_requirements}"
        )
        response = client.chat.completions.create(
            model=self._settings.openai_model,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            temperature=0.3,
        )
        return response.choices[0].message.content or ""
