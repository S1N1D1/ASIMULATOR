"""
pages.py — Page renderers for the Acacus MNVR simulator (Stage 2 MVP).

Each render_* function takes the loaded ProjectData and (where needed) the
current ScenarioInputs held in st.session_state. Pages are deliberately thin:
all maths lives in core/, all visuals in ui/charts.py and ui/components.py.

MVP pages: Executive Overview, Cost Simulator, KPI Dashboard,
Phase-Gate Decision, Validation Register, Presentation Mode.
"""
from __future__ import annotations

import pandas as pd
import streamlit as st

from core import calculations as calc
from core.calculations import ScenarioInputs
from core.data_loader import SITES, Evidence, ProjectData
from core.export import export_scenario_xlsx, export_executive_html
from core.gates import GateStatus, build_gates, phase_b_investment_readiness, recommend_phase
from ui import charts
from ui.components import (
    decision_card,
    evidence_badge,
    kpi_card,
    provisional_banner,
    recommendation_banner,
    recommendation_panel,
    section_title,
    status_pill,
    traffic_dot,
)

SITE_NAMES = list(SITES.keys())
PHASES = ["Phase A", "Phase B", "Phase C"]


# ==========================================================================
# Shared scenario state
# ==========================================================================
def get_scenario(data: ProjectData) -> ScenarioInputs:
    if "scenario" not in st.session_state:
        st.session_state.scenario = calc.default_inputs(data)
    return st.session_state.scenario


