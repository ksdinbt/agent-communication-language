# Final outcome of the exploratory phase

**Date:** 2026-10-27
**Total spend:** $0.1087 across 239 model calls, six experiment runs.
**Question this answers:** is the programme's thesis still alive, and what exactly survived?

---

## 1. Verdict in six sentences

The thesis survived, but not in the form it was written in. A typed payload **does** carry state across
turns that prose loses, and that is measurable and stable. It **does not** make the receiver attend to
caveats it would otherwise ignore, and it **does not** protect against a sender that states a wrong
number — the receiver's own cross-check does that, with or without the format. The economics are not
settled: at short sessions the payload is 5x dearer per turn, at eight turns 1.46x, and the crossover
was not reached. The strongest reason to keep going is behavioural, not financial: qualifier retention
separated the arms cleanly, and a validated response contract removed a whole class of parse failure.
The strongest reason to stop is that a peer-reviewed paper (MOC) already reports the efficiency trap we
set out to catch, and our own numbers show the payload layer is not where trust is won.

## 2. What was built and measured

| Run | Calls | Cost | What it decided |
|---|---|---|---|
| `pilot` | 12 | $0.0098 | instruction density, not syntax, dominates the bill; traps fail in prose too |
| `skill-probe` | 20 | $0.0082 | a skill document produces no wrong answers but exhausts token budgets |
| `contract-probe` | 96 | $0.0303 | a JSON contract fixes shape, not truth (one fabricated figure), and reasoning is 74% of the bill |
| `length-probe` | 8 sessions | $0.0324 | payload per-turn cost is flatter (+80% drift vs +410%); crossover not reached at 8 turns |
| `overhead-probe` | 32 | $0.0075 | a worked example beats a specification: prompt -67%, cost -39%, behaviour identical |
| `complex-probe` | 71 | $0.0204 | multi-claim and deferral cases handled; contradictions reported truthfully but rarely flagged |

## 3. Hypothesis by hypothesis

### H1 - typed payload reduces total cost at equal task success: **not shown, and likely false at small scale**

Measured per turn: `payload` $0.001489 at one turn against `nl` $0.000292; at eight turns $0.001070
against $0.000734. The payload is dearer at both lengths. Its penalty amortises (5.1x to 1.46x) and its
drift is much flatter, but no crossover was observed.

Falsified as stated ("reduces cost"), provisionally alive as "reduces the growth of cost with session
length" - which is a different hypothesis and needs sessions of 15 to 25 turns to test.

### H2 - typed claims preserve qualifications that prose loses: **supported, and the only stable behavioural signal**

Across probes: payload preserved the planted qualifier in 4/4 length-probe sessions at both lengths;
prose lost the partial-week caveat in half of them, at one turn and at eight. In the contract probe,
48/48 structured responses validated and the qualifier survived whenever the receiver did not correctly
choose to expand instead.

Caveat: the effect was measured with 2-3 repetitions per cell. It is consistent, not statistically
established.

### H3 - agents can transmit references instead of full descriptions: **mechanically supported, economically unproven**

`!EXPAND` was used correctly in 45/48 contract calls once the answer shape was validated; in prose it
appeared correctly in most deferred cases but also spuriously in non-deferred ones. The mechanism works
when it is a validated field, and it is noise when it is a sentence in a prompt.

No measurement yet shows that expansion is cheaper than having sent the detail. That is the missing half
of H3, and it is the cheapest remaining experiment.

### H4 - compact encoding does not automatically reduce total cost: **confirmed, twice**

In our own pilot the naive typed arm cost 2.4x the tokens of prose. Externally, MOC (ICML 2026) reports
total tokens rising 18.1% while presenting itself as an efficiency method. The trap is real, published,
and we fell into its milder form ourselves.

## 4. The finding that reorganises the programme

**A payload carries state; it does not create attention, and it cannot certify truth.**

Three independent observations support this. In the pilot, the planted partial-week trap was missed in
prose and in the typed payload alike. In the contract probe, one model satisfied every schema key while
reporting exactly double the correct figure, labelled `OBSERVED`, with the caveat silently dropped. In
the complex probe, all three models reported the table's true value when the sender's number was wrong -
but only because they restated the number, not because the payload's `epistemic=OBSERVED` did anything;
and only two thirds explicitly flagged the mismatch.

So the defensible claim for the specification is narrow:

> Typing a payload makes caveats **transportable and checkable**. It does not make them **noticed**, and
> it does not make a wrong number **right**. Those require a receiver-side rule - verify the value against
> the source, and state a qualifier or say why it was dropped - which is why rules 4.6 and 5.5 exist.

## 5. What is adopted

| Item | Decision | Status |
|---|---|---|
| Semantic projection for scoring | D-014 | implemented, 10 tests |
| Extensions never in `meta` | D-015 | rule in spec |
| Example-shaped contract, no per-call skill | D-023 | adopted as harness default |
| Cost reported as billed / payload / reasoning | D-019 | in all docs |
| E1 never self-declared | D-020 | rule in spec |
| Level and drift, never one average | D-021 | reporting rule |
| Crossover measured, not assumed | D-022 | reporting rule |
| Correct `!EXPAND` counts as qualifier-compliant | D-024 | scoring rule |
| `!REPORT` must carry its number; dropping a qualifier needs a reason | spec 4.6 / 5.5 | enforced by validator, 34 tests |
| SILP as benchmark arm | D-014 | runnable, 2 defects reported upstream |

## 6. What the MVP must do next

1. **Sessions of 15 to 25 turns.** Below that, the payload is measured in the regime where it is
   structurally weakest, and the crossover cannot appear.
2. **Measure expansion economics.** For each deferred payload, record the cost of the expansion round
   trip against the cost of having sent the detail inline. This is the missing half of H3 and it is one
   afternoon of work.
3. **Make the receiver's value-check a rule, not a hope.** The harness, not the model, compares
   `claims[].value` with the source. Any mismatch is a recorded finding, independent of what the model
   said. The complex probe shows models will often get this right by accident; a benchmark must not
   depend on that.
4. **Keep the behavioural metric primary.** Qualifier retention and contradiction-flagging are the
   metrics with a live signal. Cost is currently an argument against the design, and pretending
   otherwise would be the failure mode this programme exists to document.

## 7. Honest bottom line

If someone asks "did the typed payload win", the answer today is: **it won on one axis, lost on another,
and tied on a third.** It carried the caveat when prose dropped it; it cost more per turn at every
length tested; it changed nothing about whether a wrong number was caught.

That is a legitimate research result, and it is worth more than a favourable pilot would have been. The
programme should continue, but it should stop claiming an efficiency thesis and start claiming a
provenance-and-caveat thesis, with the efficiency question honestly marked as open and probably
unfavourable at small scale.
