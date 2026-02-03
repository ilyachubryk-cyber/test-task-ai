from datetime import date
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field, field_validator


class PropertyType(str, Enum):
    RESIDENTIAL = "residential"
    COMMERCIAL = "commercial"


class CalcRequest(BaseModel):
    property_type: PropertyType = Field(..., description="Residential or commercial")
    purchase_date: date = Field(..., description="Date of property purchase")
    actual_purchase_price: float = Field(..., gt=0)

    monthly_net_cold_rent: float = Field(..., gt=0, description="Net cold rent per month in EUR")
    living_area_sqm: float = Field(..., gt=0, description="Living/usable area in m²")

    num_residential_units: Optional[int] = Field(
        None, ge=0, description="Number of residential units (relevant for residential only)"
    )
    num_parking_units: int = Field(0, ge=0, description="Number of garage/parking units")

    standard_land_value_per_sqm: float = Field(..., gt=0, description="Bodenrichtwert in EUR/m²")
    plot_area_sqm: float = Field(..., gt=0, description="Plot area in m²")

    remaining_useful_life_years: int = Field(..., gt=0, description="Restnutzungsdauer in years")
    property_yield_percent: float = Field(..., gt=0, description="Liegenschaftszins in % p.a.")

    with_analysis: bool = Field(False, description="If true, include AI Analyst Insight text")

    @field_validator("num_residential_units")
    @classmethod
    def validate_units_for_residential(cls, v: Optional[int], info) -> Optional[int]:
        prop_type = info.data.get("property_type")
        if prop_type == PropertyType.RESIDENTIAL and (v is None or v <= 0):
            raise ValueError("num_residential_units must be > 0 for residential properties")
        return v


class CalcBreakdown(BaseModel):
    land_value: float

    annual_gross_income: float
    admin_costs: float
    maintenance_costs: float
    rent_loss_risk: float
    total_management_costs: float
    annual_net_income: float

    land_interest: float
    building_net_income: float

    multiplier_barwertfaktor: float
    theoretical_building_value: float
    theoretical_total_value: float

    building_share_percent: float
    land_share_percent: float

    building_value_from_purchase_price: float
    land_value_from_purchase_price: float


class CalcResponse(CalcBreakdown):
    cpi_index: float
    cpi_year: int
    cpi_month: int
    index_factor: float
    analysis_text: Optional[str] = None

