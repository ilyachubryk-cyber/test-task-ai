from decimal import Decimal, ROUND_HALF_UP

from backend.config import get_calculation_config
from backend.schemas.schemas import PropertyType, CalcBreakdown, CalcRequest


def _round_eur(value: float) -> float:
    """Round to full euro."""
    return float(Decimal(value).quantize(Decimal("1"), rounding=ROUND_HALF_UP))


def _round_one_decimal(value: float) -> float:
    """Round to one decimal place."""
    return float(Decimal(value).quantize(Decimal("0.1"), rounding=ROUND_HALF_UP))


class CalcService:
    """Standard Income Capitalization Approach (Ertragswertverfahren)."""

    def calculate(
        self,
        request: CalcRequest,
        cpi_index: float,
        index_factor: float,
    ) -> CalcBreakdown:
        """Compute land/building allocation and theoretical values."""
        prop_type = request.property_type
        rent_monthly = request.monthly_net_cold_rent

        land_value = _round_eur(request.standard_land_value_per_sqm * request.plot_area_sqm)
        annual_gross_income = _round_eur(rent_monthly * 12.0)

        admin_costs = self._admin_costs(
            prop_type, index_factor, annual_gross_income,
            request.num_residential_units or 0, request.num_parking_units,
        )
        maintenance_costs = self._maintenance_costs(
            prop_type, index_factor, request.living_area_sqm, request.num_parking_units,
        )
        rent_loss_risk = self._rent_loss_risk(prop_type, annual_gross_income)

        total_management_costs = _round_eur(
            admin_costs + maintenance_costs + rent_loss_risk
        )
        annual_net_income = _round_eur(annual_gross_income - total_management_costs)

        yield_decimal = request.property_yield_percent / 100.0
        land_interest = _round_eur(land_value * yield_decimal)
        building_net_income = _round_eur(annual_net_income - land_interest)

        n = request.remaining_useful_life_years
        multiplier = (
            (1 - (1 + yield_decimal) ** (-n)) / yield_decimal
            if yield_decimal > 0
            else float(n)
        )
        theoretical_building_value = _round_eur(building_net_income * multiplier)
        theoretical_total_value = _round_eur(theoretical_building_value + land_value)

        if theoretical_total_value <= 0:
            building_share_percent = 0.0
            land_share_percent = 0.0
            building_value_from_purchase_price = 0.0
            land_value_from_purchase_price = 0.0
        else:
            building_share_percent = (
                theoretical_building_value / theoretical_total_value * 100.0
            )
            land_share_percent = land_value / theoretical_total_value * 100.0
            building_value_from_purchase_price = _round_eur(
                request.actual_purchase_price * building_share_percent / 100.0
            )
            land_value_from_purchase_price = _round_eur(
                request.actual_purchase_price * land_share_percent / 100.0
            )

        return CalcBreakdown(
            land_value=land_value,
            annual_gross_income=annual_gross_income,
            admin_costs=admin_costs,
            maintenance_costs=maintenance_costs,
            rent_loss_risk=rent_loss_risk,
            total_management_costs=total_management_costs,
            annual_net_income=annual_net_income,
            land_interest=land_interest,
            building_net_income=building_net_income,
            multiplier_barwertfaktor=multiplier,
            theoretical_building_value=theoretical_building_value,
            theoretical_total_value=theoretical_total_value,
            building_share_percent=building_share_percent,
            land_share_percent=land_share_percent,
            building_value_from_purchase_price=building_value_from_purchase_price,
            land_value_from_purchase_price=land_value_from_purchase_price,
        )

    @staticmethod
    def _admin_costs(
        prop_type: PropertyType,
        index_factor: float,
        annual_gross_income: float,
        num_residential_units: int,
        num_parking_units: int,
    ) -> float:
        cfg = get_calculation_config()
        if prop_type == PropertyType.RESIDENTIAL:
            total = (
                cfg.admin_residential_eur_per_unit * num_residential_units
                + cfg.admin_residential_eur_per_parking * num_parking_units
            ) * index_factor
            return _round_eur(total)
        return _round_eur(cfg.admin_commercial_share * annual_gross_income)

    @staticmethod
    def _maintenance_costs(
        prop_type: PropertyType,
        index_factor: float,
        living_area_sqm: float,
        num_parking_units: int,
    ) -> float:
        cfg = get_calculation_config()
        per_m2 = _round_one_decimal(cfg.maintenance_eur_per_sqm * index_factor)
        area_part = per_m2 * living_area_sqm
        parking_per_unit = _round_eur(cfg.maintenance_eur_per_parking * index_factor)
        parking_part = parking_per_unit * num_parking_units
        return _round_eur(area_part + parking_part)

    @staticmethod
    def _rent_loss_risk(prop_type: PropertyType, annual_gross_income: float) -> float:
        cfg = get_calculation_config()
        factor = (
            cfg.rent_loss_risk_residential
            if prop_type == PropertyType.RESIDENTIAL
            else cfg.rent_loss_risk_commercial
        )
        return _round_eur(annual_gross_income * factor)
