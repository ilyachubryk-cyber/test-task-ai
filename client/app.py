import datetime
import os
from typing import Any, Dict

import requests
import streamlit as st

API_BASE_URL = os.environ.get("API_BASE_URL", "http://localhost:8000")


def _post_calculation(payload: Dict[str, Any]) -> Dict[str, Any]:
    resp = requests.post(f"{API_BASE_URL}/calculate", json=payload, timeout=30)
    resp.raise_for_status()
    return resp.json()


def main() -> None:
    st.set_page_config(page_title="KPA Tool", layout="centered")
    st.title("KPA Tool")

    with st.form("calc_form"):
        col1, col2 = st.columns(2)

        with col1:
            prop_type_label = st.selectbox(
                "Property Type",
                options=["Residential (Wohnen)", "Commercial (Gewerbe)"],
                index=0,
            )
            if prop_type_label.startswith("Residential"):
                property_type = "residential"
            else:
                property_type = "commercial"

            purchase_date = st.date_input(
                "Purchase Date",
                value=datetime.date.today(),
                format="YYYY-MM-DD",
            )

            actual_purchase_price = st.number_input(
                "Actual Purchase Price (EUR)",
                min_value=0.0,
                step=1000.0,
                value=500000.0,
            )

            monthly_net_cold_rent = st.number_input(
                "Monthly Net Cold Rent (EUR)",
                min_value=0.0,
                step=50.0,
                value=2000.0,
            )

            living_area_sqm = st.number_input(
                "Living / Usable Area (m²)",
                min_value=0.0,
                step=1.0,
                value=100.0,
            )

        with col2:
            num_residential_units = st.number_input(
                "Number of Residential Units",
                min_value=0,
                step=1,
                value=1,
            )
            num_parking_units = st.number_input(
                "Number of Garage / Parking Units",
                min_value=0,
                step=1,
                value=0,
            )

            standard_land_value = st.number_input(
                "Standard Land Value (Bodenrichtwert, EUR/m²)",
                min_value=0.0,
                step=10.0,
                value=800.0,
            )

            plot_area_sqm = st.number_input(
                "Plot Area (Grundstücksfläche, m²)",
                min_value=0.0,
                step=10.0,
                value=500.0,
            )

            remaining_useful_life_years = st.number_input(
                "Remaining Useful Life (Restnutzungsdauer, years)",
                min_value=1,
                step=1,
                value=40,
            )

            property_yield_percent = st.number_input(
                "Property Yield (Liegenschaftszins, % p.a.)",
                min_value=0.1,
                step=0.1,
                value=3.5,
            )

        with_analysis = st.checkbox("Include AI Analyst Insight (requires OpenAI API key)", value=True)

        submitted = st.form_submit_button("Calculate Calc")

    if submitted:
        payload: Dict[str, Any] = {
            "property_type": property_type,
            "purchase_date": purchase_date.isoformat(),
            "actual_purchase_price": actual_purchase_price,
            "monthly_net_cold_rent": monthly_net_cold_rent,
            "living_area_sqm": living_area_sqm,
            "num_residential_units": int(num_residential_units),
            "num_parking_units": int(num_parking_units),
            "standard_land_value_per_sqm": standard_land_value,
            "plot_area_sqm": plot_area_sqm,
            "remaining_useful_life_years": int(remaining_useful_life_years),
            "property_yield_percent": property_yield_percent,
            "with_analysis": with_analysis,
        }

        if property_type == "commercial":
            payload["num_residential_units"] = 0

        try:
            with st.spinner("Contacting backend and fetching CPI from Destatis..."):
                result = _post_calculation(payload)
        except requests.HTTPError as e:
            st.error(f"Backend error: {e.response.text}")
            return
        except Exception as e:
            st.error(f"Unexpected error while calling backend: {e}")
            return

        st.subheader("Key Results")
        col_a, col_b = st.columns(2)
        with col_a:
            st.metric("Land Value (from Purchase Price)", f"{result['land_value_from_purchase_price']:,.0f} €")
            st.metric("Building Value (from Purchase Price)", f"{result['building_value_from_purchase_price']:,.0f} €")
        with col_b:
            st.metric("Land Share", f"{result['land_share_percent']:.1f} %")
            st.metric("Building Share", f"{result['building_share_percent']:.1f} %")

        st.subheader("CPI and Indexing")
        st.markdown(
            f"- **CPI (VPI) October {result['cpi_year']}**: {result['cpi_index']:.1f} "
            f"(basis 2020=100)\n"
            f"- **Index factor vs. October 2001 (84.5)**: {result['index_factor']:.3f}"
        )

        st.subheader("Income and Cost Breakdown (per year)")
        st.write(
            {
                "Land value (Bodenwert) ": f"{result['land_value']:,.0f}",
                "Annual gross income (Rohertrag) ": f"{result['annual_gross_income']:,.0f}",
                "Administration costs (Verwaltungskosten) ": f"{result['admin_costs']:,.0f}",
                "Maintenance (Instandhaltungskosten) ": f"{result['maintenance_costs']:,.0f}",
                "Risk of rent loss (Mietausfallwagnis) ": f"{result['rent_loss_risk']:,.0f}",
                "Total management costs (Bewirtschaftungskosten) ": f"{result['total_management_costs']:,.0f}",
                "Annual net income (Reinertrag) ": f"{result['annual_net_income']:,.0f}",
                "Land interest (Bodenwertverzinsung) ": f"{result['land_interest']:,.0f}",
                "Building net income (Gebäudereinertrag) ": f"{result['building_net_income']:,.0f}",
            }
        )

        st.subheader("Theoretical Values (Income Approach)")
        st.write(
            {
                "Multiplier (Barwertfaktor)": f"{result['multiplier_barwertfaktor']:.3f}",
                "Theoretical building value ": f"{result['theoretical_building_value']:,.0f}",
                "Theoretical total value ": f"{result['theoretical_total_value']:,.0f}",
            }
        )

        if result.get("analysis_text"):
            st.subheader("AI Analyst Insight")
            st.markdown(result["analysis_text"])


if __name__ == "__main__":
    main()

