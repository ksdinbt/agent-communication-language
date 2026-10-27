# Literature review (Phase 0, systematic sweep)

**Date of sweep:** 2026-10-27
**Purpose:** complete Phase 0 by reading the works this programme cites at full text, and by running a
documented search to test the claim that E1-E4 are unaddressed. The previous documents used
`[abstract]` labels; this one promotes what could be promoted and records what the sweep forced us to
narrow.

Headline: **two of the four claimed gaps are more occupied than the first draft said.** Provenance
(E2) and uncertainty (E1) have active research literatures; authority (E3) has an adjacent formal
literature. Only E4 (progressive precision) survived the sweep untouched. The programme is still
viable, but its defensible claim is now narrower than "nobody does this" and rests on a specific,
testable distinction developed in section 6.

---

## 1. Method

**Databases and access.** Abstract and full-text retrieval through arXiv (API and PDF), ACL Anthology,
PMLR, AAAI OJS, IETF datatracker, Ecma, and a general web search backend. No institutional access to
ACM DL, Scopus, IEEE Xplore or Web of Science was used, which is a limitation, not a design choice.

**Query strings, verbatim** (all run 2026-10-27, limit 10 results each):

1. `site:arxiv.org "agent communication" semantic representation token efficiency LLM`
2. `"intermediate representation" inter-agent communication LLM protocol 2026`
3. `agent-to-agent provenance uncertainty "evidence" message LLM protocol`
4. `"progressive disclosure" OR "on demand" detail agent-to-agent communication protocol`
5. `FIPA ACL LLM agents communicative acts 2025 2026`
6. `"agent communication protocol" survey LLM multi-agent 2026 arXiv`
7. `typed claim uncertainty representation agent message protocol LLM`
8. `"authorization" OR "authority" semantics agent-to-agent message LLM protocol`

**Inclusion rule.** A hit was included if it (a) proposes or surveys a representation, protocol or
metric for what agents exchange, or (b) studies provenance, uncertainty, or authorisation *as carried
in a message or trace*. Excluded: vendor explainers, blog posts, tutorials, and papers about
multi-agent topology with no payload or message-representation component.

**Screening result.** 80 hits, ~35 unique after deduplication, 15 retained for abstract-level
screening, 6 read in full or near-full. Retained items are in section 5.

**Depth labels** are as before: `[read]` full text or the substantive sections; `[abstract]` abstract
and metadata only; `[unverified]` from secondary sources.

---

## 2. DALA - read in full

Fan, Y. et al. *Cost-Effective Communication: An Auction-based Method for Language Agent Interaction.*
AAAI-26, 40(35):29412-29420. DOI 10.1609/aaai.v40i35.40182. Preprint arXiv:2511.13193v2
(rev. 2026-04-24). **[read]**

**Method.** Communication is treated as a scarce, tradable resource. An actor network generates
candidate messages; a critic scores their *value density* (utility over cost); the density is the bid
in a budget-constrained VCG auction that allocates *speaking rights*. The actor-critic system is
trained with MAPPO on a reward combining task success and auction cost. All agents use
`gpt-4-1106-preview`; 2% of each benchmark is used as an optimisation set to learn the bidding policy,
which is then frozen and evaluated on the remaining 98%.

**Results (Table 1, accuracy %, HumanEval as pass@1).** Vanilla 82.14 on MMLU; DALA 84.32. GSM8K 85.40
to 96.18. HumanEval 71.68 to 91.21. MATH-500 73.72 to 83.42. Best multi-agent baseline (AgentPrune-R):
83.94 / 95.83 / 90.30 / 82.81.

**Cost (token consumption).**

| Benchmark | DALA | AgentPrune-R | LLM-Debate | PHP |
|---|---|---|---|---|
| MMLU | 3.80e5 | 9.60e5 | 1.50e6 | 2.60e6 |
| GSM8K | 6.20e6 | 7.50e6 | 2.20e7 | 2.60e7 |

