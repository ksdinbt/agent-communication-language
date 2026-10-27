# Pilot: two agents, two payloads, twelve exchanges

**Date:** 2026-10-27
**Purpose:** effort sizing before building the harness. This is **not** the benchmark, it does not
test H1, and no result here should be quoted as evidence about SILP or about our design.
**Cost:** $0.0098 in total. **Wall clock:** 111 s for 12 two-hop exchanges.

Script: `harness/pilot_two_agent.py`. Raw logs: `results/pilot-2026-10-27/runs.jsonl`.

---

## 1. Design

One model (`deepseek/deepseek-v4.1-flash`, temperature 0), two agents with different system prompts,
six instances, two arms, one seed, fixed two-turn schedule (A delegates, B verifies; no clarification
turn).

| Arm | Payload | Format specification |
|---|---|---|
| `nl` | one short natural-language message | three lines of role description |
| `ir` | labelled fields (`DELEGATE` / `CLAIM ... epistemic=...` / `QUALIFIER type=...` / `ASK`) | a sixteen-line format block plus four rules |

Six instances: two clean, two where the last period was extracted mid-week (an incomplete week), two
where the extract is a day older than "right now". The four trap instances are where a qualifier must
survive the hop to be correct.

**The `ir` arm is a naive typed payload, not our design and not SILP.** It exists to test whether a
receiver *uses* labelled fields at all. It is deliberately the most obvious encoding a competent
engineer would write in ten minutes, including the verbose format block that turned out to be the
expensive part.

Scoring: number present / not; qualifier present, measured two ways — the receiver's own
`STATUS: qualifier=` trailer and a keyword heuristic over its text.

## 2. Results

| Instance | Arm | Tokens | Seconds | Cost ($) | Value | Needs qualifier | Declared | Heuristic |
|---|---|---|---|---|---|---|---|---|
| clean-1 | nl | 982 | 2.7 | 0.000463 | yes | no | yes | yes |
| clean-1 | ir | 1460 | 10.9 | 0.000287 | yes | no | no | yes |
| clean-2 | nl | 679 | 3.1 | 0.000137 | yes | no | yes | yes |
| clean-2 | ir | 2852 | 12.0 | 0.001270 | yes | no | no | yes |
| partial-1 | nl | 1282 | 7.6 | 0.000422 | yes | **yes** | no | **no** |
| partial-1 | ir | 2769 | 21.2 | 0.000788 | yes | **yes** | no | **no** |
| partial-2 | nl | 1406 | 7.3 | 0.000402 | yes | **yes** | no | **no** |
| partial-2 | ir | 3609 | 22.0 | 0.001172 | no | **yes** | none | **no** |
| stale-1 | nl | 1621 | 7.0 | 0.001031 | yes | **yes** | no | yes |
| stale-1 | ir | 3625 | 7.8 | 0.002019 | no | **yes** | none | **no** |
| stale-2 | nl | 944 | 2.0 | 0.000353 | yes | **yes** | yes | yes |
| stale-2 | ir | 2453 | 7.5 | 0.001496 | yes | **yes** | yes | yes |

Means: `nl` 1,152 tokens / 5.0 s / $0.0028 per six exchanges; `ir` 2,795 tokens / 13.6 s / $0.0070.

## 3. Four findings

### 3.1 The naive typed arm costs 2.4x the tokens and 2.7x the time

`ir` is 2.4x the tokens of `nl` (2,795 vs 1,152 mean) and 2.5x the cost. The payload string is longer,
but that is not where the money went: the format block and the four rules pushed the receiver into
far longer internal reasoning. Mean reasoning tokens: **1,951** in the `ir` arm against **595** in
`nl`.

Instruction density, not payload syntax, dominated the bill. Any design that requires a page of
formatting rules to be restated in every prompt has already lost the efficiency argument before the
first message is encoded.

### 3.2 Five of twelve exchanges returned an empty message

`finish_reason=length` with `reasoning_tokens=1500` — the entire budget consumed by reasoning, no
content emitted. Four of the six `ir` first turns and one `ir` second turn. The `nl` arm never hit
the cap.

Two harness requirements follow, and they are cheap to get wrong: **log `finish_reason` and
`reasoning_tokens` per call**, and **size `max_tokens` per arm** (or disable reasoning) rather than
using one global value. My first run of this pilot used `max_tokens=400` and produced empty output in
8 of 12 exchanges, which I initially misread as a parsing failure. A harness that silently scores an
empty completion as "receiver ignored the payload" would manufacture a result.

### 3.3 The qualifier trap worked, and both arms failed it the same way

