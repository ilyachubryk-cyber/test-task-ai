from functools import lru_cache
from typing import Optional

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Project settings."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )
    
    genesis_username: str = Field(default="", description="GENESIS-Online username")
    genesis_password: str = Field(default="", description="GENESIS-Online password")
    genesis_token: Optional[str] = Field(default=None, description="GENESIS API access token (optional if username/password used)")
    genesis_cpi_code: str = Field(default="61111-0002", description="GENESIS table code for CPI (61111-0002 = months)")
    genesis_language: str = Field(default="en", description="GENESIS API language (e.g. en, de)")
    genesis_base_url: str = Field(
        default="https://www-genesis.destatis.de/genesisWS/rest/2020",
        description="GENESIS REST API base URL",
    )

    
    openai_api_key: Optional[str] = Field(default=None, description="OpenAI API key for AI Analyst")
    openai_model: str = Field(default="gpt-4o-mini", description="OpenAI model for analysis")

    api_host: str = Field(default="0.0.0.0", description="Host for the API server")
    api_port: int = Field(default=8000, ge=1, le=65535, description="Port for the API server")


class CalculationConfig(BaseSettings):
    """Constants used in calculations."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    cpi_base_oct_2001: float = 84.5

    admin_residential_eur_per_unit: float = 250.0
    admin_residential_eur_per_parking: float = 30.0

    admin_commercial_share: float = 0.03

    maintenance_eur_per_sqm: float = 9.5
    maintenance_eur_per_parking: float = 75.0

    rent_loss_risk_residential: float = 0.02
    rent_loss_risk_commercial: float = 0.04

    # LLM (AI Analyst) prompt pieces
    agent_system_prompt: str = Field(
        default=(
            "You are a German real-estate valuation expert. "
            "Explain income-capitalization (Ertragswertverfahren) results in clear, non-technical "
            "language for a financially literate but non-expert user. Keep it under about 400 words. "
            "Write in English, but keep German technical terms like 'Liegenschaftszins' where helpful."
        ),
        description="System prompt for the AI Analyst.",
    )
    agent_user_requirements: str = Field(
        default=(
            "Requirements:\n"
            "1) Explicitly state whether the property was treated as RESIDENTIAL (Wohnen) or "
            "COMMERCIAL (Gewerbe) and how this affected administration costs, maintenance, and the "
            "risk of rent loss.\n"
            "2) Explain that maintenance (and, for residential, administration) costs were adjusted "
            "using the official German Consumer Price Index (VPI) for October of the year before the "
            "purchase date, and briefly what this means for the amounts.\n"
            "3) Clearly compare the theoretical total value from the income approach with the actual "
            "purchase price, and say whether the agreed purchase price is above or below the "
            "theoretical value and by roughly what percentage.\n"
            "4) Structure the answer into short paragraphs or bullet points so that it is easy to scan.\n"
        ),
        description="User-side prompt requirements for the AI Analyst.",
    )

@lru_cache
def get_settings() -> Settings:
    """Cached settings instance."""
    return Settings()

@lru_cache
def get_calculation_config() -> CalculationConfig:
    """Cached calculation config instance."""
    return CalculationConfig()