DALA uses 60.4% fewer tokens than the previous best pruning baseline on MMLU and 76.2% fewer than PHP
on GSM8K, while scoring higher.

**What this changes for us.** Three things, one of them uncomfortable.

1. It confirms the framing that *volume* dominates: the biggest cost lever in the literature is who
   speaks, not how a message is spelled. Our benchmark holds the schedule fixed, which isolates format
   but also caps the achievable savings. That must be stated as a limitation of the design, not buried.
2. DALA is **trained**, not zero-shot. Its gains partially come from a learned policy on a 2% split.
   Our arms must therefore be zero-shot throughout, and any comparison to DALA in the write-up must
   say so, or the numbers are not comparable.
3. **Internal inconsistency in the paper:** the abstract claims "only 6.25 million tokens" while the
   cost table reports 6.20e6 for GSM8K. Minor, but it is exactly the kind of number a reviewer checks.
   Cite the table, note the discrepancy, do not repeat the abstract figure.

---

## 3. MOC - read in full

Guan, Y., Wang, L., Lu, Z., Wang, Z., Yan, W., Duan, Q. *MOC: Multi-Order Communication in LLM-based
Multi-Agent Systems.* ICML 2026, PMLR 306:37603-37619. **[read]**

**Method.** Existing schemes concatenate the outputs of immediate neighbours, which restricts the
evidence receptive field. MOC builds a structured *multi-order evidence stream* by grouping upstream
messages by hop distance (K = 2 is optimal), then applies *Semantic-Topological Merging*: redundant
messages are detected with lightweight embeddings and distilled by a small model under an explicit
length budget, preserving topological precedence. Formalised as a graph problem over an acyclic
execution order. Backbones: Gemma-2-27B-Instruct, Qwen2.5-32B-Instruct, DeepSeek-V3.2-685B-Chat.
Random DAG topologies at edge density rho in {0.3, 0.5, 0.7, 1.0}.

**Results.** Gemma-2-27B, average over six benchmarks, rho = 0.3: 0.7732 to 0.7910 (+2.30% relative).
AQuA alone +6.77% relative. Qwen2.5-32B: MMLU +2.59% to +3.84%, HumanEval +3.68% at rho = 0.3.
DeepSeek: MMLU-Pro +0.82%.

**The number that matters most for this programme.**

| Setting (MMLU) | Accuracy | Input tokens | Output tokens |
|---|---|---|---|
| Single LLM | 0.8772 | 52,904 | 1,140 |
| Vanilla MAS | 0.9228 | 1,958,918 | 490,362 |
| + MOC | 0.9263 | 2,405,945 | 486,600 |

MOC **increases** input tokens by 22.8% and total tokens by 18.1% versus the vanilla multi-agent
baseline, for +0.35 percentage points of accuracy. The consolidation operator is doing real work
inside MOC (it reduces the multi-order stream from 13.69e5 to 12.49e5 tokens, -8.8%), but the net
effect against the baseline is *more* communication, not less.

This is the strongest published evidence for our H4: a peer-reviewed paper whose stated goal is
"efficiency" reports a configuration that raises total token consumption. Anyone reporting only
"reduced redundancy" would have presented this as a saving.

**Author-admitted limitations**, verbatim: the communication order K "is currently fixed rather than
adaptively determined"; "higher-order evidence can enrich the target agent's context, it may also
introduce incorrect reasoning or even potentially malicious messages from compromised agents"; future
work on "adaptive and trust-aware schemes that dynamically select both the hop range and upstream
messages based on topology structure, evidence consistency, and message reliability".

**What this changes for us.** MOC's own future-work sentence is a mainstream, peer-reviewed statement
that **evidence consistency and message reliability are unresolved in inter-agent message selection**.
That is the cleanest possible motivation for E2 (provenance) and E3 (authority): the authors want it,
they do not have a representation for it, and they name it as future work.

---

## 4. Interlat - read in full

