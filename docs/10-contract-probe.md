# Receiver contract probe: structure in form, not in truth

**Date:** 2026-10-27
**Cost:** $0.0303 billed. **96 calls**, four models, two conditions, four instances, three reps.
**Truncated:** 0. **Empty:** 0. **Reasoning share of the bill:** 74%.

Script: `harness/contract_probe.py`. Aggregation: `harness/analyze_contract.py`.
Logs: `results/contract-probe-2026-10-27/runs.jsonl`.

---

## 1. What was asked

The earlier probes showed `!EXPAND` behaving like a suggestion and empty completions caused by tight
budgets. Two changes were tested here:

1. **Reasoning is allowed.** `max_tokens = 6000` per call, no attempt to suppress or shorten
   deliberation. Cost is reported three ways (`cost_billed`, `cost_payload`, `reasoning_tokens`) and
   only `cost_billed` may support a claim about money.
2. **The receiver's answer becomes a decision object** — a JSON document with fixed keys (`act`, `ref`,
   `granularity`, `value`, `epistemic`, `qualifier`, `answer`, `missing`) instead of prose plus a
   `STATUS:` line.

Four instances: `partial` (incomplete week), `deferred` (payload invites `!EXPAND`), `stale` (14-day-old
extract), `assumed` (tiny sample, no real source). Three repetitions each, so 12 calls per model and
condition, 96 in total.

## 2. Results

| Model | Condition | Contract valid | EXPAND correct | Qualifier | Value |
|---|---|---|---|---|---|
| deepseek-v4.1-flash-1017 | prose | n/a | n/a | 12/12 | 11/12 |
| deepseek-v4.1-flash-1017 | contract | 12/12 | 11/12 | 12/12 | 10/12 |
| gpt-6-luna | prose | n/a | n/a | 10/12 | 7/12 |
| gpt-6-luna | contract | 12/12 | 12/12 | 11/12 | 9/12 |
| mimo-v2.6-flash | prose | n/a | n/a | 12/12 | 10/12 |
| mimo-v2.6-flash | contract | 12/12 | 12/12 | 11/12 | 9/12 |
| glm-5.3-flash | prose | n/a | n/a | 12/12 | 12/12 |
| glm-5.3-flash | contract | 12/12 | 10/12 | **1/12** | **1/12** |
| **totals** | prose | - | - | **46/48** | **40/48** |
| **totals** | contract | **48/48** | **45/48** | **35/48** | **29/48** |

Excluding glm-5.3-flash, prose and contract are **identical**: 34/36 qualifier, 28/36 value each.

Cost per call, mean: contract $0.000311, prose $0.000321 (billed). `cost_payload`: $0.000080 versus
$0.000083. Total: $0.0303 billed against $0.0078 payload, with 62,015 reasoning tokens.

## 3. Findings

### 3.1 The schema works perfectly as a schema, and that is all it is

48 of 48 contract responses parsed and validated. Zero empty, zero truncated. Requiring a JSON object
removes the whole class of failure the earlier probes suffered from. This is real: the contract is the
right delivery mechanism for *shape*.

It is not a mechanism for *truth*. Under the contract, glm-5.3-flash returned:

```json
{"act": "!REPORT", "ref": null, "granularity": null, "value": null,
 "epistemic": "OBSERVED", "qualifier": "none",
 "answer": "Sports turnover in 2026-W41 was 1,780,000 EUR, which is 540,000 EUR higher than the
            1,240,000 EUR recorded for 2026-W40.", "missing": []}
```

The figure is 890,000 in the table. 1,780,000 is exactly double it. The claim is labelled `OBSERVED`,
the `qualifier` is `none` although the payload carried `partial_period`, and `value` is `null` so the
machine-readable field is empty while the prose carries a fabricated number. In the prose condition the
same model answered 12 of 12 correctly.

A schema constrains shape. A model can satisfy every key and still lie, and the more mechanical the
answer looks, the less a reviewer is inclined to check it. This is the strongest argument yet for E1
being verified by a rubric over the text plus adjudication, and never by the sender's own label.

### 3.2 The contract bought EXPAND discipline, and nothing else

`!EXPAND` was correct in 45 of 48 contract calls, against prose behaviour of 3/3, 3/3, 2/3 and 2/3 on
deferred instances — but prose also emitted `!EXPAND` on instances where nothing was deferred (4 of 12
answers for deepseek and glm, though only 2 of their 3 deferred instances were right). The contract
removes the spurious requests cleanly, because `act` is now a validated field rather than an
incidental mention.

Beyond that, the aggregate improvement is zero: with glm excluded, both conditions score the same. The
gain is in *machine-checkability*, not in answer quality.

### 3.3 Reasoning is 74% of the bill; the payload is a rounding error

Total billed $0.0303 against `cost_payload` $0.0078. Across the four models the reasoning share of the
bill ranges from 66% to 92%; mimo reported 0% in prose mode and 66% under the contract.

Two consequences, and they point in opposite directions:

- **Excluding reasoning from the headline would understate cost by a factor of four.** The proposal to
  "exclude the reasoning block from the measurement" is fine as a *secondary* metric and dishonest as a
  headline. Reported as `cost_billed` with `cost_payload` alongside, it becomes a useful decomposition.
- **If deliberation dominates, then the payload is not where the money is.** At this task size, halving
  the number of payload tokens changes the bill by a few percent. That is a direct warning for
  hypothesis H1: the format argument may be economically irrelevant on small tasks and only bite on
  long ones, where payload accumulates across many messages.

### 3.4 Two rules the specification is missing

Both come straight from the glm failure:

1. A numeric `!REPORT` must carry a non-null `value`. Leaving it null while the prose states a figure
   makes the machine-readable layer decorative and lets a wrong number hide in `answer`.
2. A receiver that discards the payload's `qualifier` must say why. `qualifier: "none"` on a payload
   that carried `partial_period` is either a decision (`definition_changed`, `sample_too_small`) or an
   error, and the schema should not accept silence.

## 4. Changes made

- `spec/ir-extension-v0.1.md` gains rules 4.6 and 5.5, plus a vector for each (`report-value-null`,
  `qualifier-dropped`).
- `harness/validate_ext.py` enforces both.
- Cost reporting is now three-way everywhere (`02-mvp-scope.md`, `03-benchmark-design.md`), decisions
  D-019 and D-020.

## 5. Limits

- n = 3 per cell; differences of one or two calls are noise, and the tables above are counts, not
  estimates of a rate with uncertainty.
- One task family, one synthetic table, four instances. No claim about other domains.
- The qualifier rubric is a keyword list, so "mentioned differently" scores as missing.
- glm-5.3-flash's collapse is a single model's behaviour under one prompt; it is reported because it is
  instructive, not because it generalises.
- `cost_payload` is derived by removing reasoning tokens at the same per-token rate, not by a separate
  bill. The derivation is an assumption about pricing, stated here so it can be challenged.
