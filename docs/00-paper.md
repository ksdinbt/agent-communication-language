# A Semantic Communication Layer for AI Agents

### Concept, research assumptions and development plan

**Version:** 0.2 (Phase 0 complete)
**Date:** 2026-10-27
**Status:** conceptual; state of the art reviewed; no experimental results yet
**Author:** BI unit, Inbet Online Ltd.

---

## Abstract

Agents built on large language models exchange information almost exclusively in natural language or
in JSON structures. Both are universal and human-readable, but they consume tokens, add latency, and
degrade under repeated re-interpretation: a claim paraphrased three times between three agents is no
longer the claim that was made. This document sets out a research programme to determine whether a
shared, typed semantic representation, independent of model, tokenizer, programming language and
transport, can improve the ratio of *correctly transmitted and used information* to *computational
cost*.

The programme does not assume that a new language is necessary. Phase 0 established that a
substantial part of the concept is already implemented: SILP specifies a reference semantic IR
compiled into multiple surface encodings with runtime negotiation. What remains unaddressed across
all reviewed work is the **epistemic and authorisational quality** of the payload: whether a claim is
an observation, an inference or a guess; where it came from; who was entitled to assert it; and
whether detail can be requested rather than pre-transmitted. The contribution we propose to test is
therefore narrow and falsifiable, and its success criterion is a measured improvement against SILP,
not against natural language alone.

---

## 1. Problem statement

Three costs are routinely conflated when agents talk to each other.

**Token cost.** Prose and verbose JSON both spend tokens on syntax and redundancy rather than on
information. This is the cost most often optimised, and the least interesting: it is measurable but
weakly coupled to task success.