Du, Z. et al. *Enabling Agents to Communicate Entirely in Latent Space.* ACL 2026 (Long), 27106-27129.
DOI 10.18653/v1/2026.acl-long.1248. Preprint arXiv:2511.09149. **[read]**

**Method.** A *reasoning* agent sends its last-layer hidden states (collected over the completion
region, delimited by `<bop>`/`<eop>`) instead of tokens; an *actor* agent consumes them through a
lightweight self-attention plus projection "communication adapter". Training uses a task loss plus a
conditional distributional separation term (matched versus mismatched latents) and an alignment term.
Two agents only, both base models (Qwen2.5-7B/0.5B-Base, LLaMA3.1-8B-Base) fine-tuned. Evaluation on
ALFWorld (episodes capped at 20 steps) and MATH.

**Results.** Latent communication beats fine-tuned CoT and single-agent baselines, including across
heterogeneous models, and produces longer but more successful trajectories. Compression to 8-128 latent
steps (about 1.8% to 28.8% of the full sequence) preserves performance; end-to-end latency falls from
9.19 s to 0.39 s with 8-step latents (about 24x), and to 0.20 s with a bridge module. A reported
maximum cross-entropy gap of about 11 percentage points favours learned compression over training-free
truncation.

**Author-admitted limitations**, verbatim and decisive: the experiments are "a controlled two-agent
setting" on two benchmarks; the method "assumes access to internal model representations, specifically
last-layer hidden states", which "may not hold for closed-source or API-only models"; and "latent
communication trades human interpretability for efficiency", complicating "debugging, monitoring, and
failure analysis".

**What this changes for us.** It sharpens the argument instead of weakening it. Interlat needs (a)
fine-tuning, (b) access to hidden states, and (c) a two-agent pair; it is the fastest channel available
and it is unavailable to anyone running models behind an API. Our claim is therefore not "we are
faster" (we are not) but "we are auditable, model-agnostic and deployable on closed models". That
sentence belongs in the paper's introduction, not in a footnote.

---

## 5. Works found by the sweep that the first draft did not have

### 5.1 Provenance - the closest occupied ground

Wang, Y. et al. *From Agent Traces to Trust: A Survey of Evidence Tracing and Execution Provenance in
LLM Agents.* arXiv:2606.04990v6, rev. 2026-10-15. **[abstract]**

Defines **execution provenance** as "a typed graph of an agent run" and **evidence tracing** as "its
projection onto evidence-support relations, distinguishing evidence that supports a conclusion from
execution that influences it". Offers a six-dimensional taxonomy (trace sources; evidence and execution
units; provenance relations; tracing granularity and timing; representation forms; trust functions)
with nine provenance relations and two cross-cutting attributes (provenance origin, trace assurance).
Reports three gaps: limited integration of fine-grained provenance with multiple trust functions, no
benchmark evaluating a complete provenance chain, and little reporting of tamper-evident or attested
traces.

**Consequence.** E2 is not white space; it is a research area with a taxonomy. Our E2 must be
positioned carefully: the survey types the **trace of an execution** (for audit after the fact), while
E2 types the **claim carried in a message** (so the receiver can weigh it before acting). Those are
different objects with different consumers. Related and complementary, not novel in the abstract.
Note also the survey's own gap statement: "no benchmark in our catalog that evaluates the complete
provenance chain" - our benchmark could plausibly serve that purpose for the message-level slice.

### 5.2 Uncertainty - adjacent and forceful

- *Uncertainty Quantification for LLM Agents: A Taxonomy, an Evaluation Protocol, and an Empirical
  Study.* arXiv:2609.07395. **[abstract]** Three-axis taxonomy (what the uncertainty is, how it is
  estimated, where it arises), step-level and trajectory-level calibration, TC-ECE metric. Finds that
  "confidence estimates from the agent's own responses do not consistently outperform a simple
  baseline" and that "one confidence number is not enough".
- *Uncertainty Propagation in LLM-Based Systems.* arXiv:2604.23505. **[abstract]** Systems-level
  account of how uncertainty is carried across model internals, workflow stages, component boundaries
  and persistent state; three-level taxonomy (intra-model, system-level, socio-technical).

