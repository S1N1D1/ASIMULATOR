"""
components.py — Reusable Streamlit UI components for the Acacus MNVR simulator.

Centralises the visual language: KPI cards, traffic-light dots, evidence badges,
and the provisional banner that enforces the 'no unvalidated value as final'
rule. Pages call these instead of writing raw HTML.
"""
from __future__ import annotations

import streamlit as st

from core.data_loader import Evidence

# Evidence -> colour + short label
_EVIDENCE_STYLE = {
    Evidence.CONFIRMED: ("#2E8B57", "Confirmed"),
    Evidence.BENCHMARK: ("#2E5A88", "Benchmark"),
    Evidence.DESIGN_ESTIMATE: ("#E8A33D", "Design-basis"),
    Evidence.VALIDATION_REQUIRED: ("#C8553D", "Validation req."),
    Evidence.PILOT_PENDING: ("#9B59B6", "Pilot pending"),
    Evidence.EXTERNAL_REQUIRED: ("#C0392B", "External req."),
}

_STATUS_COLOR = {"GO": "#2E8B57", "PARTIAL": "#E8A33D", "HOLD": "#C8553D"}


def evidence_badge(ev: Evidence) -> str:
    color, label = _EVIDENCE_STYLE.get(ev, ("#8A94A6", str(ev.value)))
    return (f"<span style='background:{color}1A;color:{color};border:1px solid "
            f"{color}55;padding:2px 8px;border-radius:10px;font-size:0.72rem;"
            f"font-weight:600;white-space:nowrap'>{label}</span>")


def traffic_dot(passes: bool, partial: bool = False) -> str:
    color = "#E8A33D" if partial else ("#2E8B57" if passes else "#C8553D")
    return (f"<span style='display:inline-block;width:12px;height:12px;"
            f"border-radius:50%;background:{color};box-shadow:0 0 0 3px "
            f"{color}22;vertical-align:middle'></span>")


def status_pill(status: str) -> str:
    color = _STATUS_COLOR.get(status, "#8A94A6")
    return (f"<span style='background:{color};color:white;padding:3px 12px;"
            f"border-radius:6px;font-weight:700;font-size:0.85rem;"
            f"letter-spacing:0.04em'>{status}</span>")


def kpi_card(label: str, value: str, sublabel: str = "", *,
             accent: str = "#1F3A5F", provisional: bool = False,
             evidence: Evidence | None = None):
    """Render an executive KPI card."""
    prov_html = ""
    if provisional:
        prov_html = ("<div style='margin-top:6px'><span style='background:#FFF2CC;"
                     "color:#9A6A00;border:1px solid #E8A33D;padding:1px 7px;"
                     "border-radius:8px;font-size:0.68rem;font-weight:700'>"
                     "PROVISIONAL</span></div>")
    ev_html = ""
    if evidence is not None:
        ev_html = f"<div style='margin-top:6px'>{evidence_badge(evidence)}</div>"
    sub_html = (f"<div style='color:#8A94A6;font-size:0.78rem;margin-top:2px'>"
                f"{sublabel}</div>") if sublabel else ""

    st.markdown(
        f"""
        <div style='background:white;border:1px solid #E6E9EF;border-left:4px solid
        {accent};border-radius:10px;padding:14px 16px;height:100%;
        box-shadow:0 1px 3px rgba(20,30,55,0.05)'>
          <div style='color:#5A6478;font-size:0.78rem;font-weight:600;
          text-transform:uppercase;letter-spacing:0.05em'>{label}</div>
          <div style='color:#1A2233;font-size:1.55rem;font-weight:700;
          margin-top:4px;line-height:1.1'>{value}</div>
          {sub_html}{ev_html}{prov_html}
        </div>
        """,
        unsafe_allow_html=True,
    )


def provisional_banner(items: list[str] | None = None):
    """The top-of-page banner enforcing the provisional rule."""
    extra = ""
    if items:
        lis = "".join(f"<li>{i}</li>" for i in items)
        extra = (f"<ul style='margin:6px 0 0 18px;padding:0;font-size:0.83rem;"
                 f"color:#7A5A00'>{lis}</ul>")
    st.markdown(
        f"""
        <div style='background:linear-gradient(90deg,#FFF8E7,#FFF2CC);
        border:1px solid #E8A33D;border-radius:10px;padding:12px 16px;
        margin-bottom:14px'>
          <div style='font-weight:700;color:#7A5A00;font-size:0.9rem'>
          &#9888;&#65039; Provisional results — evidence-gated study</div>
          <div style='color:#7A5A00;font-size:0.83rem;margin-top:2px'>
          NPV, IRR, payback, GAFTA / Development-Zone benefits and Phase B
          readiness are marked provisional until the required evidence is
          confirmed. Phases are evidence-gated, not calendar-gated.</div>
          {extra}
        </div>
        """,
        unsafe_allow_html=True,
    )