On `partial-1` and `partial-2` both arms returned a confident week-over-week comparison
(−28.2%) computed against an incomplete week, with `STATUS: qualifier=no`. The incompleteness was
visible in the table: `2026-W41` was extracted on `2026-10-21`, mid-week.

The failure was **not** an encoding failure. It happened in natural language too, where no format was
imposed at all. That is the most important result of the pilot: the problem we set out to solve at the
payload layer shows up first as an **attention** problem, and a new field in a message does not fix
attention by itself.

### 3.4 The receiver's self-report contradicts its own text

`stale-1`, `nl` arm: the answer said *"as of the latest extract date shown"* — it noticed the
staleness — and still ended with `STATUS: qualifier=no`. So the declared status was wrong while the
prose was right.

This is a concrete, reproducible instance of the E1 problem, obtained for one cent: a declared
epistemic label is not a measurement, and any design that trusts `qualifier=` from the sender without
cross-checking the text will record a false pass. It also argues for measuring on the text with a
rubric rather than on the trailer, and for treating the trailer as one input among several.

## 4. Effort sizing

| Item | Pilot reality | Implication for the MVP estimate |
|---|---|---|
| Exchanges | 12 in one run, unattended | A 40-instance × 5-arm × 3-seed run is 600 exchanges |
| Wall clock | 111 s for 12 (mean 9.3 s/exchange) | ~2 hours per full run, dominated by latency not cost |
| Money | $0.0098 for 12 | a full 600-exchange run at this model is under $0.50 |
| Code | ~250 lines, one file, no framework | the harness is a week of work, not a month: logging, scoring, arms, projection |
| Failure modes hit | empty completions, format non-compliance, self-report error | each needs a check in the harness, none needs new infrastructure |

The numbers that matter for planning: **cost is not the constraint, latency is**; and the harness's
hard part is scoring (what counts as the qualifier surviving), not orchestration.

## 5. What this changes in the plan

1. **Payload minimalism becomes a design requirement, not a taste.** If a field needs a paragraph of
   instructions in the system prompt, it belongs in a skill or a spec the receiver loads once, not in
   the prompt on every call.
2. **The skill file is not an add-on; it is the economics of the design.** See section 6.
3. **The benchmark must measure qualifier loss on the text, with a rubric**, and treat the receiver's
   declared status as a separate, weaker signal. The two disagreed in this pilot.
4. **`finish_reason` and reasoning tokens are first-class metrics.** They belong in
   `03-benchmark-design.md` next to token counts, or the harness will silently score empty messages.

## 6. SKILL.md: the delivery mechanism for conventions

This was raised while choosing the pilot, and the pilot's cost structure makes the case for it
quantitatively: 1,951 versus 595 reasoning tokens per exchange came from restating conventions in
every prompt.

A skill file is how agents already learn conventions: a short document, loaded on demand, containing
what cannot be inferred and nothing that can. For this programme it would carry:

- the field vocabulary (epistemic types, authority values, qualifier types) with one example each;
- the two rules that matter most: an `ASSUMED` claim is not actable, and an `EXPAND` request is
  cheaper than a re-send;
- the conformance cases a receiver must handle (valid, invalid, degraded-to-plain);
- the counter-example: what a message looks like when a qualifier is dropped, so the receiver can
  recognise the failure.

Design constraints, learned the hard way in the `ir` arm: **under one page**, no field list longer
than seven items, no rule that requires an exception to state, and a versioned name so a receiver can
say which conventions it holds.

Placement: `skills/<payload-name>/SKILL.md` in this repository, published alongside the specification,
and loaded by the harness in Phase 3 instead of a system-prompt format block. Phase 1 deliverable, not
Phase 3, because the payload shape and the skill text must be written together — every field that is
hard to explain in one sentence is a field that will be misread.

## 7. Limits of this pilot

- One model, one family, reasoning-enabled. A non-reasoning model would change 3.1 and 3.2 completely.
- Six instances, one seed, no repetition. Nothing here supports a claim about direction of effect.
- The qualifier heuristic is a keyword list; `stale-1` scored "survived" on the word "as of" while
  the receiver declared otherwise. Both signals are wrong in different ways, which is why the
  benchmark needs a rubric and adjudication, not keywords.
- The `ir` arm is a strawman encoding of my own writing. Its poor showing says nothing about SILP's
  frontends, which are shorter and tokenizer-checked, and nothing about our design, which does not
  exist yet.
- Two of the six instances asked for a comparison, which made the value scoring ambiguous; the
  questions were reworded between runs and the second run is the one reported.