**Consequence.** The empirical claim behind E1 ("a model's declared confidence is not a calibrated
probability") is now established in the literature by someone else, with a metric. We should cite it
rather than assert it, and we may adopt TC-ECE as the calibration instrument for E1 instead of inventing
one. E1's remaining contribution is narrower: making epistemic *type* a mandatory field of the message
rather than a post-hoc measurement over a transcript.

### 5.3 Authority and security - policy layer, not payload layer

- *Overlaying Governance: A Compositional Authorization Framework for Delegation and Scope in Agentic
  AI.* arXiv:2606.03518. **[abstract]** Treats delegation as a contractual term, adds resource-scope
  attenuation and recursive delegation chains, composes onto existing relational policies with proofs
  and empirical evaluation.
- *Securing LLM Agents Need Intent-to-Execution Integrity.* arXiv:2605.16976. **[abstract]** Position
  paper deriving four integrity properties (Tool, Instruction, Judgment, Data Flow) whose conjunction
  is "intent-to-execution integrity"; argues existing defences give only partial, non-compositional
  coverage.
- *Cryptographically Secure Agent-to-Agent Communication in Multi-Agent Systems.* arXiv:2610.23078.
  **[abstract]** Zero-trust architecture: DIDs, task-scoped verifiable credentials on a permissioned
  ledger, mTLS with hybrid post-quantum KEM, signed CBOR envelopes, ZKPs for declared task constraints.

**Consequence.** Authentication and cryptographic integrity are solved elsewhere and should not be
reimplemented here. That strengthens the honesty of E3 but weakens its novelty: what remains is that
authority is *in the payload* - a receiver can tell "this is a proposal" from "this is an authorisation"
without consulting an external policy engine, and the distinction survives forwarding. That is a
weaker claim than the first draft implied, and it should be written as such.

### 5.4 Benchmarks and taxonomies we should align with

- *ProtocolBench: Which LLM MultiAgent Protocol to Choose?* arXiv:2510.17149v3. **[abstract]**
  Compares protocols (A2A, ACP, ANP, Agora) on four axes: task success, end-to-end latency, message or
  byte overhead, and robustness under failure. Reports up to 36.5% completion-time variation and 3.48 s
  mean latency difference between protocols; introduces ProtocolRouter and ProtocolRouterBench.
- *A Technical Taxonomy of LLM Agent Communication Protocols.* arXiv:2606.19135. **[abstract]** Five
  dimensions: counterparty, payload, interaction state, discovery mechanism, schema flexibility. On
  nine protocol implementations: all agent-to-agent protocols combine hybrid payloads with session
  state; most support several predefined schemas; "two negotiate schemas at runtime"; decentralised
  discovery is rare; open gaps named are privacy and policy enforcement.
- *Token Economics for LLM Agents: A Dual-View Study.* arXiv:2605.09104. **[abstract]** Token as
  production factor, exchange medium and unit of account; micro/meso/macro plus security taxonomy.

**Consequence.** Two things. First, `ProtocolBench` already measures protocol overhead and latency:
our benchmark must either extend it (payload representation, not protocol choice) or explicitly state
the axis it adds. Second, the taxonomy's five dimensions do not contain an epistemic, provenance or
authority dimension at all - an independent confirmation, from a protocol taxonomy built by other
people, that payload semantics are classified only by *shape* (single/hybrid/schema flexibility) and
never by *claim quality*.

### 5.5 Other channels and one different field

- *HyLaT: Efficient Multi-Agent Communication via Hybrid Latent-Text Protocol.* arXiv:2605.25421.
  **[abstract]** Sends "elaborate cognitive signals" over a latent channel and "concise critical
  signals" in natural language; two-stage training. A third option between text and full latent, and a
  precedent for deliberately splitting a message by importance.
- *Proxifield: Decentralized Multi-Agent Communication through Semantic Proximity.* arXiv:2609.20889.
  **[abstract]** Decentralised routing over sparse semantic-proximity graphs; no training. Topology
  layer, not payload - but its four routing signals (address, information need, plan alignment,
  information complementarity) are close cousins of E4's "receiver asks for what it needs".
- *Transmission With Machine Language Tokens.* arXiv:2507.21454. **[abstract]** Learns a specialised
  machine language represented by token embeddings plus joint token and channel coding, for
  task-oriented semantic communication over an air interface. **This is the deep-learning semantic
  communication field, not the agent-protocol field**: it requires training a dedicated encoder and
  decoder, and it optimises bits over a physical channel rather than claims in a message. Cite it to
  draw the boundary, not as a competitor.
- *A Comparative Study of MCP and A2A for Inter-Agent Coordination.* arXiv:2607.23884. **[abstract]**
  Implementation-grounded comparison: MCP lighter, A2A richer in native lifecycle support but heavier.
  Useful for the claim that envelope layers are being evaluated empirically while payload semantics
  are not.

---

## 6. What survived, what narrowed

| Claim in v0.2 | Status after the sweep | Action |
|---|---|---|
| E4 progressive precision is unaddressed | **Survived.** No paper found that has the sender advertise resolvable references and the receiver request expansion. Nearest cousins: MCP elicitation (asks the human), A2A streaming/artifacts, Proxifield's "information needs" routing signal. | Keep as the primary novel element; name the three cousins explicitly in the paper |
| E2 provenance is unaddressed | **Narrowed.** Execution provenance is an active field with a v6 survey and a nine-relation taxonomy. Message-level claim provenance is not. | Restate E2 as "provenance *in the payload*, not in the trace"; cite 2606.04990 and adopt its vocabulary |
| E1 epistemic typing is unaddressed | **Narrowed.** Uncertainty quantification and propagation are active fields; the "one confidence number is not enough" finding is already published. | Keep the typing requirement; cite 2609.07395 for the calibration claim; adopt TC-ECE as the instrument |
| E3 authority is unaddressed | **Narrowed.** IAM-side authorisation is formal and advanced; transport security is solved. | Restate as payload-carried authority that survives forwarding; do not claim to solve authentication |
| "No benchmark measures total cost across representations" | **Weakened.** ProtocolBench measures protocol overhead/latency; MOC reports token counts. | Position our benchmark as adding the *payload representation* axis; reuse ProtocolBench's axes where they overlap |
| H4: compact encoding does not automatically reduce total cost | **Supported by external evidence.** MOC raises total tokens 18.1% while calling itself efficient. | Promote H4 from "sceptical hypothesis" to "hypothesis with a published precedent" |

**The thesis that survives**, in one sentence:

> Agent payloads are classified by every existing taxonomy according to their *shape* (text, JSON,
> hybrid, schema-negotiated), never according to the *quality of the claim they carry* (is it observed
> or assumed, where did it come from, who was allowed to assert it, and can I ask for the rest); and a
> small vocabulary of claim-quality fields, negotiable and degradable, may reduce the cost of the
> errors those distinctions prevent.

That is a narrower and more defensible programme than "a new language", and it is falsifiable: if
adding the claim-quality fields changes neither total cost nor qualification loss, the thesis is dead.

---

## 7. Limitations of this review

1. **One search backend.** No ACM DL, Scopus, IEEE Xplore or Web of Science. Papers published only in
   those venues will be missing; the "no work found on E4" statement is therefore bounded by this.
2. **Abstract-level for eight items.** Sections 5.1 to 5.5 are labelled `[abstract]`; no quantitative
   claim in this document rests on them beyond what the abstracts state.
3. **English only.** Non-English work is excluded by construction.
4. **Screening was single-reviewer**, by definition here, with no second coder and therefore no
   inter-rater agreement to report.
5. **Fast-moving field.** Two of the retained items were revised within four months of submission, and
   the sweep date is the only defensible "as of".
6. **Not a PRISMA-compliant review.** Counts are approximate, exclusions were not logged per record.
