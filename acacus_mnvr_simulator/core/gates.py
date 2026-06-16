"""
gates.py — Phase-gate decision engine for the Acacus MNVR simulator.

Implements evidence-gated (not calendar-gated) Phase A / B / C decisions with
CONJUNCTIVE logic: if any single critical requirement fails, the phase is HOLD,
regardless of how many other requirements pass. This mirrors the report's
GO/HOLD trigger logic.

Each gate check carries:
  * requirement text
  * a default status (GO / HOLD / PARTIAL) reflecting current project evidence
  * the evidence class behind it
  * is_critical — only critical checks can force a HOLD

The UI lets the presenter toggle individual checks to tell the readiness story
live, but the defaults encode the report's current position.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

from core.data_loader import Evidence


class GateStatus(str, Enum):
    GO = "GO"
    HOLD = "HOLD"
    PARTIAL = "PARTIAL"


@dataclass
class GateCheck:
    requirement: str
    status: GateStatus
    evidence: Evidence
    is_critical: bool
    note: str = ""

    @property
    def passes(self) -> bool:
        return self.status == GateStatus.GO


@dataclass
class PhaseGate:
    phase: str
    title: str
    checks: list[GateCheck]

    # ----- conjunctive evaluation -----
    @property
    def critical_checks(self) -> list[GateCheck]:
        return [c for c in self.checks if c.is_critical]

    @property
    def failed_critical(self) -> list[GateCheck]:
        return [c for c in self.critical_checks if not c.passes]

    @property
    def partial_checks(self) -> list[GateCheck]:
        return [c for c in self.checks if c.status == GateStatus.PARTIAL]

    @property
    def decision(self) -> GateStatus:
        """Conjunctive: any failed critical check => HOLD.
        If no critical failures but some checks are partial/non-GO => PARTIAL.
        Only all-GO => GO."""
        if self.failed_critical:
            return GateStatus.HOLD
        if all(c.passes for c in self.checks):
            return GateStatus.GO
        return GateStatus.PARTIAL

    @property
    def pass_count(self) -> int:
        return sum(1 for c in self.checks if c.passes)

    @property
    def decision_reason(self) -> str:
        d = self.decision
        if d == GateStatus.HOLD:
            names = "; ".join(c.requirement for c in self.failed_critical)
            return f"HOLD — critical requirement(s) not met: {names}."
        if d == GateStatus.PARTIAL:
            n = len(self.checks) - self.pass_count
            return (f"PARTIAL — no critical blocker, but {n} requirement(s) "
                    f"still open. Proceed only with documented mitigations.")
        return "GO — all requirements satisfied with current evidence."


# --------------------------------------------------------------------------
# Default gate definitions (encode the report's current readiness position)
# --------------------------------------------------------------------------
def _build_phase_a() -> PhaseGate:
    C, H, P = GateStatus.GO, GateStatus.HOLD, GateStatus.PARTIAL
    checks = [
        GateCheck("Site or interim site available", C, Evidence.DESIGN_ESTIMATE, True,
                  "TOPSIS short-list identified; lease to confirm."),
        GateCheck("UAE transition stock ready", C, Evidence.DESIGN_ESTIMATE, True,
                  "Safety stock (1,000 units) bridges the switch-over."),
        GateCheck("Inbound lane qualified", P, Evidence.BENCHMARK, False,
                  "Freight benchmark only; dual-corridor logistics managed by "
                  "design (secure in parallel, not a Phase A blocker)."),
        GateCheck("Phase A equipment ready", C, Evidence.DESIGN_ESTIMATE, False,
                  "Assembly/test bench within Phase A capex."),
        GateCheck("Burn-in rack capacity sufficient", C, Evidence.DESIGN_ESTIMATE, True,
                  "Sized from daily build rate x 3-day burn-in."),
        GateCheck("Contract cover available", P, Evidence.DESIGN_ESTIMATE, False,
                  "Phase A is sized to break even on a portfolio of small "
                  "contracts (+ optional medium); secured during ramp."),
        GateCheck("ESD and segregation passed", C, Evidence.DESIGN_ESTIMATE, False,
                  "Facility design requirement."),
        GateCheck("Record system ready", C, Evidence.DESIGN_ESTIMATE, False,
                  "ERP/MES timestamps required for lead-time CTQ."),
        GateCheck("Staff trained", P, Evidence.DESIGN_ESTIMATE, False,
                  "Training plan pending site confirmation."),
        GateCheck("OTIF target achievable", C, Evidence.BENCHMARK, False,
                  ">=95% benchmark; to be proven in pilot."),
        GateCheck("RMA response achievable", C, Evidence.DESIGN_ESTIMATE, False,
                  "<=5 day after-sales design target."),
    ]
    return PhaseGate("Phase A", "In-Jordan final assembly", checks)


def _build_phase_b() -> PhaseGate:
    C, H, P = GateStatus.GO, GateStatus.HOLD, GateStatus.PARTIAL
    checks = [
        GateCheck("Medium/large committed volume", H, Evidence.VALIDATION_REQUIRED, True,
                  "Requires committed contract volume to absorb overhead."),
        GateCheck("PCB equipment readiness", H, Evidence.VALIDATION_REQUIRED, True,
                  "In-house SMT/PCBA line not yet procured."),
        GateCheck("SMT FPY evidence", P, Evidence.BENCHMARK, True,
                  "98% target is a benchmark; needs line evidence."),
        GateCheck("BGA voiding evidence", P, Evidence.BENCHMARK, True,
                  "<=25% void target; X-ray evidence required."),
        GateCheck("Customs/local-content ruling", H, Evidence.EXTERNAL_REQUIRED, True,
                  "HS 8521.90 candidate only; broker ruling required."),
        GateCheck("Validated supplier and equipment costs", H, Evidence.VALIDATION_REQUIRED, True,
                  "Standard-cost basis; supplier quotes needed."),
        GateCheck("Overhead absorption at committed volume", P, Evidence.DESIGN_ESTIMATE, True,
                  "Depends on volume; see Cost Simulator volume view."),
        GateCheck("PMM / custom-item readiness", P, Evidence.DESIGN_ESTIMATE, False,
                  "3 custom items (PMM, harness) to be qualified."),
        GateCheck("Development-Zone threshold", P, Evidence.EXTERNAL_REQUIRED, True,
                  "30% local-content screen; ruling required."),
        GateCheck("GAFTA pathway", P, Evidence.BENCHMARK, True,
                  "40% local value-added rule of origin to be evidenced."),
    ]
    return PhaseGate("Phase B", "In-house PCBA + custom items", checks)


def _build_phase_c() -> PhaseGate:
    C, H, P = GateStatus.GO, GateStatus.HOLD, GateStatus.PARTIAL
    checks = [
        GateCheck("Local supplier qualification", H, Evidence.VALIDATION_REQUIRED, True,
                  "Local supply base not yet qualified."),
        GateCheck("Roadmap demand", H, Evidence.VALIDATION_REQUIRED, True,
                  "Requires broader-MENA contract base."),
        GateCheck("Variant testing readiness", P, Evidence.DESIGN_ESTIMATE, False,
                  "Product-variant test capability to be built."),
        GateCheck("Non-China variant readiness", H, Evidence.VALIDATION_REQUIRED, True,
                  "Alternative-origin variant not yet designed."),
        GateCheck("Local-content headroom", P, Evidence.DESIGN_ESTIMATE, True,
                  "Headroom above GAFTA/DZ thresholds required."),
        GateCheck("Wider MENA readiness", P, Evidence.DESIGN_ESTIMATE, False,
                  "Distribution and certification expansion."),
    ]
    return PhaseGate("Phase C", "Deeper local integration", checks)


def build_gates() -> dict[str, PhaseGate]:
    return {
        "Phase A": _build_phase_a(),
        "Phase B": _build_phase_b(),
        "Phase C": _build_phase_c(),
    }


def phase_b_investment_readiness(volume: int, gate_b: PhaseGate) -> tuple[str, str]:
    """Headline Phase B readiness flag used on the Cost Simulator/Exec pages.
    Always provisional because Phase B critical evidence is not yet confirmed."""
    decision = gate_b.decision
    if decision == GateStatus.HOLD:
        return ("HOLD (provisional)",
                "Phase B critical evidence (volume commitment, PCB equipment, "
                "customs ruling, validated costs) is not yet in place.")
    if decision == GateStatus.PARTIAL:
        return ("CONDITIONAL (provisional)",
                "No hard blocker, but several Phase B requirements remain open.")
    return ("READY (provisional)",
            "All modelled Phase B checks pass — confirm with signed evidence "
            "before committing capital.")


# --------------------------------------------------------------------------
# Go / no-go recommendation engine
# --------------------------------------------------------------------------
@dataclass
class Recommendation:
    headline: str            # e.g. "Proceed with Phase A"
    go_phase: str            # highest phase cleared to start ("Phase A" / "None")
    status: GateStatus       # status of the recommended phase
    rationale: str           # one-paragraph why
    next_phase: str          # the phase being held ("Phase B")
    next_blockers: list[str] # critical items blocking the next phase
    parallel_actions: list[str]  # what to pursue now to unlock the next phase
    headline_conditions: list[str] = field(default_factory=list)  # report's named conditions
    provisional: bool = True


def recommend_phase(gates: dict[str, "PhaseGate"], volume: int) -> Recommendation:
    """Derive a go/no-go recommendation from the *current* gate state.

    Logic:
      * The recommended 'go now' phase is the highest phase whose decision is GO,
        or PARTIAL (proceed with documented mitigations).
      * Any phase in HOLD cannot be the recommendation; we name its critical
        blockers and what to pursue in parallel to unlock it.
      * Always provisional, because the whole study is evidence-gated.
    """
    order = ["Phase A", "Phase B", "Phase C"]
    go_phase = "None"
    go_status = GateStatus.HOLD
    for name in order:
        d = gates[name].decision
        if d in (GateStatus.GO, GateStatus.PARTIAL):
            go_phase = name
            go_status = d
        else:
            break  # conjunctive: can't recommend a later phase past a HOLD

    # Identify the next phase being held and its blockers
    next_phase = "Phase B"
    if go_phase == "Phase B":
        next_phase = "Phase C"
    elif go_phase == "Phase C":
        next_phase = "Phase C"  # nothing beyond
    blockers = [c.requirement for c in gates.get(next_phase, gates["Phase B"]).failed_critical]

    # Compose headline + rationale
    if go_phase == "None":
        headline = "Hold — not ready to start any phase"
        rationale = (
            "Even Phase A has an unmet critical requirement under the current "
            "evidence. Resolve the Phase A blockers before committing.")
    else:
        title = gates[go_phase].title
        if go_status == GateStatus.GO:
            headline = f"Proceed with {go_phase}"
            rationale = (
                f"{go_phase} ({title}) clears all of its gate checks with current "
                f"evidence. {next_phase} stays on HOLD until its critical "
                f"requirements are met, so commit only to {go_phase} now and "
                f"pursue {next_phase} evidence in parallel.")
        else:
            headline = f"Proceed with {go_phase} (with mitigations)"
            rationale = (
                f"{go_phase} ({title}) has no critical blocker but some open "
                f"requirements — proceed with documented mitigations. {next_phase} "
                f"remains conditional pending its critical evidence.")

    # Parallel actions: the open critical items on the next phase, phrased as work
    parallel = []
    for c in gates.get(next_phase, gates["Phase B"]).failed_critical:
        parallel.append(f"Secure: {c.requirement.lower()}")
    if not parallel:
        parallel = ["Confirm signed evidence for the modelled checks before committing capital."]

    # The report's three named Phase B conditions (Ch.3.14, line 1866):
    # committed volume to absorb $750k overhead; demonstrated SMT capability
    # (FPY/BGA); written customs confirmation of local content.
    headline_conditions = [
        "Committed contract volume (medium/large tier) to absorb the "
        "$750,000 fixed overhead",
        "Demonstrated SMT capability against the FPY and BGA-voiding targets",
        "Written customs confirmation that local content clears the "
        "Development-Zone threshold (ideally GAFTA too)",
    ]

    return Recommendation(
        headline=headline,
        go_phase=go_phase,
        status=go_status,
        rationale=rationale,
        next_phase=next_phase,
        next_blockers=blockers,
        parallel_actions=parallel[:6],
        headline_conditions=headline_conditions if next_phase == "Phase B" else [],
        provisional=True,
    )


if __name__ == "__main__":
    gates = build_gates()
    for name, g in gates.items():
        print(f"{name}: {g.decision.value}  ({g.pass_count}/{len(g.checks)} checks pass)")
        print(f"   {g.decision_reason}")
    flag, why = phase_b_investment_readiness(5000, gates["Phase B"])
    print(f"\nPhase B investment readiness: {flag}\n   {why}")
    rec = recommend_phase(gates, 5000)
    print(f"\nRECOMMENDATION: {rec.headline}")
    print(f"   Go phase: {rec.go_phase} ({rec.status.value})")
    print(f"   {rec.rationale}")
    print(f"   {rec.next_phase} blockers: {rec.next_blockers}")
