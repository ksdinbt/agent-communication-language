# State of the art and gap analysis

**Verification date:** 2026-10-27
**Method:** each primary source fetched and read; claims below are labelled with how firmly they are
established:

- **[read]** - read in the primary document itself (specification text, schema, abstract page).
- **[abstract]** - read only from the official abstract/metadata page; full text not read.
- **[unverified]** - carried over from the project brief or secondary summary, not yet checked.

Nothing in this document should be cited without re-checking the version in
[`REFERENCES.md`](REFERENCES.md). Three of the seven artefacts changed status in the last twelve
months, and one of them is an individual draft that expires in January 2027.

---

## 1. SILP - Semantic Interlingua Layer Protocol

**Identity [read]:** `draft-hwang-silp-protocol-02`, published 2026-07-21, author Juwan Hwang
(Shanghai Maritime University), individual submission, `RFC stream: (None)`, `Intended RFC status:
(None)`, expires 2027-01-22. The datatracker states plainly: *"This I-D is not endorsed by the IETF
and has no formal standing in the IETF standards process."* Accompanying paper: Zenodo DOI
10.5281/zenodo.21396849. Reference implementation: `github.com/Juwan-Hwang/polyglotIR`.

**What it specifies [read]:**

- A five-layer stack, of which layers 1 and 2 are specified, layer 3 partially, layers 4 and 5 are
  reserved for future work.
- **L1, the reference IR:** a JSON-serialised *action-slot* structure with a strict root
  (`extra="forbid"`) and extensible sub-objects. Root fields: `silp`, `version`, `intent`
  (mandatory, pattern `^![A-Z][A-Z_]*$`), `entities`, `constraints`, `alternatives`, `meta`.
  `Entity` = `{id, value, action?}`. `Constraint` = `{type, value, time?}` with negation expressed as
  a `!` prefix convention on `type`. `Alternative` = `{action, target?, location?}`.
- **L2, surface frontends:** five. `code` (function-call syntax with an ABNF grammar) and `json` are
  lossless with `decode(compile(ir)) == ir`; `natural`, `nl_json` and `llmlingua2` are control
  baselines without a decoder.
- **L3, meta-protocol (partial):** error codes, session management with heartbeat renewal, frontend
  negotiation (probe messages).
- A **13-verb whitelist** of action primitives, each verified single-token and UNK-free across six
  tokenizers (gpt-4o, gpt-3.5, llama-2, qwen2.5, claude, gemini).
- Integration sections for MCP (`params` field), A2A (task/message/artifact fields) and AIDIP.
- Security considerations: zero-width and homoglyph injection (measured, 144 probes), payload
  injection, `req_id` collision probability, model identity, lossy compression risks.

**What it explicitly does not claim [read]:** it is a *payload-layer codec*, not a transport, not a
discovery protocol, not a lifecycle manager. It does not access model internals. It notes that
`req_id` and `session_id` are correlation conveniences, "not security identifiers", provide "no
replay protection", and that the verb whitelist is "advisory ... descriptive guidance, not a
schema-enforced constraint".

**Assessment.** SILP is the incumbent. It validates the core thesis of this programme (a reference IR
with pluggable encodings is practical and implementable) and simultaneously removes most of its
novelty. Any design decision here must either reuse SILP or justify a divergence in terms of a
property SILP lacks.

**Where SILP is thin, established by reading its own schema [read]:**

| Property | SILP status |
|---|---|
| Epistemic type of a claim (observed / inferred / assumed / predicted / unknown) | Absent. `meta.confidence` is a single number, `minimum: 0`, `maximum: 1`, `default: 1.0`, with no stated basis and no semantics beyond being a number |
| Provenance and evidence | Absent. No source, no observation timestamp, no reliability, no evidence object. The strings "provenance" and "evidence" do not occur in the document |
| Authority vs. proposal vs. request | Absent. The string "authoriz" does not occur. Action codes name actions; nothing distinguishes "I propose X" from "I am entitled to have X done" |
| Progressive precision / detail on demand | Absent. Negotiation concerns *frontend encoding* only; heartbeat exists to *renew* accumulated context, the inverse of progressive expansion |
| Formal semantics of negation | Convention only: prefix `type` with `!`. No scope rules, no interaction with quantifiers or ranges |
| Shared, versioned vocabulary across agents | Absent. Action codes are a whitelist, not a negotiated dictionary with versioned identifiers |
| Temporal semantics of data | `constraint.time` accepts free-form strings such as `"t+1"`, `"t+1am"`. No observation time, no staleness |

