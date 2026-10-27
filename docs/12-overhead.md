# Overhead probe: the skill is not what was expensive, and it may not be needed

**Date:** 2026-10-27
**Cost:** $0.0075 for 32 calls. **Models:** `xiaomi/mimo-v2.6-flash`, `openai/gpt-6-luna`.
**Reps:** 2 per cell.

Script: `harness/overhead_probe.py`. Logs: `results/overhead-probe-2026-10-27/runs.jsonl`.

---

## 1. Premise, and why it was wrong

After the length probe I attributed the fixed overhead to the skill document and the JSON contract
being re-read on every call, and set out to cut them. The premise was partly false, and the probe shows
why.

Four variants, same payloads, same questions, four calls per model per variant:

| Variant | Conventions supplied | Contract supplied |
|---|---|---|
| `v0` | long skill (3.2k chars, current) | prose schema: key list plus rules |
| `v1` | compact skill (1.3k) | prose schema |
| `v2` | compact skill (1.3k) | example-based: three worked JSON objects |
| `v3` | **none** | example-based |

## 2. Results

| Variant | Prompt tokens | Reasoning tokens | Billed per call | Valid JSON | Qualifier ok | EXPAND correct |
|---|---|---|---|---|---|---|
| v0 long skill + prose contract | 1,381 | 305 | $0.000262 | 8/8 | 8/8 | 8/8 |
| v1 short skill + prose contract | 861 | 526 | $0.000305 | 8/8 | 8/8 | 6/8 |
| v2 short skill + example contract | 846 | 247 | $0.000212 | 8/8 | 8/8 | 7/8 |
| **v3 no skill + example contract** | **452** | **223** | **$0.000161** | **8/8** | **8/8** | **8/8** |

## 3. Findings

### 3.1 The prompt is 67% smaller with no behavioural loss

`v3` carries 452 prompt tokens against 1,381, and costs 39% less per call ($0.000161 against
$0.000262), while scoring the same on validity, qualifier retention and `!EXPAND` correctness.

The mechanism is not "less text is better". It is that **a worked example teaches the format more
efficiently than a specification of it**. The prose contract lists eight keys, their enums and three
rules; the example contract shows three complete objects, one per decision type. Models are trained to
continue patterns, not to implement schemas.

### 3.2 Compression without an example made things worse

`v1` (compact skill, prose contract) is the informative failure: prompt tokens fell 38% but reasoning
rose 72% (305 to 526) and billed cost *increased* by 16% over `v0`, with `!EXPAND` correctness dropping
to 6/8.

So trimming prose does not reduce deliberation; it can increase it, because a terser specification
leaves more to infer. That is the opposite of the intended effect and it is the trap in "just shorten
the prompt".

### 3.3 My diagnosis of the 2,826-token overhead was wrong

The length probe reported 2,826 reasoning tokens per turn in the payload arm at T=1. Here, the same
skill and contract produce 223 to 526 reasoning tokens per call, depending on variant. The difference
is not the conventions: it is that the T=1 session carried all eight data rows in one message and asked
for a weekly judgement.

The fixed overhead is therefore **task density**, not instruction length. Cutting the skill does not
touch it. That correction matters, because the design response is different: reduce what a single
message asks the model to hold, not how the conventions are worded.

### 3.4 A scoring artefact, found and fixed

The first pass scored `v3` at 4/8 on qualifier retention. All four "misses" were `deferred` instances
where the receiver correctly chose `!EXPAND` and asked for the daily split instead of restating the
caveat. The rubric was rewarding a behaviour that is not required.

Corrected rule, now in the benchmark design: when the receiver issues a correct expansion request, the
qualifier does not have to be repeated. Restating a caveat while asking for the data behind it is
polite, not correct.

## 4. Decisions

**D-023.** For simple payloads, a separate skill document is not required: an example-shaped contract
in the system prompt matches or beats the long skill at one third of the prompt tokens. The v0 skill
stays in the repository as reference documentation for humans and for complex payloads; it is not
loaded per call. Use `v3` as the harness default until a payload needs more than one claim, a
deferred negotiation, or `!CANNOT_EXPAND`.

**D-024.** Qualifier scoring: a correct `!EXPAND` counts as qualifier-compliant. The receiver is not
required to restate a caveat while requesting the data behind it.

## 5. What this changes

1. **The overhead target moves.** The thing to attack is message density at long context, not
   convention wording. The next design question is how much of a series one message should carry.
2. **The skill file survives as documentation, not as a runtime artefact.** That simplifies the harness:
   no skill injection, no `assistant: "ok"` acknowledgement turn, one system prompt with examples.
3. **The example-shaped contract should be tested on harder payloads** (multiple claims, deferral
   chains, `!CANNOT_EXPAND`) before it is adopted generally. This probe covered one claim and one
   deferral, and the skill may earn its place exactly where the example runs out.

## 6. Limits

- n = 8 calls per variant (2 models, 2 instances, 2 reps). Counts, not rates with intervals.
- One claim, one qualifier, one deferral. Complex payloads are untested, which is precisely where the
  skill is most likely to matter.
- Both models are fast and cheap; a weaker model may need the specification rather than the example.
- `response_format: json_object` was requested in all variants, so the contract's *shape* was partly
  enforced by the API. Without it, the gap between the prose and example contracts could widen.
