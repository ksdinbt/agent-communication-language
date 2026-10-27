# References

**All entries verified:** 2026-10-27. "Read" says how deeply the source was read; do not cite an
entry marked *abstract only* for a claim that requires the full text.

---

## Primary artefacts

**[SILP]** Hwang, J. *Semantic Interlingua Layer Protocol (SILP): A Payload Codec for Cross-Model
Agent Communication.* Internet-Draft `draft-hwang-silp-protocol-02`, 2026-07-21. Individual
submission; no IETF stream; not endorsed by the IETF; expires 2027-01-22.
<https://datatracker.ietf.org/doc/draft-hwang-silp-protocol/>
*Read: full draft text (specification, IR schema, frontends, security considerations).*
Accompanying paper: Zenodo DOI <https://doi.org/10.5281/zenodo.21396849> *(not read)*.
Reference implementation: <https://github.com/Juwan-Hwang/polyglotIR> *(not inspected)*.
Author: <https://github.com/Juwan-Hwang>

**[NLIP]** Ecma International, TC56. *Natural Language Interaction Protocol, 1st edition*, approved
2025-12-10:
- ECMA-430, NLIP (the protocol) - <https://ecma-international.org/publications-and-standards/standards/ecma-430/>
- ECMA-431, binding over HTTP/HTTPS
- ECMA-432, binding over WebSocket (CBOR, RFC 8949, with UTF-8 JSON fallback)
- ECMA-433, binding over AMQP
- ECMA-434, security profiles (mandatory for conformance) - <https://ecma-international.org/wp-content/uploads/ECMA-434_1st_edition_december_2025.pdf>
- TR/113, explanatory guide (informative) - <https://ecma-international.org/wp-content/uploads/ECMA_TR-113_1st_edition_december_2025.pdf>
Specification index: <https://github.com/nlip-project/nlip_spec> · <https://nlip-project.org/>
*Read: specification index and document scopes. Full standard texts not read (per-document download).*

**[FIPA-ACL]** Foundation for Intelligent Physical Agents. *FIPA ACL Message Structure Specification*,
document SC00061G, FIPA TC Communication. **Status: Standard, 2002-12-03** (version G).
<https://www.fipa.org/specs/fipa00061/> · full text:
<https://web.archive.org/web/20250321040750/http://www.fipa.org/specs/fipa00061/SC00061G.html>
*Read: full message-parameter section (Table 1 and notes) via archive; the live fipa.org endpoint
returned HTTP 502 on 2026-10-27.*
Related: FIPA00037 Communicative Act Library, FIPA00007 Content Languages Library,
FIPA00025 Interaction Protocol Library.

**[DALA]** Fan, Y., Zhang, J., Cai, K., Yang, J., Tang, C., Wang, J., Wang, K. *Cost-Effective
Communication: An Auction-based Method for Language Agent Interaction.* Proceedings of the AAAI
Conference on Artificial Intelligence 40(35):29412-29420, AAAI-26, published 2026-03-14.
DOI <https://doi.org/10.1609/aaai.v40i35.40182>
<https://ojs.aaai.org/index.php/AAAI/article/view/40182>
*Read: full text (method, cost tables, limitations) on 2026-10-27. See `06-literature-review.md`.*

**[MOC]** Guan, Y., Wang, L., Lu, Z., Wang, Z., Yan, W., Duan, Q. *MOC: Multi-Order Communication in
LLM-based Multi-Agent Systems.* Proceedings of the 43rd International Conference on Machine
Learning, PMLR 306:37603-37619, 2026.
<https://proceedings.mlr.press/v306/guan26i.html>
*Read: full text (setup, result tables, token counts, limitations) on 2026-10-27. See `06-literature-review.md`.*

**[A2A]** Agent2Agent Protocol. Specification v1.0.0 (latest released).
<https://a2a-protocol.org/latest/specification/> · repository:
<https://github.com/a2aproject/A2A>
*Read: introduction, goals, three-layer structure (data model / operations / bindings), MCP
relationship appendix.*

**[MCP]** Model Context Protocol. Specification version 2026-07-28.
<https://modelcontextprotocol.io/specification/latest>
*Read: overview, base protocol, features, security principles.*

