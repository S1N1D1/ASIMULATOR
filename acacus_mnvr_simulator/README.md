# Acacus MNVR Manufacturing Relocation Feasibility Simulator

An interactive decision simulator for the Acacus Technologies MNVR manufacturing
relocation feasibility study (China / UAE → Jordan). Built with **Streamlit +
Plotly**, driven entirely by the controlled data source `Approved_data.xlsx`.

This is **Stage 2** of a staged build: the full core engine plus the six
presentation-critical pages, all runnable.

---

## Quick start

```bash
# 1. (optional) create a virtual environment
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate

# 2. install dependencies
pip install -r requirements.txt

# 3. run
streamlit run app.py
```

The app opens at `http://localhost:8501`. No internet connection is required —
it runs fully offline on a laptop, which is why Streamlit was chosen for the
presentation.

If port 8501 is busy: `streamlit run app.py --server.port 8600`.

---

## What's in this build (Stages 2 + 3 + 4)

All twelve pages, reachable from the sidebar:

1. **Executive Overview** — headline cost comparison, a **live go/no-go
   recommendation banner**, the decision story, phase-gate readiness, and a
   recommendation reasoning panel.
2. **Cost Simulator** — full controls (volume, phase, site, cost build-up,
   freight, trade/tax, financials). Outputs landed COGS, fully loaded unit cost,
   fixed overhead per unit, total annual cost, delta vs China, margin,
   contribution, break-even, Phase B readiness. Shows **both** the absorbed
   standard-cost view and the full-overhead-at-volume view, plus waterfall,
   volume-absorption curve and site comparison. Excel export.
3. **Sensitivity Analysis** — tornado, one-way (selectable driver/metric),
   two-way heatmap (selectable axes), best/base/worst, the named shock scenarios
   (freight, component price, warranty, no-GAFTA, no-Development-Zone, delayed
   Phase B, high volume), operational OEE shocks, site comparison.
4. **Scenario Comparison** — save scenarios and compare side by side.
5. **Capacity & Burn-in** — daily build rate, burn-in rack positions and WIP
   (daily build × 3-day burn-in), direct operators and station count, a
   capacity-vs-volume curve, and the OEE build-up.
6. **Local Content & Trade** — local value-added gauge against the GAFTA 40% and
   Development-Zone 30% thresholds, why Phase A doesn't clear them, and the
   Development-Zone tax incentives.
7. **Site Decision** — the report's TOPSIS results across three weighting schemes
   (entropy, CTQ-priority, equal), showing the tax-versus-distance breakpoint
   (Mafraq wins on entropy; Al-Muwaqqar on CTQ/equal), plus the cost-by-site view.
8. **Financial Model** — multi-year P&L and cash-flow schedule with demand
   growth, NPV / IRR / payback, a year-1 waterfall, and a full year-by-year
   table. Heavily flagged provisional — results move sharply with the assumed
   selling price.
9. **KPI Dashboard** — every CTQ/KPI with target, simulated value, pass/fail,
   traffic light, evidence status and phase.
10. **Phase-Gate Decision** — Phase A / B / C with **conjunctive** gate logic;
    toggleable checks; the recommendation recomputes live.
11. **Validation Register** — every value, evidence status and source. Filterable.
12. **Presentation Mode** — a clean seven-slide walkthrough for the live demo.

## The go/no-go recommendation

Derived **live from the gate state** and faithful to the consolidated report
(Ch. 3.14):

- **Phase A — proceed early.** Largest lead-time, working-capital and continuity
  gains at low capital and low risk; its weak points (local content, PCB
  control) are not what Phase A is for.
- **Phase B — HOLD**, until three conditions are met *together*: committed
  contract volume to absorb the $750,000 overhead; demonstrated SMT capability
  against the FPY and BGA targets; and a written customs confirmation that local
  content clears the Development-Zone threshold (ideally GAFTA too).
- **Phase C — follows** once the local supplier base and non-Chinese variants
  are qualified.

Each phase is a gate, not a date.

### Stage 5 (complete)
- **Executive summary export** — from the Executive Overview page, download a
  self-contained **HTML** summary; open it in any browser and use File → Print →
  Save as PDF for a one-page handout. Carries all provisional flags.
