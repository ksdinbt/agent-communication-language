---
name: typed-payload-v0
description: Use when sending or receiving a typed agent payload with claim status, provenance, authority and deferred detail.
version: 0.1.0
---

# Typed payload v0

Load this once per session. It replaces any format block in a prompt. Seven fields, three rules,
one counter-example. Nothing else is required to read or write a conforming payload.

## The message

One act, then claims, then what you withheld.

```
!ASSERT
claim c1 value=890000 unit=EUR epistemic=OBSERVED observed_at=2026-10-21 src=extract:2026-10-21
qualifier partial_period "week extracted at day 3 of 7"
defer r1 table granularity=[daily,per_player] cost=1800
```

Field list, complete:

1. `act` - `!ASSERT`, `!ASK`, `!REQUEST`, `!OFFER`, `!ACCEPT`, `!REJECT`, `!DELEGATE`, `!REPORT`,
   `!CANCEL`, `!EXPAND`, `!CANNOT_EXPAND`
2. `value` + `unit` - the figure, normalised on read (`890,000` = `890000` = `€890000`)
3. `epistemic` - `OBSERVED` | `DERIVED` | `ASSUMED` | `PREDICTED` | `UNKNOWN`
4. `observed_at` - when the data was captured, not when you sent the message
5. `src` - where it came from; must be resolvable by the receiver
6. `qualifier` - `none` | `partial_period` | `stale_extract` | `definition_changed` |
   `sample_too_small` | `other`, plus a short note
7. `authority` - `INFORM` | `PROPOSE` | `REQUEST` | `AUTHORISE` | `EXECUTE_REPORT`

## Three rules

**1. `ASSUMED` and `PREDICTED` are not actable.** You may quote them, labelled. You may not act on
them where money, customers or published figures are involved. If a decision depends on one, say so.

**2. Ask rather than re-send.** If the message says `defer r1 ...` and you cannot decide without it,
send `!EXPAND r1 granularity=<the coarsest level you need>`. One expansion, then act. Do not request
everything because it is cheaper than thinking.

**3. `UNKNOWN` is a real answer.** If the payload plus your data cannot decide the question, reply
`!REPORT epistemic=UNKNOWN` and name what is missing. A guess that happens to be numerically right
still loses, because the method is what is being tested.

## The counter-example

This is what a message looks like when a qualifier is lost. It is not obviously wrong, and that is
the point:

```
!ASSERT
claim c1 value=890000 unit=EUR epistemic=OBSERVED src=extract
```

What is missing: `observed_at`, and a `qualifier`. The extract was taken on day 3 of a 7-day week, so
the figure is a partial period being compared with complete periods. Without the qualifier, the
receiver will compute a -28% week-over-week change and report it as fact. That exact failure happened
in testing, in both a typed payload and in plain prose.

If you find yourself writing a figure with no `observed_at`, stop: you have removed the receiver's
only means of detecting staleness.

## When you cannot comply

Say so, once, with the field name. `!REPORT epistemic=UNKNOWN qualifier=other
"payload has no unit for claim c2"` is a correct answer. Inventing a unit, or quietly assuming
`OBSERVED` when the field is missing, is not.

---

*Conformance: `spec/ir-extension-v0.1.md` in the same repository. If this document and the
specification disagree, the specification wins - and the disagreement is a bug worth reporting.*
