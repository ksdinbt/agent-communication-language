# IR extension v0.1: progressive precision (E4)

**Status:** draft for Phase 1 review
**Date:** 2026-10-27
**Depends on:** SILP `draft-hwang-silp-protocol-02` (IR at `ir-v0.1`), `07-silp-runnability.md`,
`harness/projection.py` (projection `1.0`)
**Scope:** E4 only. E1-E3 are deliberately excluded; see section 8.

---

## 1. What this specifies

A payload that carries the **minimum sufficient message** plus declared, resolvable references, and a
single act (`!EXPAND`) by which a receiver asks for the rest.

The design goal is not compression. It is that the sender states what it *could* supply and the
receiver decides whether it needs it, so that detail is paid for only when it changes a decision.

## 2. Shape, and why it is removable

SILP's root object is strict (`extra="forbid"`), so an extension cannot be a new root field without
version gymnastics. It is therefore a sibling key, `ext`, with its own version:

```json
{
  "silp": "v1",
  "version": "ir-v0.1",
  "intent": "!ASSERT",
  "entities": [{"id": "act", "value": "turnover_2026-W41", "action": "!ASSERT"}],
  "constraints": [{"type": "segment", "value": "sports"}],
  "alternatives": [],
  "meta": {"req_id": "8f2c1a0e"},
  "ext": {
    "ext_version": "e4-v0.1",
    "authority": "PROPOSE",
    "claims": [
      {"id": "c1", "epistemic": "OBSERVED", "value": "890000", "unit": "EUR",
       "observed_at": "2026-10-21T00:00:00Z", "source": "extract:2026-10-21"}
    ],
    "qualifier": {"type": "partial_period", "note": "week extracted at day 3 of 7"},
    "precision": {
      "resolution": "deferred",
      "refs": [
        {"id": "r1", "kind": "table", "granularity": ["daily", "per_player"],
         "estimated_tokens": 1800, "evidence": ["extract:2026-10-21"]}
      ]
    }
  }
}
```

**Degradation is a conformance requirement.** Deleting `ext` must yield a document that validates
against `ir-v0.1` unchanged. That is the whole point: a receiver that does not implement E4 still gets
a usable SILP message, minus the deferral, and must then treat the figures as the sender stated them.

## 3. Fields

| Field | Type | Rule |
|---|---|---|
| `ext.ext_version` | string | `^e4-v\d+\.\d+$`. Absent `ext` means plain SILP. |
| `ext.authority` | enum | `INFORM`, `PROPOSE`, `REQUEST`, `AUTHORISE`, `EXECUTE_REPORT`. Default `INFORM`. |
| `ext.claims[]` | array | At least one when `intent` is `!ASSERT` or `!REPORT`. |
| `claims[].id` | string | Unique within the message; the handle used by `!EXPAND` and by corrections. |
| `claims[].epistemic` | enum | `OBSERVED`, `DERIVED`, `ASSUMED`, `PREDICTED`, `UNKNOWN`. No default: mandatory. |
| `claims[].value` | string or number | Compared after normalisation, see section 6. |
| `claims[].unit` | string | Mandatory when `value` is numeric and the unit is not carried by the field name. |
| `claims[].observed_at` | RFC 3339 timestamp | When the data was captured. **Not** when the message was sent. |
| `claims[].source` | string | Free-form identifier resolvable by the receiver, or a URI. |
| `ext.qualifier.type` | enum | `none`, `partial_period`, `stale_extract`, `definition_changed`, `sample_too_small`, `other`. |
| `ext.precision.resolution` | enum | `inline` (everything germane is present) or `deferred` (see `refs`). |
| `ext.precision.refs[]` | array | Required when `resolution` is `deferred`; empty otherwise. |
| `refs[].id` | string | Unique; the argument of `!EXPAND`. |
| `refs[].kind` | enum | `table`, `metric_definition`, `segment`, `period`, `evidence`, `codebook`. |
| `refs[].granularity[]` | array of strings | What the sender can supply, if asked. Ordered coarse to fine. |
| `refs[].estimated_tokens` | integer | Cost hint so the receiver can decide. Optional but recommended. |
| `refs[].evidence[]` | array | Source identifiers supporting the reference. |

### 3.1 The `!EXPAND` act

Requested by the receiver when `resolution` is `deferred` and it cannot decide:

```json
{"intent": "!EXPAND",
 "entities": [{"id": "ref", "value": "r1", "action": "!EXPAND"},
              {"id": "granularity", "value": "daily", "action": "!EXPAND"}],
 "constraints": [{"type": "reason", "value": "need within-week shape to judge period partiality"}],
 "meta": {"req_id": "9a1b2c3d", "session_id": "s1"},
 "ext": {"ext_version": "e4-v0.1", "authority": "REQUEST"}}
```

The sender answers with a message whose `precision.resolution` is `inline` and whose `refs` block is
empty, or with `intent: "!CANNOT_EXPAND"` and a `qualifier.type` explaining why (for example
`sample_too_small`). Silence is not a permitted response.

