"""
charts.py — Plotly figure builders for the Acacus MNVR simulator.

All figures use the shared THEME palette and return go.Figure objects so pages
stay declarative. Stage 3 adds tornado and two-way heatmap; the stubs for those
live here too so the import surface is stable.
"""
from __future__ import annotations

import plotly.graph_objects as go

# Shared palette (matches assets/style.css)
THEME = {
    "navy": "#1F3A5F",
    "navy_light": "#2E5A88",
    "teal": "#1B998B",
    "amber": "#E8A33D",
    "red": "#C8553D",
    "green": "#2E8B57",
    "grey": "#8A94A6",
    "grid": "#E6E9EF",
    "ink": "#1A2233",
    "paper": "rgba(0,0,0,0)",
}

_FONT = dict(family="Inter, Segoe UI, Arial, sans-serif", color=THEME["ink"], size=13)


def _base_layout(fig: go.Figure, height: int = 360, title: str = "") -> go.Figure:
    fig.update_layout(
        height=height,
        title=dict(text=title, font=dict(size=15, color=THEME["navy"])) if title else None,
        font=_FONT,
        paper_bgcolor=THEME["paper"],
        plot_bgcolor=THEME["paper"],
        margin=dict(l=50, r=24, t=44 if title else 16, b=44),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )
    fig.update_xaxes(gridcolor=THEME["grid"], zeroline=False)
    fig.update_yaxes(gridcolor=THEME["grid"], zeroline=False)
    return fig


# --------------------------------------------------------------------------
# Cost waterfall: BOM -> ... -> absorbed COGS -> +fixed OH -> fully loaded
# --------------------------------------------------------------------------
def cost_waterfall(cost) -> go.Figure:
    labels = ["BOM", "Scrap", "Labour", "Mfg OH", "Inbound", "Outbound",
              "Warranty", "Std COGS", "Fixed OH/unit", "Fully loaded"]
    measures = ["absolute", "relative", "relative", "relative", "relative",
                "relative", "relative", "total", "relative", "total"]
    values = [
        cost.bom, cost.scrap, cost.direct_labour, cost.mfg_overhead,
        cost.inbound_freight, cost.outbound_freight, cost.warranty,
        cost.absorbed_standard_cost, cost.fixed_overhead_per_unit,
        cost.fully_loaded_unit_cost,
    ]
    fig = go.Figure(go.Waterfall(
        orientation="v",
        measure=measures,
        x=labels,
        y=values,
        text=[f"${v:,.1f}" for v in values],
        textposition="outside",
        connector=dict(line=dict(color=THEME["grey"])),
        increasing=dict(marker=dict(color=THEME["navy_light"])),
        decreasing=dict(marker=dict(color=THEME["teal"])),
        totals=dict(marker=dict(color=THEME["navy"])),
    ))
    return _base_layout(fig, height=380)


# --------------------------------------------------------------------------
# Volume-cost curve: fully loaded vs China baseline across volume
# --------------------------------------------------------------------------
def volume_curve(curve: list[dict], china_baseline: float) -> go.Figure:
    vols = [p["volume"] for p in curve]
    loaded = [p["fully_loaded"] for p in curve]
    absorbed = [p["absorbed_standard"] for p in curve]

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=vols, y=loaded, name="Fully loaded (with fixed OH)",
        mode="lines", line=dict(color=THEME["navy"], width=3)))
    fig.add_trace(go.Scatter(
        x=vols, y=absorbed, name="Absorbed standard COGS",
        mode="lines", line=dict(color=THEME["teal"], width=2, dash="dot")))
    fig.add_hline(y=china_baseline, line=dict(color=THEME["red"], width=2, dash="dash"),
                  annotation_text=f"China baseline ${china_baseline:,.0f}",
                  annotation_position="top right")
    fig.update_xaxes(title="Annual volume (units/yr)")
    fig.update_yaxes(title="USD / unit")
    return _base_layout(fig, height=360)


# --------------------------------------------------------------------------
# Site comparison bar (fully loaded unit cost by site)
# --------------------------------------------------------------------------
def site_comparison(site_costs: dict[str, float], china_baseline: float) -> go.Figure:
    sites = list(site_costs.keys())
    vals = [site_costs[s] for s in sites]
    colors = [THEME["navy"], THEME["navy_light"], THEME["teal"]][:len(sites)]
    fig = go.Figure(go.Bar(
        x=sites, y=vals, marker_color=colors,
        text=[f"${v:,.1f}" for v in vals], textposition="outside"))
    fig.add_hline(y=china_baseline, line=dict(color=THEME["red"], width=2, dash="dash"),
                  annotation_text=f"China ${china_baseline:,.0f}")
    fig.update_yaxes(title="Fully loaded USD / unit")
    return _base_layout(fig, height=340)


