# Benchmark design

**Status:** draft for Phase 1 review. Nothing here has been run yet. This document exists so that
the equivalence margin and the cost formula are fixed **before** results are seen.

---

## 1. Question and decision rule

**Q:** Does an epistemically typed, provenance-carrying, progressively resolvable payload reduce total
cost at equal task success, relative to natural language, JSON, compact text and SILP?

**Position against existing benchmarks.** ProtocolBench (arXiv:2510.17149) already measures task
success, latency, message/byte overhead and failure robustness *across protocols*. This benchmark holds
the protocol fixed (A2A/MCP envelope, one transport) and varies the **payload representation**, which is
the axis ProtocolBench does not have. Where the axes overlap, this design reuses ProtocolBench's
definitions so the two can be read together.

**Decision rule (H1).** The IR arm wins if, over the task set:

- total cost is lower than SILP by at least **15%** (relative), with the 95% bootstrap CI of the
  difference excluding 0; and
- task success is within the equivalence margin of **±5 percentage points** of SILP, with the CI of
  the difference inside that margin; and
- qualification loss is lower than SILP (H2, secondary).

The margin is **pre-registered here** and may only be changed by an amendment recorded before
unblinding, with the reason stated.

---

## 2. Arms

| # | Arm | Payload | Lossless codec | Notes |
|---|---|---|---|---|
| A1 | NL | Free-form natural language | n/a | The default. No structural constraints. |
| A2 | JSON | Ad-hoc JSON, schema invented per task by the sender | n/a (self-describing) | The current practical default for structured exchange |
| A3 | Compact text | Abbreviated key/value lines, no shared IR | n/a | Tests "shorter syntax" without semantics |
| A4 | IR (ours) | Typed IR with E1-E4 | Yes (readable + compact forms) | Feature-negotiated; degrades to SILP |
| A5 | SILP | SILP IR, `code` and `json` frontends | Projection-limited (see `07-silp-runnability.md`) | Incumbent baseline, `polyglotIR` commit `45e9550`, installs and runs |

Rules that apply to every arm:

- **Fixed schedule.** Same number of turns per task: A sends task, B responds; a single optional
  clarification turn is available and is counted, not free.
- **No extra tool use** in A1-A3 that is unavailable in A4-A5, and vice versa.
- **Prompt parity.** Each arm's system prompt describes its format and its required fields and is
  length-matched to within 10% across arms, because prompt length is itself a token cost and would
  otherwise contaminate the comparison.
- **Same model pair** for all arms, pinned by version and date; model routing verified (a proxy
  substituting a different model invalidates the run).

---

## 3. Task family

One family: **delegation with verification over a tabular dataset.**

Agent A receives a dataset and a question, forms conclusions, and delegates verification to Agent B.
Agent B verifies against the same dataset and returns a result with evidence and stated uncertainty.

| Type | Task | What it stresses |
|---|---|---|
| T1 | "What was metric X in period P, and is it comparable to last period?" | Staleness, observation time, qualification (partial period, changed definition) |
| T2 | "Is hypothesis H supported by the data?" | Evidence references, inference vs observation, uncertainty |
| T3 | "Compare segments S1 and S2 on metric M, accounting for D" | Dependencies, conditions, range and unit precision |
| T4 | "Recommend action R; you may analyse but not commit" | Authority axis (propose vs execute), completion criteria |

Each task instance is generated from a template with a ground-truth answer and a ground-truth
qualifier set. Target: **40 instances**, 10 per type, balanced across three seeds.

**Data.** Synthetic tabular datasets generated from a documented script, so the repository is
reproducible and no production data leaves Inbet. Datasets include deliberately planted properties:
a stale extract, a partial last period, a definitional break between periods, and one segment with
insufficient sample size. These are the cases where qualifiers are either preserved or lost, which is
what H2 measures.

---

## 4. Metrics

**Primary**

1. `cost_billed` per task: everything the provider charges, reasoning included. `cost_payload` and
   `reasoning_tokens` are reported alongside it and never substituted for it (definitions in
   `02-mvp-scope.md`). The decode-weight `w` from the original design survives only inside
   `cost_payload` sensitivity checks, because `cost_billed` already contains the real decode cost.
2. `task_success`: binary, rule-based checker plus adjudication.
3. `qualification_loss`: count of sender qualifiers missing or unmarked at the receiver.

**Secondary**

4. `semantic_fidelity`: per-message IR comparison where both sides are IR (A4/A5); for A1-A3, scored
   by a rubric applied to the receiver's reconstructed claim set.
5. `tokens_by_tokenizer`: at least three tokenizers (the model families used), reported separately.
   Never averaged into a single "token count".
5b. `calibration`: TC-ECE (Trajectory-Checkpoint Expected Calibration Error) from arXiv:2609.07395,
   applied to the epistemic types in arm A4 and to whatever confidence the baselines emit. Adopting a
   published instrument rather than inventing one keeps the result comparable with the UQ literature.
