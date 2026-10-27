# MVP scope

**Purpose of this document:** remove every ambiguity about what the first experiment is. If a
question about scope cannot be answered from this page, the scope is wrong, not the question.

---

## 1. Definition

The MVP is **one benchmark harness, five communication arms, two agents, one task family, one
report.**

It exists to answer one question:

> On a delegation-and-verification task, does a typed payload with provenance, authority and
> progressive precision reduce total cost at equal task success, compared with natural language,
> JSON, compact text, and SILP?

It does not exist to produce a library, a standard proposal, or a multi-agent framework.

---

## 2. In scope

| Item | Detail |
|---|---|
| **Two agents** | A (delegator: receives data, forms conclusions, issues a verification task, receives the result) and B (verifier: interprets the task, checks the hypothesis against the same data, returns result with evidence and uncertainty). Different model families, pinned versions. |
| **One task family** | Delegation with verification over a tabular dataset. Four task types: (T1) fact retrieval with a qualification, (T2) hypothesis verification, (T3) metric comparison with an explicit dependency, (T4) recommendation with a stated authority limit. |
| **Five arms** | NL, JSON, compact text, IR (ours), SILP. All arms run the same tasks on the same data with the same number of turns. |
| **IR extension** | E1 epistemic type, E2 evidence reference with observation time, E3 authority axis, E4 resolvable reference with `EXPAND`. Implemented as a documented extension over SILP's IR, with a declared degradation path. |
| **Encoders and decoders** | For the IR arm: readable JSON form and compact text form, both lossless. A binary form only if it is free (CBOR of the JSON form counts). Validators for all. |
| **Semantic projection** | The single comparison function used by every arm, defined once in code and documented here, because SILP's own codec does not preserve the full IR (see `07-silp-runnability.md`). Fields outside the projection may be carried but are not scored. |
| **Harness** | Scripted runner: fixed prompts, fixed seeds, logged raw messages, token counts per tokenizer, wall-clock per step, decode-call counts, task outcome, adjudication record. |
| **Metrics and statistics** | As defined in [`03-benchmark-design.md`](03-benchmark-design.md), including pre-registered equivalence margin. |
| **Report** | Results incl. negative results, threats to validity, reproduction instructions. |

## 3. Out of scope

- Any change to transport, envelope, framing, discovery or authentication (A2A, MCP, NLIP own these).
- Multi-agent topologies beyond two agents (three-agent and negotiation are Phase 4).
- Latent-space or hidden-state communication.
- Fine-tuning or training of any model.
- A general ontology. Vocabulary is scoped to the task family only.
- Production hardening: no auth, no rate limiting, no deployment, no SLA.
- Human-in-the-loop interfaces beyond the adjudication sheet.
- Domain expansion beyond analytics-style tabular reasoning.
- Any claim about "the best" representation. The MVP measures one task family and says so.

## 4. Definitions that remove ambiguity

**Total cost, reported three ways (revised 2026-10-27).** The earlier single scalar confused two
questions. Both are reported now, and only one supports a claim about money:

| Metric | Definition | Supports a savings claim |
|---|---|---|
| `cost_billed` | what the provider invoices: prompt + completion tokens, reasoning included | **yes** |
| `cost_payload` | prompt + completion tokens minus reasoning tokens, same rate | no, alone |
| `reasoning_tokens` | reported per call, separately | n/a |

Reasoning is neither suppressed nor hidden: models may think as long as they need, `max_tokens` is
sized per condition, and `finish_reason=length` means a truncated run that is re-executed, never scored
as a behavioural failure (D-018/D-019). `cost_payload` answers a narrow, legitimate question — how much
of the bill belongs to the payload rather than to the model's deliberation — but a format that halves
`cost_payload` while doubling deliberation has saved nothing.

The per-task scalar, where one is still needed, is:

```
total_cost = tokens_in + tokens_out + w * decode_calls_tokens_equivalent + retry_cost
```

where `decode_calls_tokens_equivalent` is the inference consumed by any additional model call
required to interpret the payload (for a lossless arm: zero; for a natural-language arm parsed by a
model: nonzero), and `w` is fixed **before** the run (default 1.0, sensitivity-tested at 0.5 and 2.0).
Wall-clock latency is reported separately and never folded into this scalar.

**Task success.** Binary per task, decided by a rule-based checker against the ground-truth answer,
with human adjudication for disagreements. A result that is correct but reports a stale figure for a
current one is **not** a success (see qualification loss).

**Qualification loss.** A message pair in which the sender's IR contains a qualifier (uncertainty
marker, dependency, staleness note, authority limit) that is absent or unmarked in the IR recovered
by the receiver. Counted per qualifier, not per message.

**Equal task, equal schedule.** Every arm receives the same task text, the same data, the same turn
budget, and no arm may take extra turns. Arms differ only in payload format and the features that
format carries.

**Minimal sufficient message.** A message that, if interpreted correctly, yields the correct action
by the receiver without a follow-up. Estimated for the IR arm by construction (the IR declares what
it withheld) and for other arms by measuring follow-up turns, which are fixed and therefore zero by
design; this is a known limitation of the schedule and is discussed in the threats to validity.

## 5. Deliverables

1. `spec/ir-extension-v0.1.md` - the four properties, formally stated, with the SILP mapping.
2. `spec/conformance/` - test vectors: valid, invalid, and degradation cases.
3. `harness/` - runner, arm adapters, logging, metric computation.
4. `tasks/` - task definitions, datasets, ground truth.
5. `results/` - raw logs plus the aggregate report.
6. `REPORT.md` - findings, including the case where H1 fails.

## 6. Exit criteria

The MVP is done when **all** of the following hold:

1. Five arms run end to end without manual intervention, on at least 40 task instances, three seeds.
2. Every lossless arm passes the round-trip conformance suite (100% of valid vectors).
3. Total cost, task success, qualification loss and latency are computed automatically from logs.
4. H1 is decided against the pre-registered margin, with confidence intervals.
5. The report states whether H4 (binary/compact encoding does not automatically reduce total cost)
   held, with the decode-cost measurement that decides it.
6. A third party can reproduce one arm from the repository and the recorded model versions.

## 7. Effort estimate

| Work package | Estimate |
|---|---|
| IR extension spec + conformance vectors | 5-8 days |
| SILP adapter (wrap `polyglotIR`, two lossless frontends) | 3-5 days |
| Harness, logging, metrics | 5-8 days |
| Tasks, datasets, ground truth | 4-6 days |
| Runs, adjudication, analysis, report | 6-10 days |

Total: roughly 5 to 7 working weeks for one experienced engineer, excluding model access delays and
review cycles. This is the Phase 1 to Phase 3 scope of the main paper compressed into a single
deliverable; the roadmap's dates assume this compression is acceptable.

## 8. What would make us stop

Declared in advance, so that stopping is a decision rather than a failure:

- SILP adopts epistemic typing and provenance in a successor draft before Phase 1 freeze.
- A published benchmark already measures total cost across natural language, JSON and a typed IR on a comparable
  task family, and we cannot add a dimension to it.
- Decode cost for the compact forms exceeds the token savings in the first pilot, **and** no
  configuration of the harness changes the sign (H4 confirmed for our own design).
- Reference resolution in E4 requires a shared mutable store, which contradicts the stateless
  assumption of MCP and makes deployment implausible.

Any of these produces a written finding and an archived repository, which is a legitimate outcome.
