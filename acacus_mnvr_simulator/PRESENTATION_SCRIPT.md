# Acacus MNVR Simulator — Presentation Demo Script

A minute-by-minute guide for demoing the simulator live. Total runtime
**≈ 10–12 minutes** plus questions. Adjust by trimming the optional sections
marked *(optional)*.

---

## 0 · Before you start (5 minutes before, do this once)

1. Open Command Prompt and launch the app:
   ```
   cd "C:\Users\ASUS\OneDrive\Desktop\s4\acacus_mnvr_simulator"
   streamlit run app.py
   ```
2. Wait for the browser to open at `http://localhost:8501`.
3. **Press F11** for full-screen (hides the browser bar — looks far more
   professional).
4. Confirm the sidebar reads **"🛰️ Acacus MNVR"** with 12 pages, and the
   Executive page shows the yellow **Provisional** banner and a
   **"Proceed with Phase A"** recommendation. If you see anything about
   "180% IRR / Attractive", you're running the wrong app — stop and fix the
   folder.
5. Have this script and the report open on a second screen or printed.

**One-sentence framing to open with:**
> "This is a decision simulator built directly on our approved data. It doesn't
> try to prove Jordan is cheaper — it shows *why* the case holds even though
> it isn't, and exactly what has to be true before we commit capital."

---

## 1 · Executive Overview — the whole story in 90 seconds
**Page: Executive Overview** *(start here)*

**Click:** nothing yet — just talk through what's on screen.

**Say:**
> "Top line: China lands at **$467**, Jordan at **$475** — a **1.7% premium**.
> That's it. The relocation is not a cost play. But notice the recommendation
> banner: **proceed with Phase A**. The reason is everything the 1.7% doesn't
> capture — lead time to our MENA markets, working capital, supply continuity,
> IP protection, and trade origin."

**Point to:** the four KPI cards, then the recommendation banner.

**Say:**
> "Everything financial on this screen is flagged **provisional**. That's
> deliberate — this is an evidence-gated study, and I'll show you what that
> means in a moment."

*(optional)* Scroll down to the **recommendation panel** and read the three
Phase B conditions aloud — it primes the phase-gate section later.

---

## 2 · Cost Simulator — the volume story (the key insight)
**Page: Cost Simulator**

This is the most important interaction in the whole demo. The point: **volume,
not the 1.7%, is what matters.**

**Click:** in the sidebar, drag the **Annual volume** slider down to about
**1,500 units**.

**Say:**
> "At low volume — say we only win a couple of small contracts — watch the
> fully loaded cost. The fixed overhead of $750,000 a year is now spread over
> almost nothing, so it's **$500 a unit** of overhead alone. Jordan looks
> terrible here. This is the real start-up risk — not the 1.7%."

**Click:** now drag the **Annual volume** slider up to **20,000 units**.

**Say:**
> "Now scale up. The overhead per unit collapses to about **$38**, and the gap
> to China shrinks to near nothing. *This* is the actual decision variable:
> can we win the volume? The 1.7% premium is a footnote."

**Point to:** the **volume-absorption curve** (right chart) — the two lines and
the red China baseline.

**Say:**
> "Two views here, both honest: the dotted line is the absorbed standard cost,
> the solid line is the full overhead at volume. We never hide one behind the
> other."

*(optional)* Change **Site** in the sidebar to show the cost shifts slightly by
location, then set it back to Al-Muwaqqar.

**Reset:** put volume back to a mid value (say **10,000**) before moving on.

---

## 3 · Sensitivity Analysis — "what actually moves the answer"
**Page: Sensitivity Analysis**

**Click:** land on the page; the **tornado chart** is at the top.

**Say:**
> "If you take one chart from today, take this. Each bar is how far the unit
> cost moves when that driver swings across its realistic range. **Volume**
> dwarfs everything — including the 1.7% premium near the bottom. This is the
> overhead-absorption story, quantified."

*(optional)* Scroll to the **two-way heatmap**. 

**Say:**
> "Volume against component cost. Teal is good, red is bad. Even with a 10%
> component price rise, high volume still lands us near the China baseline."

*(optional)* Scroll to **shock scenarios**.

**Say:**
> "These are the specific stress tests — freight doubling, warranty spike,
> losing the trade benefits, a delayed Phase B. The one that hurts most is
> delayed Phase B at low volume, which is exactly why we gate it."

---

## 4 · Phase-Gate Decision — the discipline of the recommendation
**Page: Phase-Gate Decision**

This is where you show the recommendation is *earned*, not asserted.

**Click:** open the **Phase A** tab. 

**Say:**
> "Phase A — assembly in Jordan. No critical blocker. The open items are
> things we manage during ramp: training, qualifying the inbound lane,
> securing the first contracts. So Phase A is a **proceed**."

**Click:** open the **Phase B** tab.

**Say:**
> "Phase B — bringing the PCB assembly in-house — is a **HOLD**. And here's the
> logic that matters: it's **conjunctive**. Even if nine things are ready, one
> unmet critical requirement keeps it on hold. Right now we're missing
> committed volume, validated equipment costs, and a customs ruling on local
> content. All three must be true *together*."