Two of these are acknowledged by SILP as limitations rather than omissions (`req_id` not a security
identifier; whitelist not enforced). That is credit to the author, and it strengthens rather than
weakens the case that authority and provenance are open ground.

---

## 2. NLIP - Natural Language Interaction Protocol

**Identity [read]:** Ecma International standards, approved 2025-12-10, developed by Ecma TC56.
First edition, December 2025: **ECMA-430** (the protocol), **ECMA-431** (binding over HTTP/HTTPS),
**ECMA-432** (binding over WebSocket, CBOR per RFC 8949 with UTF-8 JSON fallback), **ECMA-433**
(binding over AMQP), **ECMA-434** (security profiles, mandatory for any implementation claiming
conformance), and **TR/113** (explanatory guide, informative).

**Assessment.** NLIP is an application-level protocol between agents, and between humans and agents.
Its payload is natural language and multimodal content; its bindings are standard and its security
profiles are normative. It is a *complement*, not a competitor: it standardises the envelope,
transport and security posture, and deliberately leaves the semantic payload as natural language.
That is precisely the layer this programme is about. NLIP also sets the bar for what "conformant"
means in this space: normative bindings plus mandatory security profiles, not a schema in a
repository.

**Not yet established [unverified]:** whether ECMA-430 defines any structured content type beyond
natural language, and how it treats modality negotiation in detail. Full text not read (paywalled
distribution requires per-document download).

---

## 3. FIPA-ACL

**Identity [read]:** *FIPA ACL Message Structure Specification*, document SC00061G, FIPA TC
Communication, **status: Standard, dated 2002-12-03** (promoted from version F).

**Structure [read]:** 13 message parameters in four categories:

- communicative act: `performative` (the *only* mandatory parameter);
- participants: `sender`, `receiver`, `reply-to`;
- content: `content`;
- description of content: `language`, `encoding`, `ontology`;
- conversation control: `protocol`, `conversation-id`, `reply-with`, `in-reply-to`, `reply-by`.

Extension parameters must be prefixed `X-`. The specification states that parameters may be omitted
when context allows, "however, FIPA does not specify any mechanism to handle such conditions,
therefore those implementations that omit some message parameters are not guaranteed to
interoperate". Content is "intended to be interpreted by the receiver", with the explicit warning
that referential expressions may differ between sender and receiver.

**Assessment.** FIPA-ACL is the classical formalisation of communicative acts and the direct
ancestor of every act vocabulary in use today, including SILP's action codes. Three observations
matter for this programme:

1. It separates the act (`performative`) from the content description (`language`, `encoding`,
   `ontology`) - the same separation SILP formalises as L1/L2. The idea is 24 years old.
2. It has no epistemic semantics and no provenance. `content` is opaque by design.
3. It predates the token economy entirely: nothing in it optimises for token count, and
   `ontology`-based vocabulary agreement is assumed rather than negotiated at runtime.

The one element worth stealing is conversation control: `conversation-id`, `reply-with`,
`in-reply-to` and `reply-by` are a well-tested correlation model, and `reply-by` is a deadline
mechanism that modern protocols mostly lack.

---

## 4. DALA - cost-effective communication

**Identity [read]:** Fan, Zhang, Cai, Yang, Tang, Wang, Wang. *Cost-Effective Communication: An
Auction-based Method for Language Agent Interaction.* AAAI-26, Proceedings of the AAAI Conference on
Artificial Intelligence 40(35):29412-29420. DOI 10.1609/aaai.v40i35.40182. Published 2026-03-14.
SUN YAT-SEN University and Snap Inc.

**Claim [read]:** LLM multi-agent systems suffer from "free-for-all" communication with exponential
token cost and low signal-to-noise ratio. The authors treat communication bandwidth as a scarce,
tradable resource: a centralised auction in which agents bid for the right to speak based on the
predicted value density of their message. Reported: 84.32% on MMLU, 91.21% pass@1 on HumanEval,
6.25M tokens total, and an emergent "strategic silence".

**Read in full 2026-10-27.** Method: actor network proposes candidate messages, critic scores value
density (utility over cost), density is the bid in a budget-constrained VCG auction for speaking rights,
actor-critic trained with MAPPO. All agents `gpt-4-1106-preview`; policy learned on a 2% split, then
frozen. Accuracy: MMLU 82.14 to 84.32, GSM8K 85.40 to 96.18, HumanEval 71.68 to 91.21 (pass@1),
MATH-500 73.72 to 83.42. Cost: 3.80e5 tokens on MMLU against 9.60e5 for AgentPrune-R, and 6.20e6 on
GSM8K against 2.60e7 for PHP.