# --------------------------------------------------------------------------
# Phase-gate matrix heatmap (checks x status)
# --------------------------------------------------------------------------
def gate_matrix(gates: dict) -> go.Figure:
    """Stacked horizontal bar: pass vs open checks per phase, coloured by decision."""
    phases = list(gates.keys())
    passed = [g.pass_count for g in gates.values()]
    openc = [len(g.checks) - g.pass_count for g in gates.values()]

    fig = go.Figure()
    fig.add_trace(go.Bar(
        y=phases, x=passed, name="Pass", orientation="h",
        marker_color=THEME["green"],
        text=[f"{p} pass" for p in passed], textposition="inside"))
    fig.add_trace(go.Bar(
        y=phases, x=openc, name="Open / fail", orientation="h",
        marker_color=THEME["amber"],
        text=[f"{o} open" for o in openc], textposition="inside"))
    fig.update_layout(barmode="stack")
    fig.update_xaxes(title="Number of gate checks")
    return _base_layout(fig, height=260)


# --------------------------------------------------------------------------
# KPI gauge (single metric, traffic-light coloured)
# --------------------------------------------------------------------------
def kpi_gauge(value: float, target: float, direction: str, unit: str,
              passes: bool) -> go.Figure:
    color = THEME["green"] if passes else THEME["red"]
    hi = max(value, target) * 1.3 if (value or target) else 100
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=value or 0,
        number=dict(suffix=f" {unit}" if unit and len(unit) < 6 else "",
                    font=dict(size=22)),
        gauge=dict(
            axis=dict(range=[0, hi]),
            bar=dict(color=color),
            threshold=dict(line=dict(color=THEME["navy"], width=3),
                           thickness=0.8, value=target or 0),
            bgcolor="white",
            bordercolor=THEME["grid"],
        ),
    ))
    fig.update_layout(height=180, margin=dict(l=20, r=20, t=20, b=10),
                      font=_FONT, paper_bgcolor=THEME["paper"])
    return fig


# --------------------------------------------------------------------------
# Two cost views side by side (absorbed vs fully loaded)
# --------------------------------------------------------------------------
def two_view_bar(cost, china_baseline: float) -> go.Figure:
    cats = ["Absorbed standard\nCOGS", "Fully loaded\n(at volume)"]
    vals = [cost.absorbed_standard_cost, cost.fully_loaded_unit_cost]
    fig = go.Figure(go.Bar(
        x=cats, y=vals,
        marker_color=[THEME["teal"], THEME["navy"]],
        text=[f"${v:,.1f}" for v in vals], textposition="outside"))
    fig.add_hline(y=china_baseline, line=dict(color=THEME["red"], width=2, dash="dash"),
                  annotation_text=f"China ${china_baseline:,.0f}")
    fig.update_yaxes(title="USD / unit")
    return _base_layout(fig, height=320)


# --------------------------------------------------------------------------
# Sensitivity charts (Stage 3)
# --------------------------------------------------------------------------
def one_way_line(points: list[dict], driver: str, metric_label: str,
                 baseline: float | None = None) -> go.Figure:
    xs = [p["x"] for p in points]
    ys = [p["y"] for p in points]
    fig = go.Figure(go.Scatter(x=xs, y=ys, mode="lines",
                               line=dict(color=THEME["navy"], width=3)))
    if baseline is not None:
        fig.add_hline(y=baseline, line=dict(color=THEME["red"], width=2, dash="dash"),
                      annotation_text=f"China ${baseline:,.0f}")
    fig.update_xaxes(title=driver)
    fig.update_yaxes(title=metric_label)
    return _base_layout(fig, height=360)


def tornado(rows: list[dict], metric_label: str = "Fully loaded unit cost (USD)") -> go.Figure:
    drivers = [r["driver"] for r in rows]
    base = rows[0]["base"] if rows else 0
    # Bars span from low to high, centred visually on the base
    low = [r["low"] for r in rows]
    high = [r["high"] for r in rows]
    left = [base - lo for lo in low]      # extends left of base
    right = [hi - base for hi in high]    # extends right of base

    fig = go.Figure()
    fig.add_trace(go.Bar(
        y=drivers, x=[-l for l in left], base=base, orientation="h",
        marker_color=THEME["teal"], name="Downside",
        hovertemplate="%{y}: $%{customdata:.0f}<extra></extra>",
        customdata=low))
    fig.add_trace(go.Bar(
        y=drivers, x=right, base=base, orientation="h",
        marker_color=THEME["navy_light"], name="Upside",
        hovertemplate="%{y}: $%{customdata:.0f}<extra></extra>",
        customdata=high))
    fig.add_vline(x=base, line=dict(color=THEME["ink"], width=2),
                  annotation_text=f"Base ${base:,.0f}", annotation_position="top")
    fig.update_layout(barmode="overlay")
    fig.update_xaxes(title=metric_label)
    return _base_layout(fig, height=max(320, 30 * len(drivers) + 80))