## Adjacent research

**[Interlat]** Du, Z., Wang, R., Bai, H., Cao, Z., Zhu, X., Cheng, Y., Zheng, B., Chen, W., Ying, H.
*Enabling Agents to Communicate Entirely in Latent Space.* Proceedings of ACL 2026 (Volume 1: Long
Papers), pp. 27106-27129. DOI <https://doi.org/10.18653/v1/2026.acl-long.1248>
<https://aclanthology.org/2026.acl-long.1248/>
*Read: full text (method, compression analysis, limitations) on 2026-10-27. See `06-literature-review.md`.*

**[Survey]** Yan, B., Zhou, Z., Zhang, L., Zhang, L., Zhou, Z., Miao, D., Li, Z., Li, C., Zhang, X.
*Beyond Self-Talk: A Communication-Centric Survey of LLM-Based Multi-Agent Systems.* arXiv:2502.14321
(v3, 2026-05-26); accepted by Frontiers of Computer Science.
DOI <https://doi.org/10.1007/s11704-026-50857-y> · <https://arxiv.org/abs/2502.14321>
*Read: full text (taxonomy, section 4.4 content split, section 5.3 protocol list, sections 5.5-5.6
challenges) on 2026-10-27. See `06-literature-review.md` section 5.6.*

**[ACDL]** Peleg Pelc, N., Kaminka, G. A., Goldberg, Y. *A Language for Describing Agentic LLM
Contexts.* CAIS '26 (ACM Conference on AI and Agentic Systems), May 2026.
DOI <https://doi.org/10.1145/3786335.3813126> · <https://arxiv.org/abs/2605.01920> ·
<http://www.acdlang.org>
*Read: full text (scope statement, context model, limitations) on 2026-10-27. See
`06-literature-review.md` section 5.6.*

## Works added by the systematic sweep (2026-10-27)

All entries below are published on arXiv or in the venue stated. Abstract-level only unless marked.

- **Provenance survey.** Wang, Y., Zhang, J., Wu, Z., Cai, T., Liu, Z., Sun, Z., Zheng, M., Dong, M.,
  Qiu, Y.-X., Yin, X., Zhu, Y. *From Agent Traces to Trust: A Survey of Evidence Tracing and Execution
  Provenance in LLM Agents.* arXiv:2606.04990v6, rev. 2026-10-15. **[abstract]** Closest existing work
  to E2; defines execution provenance as a typed graph of an agent run. *Read in full before any claim
  about E2's novelty is published.*
- **Uncertainty quantification.** Lin, M., Lan, Q., Guan, S., Jing, W., Fan, J., Gregg, D., Botterweck,
  G. *Uncertainty Quantification for LLM Agents: A Taxonomy, an Evaluation Protocol, and an Empirical
  Study.* arXiv:2609.07395, 2026-09-07. **[abstract]** Source of the TC-ECE calibration metric and of
  the finding that agent self-reported confidence does not reliably beat a baseline.
- **Uncertainty propagation.** Xia, B., Zhu, L., Gao, E. *Uncertainty Propagation in LLM-Based
  Systems.* arXiv:2604.23505, 2026-04-26. **[abstract]**
- **Authorisation framework.** Ibrahim, A., Li, Y. *Overlaying Governance: A Compositional
  Authorization Framework for Delegation and Scope in Agentic AI.* arXiv:2606.03518, 2026-06-02.
  **[abstract]**
- **Security position paper.** Qu, W., Xu, M., Wang, P. *Securing LLM Agents Need Intent-to-Execution
  Integrity.* arXiv:2605.16976, 2026-05-16. **[abstract]**
- **Zero-trust A2A security.** Budzyn, K., Brodzik, A., Szczepkowski, M. *Cryptographically Secure
  Agent-to-Agent Communication in Multi-Agent Systems.* arXiv:2610.23078, 2026-10-16. **[abstract]**
- **Protocol benchmark.** Du, H., Su, J., Li, J., Ding, L., Yang, Y., Han, P., Tang, X., Zhu, K., You,
  J. *ProtocolBench: Which LLM MultiAgent Protocol to Choose?* arXiv:2510.17149v3, rev. 2026-06-02.
  **[abstract]**
