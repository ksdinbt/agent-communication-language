# SILP reference implementation: runnability gate

**Date:** 2026-10-27
**Question:** can `polyglotIR` serve as benchmark arm A5, and is its claimed lossless round-trip
usable as a comparison baseline?
**Answer:** yes as an arm, but *not* under the naive definition of "lossless". The gate passes with
two conditions and two upstream bugs.

---

## 1. Environment

| Item | Value |
|---|---|
| Repository | `github.com/Juwan-Hwang/polyglotIR`, commit `45e9550`, 2026-07-21 |
| Size | 24 MB including the paper's LaTeX, figures and processed data |
| Python | 3.13.5, venv created with `uv venv` (`python3 -m venv` fails on this host: no ensurepip) |
| Install | `uv pip install -e .` - works, core dependencies are only `pydantic`, `click`, `rich` |
| pydantic | 2.14.1 |
| Not installed | `torch`, `transformers`, `llmlingua` (only needed for the `llmlingua2` lossy frontend) |

The package exposes `silp.ir` (schema, validator, whitelist), `silp.frontend` (five registered
frontends), `silp.negotiation`, and a `silpc` CLI with `compile`, `decode`, `validate`, `lock`,
`frontends`, `whitelist`.

**The implementation is real, not a sketch.** It ships the 27-case example set, a 675-run
generalisation matrix, 2,160 multi-turn heartbeat runs, ablation and entropy analyses, and the
processed data behind every figure. That raises the bar for our programme: SILP is a
well-instrumented incumbent, not a proposal.

## 2. Test suite

`pytest -q`: **183 passed, 12 failed, 1 skipped** in 6.3 s.

Of the 12 failures:

- **10 are missing dependencies**, not defects: every `test_compiles_all_frontends` case fails on
  `ModuleNotFoundError: No module named 'llmlingua'`. The `llmlingua2` frontend is intentionally
  lossy and needs `pip install llmlingua` plus `torch`.
- **2 are genuine defects** in error classification (`tests/test_phase2.py`):
  `is_infra_error("invalid api key (401)")` returns `True`, and `test_no_retry_on_auth_error` gets 2
  retries where it expects 0. The reference implementation would retry an authentication failure.

## 3. Round-trip: the claim, and what it actually measures

The draft (section 4.6) and `frontend/base.py` both promise `decode(compile(ir)) == ir` for the
`code` and `json` frontends. Two different measurements give two different answers.

### 3.1 Against the project's own verifier - 52/54 pass

`scripts/mvp_roundtrip.py::verify_roundtrip` compares a *projection* of the IR: `intent`; primary
entities as `(id, value)`; secondary entities as `(value, action)`; constraints by
`type`/`value`/`time`/`operator`/`subject`; alternatives in full. It **does not compare `meta`**.

Running it over all 27 bundled examples times both frontends: 52 of 54 pass. The two failures are
real and reproducible:

| Case | Frontend | Error |
|---|---|---|
| `case5b_tool_branch` | code | `decode() raised: Cannot parse constraint: 'disk>90%'` |
| `case5c_tool_branch` | code | `decode() raised: Cannot parse constraint: 'error_rate>5%'` |

Both involve an operator (`>`) combined with a percentage value. The code frontend emits a surface
form its own decoder cannot read back.

### 3.1b Against the benchmark's serialised projection - 36/54

Scoring the same 54 combinations on **serialised** documents (what a peer actually receives) with
`harness/projection.py` gives 36 of 54. All 16 additional failures are `code`-frontend constraint
fields that disappear on `model_dump()`.

The mechanism is worth stating precisely, because it explains why 52/54 and 36/54 are both correct
answers to slightly different questions: the `code` frontend restores `subject` with
`object.__setattr__`, which puts it in the instance `__dict__` and leaves `__pydantic_extra__` empty.
`getattr` sees it (so `verify_roundtrip`, which compares attributes, passes); `model_dump()` and every
serialisation do not (so a message on a wire loses it). The `json` frontend round-trips the field
properly.

Reported upstream as issue #3. For this programme the serialised definition is the one that matters,
which is why the benchmark scores on the projection and not on IR identity.

### 3.2 Against the promise in the docstring - 0/54