def two_way_heatmap(tw: dict, metric_label: str = "Fully loaded USD/unit",
                    china_baseline: float | None = None) -> go.Figure:
    fig = go.Figure(go.Heatmap(
        x=[f"{v:,.0f}" for v in tw["x"]],
        y=[f"{v:,.0f}" for v in tw["y"]],
        z=tw["z"],
        colorscale=[[0, THEME["teal"]], [0.5, "#FFE08A"], [1, THEME["red"]]],
        colorbar=dict(title=metric_label.split("(")[0].strip()),
        hovertemplate=(f"{tw['x_label']}: %{{x}}<br>{tw['y_label']}: %{{y}}"
                       f"<br>{metric_label}: %{{z}}<extra></extra>"),
    ))
    # Annotate cells
    for j, yv in enumerate(tw["y"]):
        for i, xv in enumerate(tw["x"]):
            fig.add_annotation(x=f"{xv:,.0f}", y=f"{yv:,.0f}", text=f"{tw['z'][j][i]:.0f}",
                               showarrow=False, font=dict(size=9, color="#2A2A2A"))
    fig.update_xaxes(title=tw["x_label"])
    fig.update_yaxes(title=tw["y_label"])
    return _base_layout(fig, height=420)


def best_base_worst_bar(bbw: dict, china_baseline: float) -> go.Figure:
    cats = ["Best", "Base", "Worst"]
    vals = [bbw[c]["fully_loaded_unit_cost"] for c in cats]
    colors = [THEME["green"], THEME["navy"], THEME["red"]]
    fig = go.Figure(go.Bar(x=cats, y=vals, marker_color=colors,
                          text=[f"${v:,.0f}" for v in vals], textposition="outside"))
    fig.add_hline(y=china_baseline, line=dict(color=THEME["ink"], width=2, dash="dash"),
                  annotation_text=f"China ${china_baseline:,.0f}")
    fig.update_yaxes(title="Fully loaded USD / unit")
    return _base_layout(fig, height=340)


def shock_bar(rows: list[dict], china_baseline: float) -> go.Figure:
    names = [r["scenario"] for r in rows]
    vals = [r["fully_loaded"] for r in rows]
    base = vals[0] if vals else 0
    colors = [THEME["navy"] if v <= base else THEME["amber"] for v in vals]
    colors[0] = THEME["teal"]
    fig = go.Figure(go.Bar(y=names, x=vals, orientation="h", marker_color=colors,
                          text=[f"${v:,.0f}" for v in vals], textposition="outside"))
    fig.add_vline(x=china_baseline, line=dict(color=THEME["red"], width=2, dash="dash"),
                  annotation_text=f"China ${china_baseline:,.0f}")
    fig.update_xaxes(title="Fully loaded USD / unit")
    fig.update_yaxes(autorange="reversed")
    return _base_layout(fig, height=380)


def oee_bar(rows: list[dict]) -> go.Figure:
    names = [r["scenario"] for r in rows]
    vals = [r["oee"] * 100 for r in rows]
    colors = [THEME["green"] if v >= 85 else (THEME["amber"] if v >= 75 else THEME["red"])
              for v in vals]
    fig = go.Figure(go.Bar(x=names, y=vals, marker_color=colors,
                          text=[f"{v:.1f}%" for v in vals], textposition="outside"))
    fig.add_hline(y=85, line=dict(color=THEME["navy"], width=2, dash="dash"),
                  annotation_text="World-class 85%")
    fig.add_hline(y=75, line=dict(color=THEME["amber"], width=1, dash="dot"),
                  annotation_text="Year-1 target 75%")
    fig.update_yaxes(title="OEE (%)", range=[0, 100])
    fig.update_xaxes(tickangle=-20)
    return _base_layout(fig, height=360)


