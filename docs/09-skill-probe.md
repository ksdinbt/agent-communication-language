# Probe: does a loaded skill change receiver behaviour?

**Date:** 2026-10-27
**Cost:** $0.0082 for 20 exchanges. **Models:** five, three of which answered.
**Question:** the pilot (`08-pilot.md`) showed conventions in the prompt cost 1,951 versus 595 reasoning
tokens per exchange. Does moving them into a skill document preserve behaviour, and does it make the
receiver use `!EXPAND`?

Script: `harness/skill_probe.py`. Logs: `results/skill-probe-2026-10-27/runs.jsonl`.

---

## 1. Design

Two conditions, same payload, same question, per model:

| Condition | Where the conventions live |
|---|---|
| `prompt_spec` | a ten-line format block in the system prompt |
| `skill` | a two-line system prompt, plus `skills/typed-payload-v0/SKILL.md` supplied once as context |

Two instances: `partial` (a figure from a three-day-old incomplete week; a qualifier must survive) and
`deferred` (the payload carries `defer r1` and the question needs within-week shape, so `!EXPAND` is the
correct move).

Measured: qualifier preserved in the answer text (keyword rubric, not self-report), whether `!EXPAND`
appeared, tokens, empty completions with their `finish_reason`.

## 2. Results

| Model | Condition | Instance | Qualifier | EXPAND | Tokens | s |
|---|---|---|---|---|---|---|
| glm-5.3-flash | prompt_spec | partial | yes | no | 1086 | 8.2 |
| glm-5.3-flash | prompt_spec | deferred | yes | **yes** | 1638 | 15.1 |
| glm-5.3-flash | skill | partial | - | no | 3170 | 9.1 |
| glm-5.3-flash | skill | deferred | - | no | 3187 | 12.4 |
| deepseek-v4.1-flash-1017 | prompt_spec | partial | yes | no | 1161 | 9.8 |
| deepseek-v4.1-flash-1017 | prompt_spec | deferred | yes | no | 967 | 4.7 |
| deepseek-v4.1-flash-1017 | skill | partial | yes | **yes (spurious)** | 2908 | 4.9 |
| deepseek-v4.1-flash-1017 | skill | deferred | - | no | 3232 | 10.3 |
| gpt-6-luna | prompt_spec | partial | yes | no | 663 | 4.0 |
| gpt-6-luna | prompt_spec | deferred | **no** | yes | 733 | 5.8 |
| gpt-6-luna | skill | partial | yes | no | 2074 | 9.9 |
| gpt-6-luna | skill | deferred | yes | **yes** | 1783 | 9.3 |
| mimo-v2.6-flash | prompt_spec | partial | yes | no | 1762 | 12.9 |
| mimo-v2.6-flash | prompt_spec | deferred | yes | no | 2016 | 57.2 |
| mimo-v2.6-flash | skill | partial | yes | **yes (spurious)** | 1534 | 8.5 |
| mimo-v2.6-flash | skill | deferred | yes | no | 1757 | 14.8 |
| nemotron-3-ultra-550b-a55b:free | both | both | - | - | 0 | HTTP 404 |

`prompt_spec`: 8 valid rows, qualifier preserved in 7. `skill`: 8 rows, qualifier preserved in 5, and
**three of the eight were empty completions**.

## 3. Findings

### 3.1 The skill failed by exhaustion, never by misunderstanding

All three empty answers are `finish_reason=length` with `reasoning_tokens=2000` — the cap. Same failure
mode as the pilot, now triggered by a larger context rather than a denser instruction: the skill adds
about 900 tokens of conventions, the reasoning model thinks proportionally longer, and the content never
gets written.

Of the five skill answers that were produced, **all five preserved the qualifier**. So there is no
evidence here that a skill degrades comprehension; there is strong evidence that it needs a bigger
budget. Any harness that scores empty completions as behavioural failures will systematically
mis-attribute a token-budget problem to the skill.

### 3.2 Token cost roughly doubled, and this probe measures the worst case

Mean tokens: 1,253 (`prompt_spec`) against 2,456 (`skill`). That is the worst case by construction:
the probe loads the skill for a single exchange. The amortising argument — load once per session, send
many messages — cannot be tested with n=1 message per session and should not be claimed from this data.

### 3.3 `!EXPAND` is a suggestion, not a mechanism

Used in 1 of 2 deferred cases under `prompt_spec` and 2 of 2 under `skill`, but also emitted
**spuriously** in two `partial` cases where nothing was deferred (deepseek, mimo). One correct example
is worth keeping: gpt-6-luna under `skill` replied

```
!EXPAND r1 granularity=daily

I can't determine whether the decline was uniform or driven by one day: daily figures are provided for
W41, but not for the W40 comparison. W41's three observed days were €310,000, €330,000, and €250,000;
the weekly comparison is also partial-period versus full-period.

STATUS: qualifier=yes
```

That is exactly the intended behaviour: ask for the coarsest sufficient expansion, and state the
remaining gap. But one instance of it, against two spurious emissions, means the mechanism is not
reliable when it is only described in prose. If E4 is to be tested, the receiver's output must have a
machine-checkable decision contract (act + ref + granularity, validated), not a sentence in a skill.

### 3.4 A listed model may still be unroutable

`nvidia/nemotron-3-ultra-550b-a55b:free` appears in `/api/v1/models` with a price of zero and returns
**HTTP 404** on every chat completion. Model availability must be probed, not read from the catalogue,
before any run is planned around it.

## 4. What changes

1. **`max_tokens` becomes a per-condition parameter**, sized to the context, and reasoning tokens are
   counted against it. The harness must distinguish "no answer because of the budget" from "wrong
   answer", and re-run rather than score.
2. **The receiver's contract becomes structural.** E4 needs a validated decision object (act, ref,
   granularity), so a missing `EXPAND` is a parse failure with a name rather than a stylistic choice.
3. **The skill survives, with a caveat.** It produces correct behaviour when the model answers, but it
   is not cheaper in a one-message session. Its economics belong in Phase 3 with real sessions.
4. **Model availability is a probe, not a lookup.** Add a pre-flight call per model.

## 5. Limits

- n = 2 instances per cell, one seed, four working models, and one of them produced no data at all.
- The qualifier rubric is a keyword list; `prompt_spec`/gpt-6-luna was scored "no" while it did emit
  `!EXPAND`, so keyword scoring conflates "did not mention" with "mentioned differently".
- `deferred` and `partial` differ in both payload and question, so condition effects and task effects
  are confounded in a two-instance design.
- Nothing here tests the extension's semantics: no `!EXPAND` response was ever served, so the round trip
  through an expansion is untested.