- **Excel scenario export** — from the Executive Overview and Cost Simulator.
- **PRESENTATION_SCRIPT.md** — a minute-by-minute demo script for the live talk:
  what to click, what to say, anticipated questions with crisp answers, and a
  fallback plan if anything breaks. Read it before presenting.

---

## How the provisional rule works

The study is **evidence-gated**. NPV, IRR, payback, GAFTA / Development-Zone
benefits and Phase B readiness are marked **PROVISIONAL** until the required
evidence is confirmed. Evidence statuses (Confirmed, Benchmark, Design-basis
estimate, Validation required, Pilot pending, External confirmation required)
flow from the workbook through every page. Only **Confirmed** evidence may back
a non-provisional figure.

The **+1.7% Jordan premium is a high-volume standard-cost comparison** and is
deliberately **not** presented as the operative start-up cost gap.

---

## Architecture

```
acacus_mnvr_simulator/
├── app.py                  # Streamlit entry point, sidebar nav, router
├── requirements.txt
├── README.md
├── data/
│   └── Approved_data.xlsx  # controlled data source
├── core/                   # UI-agnostic — ports to Dash/React unchanged
│   ├── data_loader.py      # workbook → typed dataclasses + evidence statuses
│   ├── calculations.py     # cost, capacity, burn-in, OEE, finance, break-even
│   ├── gates.py            # conjunctive Phase A/B/C gate engine
│   └── export.py           # Excel scenario export
├── ui/
│   ├── charts.py           # Plotly figures (waterfall, volume curve, gates…)
│   ├── components.py       # KPI cards, traffic lights, evidence badges
│   └── pages.py            # one render_* function per page
└── assets/
    └── style.css           # presentation theme
```

**Why this split:** every number lives in `core/` as a pure function with no
Streamlit dependency. The presentation layer (`ui/`) is the only Streamlit-aware
code. This keeps the engine testable and lets you move to Plotly Dash or a
React front end later without rewriting the maths.

---

## Data source

All numeric values are read from `data/Approved_data.xlsx` (8 sheets: BOM/COGS
detail, CTQ/KPI matrix, operations & quality, freight & trade, demand &
financials, references). The only hardcoded numbers are fixed project
assumptions from the consolidated report (working days, burn-in duration, OEE
component targets, illustrative price/capex/opex placeholders) — each is
labelled with its source and an evidence status in
`core/data_loader.py::FIXED_ASSUMPTIONS`, so nothing masquerades as a confirmed
figure. Illustrative placeholders are always flagged provisional.

To update the model, edit the workbook and restart the app (or clear the cache
from the Streamlit menu).

---

## Troubleshooting

## Deploying as a public website (Streamlit Community Cloud)

Free, permanent hosting. The flow is: code → GitHub → Streamlit Cloud → URL.

1. Push this folder's **contents** to a public GitHub repo (drag-and-drop on
   github.com works — `app.py` must be at the repo root, not nested).
2. Go to **share.streamlit.io**, sign in with GitHub, click **Create app**.
3. Point it at your repo, branch `main`, main file `app.py`, and **Deploy**.
4. After a 2–4 minute build you get a permanent `*.streamlit.app` URL.

Updating: edit/re-upload files on GitHub and the app redeploys automatically.
Free apps sleep when idle; open the URL a few minutes before presenting.

## Password protecting the app

The app reads an optional password from Streamlit **secrets** — never from the
code or the repo.

- **No password set** → the app is open (convenient for local development).
- **To require a password locally:** copy `.streamlit/secrets.toml.example` to
  `.streamlit/secrets.toml` and set `APP_PASSWORD`. That file is git-ignored.
- **To require a password on Streamlit Cloud:** open your deployed app →
  **Settings → Secrets** → paste:
  ```
  APP_PASSWORD = "your-password-here"
  ```
  Save. The app restarts and now shows a login screen. Share the password only
  with your reviewers. Change it any time from the same panel.

Because the password lives in Cloud secrets (not the repo), your GitHub code can
stay public while the running app stays private.

## Troubleshooting

- **"Data file missing"** — ensure `Approved_data.xlsx` is in `data/`.
- **Charts not showing** — `pip install -r requirements.txt` to get a compatible
  Plotly version.
- **Slow first load** — Streamlit caches the workbook after the first read.
- **Forgot the public-app password** — reset it in Settings → Secrets on
  Streamlit Cloud; takes effect on the next restart.