*Note on the record:* the abstract states "only 6.25 million tokens" while the cost table reports
6.20e6 for GSM8K. Cite the table.

**Assessment.** DALA is a *policy layer*: it decides **whether and when** an agent speaks. It is not
a language and does not touch encoding. It is also **trained, not zero-shot**, so it is cited here and
never used as a benchmark arm (decision D-012). It is nevertheless the most direct evidence for the framing
in this programme, because it demonstrates empirically that the dominant term in communication cost
is often *volume* rather than *per-message size*. Consequence for us: a payload format that saves 30%
per message while agents continue to emit twice as many messages has optimised the wrong variable.
Our benchmark therefore fixes the communication schedule across arms, and reports message counts
alongside token counts.

**Caveat [unverified]:** the abstract does not state whether the auction generalises beyond the seven
reasoning benchmarks used, nor the cost of the auction mechanism itself. Both matter before treating
strategic silence as a free win.

---

## 5. MOC - Multi-Order Communication

**Identity [read]:** Guan, Wang, Lu, Wang, Yan, Duan. *MOC: Multi-Order Communication in LLM-based
Multi-Agent Systems.* ICML 2026, PMLR 306:37603-37619.

**Claim [read]:** current schemes concatenate first-order neighbour responses, which restricts the
evidence receptive field and dilutes insights over multi-hop paths. MOC constructs a structured
multi-order evidence stream and applies a **Semantic-Topological Merging** algorithm to preserve
semantic fidelity within token constraints. Six datasets, multiple backbone scales; improves task
performance and reduces communication cost.

**Read in full 2026-10-27.** Method: group upstream messages by hop distance (K = 2 optimal) into a
multi-order evidence stream, then Semantic-Topological Merging (embedding-based redundancy detection plus
small-model distillation under a length budget). Backbones: Gemma-2-27B, Qwen2.5-32B, DeepSeek-V3.2-685B;
random DAGs at edge density 0.3 to 1.0. Relative gains: +2.30% average on Gemma at rho = 0.3, +6.77% on
AQuA, +0.72% to +3.68% on Qwen HumanEval.

**The decisive number:** on MMLU (DeepSeek setting) MOC moves input tokens from 1,958,918 to 2,405,945
and output tokens from 490,362 to 486,600 - total tokens **up 18.1%** for +0.35 percentage points of
accuracy (0.9228 to 0.9263). Its consolidation operator does reduce the multi-order stream itself
(13.69e5 to 12.49e5, -8.8%), but the net effect against the baseline is more communication, not less.

**Author-admitted limitation, verbatim:** higher-order evidence "may also introduce incorrect reasoning
or even potentially malicious messages from compromised agents", with future work on "trust-aware
schemes that dynamically select both the hop range and upstream messages based on topology structure,
evidence consistency, and message reliability".

**Assessment.** MOC is the closest work to our E2 (evidence), and it attacks the right problem: what
gets *dropped* when a message is compressed. It differs in scope - it is a message-consolidation
scheme over a fixed natural-language channel, not a typed payload with machine-checkable evidence
references. But it sets an important precedent: "semantic fidelity under token constraints" is a
measurable quantity with published baselines. Our fidelity metric should be comparable to theirs, or
the difference justified.

---

## 6. A2A

**Identity [read]:** Agent2Agent Protocol specification, **latest released version 1.0.0**,
`a2a-protocol.org`.

**Structure [read]:** three layers - a canonical data model (Task, Message, AgentCard, Part, Artifact,
Extension) expressed as Protocol Buffer messages; abstract operations (send message, send streaming
message, get task, list tasks, cancel task, get agent card); and protocol bindings (JSON-RPC, gRPC,
HTTP/REST, custom). Stated goals include capability discovery, negotiation of interaction modalities
(text, files, structured data), collaborative task management, and secure exchange "without needing
access to each other's internal state, memory, or tools". Guiding principles: reuse HTTP and
JSON-RPC 2.0, enterprise-ready security, async-first, modality-agnostic, **opaque execution**.

**Assessment.** A2A owns the envelope, task lifecycle, cancellation and discovery. Any design here
must embed into `Message`/`Part`/`Artifact` rather than compete with them. "Opaque execution" is
notable: A2A deliberately does not standardise what is inside a message, which is exactly the room
this programme occupies. Modality negotiation in A2A is about *content type*, not about semantic
feature set - a distinction worth preserving in the write-up.