# ==========================================================================
# 1. Executive Overview
# ==========================================================================
def render_executive(data: ProjectData):
    s = get_scenario(data)
    cost = calc.compute_costs(s)
    margin = calc.compute_margin(s, cost)
    gates = build_gates()
    fin = data.financials

    section_title("Executive Overview",
                  "Acacus MNVR manufacturing relocation — China/UAE to Jordan")
    provisional_banner()

    # Live go/no-go recommendation, derived from current gate state
    rec = recommend_phase(gates, s.annual_volume)
    recommendation_banner(rec)

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        kpi_card("China baseline (landed)", f"${fin.china_landed:,.2f}",
                 "Current contract-mfg cost", accent=charts.THEME["red"],
                 evidence=Evidence.CONFIRMED)
    with c2:
        kpi_card("Jordan base case (landed)", f"${fin.jordan_landed:,.2f}",
                 "Standard-cost build-up", accent=charts.THEME["navy"],
                 evidence=Evidence.CONFIRMED)
    with c3:
        kpi_card("High-volume premium", f"+${fin.jordan_premium_usd:,.2f}",
                 f"{fin.jordan_premium_pct:.1%} vs China (standard cost)",
                 accent=charts.THEME["amber"])
    with c4:
        flag, _ = phase_b_investment_readiness(s.annual_volume, gates["Phase B"])
        kpi_card("Phase B readiness", flag.split(" ")[0],
                 "Evidence-gated", accent=charts.THEME["teal"], provisional=True)

    st.markdown("")
    left, right = st.columns([1.15, 1])
    with left:
        section_title("The decision story", "")
        st.markdown(
            f"""
- **Cost is close, not cheaper.** Jordan's landed cost is **${fin.jordan_landed:,.2f}**
  vs China's **${fin.china_landed:,.2f}** — a **+${fin.jordan_premium_usd:,.2f}
  ({fin.jordan_premium_pct:.1%})** gap on a *high-volume standard-cost* basis.
  This is **not** the operative start-up gap and the case is not won or lost on
  unit cost alone.
- **Volume absorbs overhead.** ${fin.fixed_overhead_year:,.0f}/yr of fixed
  overhead dominates at low volume. The Cost Simulator shows both the absorbed
  standard-cost view and the full-overhead-at-volume view.
- **The real levers are strategic:** lead time to MENA markets, working-capital
  reduction, supply continuity, IP protection, and trade origin (GAFTA /
  Development-Zone), not the 1.7% headline.
- **Phases are evidence-gated.** Phase A (assembly) can start on a portfolio of
  small contracts; Phase B (in-house PCBA) is on **HOLD** until committed volume,
  validated equipment costs and a customs ruling exist.
            """
        )
    with right:
        section_title("Cost premium in context", "")
        st.plotly_chart(charts.two_view_bar(cost, fin.china_landed),
                        use_container_width=True, key="exec_twoview")

    st.markdown("")
    section_title("Phase-gate readiness at a glance", "")
    gcols = st.columns(3)
    for col, (name, g) in zip(gcols, gates.items()):
        with col:
            decision_card(f"{name} — {g.title}", g.decision.value, g.decision_reason)

    st.markdown("")
    recommendation_panel(rec)

    # Export the executive summary (HTML → print to PDF) and the scenario (xlsx)
    st.markdown("")
    e1, e2, _ = st.columns([1.3, 1.3, 1.4])
    with e1:
        st.download_button(
            "⬇ Executive summary (HTML / print to PDF)",
            data=export_executive_html(s, data),
            file_name="acacus_mnvr_executive_summary.html",
            mime="text/html", use_container_width=True)
    with e2:
        st.download_button(
            "⬇ Scenario data (Excel)",
            data=export_scenario_xlsx(s, data),
            file_name="acacus_mnvr_scenario.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True)
    st.caption("The HTML summary opens in any browser; use File → Print → Save as "
               "PDF for a polished one-page handout. All exported figures carry "
               "their provisional status.")


# ==========================================================================
# 2. Cost Simulator
# ==========================================================================
def render_cost_simulator(data: ProjectData):
    s = get_scenario(data)
    fin = data.financials

    section_title("Cost Simulator",
                  "Adjust assumptions; outputs update live. Both cost views shown.")

    with st.sidebar:
        st.markdown("### Cost Simulator controls")
        s.annual_volume = st.slider("Annual volume (units/yr)", 500, 30000,
                                    int(s.annual_volume), step=500)
        s.phase = st.selectbox("Phase", PHASES, index=PHASES.index(s.phase))
        s.site = st.selectbox("Site", SITE_NAMES,
                              index=SITE_NAMES.index(s.site) if s.site in SITE_NAMES else 0)
        st.caption(SITES[s.site]["note"])

        with st.expander("Cost build-up", expanded=False):
            s.bom_cost = st.number_input("BOM cost (USD/unit)", value=float(s.bom_cost), step=1.0)
            s.scrap_pct = st.slider("Scrap / yield loss (%)", 0.0, 0.10,
                                   float(s.scrap_pct), step=0.005)
            s.direct_labour = st.number_input("Direct labour (USD/unit)",
                                             value=float(s.direct_labour), step=0.1)
            s.mfg_overhead = st.number_input("Mfg overhead (USD/unit)",
                                            value=float(s.mfg_overhead), step=0.1)
            s.fixed_overhead_year = st.number_input("Fixed overhead (USD/yr)",
                                                   value=float(s.fixed_overhead_year), step=10000.0)
        with st.expander("Freight & logistics", expanded=False):
            s.inbound_freight = st.number_input("Inbound freight (USD/unit)",
                                               value=float(s.inbound_freight), step=0.1)
            s.outbound_freight = st.number_input("Outbound freight (USD/unit)",
                                                value=float(s.outbound_freight), step=0.1)
            s.sea_share = st.slider("Sea share (rest air)", 0.0, 1.0,
                                   float(s.sea_share), step=0.05)
        with st.expander("Trade, tax & warranty", expanded=False):
            s.warranty_pct = st.slider("Warranty provision (% price)", 0.0, 0.05,
                                      float(s.warranty_pct), step=0.001)
            s.tax_rate = st.slider("Tax rate (%)", 0.0, 0.25, float(s.tax_rate), step=0.01)
            s.dz_benefit = st.checkbox("Development-Zone benefit", value=s.dz_benefit)
            s.gafta_benefit = st.checkbox("GAFTA benefit", value=s.gafta_benefit)
        with st.expander("Financials", expanded=False):
            s.selling_price = st.number_input("Selling price (USD/unit)",
                                             value=float(s.selling_price), step=5.0)
            s.capex = st.number_input("Capex (USD)", value=float(s.capex), step=10000.0)
            s.opex_year = st.number_input("Opex (USD/yr)", value=float(s.opex_year), step=10000.0)
            s.discount_rate = st.slider("Discount rate (%)", 0.0, 0.30,
                                       float(s.discount_rate), step=0.01)

    # Recompute with updated inputs
    cost = calc.compute_costs(s)
    margin = calc.compute_margin(s, cost)
    gates = build_gates()
    flag, why = phase_b_investment_readiness(s.annual_volume, gates["Phase B"])

    # Output cards
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        kpi_card("Landed COGS (standard)", f"${cost.absorbed_standard_cost:,.2f}",
                 "Absorbed standard-cost view", accent=charts.THEME["teal"])
    with c2:
        kpi_card("Fixed OH / unit", f"${cost.fixed_overhead_per_unit:,.2f}",
                 f"@ {s.annual_volume:,} units/yr", accent=charts.THEME["amber"])
    with c3:
        kpi_card("Fully loaded unit cost", f"${cost.fully_loaded_unit_cost:,.2f}",
                 "Full-overhead-at-volume view", accent=charts.THEME["navy"])
    with c4:
        d = cost.delta_vs_china_loaded
        kpi_card("Delta vs China (loaded)", f"{'+' if d>=0 else ''}${d:,.2f}",
                 "Fully loaded vs baseline",
                 accent=charts.THEME["red"] if d > 0 else charts.THEME["green"])

    c5, c6, c7, c8 = st.columns(4)
    with c5:
        kpi_card("Total annual cost", f"${margin.total_annual_cost:,.0f}",
                 "Variable x volume + fixed OH", accent=charts.THEME["navy_light"])
    with c6:
        m = margin.unit_margin
        kpi_card("Unit margin", f"{'+' if m>=0 else ''}${m:,.2f}",
                 "Illustrative price", accent=charts.THEME["teal"], provisional=True)
    with c7:
        kpi_card("Annual contribution", f"${margin.annual_contribution:,.0f}",
                 "Illustrative price", accent=charts.THEME["navy"], provisional=True)
    with c8:
        be = margin.break_even_volume
        kpi_card("Break-even volume", f"{be:,} u/yr" if be else "n/a",
                 "Covers fixed overhead", accent=charts.THEME["amber"])

    st.info(f"**Phase B investment readiness: {flag}** — {why}", icon="🔒")

    st.markdown("")
    left, right = st.columns(2)
    with left:
        section_title("Cost waterfall", "BOM to fully loaded unit cost")
        st.plotly_chart(charts.cost_waterfall(cost), use_container_width=True,
                        key="cs_waterfall")
    with right:
        section_title("Volume absorption curve", "Why volume, not the 1.7%, drives the case")
        curve = calc.volume_cost_curve(s)
        st.plotly_chart(charts.volume_curve(curve, fin.china_landed),
                        use_container_width=True, key="cs_volcurve")

    # Site comparison
    section_title("Site comparison", "Fully loaded unit cost by candidate site")
    site_costs = {}
    for site in SITE_NAMES:
        s2 = ScenarioInputs(**{**s.__dict__, "site": site})
        site_costs[site] = calc.compute_costs(s2).fully_loaded_unit_cost
    st.plotly_chart(charts.site_comparison(site_costs, fin.china_landed),
                    use_container_width=True, key="cs_sites")

    # Export
    st.markdown("")
    blob = export_scenario_xlsx(s, data)
    st.download_button("⬇ Export this scenario to Excel", data=blob,
                       file_name="acacus_mnvr_scenario.xlsx",
                       mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")


# ==========================================================================
# 3. KPI Dashboard
# ==========================================================================
def render_kpi_dashboard(data: ProjectData):
    section_title("KPI Dashboard",
                  "Targets vs simulated values with traffic-light status & evidence")
    provisional_banner()

    # Build the KPI table with pass/fail
    rows = []
    for k in data.kpis:
        cur = k.default_current
        passes = True
        if k.target_value is not None and cur is not None:
            passes = (cur >= k.target_value) if k.direction == "max" else (cur <= k.target_value)
        rows.append({
            "kpi": k, "current": cur, "passes": passes,
            "partial": k.evidence in (Evidence.BENCHMARK, Evidence.DESIGN_ESTIMATE),
        })

    # Summary counts
    npass = sum(1 for r in rows if r["passes"])
    c1, c2, c3 = st.columns(3)
    with c1:
        kpi_card("KPIs tracked", str(len(rows)), "From CTQ/KPI matrix",
                 accent=charts.THEME["navy"])
    with c2:
        kpi_card("Meeting target", f"{npass}/{len(rows)}", "Simulated vs target",
                 accent=charts.THEME["green"])
    with c3:
        nconf = sum(1 for r in rows if r["kpi"].evidence == Evidence.CONFIRMED)
        kpi_card("Confirmed evidence", f"{nconf}/{len(rows)}",
                 "Rest provisional", accent=charts.THEME["amber"])

    st.markdown("")
    # Header row
    h = st.columns([0.5, 2.6, 1.2, 1.2, 0.9, 1.4, 1.0])
    for col, label in zip(h, ["", "KPI", "Target", "Simulated", "Result",
                              "Evidence", "Phase"]):
        col.markdown(f"<div style='font-weight:700;color:#5A6478;font-size:0.78rem;"
                     f"text-transform:uppercase'>{label}</div>", unsafe_allow_html=True)

    for r in rows:
        k = r["kpi"]
        cols = st.columns([0.5, 2.6, 1.2, 1.2, 0.9, 1.4, 1.0])
        cols[0].markdown(traffic_dot(r["passes"], r["partial"]), unsafe_allow_html=True)
        cols[1].markdown(f"**{k.name}**<br><span style='color:#8A94A6;font-size:0.75rem'>"
                         f"{k.unit}</span>", unsafe_allow_html=True)
        cols[2].markdown(f"<span style='font-size:0.85rem'>{k.target_text}</span>",
                         unsafe_allow_html=True)
        cur_txt = f"{r['current']:g}" if r["current"] is not None else "—"
        cols[3].markdown(f"<span style='font-size:0.9rem;font-weight:600'>{cur_txt}</span>",
                         unsafe_allow_html=True)
        res = "PASS" if r["passes"] else "FAIL"
        rc = "#2E8B57" if r["passes"] else "#C8553D"
        cols[4].markdown(f"<span style='color:{rc};font-weight:700;font-size:0.82rem'>"
                         f"{res}</span>", unsafe_allow_html=True)
        cols[5].markdown(evidence_badge(k.evidence), unsafe_allow_html=True)
        cols[6].markdown(f"<span style='font-size:0.8rem'>{k.phase}</span>",
                         unsafe_allow_html=True)
        st.markdown("<hr style='margin:6px 0;border:none;border-top:1px solid #EEF0F4'>",
                    unsafe_allow_html=True)

    st.caption("Traffic light: green = meets target with usable evidence · "
               "amber = benchmark / design-basis (provisional) · red = below target.")


# ==========================================================================
# 4. Phase-Gate Decision
# ==========================================================================
def render_phase_gate(data: ProjectData):
    s = get_scenario(data)
    section_title("Phase-Gate Decision",
                  "Conjunctive logic: one critical requirement fails → HOLD")
    provisional_banner()

    gates = build_gates()

    # Entry-state recommendation banner (before any live toggles this session)
    rec_entry = recommend_phase(gates, s.annual_volume)
    recommendation_banner(rec_entry)

    st.plotly_chart(charts.gate_matrix(gates), use_container_width=True, key="pg_matrix")

    st.markdown(
        "<div style='background:#F4F6FA;border-radius:8px;padding:10px 14px;"
        "font-size:0.85rem;color:#5A6478;margin-bottom:8px'>"
        "<b>How to read this:</b> each phase lists its requirements. "
        "<b>Critical</b> checks (🔴 marker) can force a HOLD on their own. "
        "Toggle a check to tell the readiness story live — the recommendation "
        "below recomputes immediately.</div>", unsafe_allow_html=True)

    tabs = st.tabs([f"{name} — {g.decision.value}" for name, g in gates.items()])
    for tab, (name, g) in zip(tabs, gates.items()):
        with tab:
            top = st.columns([3, 1])
            with top[0]:
                st.markdown(f"#### {name}: {g.title}")
            with top[1]:
                placeholder = st.empty()  # status pill, filled after toggles

            for i, chk in enumerate(g.checks):
                was_partial = chk.status == GateStatus.PARTIAL  # remember entry state
                cols = st.columns([0.4, 3.2, 1.0, 1.6])
                crit = "🔴" if chk.is_critical else "⚪"
                cols[0].markdown(
                    f"<div title='{'critical' if chk.is_critical else 'non-critical'}'>"
                    f"{crit}</div>", unsafe_allow_html=True)
                cols[1].markdown(
                    f"**{chk.requirement}**<br>"
                    f"<span style='color:#8A94A6;font-size:0.76rem'>{chk.note}</span>",
                    unsafe_allow_html=True)
                cols[2].markdown(evidence_badge(chk.evidence), unsafe_allow_html=True)
                key = f"gate_{name}_{i}"
                val = cols[3].checkbox("Met", value=chk.passes, key=key)
                # Met -> GO. Unmet -> keep PARTIAL if it was a non-critical
                # partial item; otherwise HOLD.
                if val:
                    chk.status = GateStatus.GO
                elif was_partial and not chk.is_critical:
                    chk.status = GateStatus.PARTIAL
                else:
                    chk.status = GateStatus.HOLD

            placeholder.markdown(status_pill(g.decision.value), unsafe_allow_html=True)
            st.markdown("---")
            decision_card(f"{name} decision", g.decision.value, g.decision_reason)

    # Live recommendation panel — reflects any toggles made above
    st.markdown("")
    rec_live = recommend_phase(gates, s.annual_volume)
    recommendation_panel(rec_live)


# ==========================================================================
# 5. Validation Register
# ==========================================================================
def render_validation(data: ProjectData):
    section_title("Validation Register",
                  "Every value, its evidence status, source, and what's needed to confirm")

    # Assemble register rows from across the data model
    reg = []
    for c in data.cost_layers:
        reg.append({"Area": "Cost layer", "Item": f"{c.layer}: {c.component}"[:60],
                    "Value": f"CN ${c.china} / JO ${c.jordan}",
                    "Evidence": c.status, "Phase": "All"})
    for k in data.kpis:
        reg.append({"Area": "KPI / CTQ", "Item": k.name,
                    "Value": k.target_text, "Evidence": k.evidence, "Phase": k.phase})
    for ft in data.freight_trade:
        if ft.item:
            reg.append({"Area": f"Freight/Trade", "Item": f"{ft.topic}: {ft.item}"[:60],
                        "Value": ft.value_text[:40], "Evidence": ft.status, "Phase": "B/C"})

    # Filters
    f1, f2 = st.columns(2)
    with f1:
        ev_filter = st.multiselect("Filter by evidence status",
                                   [e.value for e in Evidence],
                                   default=[e.value for e in Evidence])
    with f2:
        area_filter = st.multiselect("Filter by area",
                                     sorted(set(r["Area"] for r in reg)),
                                     default=sorted(set(r["Area"] for r in reg)))

    filtered = [r for r in reg if r["Evidence"].value in ev_filter and r["Area"] in area_filter]

    # Evidence summary
    counts = {}
    for r in reg:
        counts[r["Evidence"]] = counts.get(r["Evidence"], 0) + 1
    cols = st.columns(len(Evidence))
    for col, ev in zip(cols, Evidence):
        with col:
            kpi_card(ev.value, str(counts.get(ev, 0)), "", evidence=ev)

    st.markdown("")
    # Render table
    h = st.columns([1.2, 3.2, 2.2, 1.5, 0.8])
    for col, label in zip(h, ["Area", "Item", "Value", "Evidence", "Phase"]):
        col.markdown(f"<div style='font-weight:700;color:#5A6478;font-size:0.78rem;"
                     f"text-transform:uppercase'>{label}</div>", unsafe_allow_html=True)
    for r in filtered:
        cols = st.columns([1.2, 3.2, 2.2, 1.5, 0.8])
        cols[0].markdown(f"<span style='font-size:0.82rem'>{r['Area']}</span>",
                         unsafe_allow_html=True)
        cols[1].markdown(f"<span style='font-size:0.82rem'>{r['Item']}</span>",
                         unsafe_allow_html=True)
        cols[2].markdown(f"<span style='font-size:0.82rem;color:#5A6478'>{r['Value']}</span>",
                         unsafe_allow_html=True)
        cols[3].markdown(evidence_badge(r["Evidence"]), unsafe_allow_html=True)
        cols[4].markdown(f"<span style='font-size:0.8rem'>{r['Phase']}</span>",
                         unsafe_allow_html=True)
        st.markdown("<hr style='margin:5px 0;border:none;border-top:1px solid #EEF0F4'>",
                    unsafe_allow_html=True)

    st.caption(f"Showing {len(filtered)} of {len(reg)} register entries. "
               "Confirmed items may back final figures; all others are provisional.")


# ==========================================================================
# 6. Presentation Mode
# ==========================================================================
def render_presentation(data: ProjectData):
    s = get_scenario(data)
    cost = calc.compute_costs(s)
    fin = data.financials
    gates = build_gates()

    if "slide" not in st.session_state:
        st.session_state.slide = 0

    slides = _presentation_slides(data, s, cost, gates)
    n = len(slides)
    idx = st.session_state.slide % n

    # Nav
    nav = st.columns([1, 1, 6, 1])
    if nav[0].button("← Prev", use_container_width=True):
        st.session_state.slide = (idx - 1) % n
        st.rerun()
    if nav[1].button("Next →", use_container_width=True):
        st.session_state.slide = (idx + 1) % n
        st.rerun()
    nav[3].markdown(f"<div style='text-align:right;color:#8A94A6;font-weight:600'>"
                    f"{idx+1} / {n}</div>", unsafe_allow_html=True)

    slides[idx]()


def _presentation_slides(data, s, cost, gates):
    fin = data.financials

    def slide_title():
        st.markdown(
            f"""
            <div style='text-align:center;padding:48px 20px'>
              <div style='color:#8A94A6;font-size:0.9rem;letter-spacing:0.15em;
              text-transform:uppercase'>DMADV Feasibility Study</div>
              <div style='font-size:2.4rem;font-weight:800;color:#1F3A5F;
              margin-top:10px;line-height:1.1'>Acacus MNVR Manufacturing<br>
              Relocation to Jordan</div>
              <div style='color:#5A6478;font-size:1.05rem;margin-top:16px'>
              A phased, evidence-gated relocation from China / UAE —
              with Jordan, KSA and UAE as launch markets</div>
            </div>
            """, unsafe_allow_html=True)

    def slide_cost():
        section_title("1 · Cost is close, not cheaper")
        c1, c2, c3 = st.columns(3)
        with c1:
            kpi_card("China baseline", f"${fin.china_landed:,.2f}", "Landed",
                     accent=charts.THEME["red"])
        with c2:
            kpi_card("Jordan base case", f"${fin.jordan_landed:,.2f}", "Landed",
                     accent=charts.THEME["navy"])
        with c3:
            kpi_card("Premium", f"+${fin.jordan_premium_usd:,.2f}",
                     f"{fin.jordan_premium_pct:.1%} (high-volume std cost)",
                     accent=charts.THEME["amber"])
        st.markdown("> The **+1.7%** is a high-volume standard-cost comparison — "
                    "**not** the operative start-up gap. The case is not defended "
                    "on unit cost alone.")

    def slide_volume():
        section_title("2 · Volume absorbs the overhead")
        curve = calc.volume_cost_curve(s)
        st.plotly_chart(charts.volume_curve(curve, fin.china_landed),
                        use_container_width=True, key="pres_vol")
        st.markdown(f"${fin.fixed_overhead_year:,.0f}/yr of fixed overhead is the "
                    "real driver at low volume — the absorbed view and the "
                    "full-overhead view tell different stories.")

    def slide_tornado():
        section_title("3 · What actually moves the answer")
        st.plotly_chart(charts.tornado(calc.tornado_data(s)),
                        use_container_width=True, key="pres_tornado")
        st.markdown("Volume dwarfs every other lever — including the 1.7% "
                    "standard-cost premium. The case is a volume-and-strategy "
                    "decision, not a unit-cost one.")

    def slide_levers():
        section_title("4 · The real decision levers")
        st.markdown(
            """
- **Lead time** to MENA markets (days, not weeks at sea)
- **Working-capital** reduction from shorter pipelines
- **Supply continuity** and reduced single-region exposure
- **IP protection** for custom items (PMM, harness)
- **Trade origin** — GAFTA 40% rule of origin, Development-Zone incentives
            """
        )

    def slide_gates():
        section_title("5 · Phases are evidence-gated, not calendar-gated")
        gcols = st.columns(3)
        for col, (name, g) in zip(gcols, gates.items()):
            with col:
                decision_card(f"{name}", g.decision.value, g.decision_reason)
        st.markdown("> Phase B stays on **HOLD** until committed volume, validated "
                    "equipment costs and a customs ruling exist — conjunctive logic.")

    def slide_reco():
        section_title("6 · Recommendation")
        rec = recommend_phase(gates, s.annual_volume)
        decision_card(rec.headline, rec.status.value, rec.rationale)
        st.markdown("")
        if rec.headline_conditions:
            st.markdown(f"**{rec.next_phase} proceeds only when these are met together:**")
            for i, c in enumerate(rec.headline_conditions, 1):
                st.markdown(f"{i}. {c}")
        st.markdown(
            "\n*Phase C follows once the local supplier base and non-Chinese "
            "component variants are qualified. Each phase is a gate, not a date — "
            "NPV, IRR, payback, GAFTA and Development-Zone benefits remain "
            "provisional until evidence is confirmed.*")

    return [slide_title, slide_cost, slide_volume, slide_tornado,
            slide_levers, slide_gates, slide_reco]


# ==========================================================================
# 7. Sensitivity Analysis (Stage 3)
# ==========================================================================
def render_sensitivity(data: ProjectData):
    s = get_scenario(data)
    cb = data.financials.china_landed

    section_title("Sensitivity Analysis",
                  "Which assumptions move the answer — and by how much")
    provisional_banner()

    metric_label = "Fully loaded unit cost (USD/unit)"

    # --- Tornado (headline) ---
    section_title("Tornado — what matters most", "")
    st.markdown("<div style='color:#5A6478;font-size:0.86rem;margin-bottom:6px'>"
                "Each bar shows how far the fully loaded unit cost moves when one "
                "driver swings across its plausible range, holding others at base. "
                "Longest bar = biggest lever.</div>", unsafe_allow_html=True)
    st.plotly_chart(charts.tornado(calc.tornado_data(s, "fully_loaded_unit_cost"),
                                   metric_label),
                    use_container_width=True, key="sa_tornado")
    st.info("Volume is the dominant lever — far larger than the 1.7% standard-cost "
            "premium. This is the overhead-absorption story in one chart.", icon="📊")

    # --- One-way ---
    section_title("One-way sensitivity", "Sweep a single driver")
    c1, c2 = st.columns(2)
    with c1:
        driver = st.selectbox("Driver", list(calc.ONE_WAY_DRIVERS.keys()), index=0)
    with c2:
        metric = st.selectbox("Output metric",
                              ["fully_loaded_unit_cost", "delta_vs_china_loaded",
                               "unit_margin", "break_even_volume", "npv"],
                              format_func=lambda m: {
                                  "fully_loaded_unit_cost": "Fully loaded unit cost",
                                  "delta_vs_china_loaded": "Delta vs China (loaded)",
                                  "unit_margin": "Unit margin",
                                  "break_even_volume": "Break-even volume",
                                  "npv": "NPV (provisional)"}[m])
    base_ref = cb if metric == "fully_loaded_unit_cost" else None
    mlabel = {"fully_loaded_unit_cost": "Fully loaded USD/unit",
              "delta_vs_china_loaded": "Delta vs China (USD/unit)",
              "unit_margin": "Unit margin (USD)",
              "break_even_volume": "Break-even volume (units/yr)",
              "npv": "NPV (USD, provisional)"}[metric]
    st.plotly_chart(charts.one_way_line(calc.one_way(s, driver, metric), driver,
                                        mlabel, base_ref),
                    use_container_width=True, key="sa_oneway")

    # --- Two-way heatmap ---
    section_title("Two-way sensitivity heatmap", "Two drivers at once")
    h1, h2 = st.columns(2)
    with h1:
        xlab = st.selectbox("X axis", list(calc.ONE_WAY_DRIVERS.keys()),
                            index=list(calc.ONE_WAY_DRIVERS).index("Annual volume"))
    with h2:
        ylab = st.selectbox("Y axis", list(calc.ONE_WAY_DRIVERS.keys()),
                            index=list(calc.ONE_WAY_DRIVERS).index("BOM cost"))
    if xlab == ylab:
        st.warning("Pick two different drivers for the heatmap.")
    else:
        tw = calc.two_way(s, xlab, ylab, "fully_loaded_unit_cost", n=9)
        st.plotly_chart(charts.two_way_heatmap(tw, "Fully loaded USD/unit", cb),
                        use_container_width=True, key="sa_heatmap")
        st.caption("Teal = lower cost, red = higher. Cells show fully loaded "
                   f"USD/unit; China baseline ${cb:,.0f} for reference.")

    # --- Best / base / worst ---
    section_title("Best / base / worst", "Bundled optimistic vs pessimistic cases")
    bbw = calc.best_base_worst(s, data)
    bcol1, bcol2 = st.columns([1, 1])
    with bcol1:
        st.plotly_chart(charts.best_base_worst_bar(bbw, cb),
                        use_container_width=True, key="sa_bbw")
    with bcol2:
        df = pd.DataFrame({
            "Case": ["Best", "Base", "Worst"],
            "Fully loaded": [f"${bbw[c]['fully_loaded_unit_cost']:,.0f}" for c in ["Best","Base","Worst"]],
            "vs China": [f"{bbw[c]['delta_vs_china_loaded']:+,.0f}" for c in ["Best","Base","Worst"]],
            "Unit margin": [f"${bbw[c]['unit_margin']:,.0f}" for c in ["Best","Base","Worst"]],
            "Break-even": [f"{bbw[c]['break_even_volume']:,}" if bbw[c]['break_even_volume'] else "n/a" for c in ["Best","Base","Worst"]],
        })
        st.dataframe(df, hide_index=True, use_container_width=True)

    # --- Named shock scenarios ---
    section_title("Shock scenarios", "The brief's specific stress tests")
    st.plotly_chart(charts.shock_bar(calc.shock_scenarios(s, data), cb),
                    use_container_width=True, key="sa_shocks")
    st.caption("Note: GAFTA and Development-Zone benefits affect trade origin and "
               "tax — not the landed unit cost directly — so those bars match the "
               "base cost line. Their effect shows in the Financial / trade views.")

    # --- Operational (OEE/FPY) ---
    section_title("Operational shocks — OEE", "Lower availability / performance / FPY")
    st.plotly_chart(charts.oee_bar(calc.operational_shocks()),
                    use_container_width=True, key="sa_oee")

    # --- Site comparison ---
    section_title("Site comparison", "Fully loaded unit cost by candidate site")
    sites = calc.site_sensitivity(s, data, "fully_loaded_unit_cost")
    st.plotly_chart(charts.site_comparison(sites, cb),
                    use_container_width=True, key="sa_sites")


# ==========================================================================
# 8. Scenario Comparison (Stage 3)
# ==========================================================================
def render_scenario_comparison(data: ProjectData):
    s = get_scenario(data)
    cb = data.financials.china_landed

    section_title("Scenario Comparison",
                  "Save the current scenario, tweak, and compare side by side")
    provisional_banner()

    if "saved_scenarios" not in st.session_state:
        st.session_state.saved_scenarios = {}

    # Controls to save current scenario
    c1, c2, c3 = st.columns([2, 1, 1])
    with c1:
        name = st.text_input("Scenario name",
                             value=f"{s.site} · {s.annual_volume:,}u · {s.phase}")
    with c2:
        st.markdown("<div style='height:28px'></div>", unsafe_allow_html=True)
        if st.button("➕ Save current scenario", use_container_width=True):
            st.session_state.saved_scenarios[name] = calc.scenario_summary(s, data)
            st.success(f"Saved “{name}”.")
    with c3:
        st.markdown("<div style='height:28px'></div>", unsafe_allow_html=True)
        if st.button("🗑 Clear all", use_container_width=True):
            st.session_state.saved_scenarios = {}
            st.rerun()

    # Always include the current (live) scenario plus a China reference
    rows = {"➤ Current (live)": calc.scenario_summary(s, data)}
    rows.update(st.session_state.saved_scenarios)

    if len(rows) <= 1 and not st.session_state.saved_scenarios:
        st.info("Adjust inputs on the Cost Simulator, then save scenarios here to "
                "compare them. The current live scenario is always shown.", icon="💡")

    # Build comparison table
    metrics = [
        ("Volume (u/yr)", "volume", "{:,}"),
        ("Site", "site", "{}"),
        ("Phase", "phase", "{}"),
        ("Absorbed COGS", "absorbed_standard_cost", "${:,.0f}"),
        ("Fully loaded", "fully_loaded_unit_cost", "${:,.0f}"),
        ("Fixed OH/unit", "fixed_overhead_per_unit", "${:,.0f}"),
        ("Δ vs China", "delta_vs_china_loaded", "{:+,.0f}"),
        ("Unit margin", "unit_margin", "${:,.0f}"),
        ("Annual contrib.", "annual_contribution", "${:,.0f}"),
        ("Break-even (u/yr)", "break_even_volume", "{:,}"),
        ("Local value add", "local_value_added_pct", "{:.0%}"),
        ("NPV (prov.)", "npv", "${:,.0f}"),
        ("IRR (prov.)", "irr", "{:.1%}"),
        ("Payback yrs (prov.)", "payback_years", "{}"),
    ]
    table = {"Metric": [m[0] for m in metrics]}
    for sc_name, summ in rows.items():
        col = []
        for _, key, fmt in metrics:
            v = summ.get(key)
            if v is None:
                col.append("n/a")
            else:
                try:
                    col.append(fmt.format(v))
                except (ValueError, TypeError):
                    col.append(str(v))
        table[sc_name] = col
    st.dataframe(pd.DataFrame(table), hide_index=True, use_container_width=True)

    # Delta vs China bar across saved scenarios
    if rows:
        section_title("Fully loaded cost across scenarios", "")
        names = list(rows.keys())
        vals = [rows[n]["fully_loaded_unit_cost"] for n in names]
        import plotly.graph_objects as go
        colors = [charts.THEME["navy"] if v <= cb else charts.THEME["amber"] for v in vals]
        fig = go.Figure(go.Bar(x=names, y=vals, marker_color=colors,
                              text=[f"${v:,.0f}" for v in vals], textposition="outside"))
        fig.add_hline(y=cb, line=dict(color=charts.THEME["red"], width=2, dash="dash"),
                      annotation_text=f"China ${cb:,.0f}")
        fig.update_yaxes(title="Fully loaded USD / unit")
        fig.update_xaxes(tickangle=-15)
        fig.update_layout(height=360, font=dict(family="Inter, Arial", color=charts.THEME["ink"]),
                          paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                          margin=dict(l=50, r=24, t=20, b=80))
        fig.update_yaxes(gridcolor=charts.THEME["grid"])
        st.plotly_chart(fig, use_container_width=True, key="sc_compare")


# ==========================================================================
# 9. Capacity & Burn-in Model (Stage 4)
# ==========================================================================
def render_capacity(data: ProjectData):
    s = get_scenario(data)
    cap = calc.compute_capacity(s)
    oee = calc.compute_oee()

    section_title("Capacity & Burn-in Model",
                  "Build rate, burn-in WIP, operators and line sizing vs volume")
    provisional_banner()

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        kpi_card("Daily build rate", f"{cap.daily_build_rate:g} u/day",
                 f"{cap.working_days} working days/yr", accent=charts.THEME["navy"])
    with c2:
        kpi_card("Burn-in rack positions", f"{cap.burn_in_rack_positions:g}",
                 "Daily build × 3-day burn-in", accent=charts.THEME["teal"])
    with c3:
        kpi_card("Burn-in WIP", f"{cap.burn_in_wip:g} units",
                 "Work-in-progress in burn-in", accent=charts.THEME["amber"])
    with c4:
        kpi_card("Direct operators", f"{cap.direct_operators:g}",
                 f"≈{cap.assembly_stations} assembly stations",
                 accent=charts.THEME["navy_light"])

    st.markdown("")
    section_title("How capacity scales with volume", "")
    st.plotly_chart(charts.capacity_vs_volume(s, calc),
                    use_container_width=True, key="cap_curve")
    st.caption("Burn-in rack positions and WIP both equal daily build rate × the "
               "3-day burn-in window. If the burn-in duration changes, this model "
               "updates — capacity is design-basis until proven in a pilot lot.")

    st.markdown("")
    section_title("OEE build-up", "Availability × Performance × Quality")
    o1, o2 = st.columns([1, 1.3])
    with o1:
        kpi_card("Steady-state OEE", f"{oee.oee:.1%}",
                 f"A {oee.availability:.0%} × P {oee.performance:.0%} × Q {oee.quality:.0%}",
                 accent=charts.THEME["teal"], evidence=Evidence.BENCHMARK)
        st.markdown("<div style='color:#5A6478;font-size:0.84rem;margin-top:8px'>"
                    "Year-1 target 75% (ramp) · Year-3 / world-class 85%.</div>",
                    unsafe_allow_html=True)
    with o2:
        st.plotly_chart(charts.oee_bar(calc.operational_shocks()),
                        use_container_width=True, key="cap_oee")


# ==========================================================================
# 10. Local Content & Trade Benefits (Stage 4)
# ==========================================================================
def render_local_content(data: ProjectData):
    s = get_scenario(data)
    cost = calc.compute_costs(s)
    lc = calc.compute_local_content(s, cost, data)

    section_title("Local Content & Trade Benefits",
                  "GAFTA rule-of-origin and Development-Zone thresholds")
    provisional_banner([
        "Local value-added is a design-basis estimate; a customs ruling is "
        "required before any GAFTA or Development-Zone benefit is claimed."])

    c1, c2, c3 = st.columns([1.2, 1, 1])
    with c1:
        section_title("Local value added", "")
        st.plotly_chart(charts.local_content_gauge(
            lc.local_value_added_pct, lc.gafta_threshold, lc.dz_threshold),
            use_container_width=True, key="lc_gauge")
    with c2:
        kpi_card("GAFTA 40% threshold",
                 "PASS" if lc.gafta_pass else "FAIL",
                 f"Local value added {lc.local_value_added_pct:.1%} vs 40%",
                 accent=charts.THEME["green"] if lc.gafta_pass else charts.THEME["red"],
                 provisional=True, evidence=Evidence.BENCHMARK)
    with c3:
        kpi_card("Development-Zone 30% screen",
                 "PASS" if lc.dz_pass else "FAIL",
                 f"Local value added {lc.local_value_added_pct:.1%} vs 30%",
                 accent=charts.THEME["green"] if lc.dz_pass else charts.THEME["red"],
                 provisional=True, evidence=Evidence.EXTERNAL_REQUIRED)

    st.markdown("")
    st.markdown(
        f"""
**Why Phase A does not clear the thresholds.** Phase A is assembly only — the
board, memory, storage and modules arrive finished and imported, so the value
added in Jordan is essentially the conversion cost (labour, overhead, local
handling, and any locally made harness or enclosure). Against a unit value of
about ${cost.fully_loaded_unit_cost:,.0f}, that conversion value is currently
**{lc.local_value_added_pct:.1%}** — below both the 30% Development-Zone screen
and the 40% GAFTA threshold.

**Implication (straight from the report):** Phase A delivers lead time and
continuity, but it does **not** on its own deliver the trade or tax benefits.
The relocation should not be justified to the business on those benefits until a
later phase (in-house PCBA + custom items) raises local content. This is exactly
what the Phase B gate requires a written customs ruling to confirm.
        """
    )

    # Development-zone tax incentives summary
    section_title("Development-Zone incentives (if eligible)", "")
    fin = data.financials
    t1, t2, t3 = st.columns(3)
    with t1:
        kpi_card("Manufacturing income tax", f"{fin.dz_income_tax:.0%}",
                 "Development-Zone rate", accent=charts.THEME["navy"],
                 evidence=Evidence.BENCHMARK)
    with t2:
        kpi_card("Customs / sales tax", f"{fin.dz_customs_exemption:.0%}",
                 "Exemption on inputs/equipment", accent=charts.THEME["teal"],
                 evidence=Evidence.BENCHMARK)
    with t3:
        kpi_card("GAFTA preference", "Tariff relief",
                 "On qualifying MENA exports", accent=charts.THEME["amber"],
                 evidence=Evidence.BENCHMARK)
    st.caption("Source: invest.jo development-zone incentives and Jordan Export "
               "Portal GAFTA matrix (public benchmarks). Eligibility depends on "
               "the customs ruling and meeting the local-content threshold.")


# ==========================================================================
# 11. Site Decision Simulator (Stage 4)
# ==========================================================================
def render_site_decision(data: ProjectData):
    s = get_scenario(data)
    cb = data.financials.china_landed

    section_title("Site Decision Simulator",
                  "TOPSIS short-list and the tax-versus-distance breakpoint")
    provisional_banner([
        "TOPSIS land-cost and incentive inputs are indicative; confirm against "
        "current development-company schedules before committing site capital."])

    scheme = st.radio("Weighting scheme", ["ctq", "entropy", "equal"],
                      format_func=lambda x: {"ctq": "CTQ-priority",
                                             "entropy": "Entropy",
                                             "equal": "Equal weights"}[x],
                      horizontal=True)

    ranking = calc.topsis_ranking(scheme)
    winner = ranking[0]

    st.markdown("")
    decision_card(f"TOPSIS pick under {scheme.upper()} weighting: {winner['site']}",
                  "GO", f"Closeness coefficient {winner['closeness']:.3f}. "
                  f"{winner['note']}")

    st.markdown("")
    section_title("Closeness coefficient by site and weighting scheme", "")
    rbs = {sch: {site: calc.TOPSIS_RESULTS[site][sch][0]
                 for site in calc.TOPSIS_RESULTS} for sch in ["entropy", "ctq", "equal"]}
    st.plotly_chart(charts.topsis_chart(rbs), use_container_width=True, key="site_topsis")

    st.info("**The decision depends on the weighting.** Mafraq wins on entropy "
            "(which concentrates weight on incentives), while Al-Muwaqqar wins on "
            "CTQ-priority and equal weights. The report flags this as a "
            "tax-versus-distance breakpoint to resolve in the financial model — "
            "Mafraq's incentives vs its 65 km distance from the engineering team.",
            icon="⚖️")

    st.markdown("")
    section_title("Cost view: fully loaded unit cost by site", "")
    sites = calc.site_sensitivity(s, data, "fully_loaded_unit_cost")
    st.plotly_chart(charts.site_comparison(sites, cb),
                    use_container_width=True, key="site_cost")
    st.caption("Cost deltas between sites are design-basis facility/logistics "
               "adjustments to the Jordan base case. The TOPSIS decision combines "
               "this with nine other criteria (land, distance, labour, "
               "infrastructure, incentives, expansion, electronics, customs).")

    # Criteria reference
    with st.expander("TOPSIS criteria (Table 2.14)"):
        for cid, label, direction in calc.TOPSIS_CRITERIA:
            arrow = "↑ higher better" if direction == "max" else "↓ lower better"
            st.markdown(f"**{cid}** — {label}  ·  *{arrow}*")


# ==========================================================================
# 12. Financial Model (Stage 4)
# ==========================================================================
def render_financial_model(data: ProjectData):
    s = get_scenario(data)

    section_title("Financial Model",
                  "Multi-year P&L and cash flow — fully provisional")
    provisional_banner([
        "Selling price, capex, opex and discount rate are design-basis "
        "placeholders, NOT booked figures. NPV / IRR / payback move sharply with "
        "the selling-price assumption and must not be presented as final."])

    with st.sidebar:
        st.markdown("### Financial Model controls")
        growth = st.slider("Annual demand growth", 0.0, 0.30, 0.10, step=0.01,
                           help="Year-on-year volume growth across the horizon.")
        s.horizon_years = st.slider("Horizon (years)", 3, 10, int(s.horizon_years))

    fs = calc.financial_schedule(s, data, demand_growth=growth)

    # Headline cards
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        kpi_card(f"{s.horizon_years}-year NPV", f"${fs.npv:,.0f}",
                 f"@ {s.discount_rate:.0%} discount", provisional=True,
                 accent=charts.THEME["green"] if fs.npv >= 0 else charts.THEME["red"])
    with c2:
        irr_txt = f"{fs.irr:.1%}" if fs.irr is not None else "n/a"
        kpi_card("IRR", irr_txt, "Internal rate of return", provisional=True,
                 accent=charts.THEME["navy"])
    with c3:
        pb = f"{fs.payback_years} yrs" if fs.payback_years else "beyond horizon"
        kpi_card("Payback", pb, "Undiscounted", provisional=True,
                 accent=charts.THEME["amber"])
    with c4:
        kpi_card("Selling price (assumed)", f"${s.selling_price:,.0f}",
                 "Illustrative — drives everything", provisional=True,
                 accent=charts.THEME["navy_light"])

    st.warning("**Read this before quoting any number here.** These results are "
               "dominated by the assumed selling price. At the current placeholder "
               f"price of ${s.selling_price:,.0f} and volume "
               f"{s.annual_volume:,}/yr, the model may show losses or gains purely "
               "as a function of that assumption. Change the price on the Cost "
               "Simulator to see the swing. This is why the study treats all "
               "financial returns as provisional and evidence-gated.", icon="⚠️")

    st.markdown("")
    left, right = st.columns(2)
    with left:
        section_title("Annual net & cumulative cash", "")
        st.plotly_chart(charts.financial_cashflow(fs),
                        use_container_width=True, key="fm_cashflow")
    with right:
        section_title("Year-1 P&L waterfall", "")
        st.plotly_chart(charts.financial_waterfall(fs, 0),
                        use_container_width=True, key="fm_waterfall")

    # Full schedule table
    st.markdown("")
    section_title("Year-by-year schedule", "")
    table = {
        "Year": [f"Y{y}" for y in fs.years],
        "Volume": [f"{v:,}" for v in fs.volume],
        "Revenue": [f"${r/1e6:.2f}M" for r in fs.revenue],
        "COGS": [f"${c/1e6:.2f}M" for c in fs.cogs],
        "Gross": [f"${g/1e6:.2f}M" for g in fs.gross],
        "Opex": [f"${o/1e3:.0f}k" for o in fs.opex],
        "EBIT": [f"${e/1e6:.2f}M" for e in fs.ebit],
        "Tax": [f"${t/1e3:.0f}k" for t in fs.tax],
        "Net": [f"${n/1e6:.2f}M" for n in fs.net],
        "Cumulative": [f"${c/1e6:.2f}M" for c in fs.cumulative_fcf],
    }
    st.dataframe(pd.DataFrame(table), hide_index=True, use_container_width=True)
    st.caption(f"Capex of ${s.capex:,.0f} applied at year 1. Tax at "
               f"{s.tax_rate:.0%} (Development-Zone manufacturing rate) on positive "
               "EBIT only. All figures provisional.")