Comparing `model_dump(mode="json")` of the original and the decoded IR, **none** of the 54
combinations survive. Three causes, all structural rather than accidental:

1. **Secondary entity ids are lost.** `{id: "notify", value: "zhangsan", action: "!EMAIL"}` comes back
   as `{id: "act", ...}`. The project's verifier knows this and deliberately compares only
   `(value, action)` for secondary entities, with the comment *"id may be lost in code frontend
   (positional args always decode as id='act')"*.
2. **Constraint `subject` is dropped** by at least the code frontend: `loc(me, Beijing, t+1am)`
   decodes without `subject: "me"`.
3. **`meta` is not transported at all.** For `case1`: `priority` 1 → 0, `confidence` 0.9 → 1.0,
   `seq` `["reason_first"]` → `[]`, and `req_id` `a3f9` → `1383`, i.e. a *new* identifier is generated
   on decode.

Cause 3 is the one that matters for this programme.

## 4. What this means for arm A5

**The gate passes.** The codebase installs in under a minute, the CLI works, the core tests pass, and
the two lossless frontends compile every example. A5 is implementable.

**Condition 1: "lossless" must be defined before it is used.** Our benchmark cannot compare full IRs
across arms, because SILP's own codec does not preserve them. The comparison must be made on a
declared **semantic projection**, and that projection must be identical for every arm - otherwise arm
A4 would be penalised for carrying fields A5 silently drops. The projection belongs in
`03-benchmark-design.md` and in code, not in prose.

**Condition 2: `meta` is not a safe place for our extensions.** SILP already keeps `confidence` in
`meta` - the one epistemic field it has - and `meta` does not round-trip. Two consequences:

- SILP's `confidence` cannot be measured fairly across a two-agent hop without fixing the codec or
  redefining the metric, because the value is replaced by the schema default on decode.
- Our E1-E4 fields must live in the **semantic body** (entities, constraints, alternatives) or in an
  extension that the codec actually carries. Putting them in `meta` would inherit a silent data-loss
  bug. This is a design constraint discovered by running the code, not by reading the draft.

**Two bugs reported upstream** (courtesy, not a blocker). Both were verified to a root cause before
reporting, with minimal reproductions and suggested patches:

| Issue | Defect | Root cause |
|---|---|---|
| [#1](https://github.com/Juwan-Hwang/polyglotIR/issues/1) | `disk>90%` compiles but does not decode | `code.py:177`, value character class `[\w.]+` excludes `%` |
| [#2](https://github.com/Juwan-Hwang/polyglotIR/issues/2) | `is_infra_error("...401")` returns `True`, contradicting its docstring and two failing tests | `models.py:102-114` lists `401|403` as retryable infrastructure errors |
| #3 (filed 2026-10-27, pending number) | extra constraint fields survive only in memory: 36/54 on serialised documents | `code.py` restores them with `object.__setattr__`, so `model_dump()` drops them |

If #1 is fixed upstream, the round-trip result on this commit improves from 52/54 to 54/54 under the
project's own definition; it does not change the projection result, which is why D-014 stands either
way.

## 5. Residual unknowns

- The `json` frontend's behaviour on `subject` was observed only through the aggregate comparison; a
  per-frontend matrix should be produced in Phase 1 rather than inferred.
- Nothing here tested `silp.negotiation` (handshake, sessions, heartbeat) or the `bench` layers 4-5.
  Those are irrelevant to A5 as a payload codec, but relevant if we later adopt SILP's negotiation
  instead of defining our own.
- The 675-run matrix and heartbeat data were not re-executed; only the bundled processed CSVs were
  read. Reproducing them requires API keys and is out of scope for the gate.

## 6. Verdict

| Item | Status |
|---|---|
| Installs and runs on Linux | yes |
| CLI usable | yes |
| Core test suite | 183 pass, 2 genuine failures |
| Lossless frontends compile all examples | yes |
| Round-trip under project's own definition | 52/54 |
| Round-trip under full-IR equality | 0/54 |
| Usable as benchmark arm A5 | **yes, with a declared semantic projection** |
| Defects reported to the author | 2 (issues #1 and #2) |
| Safe to extend via `meta` | **no** |
