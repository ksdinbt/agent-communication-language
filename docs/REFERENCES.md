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
*Read: abstract and bibliographic record. Full paper not read.*

**[MOC]** Guan, Y., Wang, L., Lu, Z., Wang, Z., Yan, W., Duan, Q. *MOC: Multi-Order Communication in
LLM-based Multi-Agent Systems.* Proceedings of the 43rd International Conference on Machine
Learning, PMLR 306:37603-37619, 2026.
<https://proceedings.mlr.press/v306/guan26i.html>
*Read: abstract and bibliographic record. Full paper not read.*

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
*Read: abstract and bibliographic record. Full paper not read.*

**[Survey]** Yan, B., Zhou, Z., Zhang, L., Zhang, L., Zhou, Z., Miao, D., Li, Z., Li, C., Zhang, X.
*Beyond Self-Talk: A Communication-Centric Survey of LLM-Based Multi-Agent Systems.* arXiv:2502.14321
(v3, 2026-05-26); accepted by Frontiers of Computer Science.
DOI <https://doi.org/10.1007/s11704-026-50857-y> · <https://arxiv.org/abs/2502.14321>
*Read: abstract. **Read the full text before writing the related-work section.***

**[ACDL]** Peleg Pelc, N., Kaminka, G. A., Goldberg, Y. *A Language for Describing Agentic LLM
Contexts.* CAIS '26 (ACM Conference on AI and Agentic Systems), May 2026.
DOI <https://doi.org/10.1145/3786335.3813126> · <https://arxiv.org/abs/2605.01920> ·
<http://www.acdlang.org>
*Read: abstract and bibliographic record.*

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

## Known gaps in this list

1. No inspection of `polyglotIR` source; claims about SILP's implementation quality are therefore
   absent, not implied.
2. ECMA-430 to 433 full texts not read; the NLIP summary is based on document scopes.
3. Full texts of DALA, MOC, Interlat and the communication survey not read; each is cited at abstract
   level only, and no quantitative claim is made from them beyond what the abstract states.
4. No systematic literature search yet. Phase 1 must run one (at minimum: ACM DL, ACL Anthology,
   arXiv cs.MA and cs.CL, IEEE, plus citation chasing from the communication survey) and record the
   query strings and date, or the claim "this gap is unaddressed" is an assertion rather than a
   finding.