6. `latency_end_to_end`, with decode calls visible.
7. `parse_failures` and `retry_cost`.
8. `expansion_requests`: count and cost in A4; zero by construction in others (see threats).
9. `finish_reason` per call, and `reasoning_tokens` where the provider reports them. Added after the
   pilot (docs/08-pilot.md): a reasoning model exhausted a 1,500-token budget on internal reasoning in
   5 of 12 exchanges and returned an empty message. A harness that scores an empty completion as
   "receiver ignored the payload" manufactures a result. Empty completions are a separate outcome and
   never a silent zero.
9b. `qualifier_compliance`: a correct `!EXPAND` counts as compliant, because the receiver is asking
   for the data behind the caveat rather than ignoring it. Added after the overhead probe
   (`12-overhead.md`), where a stricter rule scored correct behaviour as a failure.
10. `declared_status` versus `rubric_qualifier`. The pilot found a case where the receiver's own
    `qualifier=no` trailer contradicted its prose, which correctly reported staleness. Scoring uses the
    rubric; the self-report is recorded as a separate, weaker signal.

---

## 5. Measurement protocol

1. Pin model versions, decoding parameters (temperature, top_p, max tokens) and seed per run.
2. Run each arm against each task instance **three times** with different seeds; report per-seed
   aggregates and the pooled estimate.
3. Log every message verbatim with its tokenised length in each tokenizer, plus the timestamp.
4. Compute metrics from logs by script, never by hand.
5. Adjudicate disagreements blind: the adjudicator sees the task, the ground truth and the receiver's
   final artefact, not the arm label.
6. Freeze the analysis script before unblinding the arm labels.

**Scoring unit.** All arms are scored on the same declared semantic projection, not on raw IR
identity. SILP's own codec drops secondary entity ids, constraint `subject` and the whole `meta`
object on decode (measured: 0/54 full-IR round-trips, 52/54 on its own projection), so scoring on
identity would penalise any arm that carries more. The projection is versioned with the harness.

**Statistics.** Paired comparison per task instance (same instance across arms). Report mean
difference with 10,000-resample bootstrap CI and, for success rates, a paired test appropriate to
binary outcomes with the instance as the unit. No p-value without an interval. Single-run numbers are
not reported as findings.

---

## 6. Threats to validity

| Threat | Effect | Handling |
|---|---|---|
| Prompt length differences | Prompt tokens leak into the cost comparison | Length-match across arms within 10%; report prompt tokens separately |
| Model familiarity with formats | JSON is far better represented in training data than a novel IR | Report per model family; treat the IR's disadvantage as intrinsic to novelty, not noise |
| Fixed schedule hides the benefit of E4 | Progressive precision saves turns, but turns are fixed | Measure `expansion_requests` and simulate a variable-turn variant in a small pilot; state the limitation in the headline result. Note that fixing the schedule also caps the achievable saving, because DALA's results show volume dominates and volume is held constant here by construction |
| Decode cost mis-estimation | The economic conclusion flips | Count actual decode calls and their tokens; never infer from character counts |
| Adjudicator bias | Success rate drifts toward the interesting arm | Blind adjudication; two adjudicators on 20% sample, report agreement |
| Task templates too easy | Ceiling effect flattens all arms | Planted qualifiers and stale data are mandatory in every instance; pilot for spread before the main run |
| Single task family | No external validity | Explicitly stated; no generalisation claim beyond delegation-with-verification |
| SILP adapter fidelity | An unfair implementation of the incumbent weakens the result | Adapter reviewed against the draft's conformance text; publish the adapter |
| Latency dependence on provider load | Unstable secondary metric | Report medians and interquartile ranges; run arms interleaved, not in batches by arm |

---

## 7. Artefacts and reproduction

```
tasks/            templates, generated instances, ground truth, qualifier sets
datasets/         generated data + generator script + seeds
harness/          runner, arm adapters, checkers, metric computation
spec/             IR extension, conformance vectors, SILP mapping
logs/             raw per-run message logs (JSONL), one file per arm/seed
results/          aggregates, bootstrap outputs, adjudication sheets
REPORT.md         findings, incl. negative results and validity discussion
```

Every run records: git commit, model identifiers and versions, provider, decoding parameters, seeds,
wall-clock, tokenizer versions, and total spend. A run that cannot be reproduced from these fields is
not reported.

---

## 8. What a good negative result looks like

If the IR arm loses, the useful finding is *which* property failed to pay:

- cost higher than SILP because decode calls dominate: quantifies H4 for our own design;
- cost lower but success equal or worse: shows that the savings came from dropping information;
- qualification loss unchanged: shows epistemic typing does not survive a hop, which is a result
  about models, not about protocols;
- no difference at all on this task family: bounds the effect size and tells the next investigator
  where not to look.

All four are publishable. None of them is a reason to re-run with a friendlier margin.