# --------------------------------------------------------------------------
# Stage 4 charts
# --------------------------------------------------------------------------
def capacity_vs_volume(s, calc_module, lo: int = 1000, hi: int = 30000,
                       steps: int = 20) -> go.Figure:
    """Daily build rate and burn-in WIP across a volume sweep."""
    vols, daily, wip, ops = [], [], [], []
    span = hi - lo
    for i in range(steps + 1):
        v = int(lo + span * i / steps)
        s2 = calc_module.ScenarioInputs(**{**s.__dict__, "annual_volume": v})
        cap = calc_module.compute_capacity(s2)
        vols.append(v); daily.append(cap.daily_build_rate)
        wip.append(cap.burn_in_wip); ops.append(cap.direct_operators)
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=vols, y=daily, name="Daily build rate (u/day)",
                             line=dict(color=THEME["navy"], width=3)))
    fig.add_trace(go.Scatter(x=vols, y=wip, name="Burn-in WIP (units)",
                             line=dict(color=THEME["teal"], width=2, dash="dot")))
    fig.add_trace(go.Scatter(x=vols, y=ops, name="Direct operators",
                             line=dict(color=THEME["amber"], width=2), yaxis="y2"))
    fig.update_layout(
        yaxis=dict(title="Units"),
        yaxis2=dict(title="Operators", overlaying="y", side="right", showgrid=False))
    fig.update_xaxes(title="Annual volume (units/yr)")
    return _base_layout(fig, height=380)


def local_content_gauge(lva_pct: float, gafta: float, dz: float) -> go.Figure:
    """Local value-added with GAFTA (40%) and DZ (30%) threshold markers."""
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=lva_pct * 100,
        number=dict(suffix="%", font=dict(size=26)),
        gauge=dict(
            axis=dict(range=[0, 60]),
            bar=dict(color=THEME["navy"]),
            steps=[
                dict(range=[0, dz * 100], color="#FBE9E7"),
                dict(range=[dz * 100, gafta * 100], color="#FFF3D6"),
                dict(range=[gafta * 100, 60], color="#E3F2E9"),
            ],
            threshold=dict(line=dict(color=THEME["red"], width=3),
                           thickness=0.85, value=gafta * 100),
        ),
    ))
    fig.update_layout(height=260, margin=dict(l=30, r=30, t=30, b=10),
                      font=_FONT, paper_bgcolor=THEME["paper"])
    return fig


def topsis_chart(rows_by_scheme: dict) -> go.Figure:
    """Grouped bars: closeness coefficient per site across weighting schemes."""
    schemes = ["entropy", "ctq", "equal"]
    labels = {"entropy": "Entropy", "ctq": "CTQ-priority", "equal": "Equal"}
    sites = list(rows_by_scheme["ctq"].keys()) if isinstance(rows_by_scheme, dict) else []
    fig = go.Figure()
    colors = {"entropy": THEME["amber"], "ctq": THEME["navy"], "equal": THEME["teal"]}
    for sch in schemes:
        vals = [rows_by_scheme[sch][site] for site in sites]
        fig.add_trace(go.Bar(name=labels[sch], x=sites, y=vals,
                             marker_color=colors[sch],
                             text=[f"{v:.3f}" for v in vals], textposition="outside"))
    fig.update_layout(barmode="group")
    fig.update_yaxes(title="TOPSIS closeness coefficient")
    return _base_layout(fig, height=380)


def financial_cashflow(fs) -> go.Figure:
    """Bar of annual net + line of cumulative cash flow."""
    yrs = [f"Y{y}" for y in fs.years]
    fig = go.Figure()
    colors = [THEME["green"] if n >= 0 else THEME["red"] for n in fs.net]
    fig.add_trace(go.Bar(x=yrs, y=fs.net, name="Net (after-tax)",
                         marker_color=colors,
                         text=[f"${n/1e6:.2f}M" for n in fs.net], textposition="outside"))
    fig.add_trace(go.Scatter(x=yrs, y=fs.cumulative_fcf, name="Cumulative cash",
                             line=dict(color=THEME["navy"], width=3), mode="lines+markers"))
    fig.add_hline(y=0, line=dict(color=THEME["grey"], width=1))
    fig.update_yaxes(title="USD")
    return _base_layout(fig, height=380)


def financial_waterfall(fs, year_idx: int = 0) -> go.Figure:
    """Revenue → COGS → opex → tax → net for a chosen year."""
    i = year_idx
    fig = go.Figure(go.Waterfall(
        orientation="v",
        measure=["absolute", "relative", "relative", "relative", "total"],
        x=["Revenue", "COGS", "Opex", "Tax", "Net"],
        y=[fs.revenue[i], -fs.cogs[i], -fs.opex[i], -fs.tax[i], fs.net[i]],
        text=[f"${v/1e6:.2f}M" for v in
              [fs.revenue[i], -fs.cogs[i], -fs.opex[i], -fs.tax[i], fs.net[i]]],
        textposition="outside",
        connector=dict(line=dict(color=THEME["grey"])),
        increasing=dict(marker=dict(color=THEME["navy_light"])),
        decreasing=dict(marker=dict(color=THEME["red"])),
        totals=dict(marker=dict(color=THEME["navy"])),
    ))
    return _base_layout(fig, height=360)