def section_title(text: str, subtitle: str = ""):
    sub = (f"<div style='color:#8A94A6;font-size:0.9rem;margin-top:-2px'>"
           f"{subtitle}</div>") if subtitle else ""
    st.markdown(
        f"""
        <div style='margin:6px 0 10px 0'>
          <div style='font-size:1.35rem;font-weight:700;color:#1F3A5F'>{text}</div>
          {sub}
        </div>
        """,
        unsafe_allow_html=True,
    )


def decision_card(title: str, status: str, reason: str):
    color = _STATUS_COLOR.get(status, "#8A94A6")
    st.markdown(
        f"""
        <div style='background:white;border:1px solid #E6E9EF;border-top:5px solid
        {color};border-radius:10px;padding:16px 18px'>
          <div style='display:flex;justify-content:space-between;align-items:center'>
            <div style='font-size:1.1rem;font-weight:700;color:#1A2233'>{title}</div>
            {status_pill(status)}
          </div>
          <div style='color:#5A6478;font-size:0.86rem;margin-top:8px'>{reason}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def recommendation_banner(rec):
    """Prominent go/no-go banner, colour-keyed to the recommended phase status."""
    status = rec.status.value if hasattr(rec.status, "value") else str(rec.status)
    accent = _STATUS_COLOR.get(status, "#8A94A6")
    go = "GO" if status in ("GO", "PARTIAL") and rec.go_phase != "None" else "HOLD"
    icon = "✓" if go == "GO" else "⏸"
    prov = ("<span style='background:#FFF2CC;color:#9A6A00;border:1px solid "
            "#E8A33D;padding:1px 8px;border-radius:8px;font-size:0.7rem;"
            "font-weight:700;margin-left:10px'>PROVISIONAL</span>")
    st.markdown(
        f"""
        <div style='background:linear-gradient(100deg,{accent}14,{accent}05);
        border:1px solid {accent}55;border-left:6px solid {accent};
        border-radius:12px;padding:16px 20px;margin-bottom:16px'>
          <div style='display:flex;align-items:center;gap:12px'>
            <div style='font-size:1.6rem;color:{accent}'>{icon}</div>
            <div>
              <div style='color:#5A6478;font-size:0.74rem;font-weight:700;
              text-transform:uppercase;letter-spacing:0.08em'>
              Current recommendation{prov}</div>
              <div style='font-size:1.35rem;font-weight:800;color:#1A2233;
              margin-top:1px'>{rec.headline}</div>
            </div>
          </div>
          <div style='color:#3A4456;font-size:0.9rem;margin-top:10px;
          line-height:1.45'>{rec.rationale}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def recommendation_panel(rec):
    """Dedicated reasoning panel: what to do now, what's holding the next phase."""
    status = rec.status.value if hasattr(rec.status, "value") else str(rec.status)
    accent = _STATUS_COLOR.get(status, "#8A94A6")

    cond_html = ""
    if rec.headline_conditions:
        lis = "".join(
            f"<li style='margin-bottom:6px'>{c}</li>" for c in rec.headline_conditions)
        cond_html = (
            f"<div style='margin-top:14px'>"
            f"<div style='font-weight:700;color:#1A2233;font-size:0.92rem'>"
            f"{rec.next_phase} proceeds only when these are met together:</div>"
            f"<ol style='margin:8px 0 0 18px;padding:0;color:#3A4456;"
            f"font-size:0.88rem'>{lis}</ol></div>")

    parallel_html = ""
    if rec.parallel_actions:
        lis = "".join(
            f"<li style='margin-bottom:4px'>{a}</li>" for a in rec.parallel_actions)
        parallel_html = (
            f"<div style='margin-top:14px'>"
            f"<div style='font-weight:700;color:#1A2233;font-size:0.92rem'>"
            f"Pursue in parallel (to unlock {rec.next_phase}):</div>"
            f"<ul style='margin:8px 0 0 18px;padding:0;color:#3A4456;"
            f"font-size:0.88rem'>{lis}</ul></div>")

    st.markdown(
        f"""
        <div style='background:white;border:1px solid #E6E9EF;border-radius:12px;
        padding:18px 20px'>
          <div style='display:flex;justify-content:space-between;align-items:center'>
            <div style='font-size:1.1rem;font-weight:800;color:#1F3A5F'>
            Recommendation &amp; reasoning</div>
            {status_pill(status)}
          </div>
          <div style='color:#3A4456;font-size:0.92rem;margin-top:10px;
          line-height:1.5'><b>Do now:</b> {rec.headline}. {rec.rationale}</div>
          {cond_html}
          {parallel_html}
          <div style='margin-top:14px;padding-top:12px;border-top:1px solid #EEF0F4;
          color:#8A94A6;font-size:0.78rem'>Each phase is a gate, not a date. This
          recommendation recomputes live as gate checks are toggled, and all
          financial / trade benefits remain provisional until evidence is
          confirmed.</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