- **Protocol taxonomy.** Sander, L., Gidey, H. K., Lenz, A. *A Technical Taxonomy of LLM Agent
  Communication Protocols.* arXiv:2606.19135, 2026-06-17. **[abstract]**
- **Token economics survey.** Chen, Y., Chen, J., He, C. *Token Economics for LLM Agents: A Dual-View
  Study from Computing and Economics.* arXiv:2605.09104, 2026-05-09. **[abstract]**
- **Hybrid latent-text protocol.** Mou, X., Wang, S., Li, Z. *HyLaT: Efficient Multi-Agent
  Communication via Hybrid Latent-Text Protocol.* arXiv:2605.25421v2, rev. 2026-10-23. **[abstract]**
- **Latent communication survey.** Liu, Y. *Beyond tokens: a unified framework for latent communication
  in LLM-based multi-agent systems.* arXiv:2606.05711v3, rev. 2026-07-15. **[abstract]** Three-axis
  framework over eighteen methods, 2024-2026.
- **Decentralised routing.** Tambwekar, P., Feng, Y., Patel, D. *Proxifield: Decentralized Multi-Agent
  Communication through Semantic Proximity.* arXiv:2609.20889, 2026-09-16. **[abstract]**
- **Semantic-communication lineage (different field).** Xiao, Z., Ye, C., Feng, Y., Hu, Y., Jiao, T.,
  Cai, L., Liu, G. *Transmission With Machine Language Tokens: A Paradigm for Task-Oriented Agent
  Communication.* arXiv:2507.21454, 2025-07-29. **[abstract]** Learned machine-token codec for
  task-oriented semantic communication over a channel. Not an agent-protocol competitor; cite as the
  boundary case.
- **MCP vs A2A.** Predoaia, I., Vu, T. M., Barmpis, K. *A Comparative Study of MCP and A2A for
  Inter-Agent Coordination in LLM-Based Systems.* arXiv:2607.23884, 2026-07-26. **[abstract]**
- **NLIP design rationale.** Xing, L., Topaloglu, R. O., Sinha, R. *The Natural Language Interaction
  Protocol and Standard for AI Agents.* arXiv:2609.04135, 2026-09-03. **[abstract]** Design rationale,
  message model, bindings and reference implementation for ECMA-430.

## Standards referenced by the above

- RFC 2119 / BCP 14, key words for requirement levels.
- RFC 5234, ABNF.
- RFC 8174, ambiguity of uppercase key words.
- RFC 8949, CBOR.
- JSON-RPC 2.0, <https://www.jsonrpc.org/>

## Verification log

| Date | Action |
|---|---|
| 2026-10-27 | Initial Phase 0 sweep: SILP datatracker page and full draft; NLIP spec index; FIPA SC00061G via web archive (live endpoint 502); DALA and MOC abstract pages; A2A v1.0.0 spec; MCP 2026-07-28 spec; Interlat, Survey, ACDL abstract pages |
| 2026-10-27 | Systematic sweep, 8 recorded query strings, 80 hits, 15 retained. Promoted DALA, MOC, Interlat, the communication survey and ACDL to `[read]` after full-text reading. Added 15 works. Method and screening: `06-literature-review.md` |

## Known gaps in this list

1. `polyglotIR` was inspected and executed on 2026-10-27 (commit `45e9550`); results in
   `07-silp-runnability.md`. The 675-run matrix, heartbeat runs and negotiation module were **not**
   re-executed, so claims about SILP's experimental results rest on its published data, not on our
   reproduction.
2. ECMA-430 to 433 full texts not read; the NLIP summary is based on document scopes.
3. Full texts of DALA, MOC, Interlat and the communication survey not read; each is cited at abstract
   level only, and no quantitative claim is made from them beyond what the abstract states.
4. The systematic sweep was run on 2026-10-27 (`06-literature-review.md`): eight recorded query
   strings, one general search backend. It did **not** cover ACM DL, Scopus, IEEE Xplore or Web of
   Science (no access), and screening was single-reviewer. The gap claim is therefore bounded by those
   exclusions and should be re-run with citation chasing from the top three surveys before any external
   publication.
