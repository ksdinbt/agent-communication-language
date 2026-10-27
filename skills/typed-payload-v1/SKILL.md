---
name: typed-payload-v1
description: Use when sending or receiving a typed agent payload. Compact form: one page, seven fields, two rules.
version: 1.0.0
---

# Typed payload v1 (compact)

```
!ASSERT c1 value=890000 unit=EUR epistemic=OBSERVED observed_at=2026-10-21 src=extract:2026-10-21
qualifier partial_period "week extracted at day 3 of 7"
```

Fields: `act` (!ASSERT !ASK !REQUEST !REPORT !OFFER !ACCEPT !REJECT !DELEGATE !CANCEL !EXPAND
!CANNOT_EXPAND) · `value` `unit` · `epistemic` (OBSERVED DERIVED ASSUMED PREDICTED UNKNOWN) ·
`observed_at` (when captured, not when sent) · `src` · `qualifier` (none partial_period stale_extract
definition_changed sample_too_small other) · `authority` (INFORM PROPOSE REQUEST AUTHORISE
EXECUTE_REPORT) · `defer` (ref, kind, granularity, cost)

**Two rules.** `ASSUMED` and `PREDICTED` are quotable, not actable. `UNKNOWN` is a valid answer: name
the gap instead of guessing.

**Ask, do not re-send.** `defer r1 table granularity=[weekly,daily]` invites `!EXPAND r1
granularity=daily`. Once, then act.

**Counter-example.** `value=890000 epistemic=OBSERVED src=extract` with no `observed_at` and no
`qualifier` is a partial week compared against full weeks, and it will be reported as a decline.