## 4. Rules a conforming sender must satisfy

1. **Only evidentiary detail may be deferred.** `intent`, `entities`, `constraints` and `alternatives`
   are never deferred: they determine what the message *is*. A message that defers a constraint is
   invalid, not merely unhelpful.
2. **`resolution: deferred` requires at least one ref**, and every ref must carry a non-empty
   `granularity`; a reference the sender cannot resolve is a broken promise.
3. **`epistemic` is mandatory on every claim.** Omitting it is an error, not a default to `OBSERVED`.
4. **`observed_at` is mandatory on `OBSERVED` and `DERIVED` claims.** A figure without an observation
   time cannot be checked for staleness by the receiver.
5. **`authority: AUTHORISE` requires a `source`** naming who authorised it.
6. **A numeric `!REPORT` must carry a non-null `value`.** A null `value` with a figure in the prose is
   invalid: the machine-readable layer must contain the number a consumer would act on, or the number
   must not be there at all. Without that, the receiver
   must treat the message as `PROPOSE` regardless of what it says.

## 5. Rules a conforming receiver must satisfy

1. **At most one `!EXPAND` before acting.** Two rounds turn a payload into a conversation, which is what
   we are trying to avoid.
2. **`ASSUMED` and `PREDICTED` claims are not grounds for action** that affects money, customers or
   published figures. The receiver may quote them, labelled.
3. **`UNKNOWN` is a valid answer.** If the message plus the data cannot decide the question, the
   receiver reports `UNKNOWN` with the missing information named, and does not guess. A guessed answer
   scores zero even when numerically correct, because the method is what we are testing.
4. **Dropping the sender's `qualifier` requires a reason.** `qualifier: "none"` is only valid when the
   receiver either confirms the qualifier does not apply or names the change (`definition_changed`,
   `sample_too_small`). Silently discarding `partial_period` is an error.
5. **A deferred reference that the receiver needed but did not request is a receiver error**, recorded
   as such. This is the one place where the failure is not the sender's.

## 6. Normalisation (shared with the benchmark)

Values are compared after the normalisation implemented in `harness/projection.py`:

- numbers become floats: `890000`, `890,000`, `890 000`, `€890000` are the same value;
- units are preserved as lowercase suffixes: `90%`, `200ms`;
- text is lowercased and whitespace-collapsed;
- entity ids and all `meta` fields are excluded from comparison (see `07-silp-runnability.md` for the
  measurement that forced this);
- `ext` quality fields (`epistemic`, `authority`, `qualifier`, `refs`) **are** compared, because they
  are the payload of this specification.

## 7. Conformance vectors

`spec/conformance/` contains, for each case, the IR and the expected outcome:

| Vector | Expectation |
|---|---|
| `defer-valid.json` | valid; `ext` present; dropping `ext` still validates as `ir-v0.1` |
| `defer-invalid-constraint.json` | invalid: a constraint is marked deferred |
| `defer-no-refs.json` | invalid: `resolution=deferred` with empty `refs` |
| `epistemic-missing.json` | invalid: claim without `epistemic` |
| `observed-no-time.json` | invalid: `OBSERVED` without `observed_at` |
| `expand-request.json` | valid `!EXPAND` with ref id and granularity |
| `cannot-expand.json` | valid `!CANNOT_EXPAND` with a qualifier reason |
| `degraded-plain.json` | the same message with `ext` removed: valid `ir-v0.1` |

The projection must report `defer-valid` and `degraded-plain` as **different** (the extension changes
meaning) but both must be *valid* documents. A test asserting otherwise is testing the wrong thing.

## 8. What is deliberately missing

- **E1 beyond a type label.** `epistemic` is a closed set with no confidence value. The pilot showed a
  receiver's own confidence statement contradicted its prose (`08-pilot.md`, finding 4), so a numeric
  field would invite the same error at the protocol level.
- **E2 beyond `source` and `observed_at`.** Evidence chains, hashes and trust scoring belong to the
  execution-provenance literature (arXiv:2606.04990) and are out of scope here.
- **E3 beyond the authority enum.** Authentication and policy enforcement are transport and IAM
  concerns; this field only makes the authority status travel with the payload.
- **Negotiation of feature support.** Until a receiver's capability is exchangeable, `ext` is
  best-effort and degradation is the only guarantee.

## 9. Open questions for Phase 1 review

1. Is `ext` the right carrier, or should the extension be an `entities`/`constraints` convention inside
   SILP's extensible sub-objects? `ext` is cleaner to validate and to strip; the sub-object route
   needs no version bump but pollutes the semantic body.
2. Should `estimated_tokens` be mandatory? It is the only field that lets a receiver make a cost
   decision, and it is also the field most likely to be wrong.
3. What is the unit of `EXPAND` cost in the benchmark: one extra round trip, or the tokens of the
   expanded payload? Both matter and they are not proportional.
4. Does `!EXPAND` belong in the act vocabulary at all, or should it be a `constraint` on a normal
   request? The FIPA lineage would make it a performative; SILP's whitelist would exclude it.
