# Length probe: does the payload gap grow with session length?

**Date:** 2026-10-27
**Cost:** $0.0324 billed for 8 sessions (131 calls). **Truncated calls:** 3, all on the slowest model.
**Models:** `xiaomi/mimo-v2.6-flash`, `openai/gpt-6-luna`. **Reps:** 1 per cell.

Script: `harness/length_probe.py`. Aggregation: `harness/analyze_length.py`.
Logs: `results/length-probe-2026-10-27/runs.jsonl`.

---

## 1. The question this replaces

The single-exchange probes answered "is this format cheaper per message". That is the wrong question
for real deployment, where sessions run for many turns and a per-message difference either compounds
or washes out. This probe measures the **slope**.

Design: the same eight weeks of sports turnover, delivered two ways.

- **Aggregate (T=1)**: Agent A receives the whole series in one message and writes one update.
- **Incremental (T=8)**: one row per turn, A and B alternating, eight times.

Same information, same traps (an incomplete week and an old extract), same final question ("which week
was weakest and why"). Both arms carry the traps, so qualifier survival is comparable across lengths.

Two arms: `nl` (prose both ways) and `payload` (typed payload from A, validated JSON decision from B).

**Cost per turn** is the comparable number, not cost per session: an eight-turn session costs roughly
eight times a one-turn session by construction.

## 2. Results

| Arm | Length | Sessions | Billed per turn | Payload per turn | Reasoning tokens per turn |
|---|---|---|---|---|---|
| nl | 1 | 2 | $0.000292 | $0.000142 | 296 |
| nl | 8 | 2 | $0.000734 | $0.000384 | 920 |
| payload | 1 | 2 | $0.001489 | $0.000366 | 2,826 |
| payload | 8 | 2 | $0.001070 | $0.000374 | 1,365 |

| Arm | Length | Qualifier: partial | Qualifier: stale | Weakest week right |
|---|---|---|---|---|
| nl | 1 | 1/2 | 1/2 | 2/2 |
| nl | 8 | 1/2 | 2/2 | 2/2 |
| payload | 1 | **2/2** | **2/2** | 2/2 |
| payload | 8 | **2/2** | **2/2** | 2/2 |

Per-turn cost drift across the session (T=8 only): `nl` first turn $0.000154, last turn $0.000786,
**+410%**. `payload` first $0.000640, last $0.001149, **+80%**.

## 3. Findings

### 3.1 The typed payload is more expensive per turn, but the penalty is a fixed overhead that amortises

At one turn, `payload` costs 5.1 times the prose arm per turn ($0.001489 against $0.000292). At eight
turns the ratio falls to 1.46 ($0.001070 against $0.000734). The absolute gap shrinks from $0.0012 to
$0.0003 per turn.

The mechanism is visible in the reasoning column: at T=1 the payload arm spends 2,826 reasoning tokens
per turn, at T=8 it spends 1,365. The skill document and the JSON contract are a per-session fixed
cost, and they dominate exactly when the session is short.

**Consequence for H1:** a typed payload cannot win by being cheaper per message at small scale. It can
only win where the per-session overhead is amortised and the drift advantage compounds. Which is the
next finding.

### 3.2 The real length effect is on drift, and it favours the payload

Prose sessions get progressively more expensive: per-turn cost rises 410% from the first turn to the
last, because each turn carries prior prose forward and the model keeps re-reading it. The payload arm
rises only 80%, because structured replies are compact and the carried history stays small.

So the honest statement is not "the payload is cheaper at length". It is: **the payload's per-turn cost
is flatter, and flatness is what eventually wins** — but at eight turns it has not won yet. Prose's
last turn ($0.000786) is still below the payload's last turn ($0.001149). The crossover is beyond this
horizon and has not been measured.

### 3.3 Qualifier survival separates the arms cleanly, and length does not fix prose

The payload arm preserved both planted qualifiers in 4 of 4 sessions at both lengths. The prose arm lost
the partial-week qualifier in half the sessions, at one turn and at eight: it did not improve with more
context, and in one case the weekly comparison was produced from an incomplete week without comment.
The stale-extract qualifier did surface more often in the eight-turn prose sessions (2/2 against 1/2),
which is consistent with more chances to notice, not with better method.

This is the first probe where a behavioural difference is stable across lengths and models. It is still
n = 2 per cell and carries no statistical claim.

### 3.4 The reasoning budget still bites on the slow model

Three calls ended `finish_reason=length` (two in `mimo` prose T=8, one in `mimo` payload T=8). They are
counted, not silently dropped, and they mean the `mimo` cost figures at T=8 are lower bounds.

## 4. Decisions

**D-021.** Format effects are reported as two quantities, never one: **per-turn cost** and **per-turn
cost drift** (first turn against last turn). An arm that is dearer per turn but flat is a different
proposition from one that is cheap and steep, and a single average hides the difference.

**D-022.** The crossover point between arms is a measured quantity, not an assumption. The MVP does not
claim that a typed payload is economical; it reports the crossover if one is found within the tested
horizon, and states the horizon. Eight turns is not enough.

## 5. What this changes in the plan

1. **The H1 test needs longer sessions.** A 40-instance benchmark at one or two turns would measure the
   regime where the payload is at its worst. Either the task family gets sessions of 15 to 25 turns, or
   H1 is tested on drift and behaviour rather than on absolute cost.
2. **Qualifier retention is the metric with a live signal.** It separated the arms at both lengths while
   cost did not. That argues for making it a primary metric rather than a secondary one.
3. **The fixed overhead is the thing to attack in design.** 2,826 reasoning tokens per turn at T=1 is
   the skill plus the contract being re-read. If that can be cut to a few hundred, the payload arm's
   disadvantage at short length largely disappears, and its drift advantage starts from a lower floor.

## 6. Limits

- n = 2 sessions per cell, one repetition, two models. Counts and means only; no confidence intervals.
- One task family (weekly series tracking), one planted trap type per category, synthetic data.
- The aggregate arm gives one big message; real agents rarely do exactly that, so T=1 is a reference
  point rather than a deployment scenario.
- `mimo` was slower by an order of magnitude and hit the token budget three times, so its T=8 numbers
  are the least reliable in the table.
- The final answer is scored from the last reply alone; a model that stated the qualifier in an earlier
  turn and dropped it in the last would be scored as a loss. That is deliberate (the artefact is what
  ships) but it is a choice.