**Interpretation cost.** Every hop that re-reads and re-writes a message is a lossy operation
performed by a stochastic system. Qualified statements ("probably", "unless the promotion is still
running", "based on last week's extract") are the first casualties, and negations and numeric ranges
are the second. The failure is silent: the receiving agent does not know that a caveat was dropped.

**Trust cost.** A structurally valid message says nothing about whether its sender was entitled to
assert it, whether the evidence behind it is current, or whether the sender's stated confidence
corresponds to anything. Today this is handled by out-of-band convention: system prompts, role
descriptions, human review.

The design objective follows from this, and it is deliberately not "fewer tokens":

> Maximise the amount of correctly transmitted **and correctly used** information per unit of
> computational cost.

A compact syntax that halves the token count but costs an extra model call to decode has not
improved anything. This is the central risk of the entire programme, and the benchmarks in
[`03-benchmark-design.md`](03-benchmark-design.md) are built to expose it.

---

## 2. What already exists

Phase 0 reviewed seven artefacts. Full detail, verification status and citations are in
[`01-state-of-the-art.md`](01-state-of-the-art.md) and [`REFERENCES.md`](REFERENCES.md). Summary:

| Artefact | What it is, verified | What it already solves |
|---|---|---|
| **SILP** | Individual Internet-Draft `draft-hwang-silp-protocol-02`, 2026-07-21, no IETF standing, expires 2027-01-22 | Reference action-slot IR; five surface frontends (two lossless); frontend negotiation; session and heartbeat; 13-verb whitelist verified across six tokenizers; MCP/A2A embedding |
| **NLIP** | Ecma standards ECMA-430 to ECMA-434 plus TR/113, approved 2025-12-10 | Application-level protocol for agent and human-agent interaction; bindings over HTTP, WebSocket (CBOR), AMQP; mandatory security profiles |
| **FIPA-ACL** | SC00061G, FIPA Standard since 2002-12-03 | Communicative acts; 13 message parameters; conversation control (`protocol`, `conversation-id`, `reply-with`, `in-reply-to`, `reply-by`) |
| **DALA** | AAAI-26, 40(35):29412-29420 | Communication as a scarce, auctioned resource; learned decision about *whether to speak* |
| **MOC** | ICML 2026, PMLR 306:37603-37619 | Multi-order evidence streams and Semantic-Topological Merging under token constraints |
| **A2A** | v1.0.0 | Task lifecycle, discovery via Agent Card, modality negotiation, cancellation, artifacts |
| **MCP** | Specification 2026-07-28 | Tool/resource/prompt access; JSON-RPC 2.0; per-request capability negotiation |

Two conclusions follow directly.

**First:** "semantic IR plus multiple encodings plus format negotiation" is prior art as of July
2026. SILP occupies that ground, including the round-trip guarantee and the tokenizer-aware
vocabulary. A project whose pitch is that sentence has no thesis.

**Second:** the ground SILP leaves empty is specific and checkable. Reading its JSON Schema: the
`meta` object carries `req_id`, `session_id`, `priority`, `confidence` (number, 0 to 1, default 1.0),
`seq`, `out`, `next_agent`. There is no epistemic type, no evidence reference, no source, no
timestamp of observation, no distinction between proposing and authorising an action, and no
mechanism for a receiver to request detail that was not sent. Session heartbeat exists to *renew*
context, which is the opposite operation to *progressively expanding* it.

---

## 3. Proposed contribution

Four properties, each of which must be shown to matter or be dropped.

### E1. Epistemic typing

Every claim carries its epistemic status from a closed set: `OBSERVED`, `DERIVED` (inference from
stated premises), `ASSUMED`, `PREDICTED`, `UNKNOWN` (explicit ignorance, with the question that would
resolve it). Claim types are structural, not decorative: a receiver may act on `OBSERVED` and must
not treat `ASSUMED` as established.

Calibration is handled honestly. A model's declared confidence is **not** a statistically calibrated
probability, and the representation must not pretend otherwise. Numeric confidence is permitted only
alongside a stated basis (for example "empirical frequency over N observations", "model self-report",
"expert prior"), and downstream agents are required to treat unbased numbers as ordinal at best.

### E2. Provenance and evidence

A claim may reference evidence objects: `{source_id, retrieved_at, method, reliability, hash}`. The
representation distinguishes the *time of observation* from the *time of sending*, because the
commonest silent failure in analytics agent chains is a stale number presented as current. Evidence
objects may be sent inline (small) or by reference into a shared, versioned store (large), which is
also the hook for progressive precision.

### E3. Authority semantics

One axis separates *what is being done with a proposition*, and it is orthogonal to the
communicative act: `INFORM`, `PROPOSE`, `REQUEST`, `AUTHORISE`, `EXECUTE_REPORT`. The receiving agent
must be able to check authorisation independently of message validity. This is the answer to the
obvious attack on any compact protocol: a perfectly formed message from a compromised agent is still
a perfectly formed message.

### E4. Progressive semantic precision

The sender transmits the minimum sufficient message and marks what it withheld as *resolvable
references* with declared granularity ("daily level available; per-player level available on
request"). The receiver may issue `EXPAND(reference, granularity)`. This is the property most likely
to produce real cost savings and the hardest to get right, because it requires the sender to
pre-compute and advertise what it can supply, and the receiver to know what it needs.

### What is deliberately not added

No new transport, no new envelope, no new discovery, no new security model, no ontology of the world.
Layers 1 and 2 of the architecture are inherited wholesale from A2A/MCP/NLIP; only the payload is
ours to define. This is a scope decision, not a limitation to be apologised for: it is the only way
the experiment stays affordable.

---

## 4. Architecture

Four layers, loosely coupled, each replaceable. The mapping to existing work is explicit because it
determines what the project must actually build.

### L1. Encoding and transport

**Inherited.** Binary and text encodings, serialisation, framing, versioning and transmission error
handling are solved by NLIP bindings (HTTP, WebSocket with CBOR, AMQP) and A2A protocol bindings
(JSON-RPC, gRPC, REST). We define no transport.

**Ours:** a mandate that the same IR be encodable in at least three interchangeable forms, and a
conformance test that all lossless forms round-trip to a semantically identical IR.

### L2. Communication protocol

**Inherited.** Envelope, sender and receiver identity, task identification, correlation and
acknowledgement, delegation, cancellation, acceptance and rejection, capability discovery, and
permission boundaries are specified by A2A (task lifecycle, Agent Card, cancellation) and FIPA-ACL
(conversation control parameters). NLIP supplies the security profiles.

**Ours:** the authority axis E3, carried in the payload and checkable by the receiver, plus the
negotiation of *which IR features* both parties support (a strict subset of SILP's frontend
negotiation, extended from encoding to semantics).

### L3. Semantic intermediate representation

**Partly inherited.** SILP's action-slot IR covers intent, argument slots, constraints, alternatives
and protocol metadata. Where SILP suffices, we should use it rather than define a competitor: a
project that forks SILP's IR for cosmetic reasons has produced a dialect, not a contribution.

**Ours:** the four additions E1, E2, E3, E4 as *optional, feature-negotiated* extensions that degrade
gracefully to plain SILP. A receiver that does not understand epistemic typing must still be able to
consume the message as SILP, minus the typing. If that graceful degradation does not work, the design
is wrong.

The IR must be able to express: facts, entities, events and relations; communicative intent;
conditions, dependencies and plans; uncertainty, hypotheses and admitted gaps; provenance, evidence
and observation times; and requirements, constraints and completion criteria.

### L4. Intent and reasoning

**Out of scope for MVP.** Goals, plans, belief state, negotiation of meaning, and conflict resolution
between agents are research problems in their own right. The MVP measures two-agent payload fidelity
only. L4 appears in Phase 4 as negotiation of *vocabulary and format*, not of goals.

---

## 5. Requirements

### 5.1 Kinds of information that must be distinguishable

1. **Facts and assertions** - what the agent holds true, and on what basis (E1, E2).
2. **Hypotheses and inferences** - what it suspects but has not established (E1).
3. **Communicative acts** - `ASSERT`, `ASK`, `REQUEST`, `OFFER`, `ACCEPT`, `REJECT`, `DELEGATE`,
   `REPORT`, `CANCEL`, `EXPAND`. The first nine align with FIPA and SILP; `EXPAND` is ours.
4. **Conditions and dependencies** - `IF`, `THEN`, `UNLESS`, `REQUIRES`, `DEPENDS_ON`, `BEFORE`,
   `AFTER`.
5. **Epistemic uncertainty** - observation, assumption, prediction and ignorance kept apart (E1).
6. **Provenance** - source, time of observation, context, reliability (E2).
7. **Authority** - description, proposal, request, authorisation, execution report (E3).

### 5.2 Ambiguity classes the representation must forbid

Negation scope; unit and currency; numeric ranges and open bounds; identifier namespace; contextual
reference (which "last week", which "segment"); execution conditions ("when", "unless", "at most").
Each of these has a mandated resolution rule, and a message that leaves one open fails validation
rather than being interpreted by the receiver. This is the single largest practical difference from
JSON-over-prose, where all six are resolved by the model's judgement at the moment of reading.

### 5.3 Deployment requirements

Black-box text interface only: no model-internal access, no fine-tuning, no latent manipulation.
A conforming decoder must be implementable by a mid-size model with a short prompt. If a feature
requires a frontier model to decode reliably, it is not a protocol feature but a model feature, and it
must be labelled as such.

---

## 6. Hypotheses

Each hypothesis is stated so it can fail. H1 is the one that matters; H2 to H4 are secondary.

**H1 (primary).** A shared typed representation with progressive resolution reduces total system cost
(tokens plus decode calls, converted to a common unit) at equal task success, compared with (a) natural
language, (b) JSON, and (c) SILP, on the task family defined in the MVP.

*Falsified if:* total cost is not lower than SILP by a pre-registered margin, or task success drops
by more than the equivalence margin.

**H2.** Epistemic typing plus provenance reduces the rate of *silently dropped qualifications*
(unreported caveats, stale figures presented as current) relative to all baselines, measured by
auditing decoded messages against the ground-truth task state.

*Falsified if:* the qualification-loss rate is indistinguishable from SILP within confidence
intervals.

**H3.** Agents do not need to transmit the full description every time; with agreed identifiers and
references they can transmit a minimal message, provided the reference store is versioned and
immutable.

*Falsified if:* reference resolution errors exceed the tolerance, or if the receiver's expansion
requests cost more than the tokens saved.

**H4.** Compact syntax and binary encoding do **not** automatically reduce total cost, because
decoding consumes inference.

*This hypothesis predicts the failure of a common assumption, including ours.* It is retained
deliberately: a benchmark that cannot detect this is worthless.

---

## 7. Roadmap

Timelines assume a small, experienced team. They are estimates, not commitments. Each phase has an
exit gate; a failed gate returns to the previous phase rather than proceeding.

### Phase 0 - Research and baseline (1-2 weeks) - **complete**

Review SILP, NLIP, FIPA-ACL, DALA, MOC, A2A, MCP; establish what is already solved; identify gaps;
define the task family, the arms and the metrics.
**Output:** [`01-state-of-the-art.md`](01-state-of-the-art.md),
[`02-mvp-scope.md`](02-mvp-scope.md), [`03-benchmark-design.md`](03-benchmark-design.md).
**Gate:** the gaps are specific enough to be tested, and the incumbent baseline is runnable.

### Phase 1 - Semantic IR (weeks 3-5)

Formalise types, operators and semantics for E1 to E4 as a feature-negotiated extension of SILP's IR.
Formalise negation, uncertainty, conditions and temporal relations. Define the message schema, the
versioning and compatibility rules, and the conformance suite.
**Output:** IR specification v0.1; reference parser; conformance tests.
**Gate:** round-trip conformance for all lossless encodings, and a documented degradation path to
plain SILP.

### Phase 2 - Encoding and decoder (weeks 6-9)

Implement at least three representations of the same IR: a readable structural form, a compact text
form, and a binary form. Implement encoders, decoders and validators. Round-trip and semantic
equivalence tests. Token counts across several tokenizers.
**Output:** tooling sufficient to run the benchmark.
**Gate:** no semantic loss across lossless forms; decode cost measured, not assumed.

### Phase 3 - Two-agent benchmark (weeks 10-13)

Agent A generates, Agent B interprets and acts, across model families. Tasks covering facts,
delegation, planning and data analysis. Error, ambiguity, conflict and missing-information cases.
Measure cost, latency and effectiveness.
**Output:** prototype and benchmark report.
**Gate:** H1 is decided, in either direction.

### Phase 4 - Negotiation and multi-agent (months 4-5)

Feature negotiation, acknowledgements and retries, shared vocabularies with versioned identifiers,
domain extensions, three-or-more-agent collaboration.
**Output:** interoperable protocol prototype.
**Gate:** two independently implemented peers interoperate without a shared codebase.

### Phase 5 - Open specification and deployment (from month 6)

Publish the specification, the reference implementation, the public benchmark and test corpus.
Security and compatibility testing. Assessment of integration with SILP, A2A and NLIP.
**Output:** an open artefact ready for independent evaluation.

---

## 8. Metrics and success criteria

Measured per arm, per task, across models:

- **Semantic fidelity** - agreement between the IR recovered by the receiver and the IR sent, scored
  by a rule-based comparator plus human adjudication on a sample.
- **Task success** - did the receiver produce the correct artefact or decision.
- **Tokens in and out**, per tokenizer, reported separately rather than normalised away.
- **Total cost** - inference for encoding and decoding included, in a stated unit (token-equivalents
  and wall-clock, both reported).
- **End-to-end latency**, with decode calls counted.
- **Robustness** - behaviour under ambiguity, conflicting inputs and missing information.
- **Cross-model compatibility** - same task, different model pairs.
- **Recovery cost** - tokens and latency to repair a failed or ambiguous exchange.

Proposed Phase 3 criteria, explicitly as experimental targets rather than expected results:

1. Minimum 99% decoding correctness on a closed, well-defined test set.
2. At least 30% token reduction on selected structural tasks, **reported alongside total-cost delta**.
3. No material degradation in task success (equivalence margin declared before the run).
4. Documented improvement in total cost or latency in at least one realistic scenario.

Measurement uncertainty must be reported: confidence intervals, seeds, model versions and dates.
Single-run comparisons are not evidence.

---

## 9. Risks

| Risk | Why it bites | Mitigation |
|---|---|---|
| **Models cannot read compact syntax reliably** | The receiver mis-parses, or falls back to improvisation; the protocol becomes model-specific | Decoder conformance suite; capability negotiation; no lossless claim without test coverage |
| **Decoding cost exceeds token savings** | The core economic assumption fails silently because only tokens were measured | Total cost is the primary metric (H4); decode calls counted |
| **Semantic loss under compression** | Caveats and dependencies disappear, and the receiver does not know | Epistemic typing makes dropped qualifications auditable (H2) |
| **Incompatible vocabularies** | The same identifier means different things to two agents | Versioned, content-addressed vocabulary; no silent reuse |
| **Security** | A valid message is not an authorised one | E3 authority axis; trust anchored outside the payload |
| **No advantage over SILP** | The project is a syntax variant of existing work | SILP is a benchmark arm from day one (H1); abandonment is a legitimate outcome |
| **Sunk-cost drift** | Phase 0 findings get quietly softened to keep the original pitch alive | This document states the prior art explicitly and keeps H4 as a falsifier |

---

## 10. Where the value would be

Not in "a new language". Interlingua-style designs are old: the idea descends from machine
translation interlinguas and from graph-semantic representations such as AMR, and SILP already ports
it to the LLM-agent setting. The defensible value is a demonstration that a shared representation can
hold four properties at once:

- high semantic fidelity, including caveats and negations;
- token and computational efficiency, measured end to end;
- independence from model, tokenizer and vendor;
- dynamic negotiation of encoding *and* of semantic feature set;
- interoperability with existing protocols at the transport and envelope level.

The one property worth singling out is **progressive semantic precision**: the sender transmits the
minimum sufficient message and declares what else it can supply; the receiver requests detail only
when it needs it. It is the only proposal here that changes the *shape* of a conversation rather than
its syntax, and it is the cheapest to test with two agents.

---

## 11. First experiment

Two agents, deliberately different model families, one shared data-analysis task.

Agent A receives the data, draws conclusions, and delegates a verification task. Agent B verifies the
hypothesis against the same data and returns a result with evidence and an explicit uncertainty
statement.

Five arms, same tasks, same data:

1. Natural language.
2. JSON.
3. Compact text representation.
4. Shared IR with alternative encoding (ours).
5. **SILP** (`polyglotIR`, its two lossless frontends) as the incumbent.

Arm 5 is not optional. Comparing a new representation only against prose guarantees a favourable
result and teaches nothing.

The question is not whether the new representation is shorter. It is whether it changes total cost
and correctness when the receiver must *act* on the message: whether the caveat survived, whether the
figure was current, whether the action was authorised, and whether asking for detail was cheaper than
having sent it.

---

## 12. Instructions for the continuing agent

Continue in a research-and-engineering mode. Do not assume a new language is required, and do not
assume the concept is novel.

1. Re-verify the status of SILP, NLIP, FIPA-ACL, DALA, MOC, A2A and MCP before any architectural
   decision. Three of these changed status in the last year; SILP is an individual draft that expires
   on 2027-01-22 and may be revised or abandoned.
2. Keep the gap list in `01-state-of-the-art.md` current. A gap that closes is a finding, not an
   inconvenience.
3. Define the smallest experiment that can falsify H1, and pre-register the equivalence margin.
4. Propose the formal semantics of the IR extension before implementing it.
5. Separate facts confirmed by sources from hypotheses and design assumptions, in every document.
6. Treat "no advantage over SILP" as a publishable result.

**Objective:** determine whether a model-independent semantic communication layer measurably improves
the efficiency and reliability of cooperation between models, and if not, say so with evidence.