---

## 7. MCP

**Identity [read]:** Model Context Protocol specification, version **2026-07-28**, `modelcontextprotocol.io`.

**Structure [read]:** JSON-RPC 2.0; "stateless, self-contained requests"; per-request capability
negotiation. Servers expose resources, prompts and tools; clients may offer elicitation. Utilities
include progress tracking, cancellation and error reporting. Optional extensions (opt-in, negotiated
during initialisation) cover asynchronous long-running operations, structured workflow instructions
and inline UI.

**Assessment.** MCP is a tool-and-context protocol, not an agent-to-agent language. It matters here
for one reason: it is where most deployed agent traffic actually carries its payload (`params`,
tool results), so an encoding that cannot live inside an MCP tool result will not be adopted
regardless of its merits. SILP already claims this embedding; ours must be demonstrated, not
asserted.

---

## 8. Adjacent paradigms that must be acknowledged

### 8.1 Latent-space communication

Du et al., *Enabling Agents to Communicate Entirely in Latent Space*, ACL 2026 (Long Papers),
pp. 27106-27129, DOI 10.18653/v1/2026.acl-long.1248. **[read: abstract]** Proposes *Interlat*: agents
exchange continuous last hidden states instead of discrete tokens, with a learned compression stage;
reports improvement over fine-tuned chain-of-thought and single-agent baselines, including across
heterogeneous models, and inference acceleration up to 24x.

This is the strongest competing answer to the same question. If bandwidth and fidelity are the
problem, latent states are the information-theoretically natural payload. Two consequences:

- Any claim that symbolic IRs are the *best* way to compress agent communication is unproven, and
  should not be asserted. The defensible claim is narrower: symbolic IRs are **auditable and
  model-agnostic**, whereas latent exchange is neither, and auditability is a hard requirement in
  regulated or accountable settings such as analytics and financial reporting.
- The benchmark should include a latent-transport arm only if a reproducible implementation is
  available; otherwise the limitation must be stated in the report.

### 8.2 Communication-centric survey

Yan et al., *Beyond Self-Talk: A Communication-Centric Survey of LLM-Based Multi-Agent Systems*,
arXiv:2502.14321v3 (revised 2026-05-26), accepted by Frontiers of Computer Science, DOI
10.1007/s11704-026-50857-y. **[read: abstract]** A structured framework combining system-level
communication (architecture, goals, protocols) with internal communication (strategies, paradigms,
objects, content); identifies communication efficiency, security vulnerabilities, inadequate
benchmarking and scalability as open challenges.

Read this before writing any "related work" section. If a claim in this repository contradicts the
survey, the survey is probably right.

### 8.3 Context description language

Peleg Pelc, Kaminka, Goldberg, *A Language for Describing Agentic LLM Contexts* (ACDL), CAIS '26,
arXiv:2605.01920. **[read: abstract]** A language for specifying the structure and dynamics of LLM
input contexts - role message sequences, dynamic content, time-indexed references, conditional and
iterative structure - independent of implementation.

ACDL describes *contexts*, not messages between agents. It is worth knowing because it shows the
design space is being colonised quickly, and because its time-indexed references are the same
primitive E2 and E4 need.

---

## 9. Gap matrix

`+` present and specified, `~` partial or convention only, `-` absent, `?` not established from
sources read.

| Property | SILP | NLIP | FIPA-ACL | A2A | MCP | DALA | MOC |
|---|---|---|---|---|---|---|---|
| Semantic IR for payload | + | - | ~ (content opaque) | - | - | - | ~ |
| Multiple encodings of one IR | + | - | ~ (language/encoding params) | - | - | - | - |
| Lossless round-trip guarantee | + | n/a | - | n/a | n/a | n/a | - |
| Runtime negotiation of encoding | + | ? | - | ~ (modality) | ~ (capability) | - | - |
| Tokenizer-aware vocabulary | + | - | - | - | - | - | - |
| Epistemic typing of claims | - (~ scalar) | - | - | - | - | - | - |
| Provenance / evidence / observation time | - | - | - | - | ~ (resources) | - | ~ |
| Authority: propose vs request vs authorise | - | ? | ~ (performatives) | ~ (authN at transport) | ~ (consent) | - | - |
| Progressive precision / detail on demand | - | - | - | - | ~ (elicitation) | - | - |
| Shared versioned vocabulary | - | ? | ~ (ontology name) | ~ (AgentCard) | ~ (schemas) | - | - |
| Conversation correlation and deadlines | + | ? | + (`reply-by`) | + (task ids) | ~ | - | - |
| Transport and framing | - (explicit non-goal) | + | - | + | + | - | - |
| Named security profiles | ~ (threats listed) | + (ECMA-434) | - | ~ | ~ | - | - |

