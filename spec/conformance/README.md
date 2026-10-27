# Conformance vectors

One file per case, plus `expectations.json` mapping filename to expected validity. `harness/validate_ext.py`
implements the rules; `harness/test_ext_conformance.py` runs the vectors and asserts the expectations.

| Vector | Expected | Exercises |
|---|---|---|
| `defer-valid.json` | valid | the full E4 shape: claims, qualifier, deferred ref with granularity and cost hint |
| `defer-invalid-constraint.json` | invalid | rule 4.1, only evidentiary detail may be deferred |
| `defer-no-refs.json` | invalid | rule 4.2, `deferred` requires at least one ref |
| `epistemic-missing.json` | invalid | rule 4.3, `epistemic` is mandatory |
| `observed-no-time.json` | invalid | rule 4.4, `OBSERVED` requires `observed_at` |
| `expand-request.json` | valid | the `!EXPAND` act with ref and granularity, authority=REQUEST |
| `cannot-expand.json` | valid | `!CANNOT_EXPAND` with a qualifier reason |
| `degraded-plain.json` | valid | plain SILP with no `ext`; the degradation target |

Every vector must also survive the degradation check: stripping `ext` leaves a document that still
satisfies the root contract. That is asserted for all eight, including the invalid ones, because a
sender that writes an invalid extension should still produce something a plain SILP receiver can use.

Two properties are asserted separately because they are easy to conflate: a document can be **valid**
and still be **semantically different** from its degraded form. `defer-valid.json` and its stripped
version must therefore compare unequal under the projection, or the extension is doing nothing.
