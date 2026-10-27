# Agent Communication Language

A research programme on **model-independent semantic communication between AI agents**: whether a
shared, typed representation of meaning, encoded in several interchangeable formats, measurably
improves the cost, reliability and fidelity of agent-to-agent information exchange compared with
natural language or JSON.

- **Status:** Phase 0 (research and baseline) complete; Phase 1 not started.
- **Owner:** BI unit, Inbet Online Ltd.
- **Nature of this repository:** research documentation. It intentionally contains **no claim of
  novelty yet**. See [What is actually new](#what-is-actually-new) below.
- **Working draft (Polish):** maintained in Trilium, note *Agent Communication Language*. The
  English documents here are the authoritative version.

## Start here

| Document | Purpose |
|---|---|
| [`docs/00-paper.md`](docs/00-paper.md) | The paper: problem, architecture, requirements, hypotheses, roadmap, metrics, risks |
| [`docs/01-state-of-the-art.md`](docs/01-state-of-the-art.md) | Verified status of SILP, NLIP, FIPA-ACL, DALA, MOC, A2A, MCP, plus the gap analysis |
| [`docs/02-mvp-scope.md`](docs/02-mvp-scope.md) | Unambiguous MVP: in scope, out of scope, exit criteria |
| [`docs/03-benchmark-design.md`](docs/03-benchmark-design.md) | Experiment protocol: arms, tasks, metrics, statistics, threats to validity |
| [`docs/04-glossary.md`](docs/04-glossary.md) | One term, one meaning (PL/EN) |
| [`docs/05-decisions.md`](docs/05-decisions.md) | Dated decisions, with what would overturn each |
| [`docs/06-literature-review.md`](docs/06-literature-review.md) | Systematic sweep: method, query log, full-text findings, and what each gap claim survived |
| [`docs/07-silp-runnability.md`](docs/07-silp-runnability.md) | Gate result: does the incumbent actually run, and what does its "lossless" round-trip really preserve |
| [`docs/08-pilot.md`](docs/08-pilot.md) | Two-agent pilot: 12 exchanges for one cent, and what it changed in the plan |
| [`docs/09-skill-probe.md`](docs/09-skill-probe.md) | Does a loaded skill change receiver behaviour? Five models, two conditions, one clear failure mode |
| [`docs/10-contract-probe.md`](docs/10-contract-probe.md) | Receiver contract: 48/48 valid responses, one fabricated figure, and reasoning at 74% of the bill |
| [`docs/11-length-probe.md`](docs/11-length-probe.md) | Does the payload gap grow with session length? Two quantities, and a crossover not yet reached |
| [`docs/12-overhead.md`](docs/12-overhead.md) | The convention overhead, attacked: 67% smaller prompt, and why a worked example beats a schema |
| [`docs/13-final-outcome.md`](docs/13-final-outcome.md) | **Start here for the conclusion:** what survived, what did not, and what the MVP must do next |
| [`spec/ir-extension-v0.1.md`](spec/ir-extension-v0.1.md) | E4 specification: deferred detail, `!EXPAND`, degradation to plain SILP |
| [`skills/typed-payload-v0/SKILL.md`](skills/typed-payload-v0/SKILL.md) | The agent-facing skill: seven fields, three rules, one counter-example |
| [`docs/REFERENCES.md`](docs/REFERENCES.md) | Every source with version, status and verification date |

## What is actually new

As of 2026-10-27, the concept "a semantic intermediate representation compiled into several surface
encodings, with runtime negotiation of the encoding" is **already specified** by SILP
(`draft-hwang-silp-protocol-02`, July 2026). Any paper built on that thesis alone is not
publishable.

This programme therefore targets four concrete, verifiable gaps that SILP and the other cited
protocols do not cover:

1. **Epistemic typing** - distinguishing observations, inferences, assumptions, predictions and
   acknowledged ignorance, instead of a single scalar `confidence`.
2. **Provenance and evidence** - every claim carries source, observation time and reliability of
   that source, so a receiving agent can weigh it rather than trust it.
3. **Authority semantics** - separating "describing an action", "proposing it", "requesting it",
   "authorising it" and "having executed it". A well-formed message is not an authorised one.
4. **Progressive semantic precision** - sending the minimum sufficient message plus resolvable
   references, and expanding detail only on demand.

The contribution is the **evaluation**, not the syntax: whether these properties buy measurable
accuracy or cost, against SILP as the incumbent baseline rather than only against natural language.

## Non-goals

- Replacing A2A, MCP or NLIP transport and envelope layers.
- Latent-space or hidden-state communication (a genuinely different paradigm, tracked in
  `docs/01-state-of-the-art.md`).
- A new compression algorithm.
- A production library. Phase 1-3 produce a reference implementation and a benchmark harness only.

## Reproducing the baseline

Phase 0 was desk research; every claim in `docs/01-state-of-the-art.md` is marked as *read from the
source*, *read from the abstract only*, or *unverified*. Verification dates are recorded. Nothing in
this repository should be cited without checking the source version listed in `docs/REFERENCES.md`,
because three of the seven cited artefacts changed status within the last twelve months.