**The white space is therefore:** epistemic typing, provenance with observation time, an authority
axis distinct from message validity, and progressive precision. Note that the last one has a partial
neighbour in MCP's *elicitation*: the server asks the *human* for missing information. Ours asks the
*sending agent* to expand a reference it already declared. The difference is worth stating precisely,
because a reviewer will notice the resemblance.

### 9b. The same matrix against the post-sweep literature (added 2026-10-27)

The systematic sweep (`06-literature-review.md`) found active work on three of the four properties, so
the matrix above is only half the picture. Columns: **Prov** = execution-provenance survey
(arXiv:2606.04990); **UQ** = agent uncertainty taxonomy and evaluation protocol (arXiv:2609.07395);
**AuthZ** = compositional authorisation framework (arXiv:2606.03518); **Tax** = protocol taxonomy
(arXiv:2606.19135); **PB** = ProtocolBench (arXiv:2510.17149); **SILP** as before.

| Property | SILP | Prov | UQ | AuthZ | Tax | PB |
|---|---|---|---|---|---|---|
| Types the claim inside a message | - | - | - | - | - | - |
| Types the agent run / trace | - | + | ~ | - | - | - |
| Provenance with observation time, per claim | - | ~ (trace-level) | - | - | - | - |
| Calibration metric for stated confidence | - | ~ | + (TC-ECE) | - | - | - |
| Epistemic type as a mandatory message field | - | - | ~ (measured, not declared) | - | - | - |
| Authority as payload semantics | - | - | - | ~ (policy layer) | - | - |
| Progressive precision / expansion on request | - | - | - | - | - | - |
| Payload dimension in a protocol taxonomy | ~ (as a draft) | - | - | - | ~ (shape only) | - |
| Measured protocol cost and latency | - | - | - | - | - | + |

Two things this table establishes, and one it admits:

1. **No existing taxonomy classifies a payload by the quality of the claim it carries.** The protocol
   taxonomy (2606.19135) classifies payloads by *shape* - single, hybrid, schema-negotiated - with five
   dimensions that contain no epistemic, provenance or authority dimension. That is independent
   confirmation from other researchers that the space is classified structurally, not semantically.
2. **Provenance exists as a research area, but for a different object.** The provenance survey types
   the *run*; nothing found types the *claim on the wire*.
3. **We are not first to E1, E2 or E3 in the abstract.** We may be first to put them in the payload as
   mandatory, negotiable fields. That is a narrower claim and it must be written as one.

---

## 10. Conclusions from Phase 0

0. **Phase 0 closed 2026-10-27 after the systematic sweep.** Six works read in full or near-full, 15
   retained, 8 query strings recorded. The sweep did not kill the programme; it removed three
   rhetorical claims from it.
1. **Do not build a new language. Build a benchmarked extension.** SILP already occupies layers 1 and
   2 with an implementable, testable design. Duplicating it guarantees irrelevance.
2. **Adopt SILP as the incumbent baseline in every experiment.** Comparing only against prose is
   rigging the result.
3. **Narrow the claim to what can be measured.** Four properties, two agents, five arms, one task
   family. Anything larger will not finish.
4. **Fix the schedule, vary the payload.** DALA shows volume dominates; if arms differ in message
   count they are not comparable.
5. **Acknowledge latent communication.** It is the strongest alternative and it defeats the naive
   "symbols are more efficient" argument. Our argument must be auditability and model independence,
   not raw efficiency.
6. **Watch the expiry.** `draft-hwang-silp-protocol-02` expires 2027-01-22. Re-check before Phase 1
   design freeze; a successor draft could close one of the four gaps, and that would be a finding,
   not an inconvenience.
7. **Stop claiming novelty for E1, E2 and E3 in the abstract.** Uncertainty quantification and
   execution provenance are published research areas; authorisation has a formal literature. The claim
   is now: *claim-quality fields inside the payload*, with E4 as the genuinely unoccupied mechanism.
8. **Cite the external evidence for H4.** MOC (ICML 2026) reports an 18.1% increase in total tokens
   while presenting itself as an efficiency method. That is a published precedent for the trap our
   benchmark exists to catch.