**Click (the money moment):** tick a couple of the Phase B critical checkboxes
— e.g. "Medium/large committed volume" and "Customs/local-content ruling" —
and scroll down to the **recommendation panel** at the bottom.

**Say:**
> "If we secure these — and only if — the recommendation updates live. The
> simulator isn't cheerleading; it's enforcing the evidence. Each phase is a
> gate, not a date."

**Then untick them** to return to the honest current state.

---

## 5 · Financial Model — handling the NPV question head-on
**Page: Financial Model**

Go here **deliberately**, especially if someone is about to ask "so what's the
return?". Pre-empt it.

**Say:**
> "You'll want a number. Here it is — and here's why I'm not going to let you
> hold me to it." 

**Point to:** the headline NPV/IRR cards and the **amber warning box**.

**Say:**
> "These move entirely with the assumed selling price, which is a placeholder,
> not a booked price. Change the price and the NPV flips. That's the honest
> position: the financial return is a function of the price we can command and
> the volume we win — which is why the case rests on strategy, lead time, and
> trade access, not on a spreadsheet IRR. Anyone who shows you a confident
> 180% return on this data is fooling themselves."

*(optional)* Bump the **demand growth** slider in the sidebar to show the
multi-year cash flow improving as volume ramps.

---

## 6 · Site Decision — *(optional, if time / if asked about location)*
**Page: Site Decision**

**Click:** toggle the weighting scheme between **CTQ-priority** and **Entropy**.

**Say:**
> "We short-listed three sites with TOPSIS. The honest finding is that the
> winner depends on how you weight the criteria — Mafraq wins if you weight
> incentives heavily, Al-Muwaqqar wins on a balanced view. That's the
> tax-versus-distance trade-off we resolve in the financial model, not a
> decision to rush."

---

## 7 · Close — Validation Register + the one-line recommendation
**Page: Validation Register** *(optional, 15 seconds)*

**Say:**
> "Everything you've seen is backed by this register — every value, its
> evidence status, and what's needed to confirm it. Nothing unproven is dressed
> up as final."

**Closing line (return to Executive Overview):**
> "So the recommendation is simple and disciplined: **start Phase A now** — it's
> low capital, low risk, and captures the strategic wins. **Hold Phase B** until
> we have committed volume, proven SMT capability, and a customs ruling. The
> data supports moving, carefully, in that order."

**Click:** the **Executive summary (HTML)** download button to show you can hand
out a one-page PDF. *(Do this only if asked, or to end on a concrete artifact.)*

---

## Anticipated questions & crisp answers

**"Why relocate if it's more expensive?"**
> Because unit cost is the wrong lens. The 1.7% is a high-volume standard-cost
> gap. The value is lead time, working capital, continuity, IP and trade origin
> — and at volume the gap nearly disappears.

**"What's the NPV / payback?"**
> Provisional by design — it's dominated by the assumed selling price, which
> isn't booked. The model shows the *shape*: returns scale with volume and
> price. We're not committing capital on it; we're committing to Phase A, which
> is low-cost and low-risk.

**"Is Jordan ready for this?"**
> Phase A, yes — it's assembly. Phase B (in-house PCB) is gated on evidence we
> don't yet have: committed volume, demonstrated yield, and a customs ruling.
> The simulator holds it until those exist.

**"Why not just stay in China?"**
> Geopolitical corridor risk (Hormuz/Suez), the NDAA §1260H exclusion of
> Chinese AI hardware from US-aligned buyers, and the trade-origin upside in
> MENA. Continuity and market access, not cost.

**"How do we get the trade/tax benefits?"**
> Not from Phase A — assembly only gives ~27% local value, below the 30% / 40%
> thresholds. They come in Phase B when local content rises, and only with a
> written customs ruling. The Local Content page shows this.

**"Which site?"**
> Short-listed to three. The choice hinges on a tax-versus-distance breakpoint
> we resolve in the financial model. Not a snap decision.

---

## If something breaks (fallback plan)

- **App won't start / crashes:** you have the **Executive summary HTML/PDF** —
  export it beforehand and keep it open as a backup. The numbers are the same.
- **A chart looks wrong:** refresh the browser (the data reloads from the
  controlled file). Don't debug live — move to the next page and return.
- **Someone challenges a number:** open the **Validation Register** and show its
  evidence status. "That's a benchmark/design-basis figure, flagged provisional"
  is always a safe, honest answer.
- **Projector / dark-mode issue:** the app is locked to a light theme, so it
  reads correctly regardless of the laptop's settings.

---

## The three sentences to land (if you remember nothing else)

1. **It's not a cost play** — the 1.7% premium is a footnote; volume is the
   real variable.
2. **Phase A now, Phase B on evidence** — conjunctive gates, not a calendar.
3. **The financials are provisional by design** — returns hinge on price and
   volume, so the case rests on strategy, not a spreadsheet IRR.
