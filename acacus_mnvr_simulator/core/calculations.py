"""
calculations.py — Pure calculation functions for the Acacus MNVR simulator.

Every function is UI-agnostic and deterministic so the same engine can back a
Streamlit front end now and a Dash/React front end later. Nothing here reads
files or touches Streamlit. All inputs arrive via the ScenarioInputs dataclass.

The two cost views required by the brief are both implemented:
  * absorbed_standard_cost   -> the standard-cost landed view (1.7% high-volume gap)
  * full_overhead_at_volume  -> fixed overhead spread across actual volume
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from core.data_loader import (
    FIXED_ASSUMPTIONS,
    SITES,
    Evidence,
    ProjectData,
)


# --------------------------------------------------------------------------
# Scenario inputs (everything the Cost Simulator controls feed)
# --------------------------------------------------------------------------
@dataclass
class ScenarioInputs:
    annual_volume: int = 5000
    phase: str = "Phase A"
    site: str = "Al-Muwaqqar"

    # Cost build-up (USD/unit unless noted) — defaults filled from data at runtime
    bom_cost: float = 442.78
    scrap_pct: float = 0.02
    direct_labour: float = 5.7
    mfg_overhead: float = 10.4
    fixed_overhead_year: float = 750000.0
    inbound_freight: float = 4.5
    outbound_freight: float = 2.8
    sea_share: float = 0.85          # rest assumed air
    air_premium_per_unit: float = 3.0  # extra USD/unit on the air share
    warranty_pct: float = 0.0        # of selling price

    # Trade / tax
    tax_rate: float = 0.05
    dz_benefit: bool = True
    gafta_benefit: bool = True

    # Financials
    capex: float = 600000.0
    opex_year: float = 250000.0
    discount_rate: float = 0.12
    selling_price: float = 520.0
    horizon_years: int = 5

    # Baseline for deltas
    china_baseline_landed: float = 467.14


def default_inputs(data: ProjectData) -> ScenarioInputs:
    """Construct a default scenario straight from the controlled data."""
    jordan = {c.layer: c for c in data.cost_layers}
    labour = next((c.jordan for c in data.cost_layers if "labour" in c.layer.lower()), 5.7)
    overhead = next((c.jordan for c in data.cost_layers if "manufacturing overhead" in c.layer.lower()), 10.4)
    inbound = next((c.jordan for c in data.cost_layers if "inbound" in c.layer.lower()), 4.5)
    outbound = next((c.jordan for c in data.cost_layers if "outbound" in c.layer.lower()), 2.8)
    return ScenarioInputs(
        bom_cost=data.financials.bom_total,
        direct_labour=labour,
        mfg_overhead=overhead,
        fixed_overhead_year=data.financials.fixed_overhead_year,
        inbound_freight=inbound,
        outbound_freight=outbound,
        tax_rate=data.financials.dz_income_tax,
        discount_rate=FIXED_ASSUMPTIONS["default_discount_rate"]["value"],
        selling_price=FIXED_ASSUMPTIONS["default_selling_price"]["value"],
        capex=FIXED_ASSUMPTIONS["default_capex"]["value"],
        opex_year=FIXED_ASSUMPTIONS["default_opex_year"]["value"],
        horizon_years=int(FIXED_ASSUMPTIONS["project_horizon_years"]["value"]),
        china_baseline_landed=data.financials.china_landed,
    )


# --------------------------------------------------------------------------
# Cost build-up
# --------------------------------------------------------------------------
@dataclass
class CostResult:
    bom: float
    scrap: float
    direct_labour: float
    mfg_overhead: float
    inbound_freight: float
    outbound_freight: float
    warranty: float
    # Views
    absorbed_standard_cost: float        # landed COGS, standard-cost view
    fixed_overhead_per_unit: float
    fully_loaded_unit_cost: float        # standard view + fixed OH/unit
    full_overhead_at_volume: float       # same, but emphasises volume absorption
    # Deltas
    delta_vs_china_standard: float       # absorbed standard vs China baseline
    delta_vs_china_loaded: float         # fully loaded vs China baseline
    # Components used
    freight_blended: float = 0.0


def site_adjustments(site: str) -> tuple[float, float]:
    s = SITES.get(site, {})
    return s.get("overhead_delta", 0.0), s.get("outbound_delta", 0.0)


def compute_costs(s: ScenarioInputs) -> CostResult:
    """Compute the full per-unit cost build-up for one scenario."""
    oh_delta, ob_delta = site_adjustments(s.site)

    scrap = s.bom_cost * s.scrap_pct
    mfg_overhead = s.mfg_overhead + oh_delta
    outbound = s.outbound_freight + ob_delta

    # Blend inbound freight across sea/air mix (air share carries a premium)
    air_share = max(0.0, 1.0 - s.sea_share)
    freight_blended = s.inbound_freight + air_share * s.air_premium_per_unit

    warranty = s.selling_price * s.warranty_pct

    absorbed = (
        s.bom_cost
        + scrap
        + s.direct_labour
        + mfg_overhead
        + freight_blended
        + outbound
        + warranty
    )

    volume = max(1, s.annual_volume)
    fixed_oh_per_unit = s.fixed_overhead_year / volume
    fully_loaded = absorbed + fixed_oh_per_unit

    return CostResult(
        bom=s.bom_cost,
        scrap=scrap,
        direct_labour=s.direct_labour,
        mfg_overhead=mfg_overhead,
        inbound_freight=freight_blended,
        outbound_freight=outbound,
        warranty=warranty,
        absorbed_standard_cost=round(absorbed, 2),
        fixed_overhead_per_unit=round(fixed_oh_per_unit, 2),
        fully_loaded_unit_cost=round(fully_loaded, 2),
        full_overhead_at_volume=round(fully_loaded, 2),
        delta_vs_china_standard=round(absorbed - s.china_baseline_landed, 2),
        delta_vs_china_loaded=round(fully_loaded - s.china_baseline_landed, 2),
        freight_blended=round(freight_blended, 2),
    )


# --------------------------------------------------------------------------
# Margin / contribution / break-even
# --------------------------------------------------------------------------
@dataclass
class MarginResult:
    unit_margin: float
    annual_contribution: float
    total_annual_cost: float
    break_even_volume: Optional[float]
    break_even_note: str = ""


def compute_margin(s: ScenarioInputs, cost: CostResult) -> MarginResult:
    unit_margin = s.selling_price - cost.fully_loaded_unit_cost
    annual_contribution = unit_margin * s.annual_volume
    total_annual_cost = cost.absorbed_standard_cost * s.annual_volume + s.fixed_overhead_year

    # Break-even volume: volume where selling price covers variable + fixed OH/unit.
    variable = cost.absorbed_standard_cost
    contribution_per_unit = s.selling_price - variable
    if contribution_per_unit > 0:
        be = s.fixed_overhead_year / contribution_per_unit
        note = f"Covers ${s.fixed_overhead_year:,.0f} fixed overhead at this price/cost."
    else:
        be = None
        note = "Selling price does not exceed variable cost — no break-even at this price."
    return MarginResult(
        unit_margin=round(unit_margin, 2),
        annual_contribution=round(annual_contribution, 2),
        total_annual_cost=round(total_annual_cost, 2),
        break_even_volume=round(be) if be else None,
        break_even_note=note,
    )


def volume_cost_curve(s: ScenarioInputs, lo: int = 1000, hi: int = 30000,
                      steps: int = 30) -> list[dict]:
    """Fully-loaded unit cost vs China baseline across a volume sweep."""
    out = []
    span = hi - lo
    for i in range(steps + 1):
        v = int(lo + span * i / steps)
        s2 = ScenarioInputs(**{**s.__dict__, "annual_volume": v})
        c = compute_costs(s2)
        out.append({
            "volume": v,
            "fully_loaded": c.fully_loaded_unit_cost,
            "absorbed_standard": c.absorbed_standard_cost,
            "china_baseline": s.china_baseline_landed,
            "delta_loaded": c.delta_vs_china_loaded,
        })
    return out


# --------------------------------------------------------------------------
# Capacity & burn-in
# --------------------------------------------------------------------------
@dataclass
class CapacityResult:
    daily_build_rate: float
    burn_in_rack_positions: float
    burn_in_wip: float
    direct_operators: float
    assembly_stations: int
    working_days: int


def compute_capacity(s: ScenarioInputs) -> CapacityResult:
    wd = int(FIXED_ASSUMPTIONS["working_days_year"]["value"])
    burn_days = int(FIXED_ASSUMPTIONS["burn_in_days"]["value"])
    eff_hours = FIXED_ASSUMPTIONS["effective_labour_hours_year"]["value"]
    hours_per_unit = FIXED_ASSUMPTIONS["annual_labour_hours_per_unit"]["value"]

    daily = s.annual_volume / wd
    rack = daily * burn_days
    wip = daily * burn_days
    annual_labour_hours = s.annual_volume * hours_per_unit
    operators = annual_labour_hours / eff_hours if eff_hours else 0.0
    stations = max(1, round(operators / 2)) if operators else 1

    return CapacityResult(
        daily_build_rate=round(daily, 1),
        burn_in_rack_positions=round(rack),
        burn_in_wip=round(wip),
        direct_operators=round(operators, 1),
        assembly_stations=stations,
        working_days=wd,
    )


# --------------------------------------------------------------------------
# OEE
# --------------------------------------------------------------------------
@dataclass
class OEEResult:
    availability: float
    performance: float
    quality: float
    oee: float


def compute_oee(availability: float | None = None,
                performance: float | None = None,
                quality: float | None = None) -> OEEResult:
    a = availability if availability is not None else FIXED_ASSUMPTIONS["oee_availability"]["value"]
    p = performance if performance is not None else FIXED_ASSUMPTIONS["oee_performance"]["value"]
    q = quality if quality is not None else FIXED_ASSUMPTIONS["oee_quality"]["value"]
    return OEEResult(a, p, q, round(a * p * q, 4))


# --------------------------------------------------------------------------
# Local content & trade thresholds
# --------------------------------------------------------------------------
@dataclass
class LocalContentResult:
    local_value_added_pct: float
    gafta_pass: bool
    gafta_threshold: float
    dz_pass: bool
    dz_threshold: float
    provisional: bool = True


def compute_local_content(s: ScenarioInputs, cost: CostResult,
                          data: ProjectData) -> LocalContentResult:
    """Local value added = non-imported (processing + local) value / total cost.

    With Phase A assembly only, local value added is the conversion work
    (labour + overhead + local handling) over the landed cost. This is a
    design-basis estimate and is always flagged provisional pending a customs
    ruling.
    """
    local_value = (
        cost.direct_labour
        + cost.mfg_overhead
        + cost.outbound_freight
        + cost.fixed_overhead_per_unit
    )
    total = cost.fully_loaded_unit_cost
    lva = (local_value / total) if total else 0.0

    gafta_t = data.financials.gafta_threshold
    dz_t = FIXED_ASSUMPTIONS["dz_local_content_threshold"]["value"]
    return LocalContentResult(
        local_value_added_pct=round(lva, 4),
        gafta_pass=lva >= gafta_t,
        gafta_threshold=gafta_t,
        dz_pass=lva >= dz_t,
        dz_threshold=dz_t,
        provisional=True,
    )


# --------------------------------------------------------------------------
# Financial model: NPV / IRR / payback
# --------------------------------------------------------------------------
@dataclass
class FinanceResult:
    cash_flows: list[float]
    npv: Optional[float]
    irr: Optional[float]
    payback_years: Optional[float]
    provisional: bool = True
    note: str = ""


def _npv(rate: float, flows: list[float]) -> float:
    return sum(cf / ((1 + rate) ** t) for t, cf in enumerate(flows))


def _irr(flows: list[float]) -> Optional[float]:
    """Bisection IRR — robust, no external solver, returns None if no sign change."""
    if not flows or all(f >= 0 for f in flows) or all(f <= 0 for f in flows):
        return None
    lo, hi = -0.9, 5.0
    f_lo, f_hi = _npv(lo, flows), _npv(hi, flows)
    if f_lo * f_hi > 0:
        return None
    for _ in range(200):
        mid = (lo + hi) / 2
        f_mid = _npv(mid, flows)
        if abs(f_mid) < 1e-6:
            return mid
        if f_lo * f_mid < 0:
            hi, f_hi = mid, f_mid
        else:
            lo, f_lo = mid, f_mid
    return (lo + hi) / 2


def compute_finance(s: ScenarioInputs, cost: CostResult,
                    margin: MarginResult) -> FinanceResult:
    """Build a simple n-year cash flow: -capex at t0, then after-tax operating
    cash flow each year. Always provisional (illustrative capex/opex/price)."""
    annual_pretax = margin.annual_contribution - s.opex_year
    after_tax = annual_pretax * (1 - s.tax_rate) if annual_pretax > 0 else annual_pretax

    flows = [-s.capex] + [after_tax] * s.horizon_years
    npv = round(_npv(s.discount_rate, flows), 0)
    irr = _irr(flows)
    irr = round(irr, 4) if irr is not None else None

    # Payback (simple, undiscounted)
    cum = -s.capex
    payback = None
    for yr in range(1, s.horizon_years + 1):
        cum += after_tax
        if cum >= 0:
            prev = cum - after_tax
            payback = round(yr - 1 + (-prev / after_tax), 2) if after_tax else None
            break

    note = ("Illustrative: capex, opex, selling price and discount rate are "
            "design-basis placeholders, not booked figures.")
    return FinanceResult(
        cash_flows=[round(f, 0) for f in flows],
        npv=npv,
        irr=irr,
        payback_years=payback,
        provisional=True,
        note=note,
    )


# --------------------------------------------------------------------------
# Scenario delta helper (for scenario comparison in Stage 3)
# --------------------------------------------------------------------------
def scenario_summary(s: ScenarioInputs, data: ProjectData) -> dict:
    cost = compute_costs(s)
    margin = compute_margin(s, cost)
    cap = compute_capacity(s)
    fin = compute_finance(s, cost, margin)
    lc = compute_local_content(s, cost, data)
    return {
        "volume": s.annual_volume,
        "phase": s.phase,
        "site": s.site,
        "absorbed_standard_cost": cost.absorbed_standard_cost,
        "fully_loaded_unit_cost": cost.fully_loaded_unit_cost,
        "fixed_overhead_per_unit": cost.fixed_overhead_per_unit,
        "delta_vs_china_loaded": cost.delta_vs_china_loaded,
        "unit_margin": margin.unit_margin,
        "annual_contribution": margin.annual_contribution,
        "break_even_volume": margin.break_even_volume,
        "daily_build_rate": cap.daily_build_rate,
        "burn_in_wip": cap.burn_in_wip,
        "direct_operators": cap.direct_operators,
        "npv": fin.npv,
        "irr": fin.irr,
        "payback_years": fin.payback_years,
        "local_value_added_pct": lc.local_value_added_pct,
        "gafta_pass": lc.gafta_pass,
    }


# ==========================================================================
# SENSITIVITY ANALYSIS (Stage 3)
# ==========================================================================
def _clone(s: ScenarioInputs, **overrides) -> ScenarioInputs:
    return ScenarioInputs(**{**s.__dict__, **overrides})


def _metric_value(s: ScenarioInputs, metric: str) -> float:
    """Return a single output metric for a scenario (used by all sensitivities)."""
    cost = compute_costs(s)
    if metric == "fully_loaded_unit_cost":
        return cost.fully_loaded_unit_cost
    if metric == "absorbed_standard_cost":
        return cost.absorbed_standard_cost
    if metric == "delta_vs_china_loaded":
        return cost.delta_vs_china_loaded
    margin = compute_margin(s, cost)
    if metric == "unit_margin":
        return margin.unit_margin
    if metric == "annual_contribution":
        return margin.annual_contribution
    if metric == "break_even_volume":
        return margin.break_even_volume or 0.0
    if metric == "npv":
        fin = compute_finance(s, cost, margin)
        return fin.npv or 0.0
    return cost.fully_loaded_unit_cost


# --- One-way sensitivity: sweep one input, watch one metric -----------------
# Each entry: label -> (attribute, low_factor_or_abs, high, is_factor)
ONE_WAY_DRIVERS = {
    "Annual volume": ("annual_volume", 1000, 30000, False),
    "BOM cost": ("bom_cost", 0.85, 1.15, True),
    "Direct labour": ("direct_labour", 0.7, 1.5, True),
    "Mfg overhead": ("mfg_overhead", 0.7, 1.5, True),
    "Fixed overhead": ("fixed_overhead_year", 0.8, 1.3, True),
    "Inbound freight": ("inbound_freight", 0.5, 2.5, True),
    "Outbound freight": ("outbound_freight", 0.5, 2.0, True),
    "Warranty %": ("warranty_pct", 0.0, 0.015, False),
    "Selling price": ("selling_price", 0.9, 1.15, True),
    "Tax rate": ("tax_rate", 0.0, 0.16, False),
    "Discount rate": ("discount_rate", 0.06, 0.20, False),
}


def one_way(s: ScenarioInputs, driver_label: str, metric: str,
            steps: int = 25) -> list[dict]:
    attr, lo, hi, is_factor = ONE_WAY_DRIVERS[driver_label]
    base = getattr(s, attr)
    lo_v = base * lo if is_factor else lo
    hi_v = base * hi if is_factor else hi
    out = []
    for i in range(steps + 1):
        x = lo_v + (hi_v - lo_v) * i / steps
        if attr in ("annual_volume",):
            x = int(x)
        out.append({"x": x, "y": _metric_value(_clone(s, **{attr: x}), metric)})
    return out


# --- Tornado: low/high swing of each driver around the base -----------------
def tornado_data(s: ScenarioInputs, metric: str = "fully_loaded_unit_cost") -> list[dict]:
    base_val = _metric_value(s, metric)
    rows = []
    for label, (attr, lo, hi, is_factor) in ONE_WAY_DRIVERS.items():
        base = getattr(s, attr)
        lo_v = base * lo if is_factor else lo
        hi_v = base * hi if is_factor else hi
        if attr == "annual_volume":
            lo_v, hi_v = int(lo_v), int(hi_v)
        y_lo = _metric_value(_clone(s, **{attr: lo_v}), metric)
        y_hi = _metric_value(_clone(s, **{attr: hi_v}), metric)
        low_out = min(y_lo, y_hi)
        high_out = max(y_lo, y_hi)
        rows.append({
            "driver": label,
            "low": low_out,
            "high": high_out,
            "base": base_val,
            "swing": abs(high_out - low_out),
        })
    rows.sort(key=lambda r: r["swing"])  # ascending so biggest is at top in barh
    return rows


# --- Two-way sensitivity heatmap --------------------------------------------
def two_way(s: ScenarioInputs, x_label: str, y_label: str,
            metric: str = "fully_loaded_unit_cost", n: int = 9) -> dict:
    xattr, xlo, xhi, xf = ONE_WAY_DRIVERS[x_label]
    yattr, ylo, yhi, yf = ONE_WAY_DRIVERS[y_label]
    xbase, ybase = getattr(s, xattr), getattr(s, yattr)
    xs_lo = xbase * xlo if xf else xlo
    xs_hi = xbase * xhi if xf else xhi
    ys_lo = ybase * ylo if yf else ylo
    ys_hi = ybase * yhi if yf else yhi

    xs = [xs_lo + (xs_hi - xs_lo) * i / (n - 1) for i in range(n)]
    ys = [ys_lo + (ys_hi - ys_lo) * j / (n - 1) for j in range(n)]
    if xattr == "annual_volume":
        xs = [int(v) for v in xs]
    if yattr == "annual_volume":
        ys = [int(v) for v in ys]

    z = []
    for yv in ys:
        row = []
        for xv in xs:
            val = _metric_value(_clone(s, **{xattr: xv, yattr: yv}), metric)
            row.append(round(val, 1))
        z.append(row)
    return {"x": xs, "y": ys, "z": z, "x_label": x_label, "y_label": y_label}


# --- Best / base / worst ----------------------------------------------------
def best_base_worst(s: ScenarioInputs, data: ProjectData) -> dict:
    """Construct optimistic / base / pessimistic bundles and summarise each."""
    best = _clone(s,
                  bom_cost=s.bom_cost * 0.95,
                  inbound_freight=s.inbound_freight * 0.7,
                  outbound_freight=s.outbound_freight * 0.8,
                  mfg_overhead=s.mfg_overhead * 0.85,
                  warranty_pct=0.0,
                  selling_price=s.selling_price * 1.08)
    worst = _clone(s,
                   bom_cost=s.bom_cost * 1.10,
                   inbound_freight=s.inbound_freight * 2.0,
                   outbound_freight=s.outbound_freight * 1.5,
                   mfg_overhead=s.mfg_overhead * 1.3,
                   warranty_pct=0.015,
                   selling_price=s.selling_price * 0.95)
    return {
        "Best": scenario_summary(best, data),
        "Base": scenario_summary(s, data),
        "Worst": scenario_summary(worst, data),
    }


# --- Named shock scenarios (the brief's specific list) ----------------------
def shock_scenarios(s: ScenarioInputs, data: ProjectData) -> list[dict]:
    defs = [
        ("Base case", {}),
        ("Freight shock (sea x2.5)", {"inbound_freight": s.inbound_freight * 2.5}),
        ("Component price +10%", {"bom_cost": s.bom_cost * 1.10}),
        ("Warranty +1.5%", {"warranty_pct": 0.015}),
        ("No GAFTA benefit", {"gafta_benefit": False}),
        ("No Development-Zone benefit", {"dz_benefit": False, "tax_rate": 0.20}),
        ("Delayed Phase B (low vol 1,500)", {"annual_volume": 1500}),
        ("High volume (20,000)", {"annual_volume": 20000}),
    ]
    rows = []
    for name, ov in defs:
        sc = _clone(s, **ov) if ov else s
        summ = scenario_summary(sc, data)
        rows.append({
            "scenario": name,
            "fully_loaded": summ["fully_loaded_unit_cost"],
            "delta_vs_china": summ["delta_vs_china_loaded"],
            "unit_margin": summ["unit_margin"],
            "break_even": summ["break_even_volume"],
        })
    return rows


# --- Lower OEE / FPY effect (operational shocks) ----------------------------
def operational_shocks() -> list[dict]:
    """Show OEE under degraded component performance (illustrative)."""
    scenarios = [
        ("Target (A90/P95/Q99)", 0.90, 0.95, 0.99),
        ("Lower availability (A80)", 0.80, 0.95, 0.99),
        ("Lower performance (P85)", 0.90, 0.85, 0.99),
        ("Lower FPY/quality (Q95)", 0.90, 0.95, 0.95),
        ("Combined degradation", 0.82, 0.88, 0.96),
    ]
    out = []
    for name, a, p, q in scenarios:
        r = compute_oee(a, p, q)
        out.append({"scenario": name, "availability": a, "performance": p,
                    "quality": q, "oee": r.oee})
    return out


# --- Site comparison across a metric ----------------------------------------
def site_sensitivity(s: ScenarioInputs, data: ProjectData,
                     metric: str = "fully_loaded_unit_cost") -> dict:
    from core.data_loader import SITES
    out = {}
    for site in SITES:
        out[site] = _metric_value(_clone(s, site=site), metric)
    return out


# ==========================================================================
# SITE DECISION — TOPSIS results from the report (Stage 4)
# ==========================================================================
# Closeness coefficients and ranks under the three weighting schemes,
# transcribed from the consolidated report (Table 2.20 / 3.16). The decision
# depends on the weighting scheme — the report's "tax-versus-distance breakpoint".
TOPSIS_RESULTS = {
    "KA II Sahab": {
        "entropy": (0.427, 3), "ctq": (0.551, 2), "equal": (0.528, 2),
        "note": "Robust Amman-cluster candidate; strong infrastructure & electronics ecosystem.",
    },
    "Al-Muwaqqar": {
        "entropy": (0.410, 4), "ctq": (0.556, 1), "equal": (0.531, 1),
        "note": "Strongest CTQ / equal-weight candidate; balanced across criteria.",
    },
    "KHBTDA Mafraq": {
        "entropy": (0.579, 1), "ctq": (0.471, 4), "equal": (0.510, 3),
        "note": "Best entropy result (incentive spread); needs tax-vs-distance breakpoint review (65 km from engineering team).",
    },
}

# Raw TOPSIS criteria (Table 2.14): direction min/max and a short label.
TOPSIS_CRITERIA = [
    ("C1", "Land cost (JOD/m²)", "min"),
    ("C2", "Distance to Aqaba (km)", "min"),
    ("C3", "Distance to Amman (km)", "min"),
    ("C4", "Labour availability (1-5)", "max"),
    ("C5", "Labour-cost level (1-5, lower better)", "min"),
    ("C6", "Infrastructure (1-5)", "max"),
    ("C7", "Incentives (1-5)", "max"),
    ("C8", "Expansion (1-5)", "max"),
    ("C9", "Electronics ecosystem (1-5)", "max"),
    ("C10", "Customs / export (1-5)", "max"),
]


def topsis_ranking(scheme: str = "ctq") -> list[dict]:
    """Return sites ranked by closeness under the chosen weighting scheme."""
    rows = []
    for site, d in TOPSIS_RESULTS.items():
        cc, rank = d[scheme]
        rows.append({"site": site, "closeness": cc, "rank": rank, "note": d["note"]})
    rows.sort(key=lambda r: r["rank"])
    return rows


# ==========================================================================
# FINANCIAL MODEL — multi-year schedule (Stage 4)
# ==========================================================================
@dataclass
class FinancialSchedule:
    years: list[int]
    volume: list[int]
    revenue: list[float]
    cogs: list[float]
    gross: list[float]
    opex: list[float]
    ebit: list[float]
    tax: list[float]
    net: list[float]
    capex: list[float]
    free_cash_flow: list[float]
    cumulative_fcf: list[float]
    discounted_fcf: list[float]
    npv: float
    irr: Optional[float]
    payback_years: Optional[float]
    provisional: bool = True


def financial_schedule(s: ScenarioInputs, data: ProjectData,
                       demand_growth: float = 0.0) -> FinancialSchedule:
    """Build a year-by-year P&L and cash-flow schedule over the horizon.

    Volume can grow year-on-year via demand_growth. All figures provisional
    because price/capex/opex/discount-rate are design-basis placeholders.
    """
    cost = compute_costs(s)
    n = s.horizon_years
    years, vol, rev, cogs, gross, opex, ebit, tax, net = ([] for _ in range(9))
    capex, fcf, cum, disc = [], [], [], []

    running_vol = s.annual_volume
    cumulative = -s.capex
    for yr in range(1, n + 1):
        v = int(running_vol)
        r = v * s.selling_price
        # COGS uses absorbed standard cost (variable) + fixed overhead for the year
        variable_cogs = v * cost.absorbed_standard_cost
        c = variable_cogs + s.fixed_overhead_year
        g = r - c
        o = s.opex_year
        e = g - o
        t = e * s.tax_rate if e > 0 else 0.0
        nt = e - t
        cap = s.capex if yr == 1 else 0.0
        f = nt - (cap if yr == 1 else 0.0)
        cumulative += (nt if yr > 1 else (nt - s.capex))
        years.append(yr); vol.append(v); rev.append(r); cogs.append(c)
        gross.append(g); opex.append(o); ebit.append(e); tax.append(t); net.append(nt)
        capex.append(cap); fcf.append(f); cum.append(cumulative)
        disc.append(f / ((1 + s.discount_rate) ** yr))
        running_vol *= (1 + demand_growth)

    npv_val = round(-s.capex + sum(disc) + s.capex - s.capex, 0)  # see note below
    # Clean NPV: -capex at t0 already inside year-1 fcf via cap; so recompute simply:
    flows = [-s.capex] + [net[i] for i in range(n)]
    npv_val = round(_npv(s.discount_rate, flows), 0)
    irr_val = _irr(flows)
    irr_val = round(irr_val, 4) if irr_val is not None else None

    # Payback from cumulative net (undiscounted)
    payback = None
    c2 = -s.capex
    for i in range(n):
        prev = c2
        c2 += net[i]
        if c2 >= 0 and net[i] > 0:
            payback = round(yr_frac(i + 1, prev, net[i]), 2)
            break

    return FinancialSchedule(
        years=years, volume=vol, revenue=rev, cogs=cogs, gross=gross,
        opex=opex, ebit=ebit, tax=tax, net=net, capex=capex,
        free_cash_flow=fcf, cumulative_fcf=cum, discounted_fcf=disc,
        npv=npv_val, irr=irr_val, payback_years=payback, provisional=True,
    )


def yr_frac(year: int, prev_cum: float, this_net: float) -> float:
    return (year - 1) + (-prev_cum / this_net) if this_net else year


if __name__ == "__main__":
    from core.data_loader import load_project_data
    d = load_project_data()
    s = default_inputs(d)
    c = compute_costs(s)
    m = compute_margin(s, c)
    cap = compute_capacity(s)
    fin = compute_finance(s, c, m)
    lc = compute_local_content(s, c, d)
    print(f"Absorbed standard COGS:   ${c.absorbed_standard_cost}")
    print(f"Fixed OH/unit @ {s.annual_volume}: ${c.fixed_overhead_per_unit}")
    print(f"Fully loaded unit cost:   ${c.fully_loaded_unit_cost}")
    print(f"Delta vs China (loaded):  ${c.delta_vs_china_loaded}")
    print(f"Unit margin:              ${m.unit_margin}")
    print(f"Break-even volume:        {m.break_even_volume} units/yr")
    print(f"Daily build / burn-in WIP: {cap.daily_build_rate} / {cap.burn_in_wip}")
    print(f"Direct operators:         {cap.direct_operators}")
    print(f"NPV / IRR / payback:      ${fin.npv:,.0f} / "
          f"{fin.irr:.1%} / {fin.payback_years} yrs" if fin.irr else
          f"NPV ${fin.npv:,.0f} / IRR n/a / payback {fin.payback_years}")
    print(f"Local value added:        {lc.local_value_added_pct:.1%} "
          f"(GAFTA {'PASS' if lc.gafta_pass else 'FAIL'} @ {lc.gafta_threshold:.0%})")
