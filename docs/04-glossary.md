# Glossary

One term, one meaning, in both working languages. If a document in this repository uses a term that
is not here, either add it or stop using it. Terms marked *(avoid)* are in circulation elsewhere and
are deliberately not used here, because their ambiguity has cost us arguments.

---

## Core concepts

| EN | PL | Definition | Not to be confused with |
|---|---|---|---|
| **Agent communication language (ACL)** | język komunikacji agentów | A representation for what one agent tells another, including the act performed and the content carried | A transport protocol; a tool-calling schema |
| **Semantic IR (intermediate representation)** | semantyczna reprezentacja pośrednia | The single typed structure that carries meaning, from which surface encodings are compiled and to which they decode | An internal model representation (hidden states) |
| **Surface encoding** | kodowanie powierzchniowe / postać powierzchniowa | A concrete serialisation of the IR: readable, compact, binary, natural-language | The IR itself; a compression algorithm |
| **Lossless frontend** | frontend bezstratny | An encoding where decode(compile(ir)) yields a semantically identical IR | "Exact byte equality" |
| **Semantic equivalence** | równoważność semantyczna | Two messages mean the same thing under the IR's semantics, regardless of encoding | Textual similarity |
| **Feature negotiation** | negocjacja funkcji semantycznych | Runtime agreement on which IR features (E1-E4) both parties support | Encoding negotiation (which format) |
| **Envelope** | koperta | Outer message structure: sender, receiver, correlation, task reference | Payload |
| **Payload** | ładunek / treść semantyczna | The semantic content inside the envelope | The whole message |

## The four properties (E1-E4)

| EN | PL | Definition |
|---|---|---|
| **Epistemic type** | typ epistemiczny | The status of a claim: `OBSERVED`, `DERIVED`, `ASSUMED`, `PREDICTED`, `UNKNOWN` |
| **Calibration** | kalibracja | Whether a stated confidence corresponds to observed frequency. A model's self-reported confidence is **uncalibrated** unless shown otherwise |
| **Provenance** | pochodzenie | Source of a claim: `source_id`, `retrieved_at`, `method`, `reliability`, `hash` |
| **Observation time** | czas obserwacji | When the data behind a claim was captured. Distinct from send time, always |
| **Staleness** | nieaktualność | The gap between observation time and the moment a claim is used |
| **Authority axis** | oś uprawnień | What is being done with a proposition: `INFORM`, `PROPOSE`, `REQUEST`, `AUTHORISE`, `EXECUTE_REPORT` |
| **Progressive semantic precision** | stopniowana precyzja semantyczna | Sending the minimum sufficient message plus resolvable references, expanding on demand |
| **Resolvable reference** | odniesienie rozwiązywalne | A reference the sender declares it can expand, with the granularity it can supply |
| **EXPAND** | EXPAND | The act by which a receiver requests expansion of a resolvable reference |

## Measurement

| EN | PL | Definition | Not to be confused with |
|---|---|---|---|
| **Total cost** | koszt całkowity | Tokens in and out, plus inference consumed by decoding, plus retries, in token-equivalents | Token count |
| **Decode cost** | koszt dekodowania | Inference spent turning a payload into an IR or into an actionable interpretation | Parsing cost (CPU only) |
| **Token-equivalent** | ekwiwalent tokenowy | A common unit for inference work, so decode calls can be added to tokens | A universal currency; the weight `w` is a declared assumption |
| **Task success** | skuteczność zadania | Whether the receiver produced the correct artefact or decision | Message validity |
| **Semantic fidelity** | wierność semantyczna | Agreement between the IR sent and the IR recovered | Task success (a faithful message can still be acted on wrongly) |
| **Qualification loss** | utrata zastrzeżeń | A qualifier present at the sender and absent or unmarked at the receiver | Compression ratio |
| **Equivalence margin** | margines równoważności | The maximum success difference still counted as "no material degradation", fixed before the run | Statistical significance |
| **Pre-registration** | prerejestracja | Fixing margins, metrics and the decision rule before seeing results | Publishing a plan after the fact |

## Incumbent and adjacent work

| EN | PL | Definition |
|---|---|---|
| **SILP** | SILP | `draft-hwang-silp-protocol-02`, individual Internet-Draft defining a payload codec: action-slot IR compiled into five frontends, with session management and frontend negotiation |
| **NLIP** | NLIP | Ecma ECMA-430 to 434: application-level protocol for agent and human-agent interaction, natural-language payload, standard bindings and security profiles |
| **FIPA-ACL** | FIPA-ACL | SC00061G (Standard, 2002): communicative acts and 13 message parameters |
| **DALA** | DALA | AAAI-26 auction-based communication policy: which agent gets to speak |
| **MOC** | MOC | ICML 2026 multi-order evidence stream with Semantic-Topological Merging |
| **A2A** | A2A | Agent2Agent protocol v1.0.0: task lifecycle, discovery, modality negotiation |
| **MCP** | MCP | Model Context Protocol: tool, resource and prompt access over JSON-RPC |
| **Latent communication** | komunikacja w przestrzeni ukrytej | Exchanging continuous hidden states instead of tokens (e.g. Interlat, ACL 2026) |

## Terms deliberately avoided

| Term *(avoid)* | Why | Use instead |
|---|---|---|
| "Agent language" | Implies a full natural language with grammar and vocabulary growth | Agent communication language / payload representation |
| "Compression" | It is a side effect, not the goal; and it invites the decode-cost trap | Compact encoding, with the cost measured |
| "Protocol" (for the payload alone) | The protocol layer is A2A/MCP/NLIP; the payload is not a protocol | Payload representation, semantic layer |
| "Confidence score" | Suggests calibration that does not exist | Declared confidence, with its basis stated, or epistemic type |
| "Token savings" | Partial metric that misleads | Total cost |
| "Truth" / "ground truth belief" | An agent's claim is not truth, and the protocol cannot make it so | Claim, with provenance and epistemic type |
| "Semantic compression" | Sounds like the deep-learning semantic-communication literature, which is a different field (noisy-channel coding) | Progressive semantic precision |

## One-sentence summary of the whole programme, in both languages

> **EN:** Test whether making agent payloads epistemically typed, provenance-carrying, authority-aware
> and progressively resolvable reduces total communication cost at equal task success, measured
> against SILP rather than against prose.
>
> **PL:** Sprawdzić, czy nadanie ładunkom agentów typu epistemicznego, pochodzenia, osi uprawnień i
> stopniowalnej precyzji obniża całkowity koszt komunikacji przy niezmienionej skuteczności zadań,
> mierzone wobec SILP, a nie wobec prozy.
