"""
app.py — Entry point for the Acacus MNVR Manufacturing Relocation Simulator.

Run with:  streamlit run app.py

Sidebar navigation routes to the six MVP pages. Core calculation modules are
UI-agnostic so this front end can later be swapped for Dash/React without
touching the maths.
"""
from __future__ import annotations

from pathlib import Path

import streamlit as st

from core.auth import check_password
from core.data_loader import load_project_data
from ui import pages

st.set_page_config(
    page_title="Acacus MNVR Simulator",
    page_icon="🛰️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---- Load theme CSS ----
_CSS = Path(__file__).parent / "assets" / "style.css"
if _CSS.exists():
    st.markdown(f"<style>{_CSS.read_text()}</style>", unsafe_allow_html=True)


# ---- Load controlled data once, with a clear error if missing ----
@st.cache_data(show_spinner="Loading controlled data…")
def _load():
    return load_project_data()


def main():
    # Password gate (no-op if no password is configured in secrets)
    if not check_password():
        st.stop()

    try:
        data = _load()
    except FileNotFoundError as e:
        st.error(f"**Data file missing.** {e}")
        st.stop()
    except Exception as e:  # noqa: BLE001
        st.error(f"**Could not read Approved_data.xlsx.** {e}")
        st.info("Check that the workbook in data/ has the expected sheet names.")
        st.stop()

    # ---- Sidebar brand + nav ----
    with st.sidebar:
        st.markdown(
            """
            <div style='padding:6px 0 10px 0'>
              <div style='font-size:1.15rem;font-weight:800;color:#1F3A5F'>
              🛰️ Acacus MNVR</div>
              <div style='color:#8A94A6;font-size:0.78rem;margin-top:-2px'>
              Relocation Feasibility Simulator</div>
            </div>
            """, unsafe_allow_html=True)

        page = st.radio(
            "Navigate",
            ["Executive Overview", "Cost Simulator", "Sensitivity Analysis",
             "Scenario Comparison", "Capacity & Burn-in", "Local Content & Trade",
             "Site Decision", "Financial Model", "KPI Dashboard",
             "Phase-Gate Decision", "Validation Register", "Presentation Mode"],
            label_visibility="collapsed",
        )
        st.markdown("<hr style='margin:10px 0;border:none;border-top:1px solid #E6E9EF'>",
                    unsafe_allow_html=True)
        st.caption("Data source: **Approved_data.xlsx** (controlled). "
                   "All financial, trade and Phase B outputs are provisional "
                   "until evidence is confirmed.")

    # ---- Route ----
    router = {
        "Executive Overview": pages.render_executive,
        "Cost Simulator": pages.render_cost_simulator,
        "Sensitivity Analysis": pages.render_sensitivity,
        "Scenario Comparison": pages.render_scenario_comparison,
        "Capacity & Burn-in": pages.render_capacity,
        "Local Content & Trade": pages.render_local_content,
        "Site Decision": pages.render_site_decision,
        "Financial Model": pages.render_financial_model,
        "KPI Dashboard": pages.render_kpi_dashboard,
        "Phase-Gate Decision": pages.render_phase_gate,
        "Validation Register": pages.render_validation,
        "Presentation Mode": pages.render_presentation,
    }
    router[page](data)


if __name__ == "__main__":
    main()
