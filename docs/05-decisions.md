# Decisions log

Short, dated, reversible entries. Each decision records what was decided, why, and what would
overturn it. Superseded decisions are struck through rather than deleted, because the reasoning is
often more useful than the outcome.

---

**D-001 · 2026-10-27 · Reframe the contribution away from "a new language"**
SILP (`draft-hwang-silp-protocol-02`, July 2026) already specifies a reference IR compiled into
multiple surface encodings with runtime negotiation. Presenting that as the thesis would be prior
art. The programme now targets four properties SILP lacks: epistemic typing, provenance with
observation time, an authority axis, and progressive semantic precision.
*Would be overturned by:* a documented reading of SILP that shows any of the four is actually
covered. Re-read the schema before claiming this again.

**D-002 · 2026-10-27 · SILP is a benchmark arm, not a competitor to beat rhetorically**
Arm A5 uses `polyglotIR` with its two lossless frontends. Comparing a new representation only against
natural language and JSON would manufacture a favourable result.
*Would be overturned by:* SILP becoming unusable (no runnable implementation) - in which case the
adapter is re-implemented from the draft and the deviation documented.

**D-003 · 2026-10-27 · Total cost is the primary metric; token count is reported, not optimised**
Following DALA's finding that communication volume dominates, and because decode inference can erase
token savings. Weight `w` for decode cost is fixed at 1.0 before the run, sensitivity-tested at 0.5
and 2.0.

**D-004 · 2026-10-27 · Scope limited to two agents and one task family**
Delegation with verification over tabular data. Multi-agent negotiation is Phase 4. A broader scope
would not finish, and an unfinished benchmark produces no finding.

**D-005 · 2026-10-27 · English is authoritative; Polish working draft lives in Trilium**
The source brief was Polish. The repository documents are English so that the work can be reviewed
externally; the Polish draft remains the place for fast, informal iteration.

**D-006 · 2026-10-27 · Latent communication is acknowledged, not dismissed**
Interlat (ACL 2026) is the strongest competing answer on efficiency grounds. The defensible claim here
is auditability and model independence, not raw compression. Any text asserting that symbolic IRs are
inherently more efficient must be removed.

**D-007 · 2026-10-27 · Private repository, no open specification yet**
Phase 5 of the roadmap calls for publication. Until the benchmark produces a result, the repository
stays private: an open spec with no evidence behind it attracts exactly the wrong kind of attention.

**D-008 · 2026-10-27 · Stopping conditions declared in advance**
Four conditions in `02-mvp-scope.md` end the project with a written finding. Declaring them before
the run is what makes "no advantage over SILP" a result rather than a defeat.

**D-009 · 2026-10-27 · E2 and E1 reframed after the systematic sweep**
The sweep found execution provenance to be an active research area (survey arXiv:2606.04990v6, nine
provenance relations) and uncertainty quantification to be established, including the finding that one
confidence score is insufficient (arXiv:2609.07395). E2 is therefore restated as provenance **in the
payload**, not in the trace; E1 keeps only the requirement that epistemic type be a mandatory message
field. Claims of the form "nobody does this" are removed from all documents.
*Would be overturned by:* a paper that specifies claim provenance inside an inter-agent message schema.

**D-010 · 2026-10-27 · E3 does not claim authentication**
Authorisation frameworks (arXiv:2606.03518) and zero-trust transport security (arXiv:2610.23078) are
advanced and out of scope. E3 is limited to an authority axis carried in the payload that survives
forwarding.
*Would be overturned by:* an existing payload specification that already distinguishes propose, request
and authorise at message level.

**D-011 · 2026-10-27 · E4 is the primary novel element and the cheapest to test**
No work found in which the sender advertises resolvable references and the receiver requests expansion.
Nearest cousins named in the paper: MCP elicitation (human), A2A streaming/artifacts, Proxifield's
"information need" routing signal. E4 drives the MVP.
*Would be overturned by:* a paper implementing sender-advertised, receiver-initiated expansion.

**D-012 · 2026-10-27 · DALA is cited, never benchmarked against**
DALA is trained (MAPPO on a 2% split) while our arms are zero-shot, so a direct comparison would be
invalid. It is cited for the volume finding and for its cost table, not as an arm.
*Would be overturned by:* a zero-shot ablation of DALA in its own paper.

**D-013 · 2026-10-27 · Adopt TC-ECE for epistemic calibration instead of inventing a metric**
arXiv:2609.07395 supplies a calibration instrument and the empirical reason for E1. Reimplementing it
would duplicate published work and weaken comparability.

**D-014 · 2026-10-27 · A5 (SILP) is a usable arm, under a declared semantic projection**
The reference implementation installs and runs (`uv pip install -e .`, core deps only), compiles all
27 bundled examples with its two lossless frontends, and passes 183 of 197 tests. It does **not**
round-trip the full IR: 0/54 by identity, 52/54 under its own projection, because secondary entity
ids, constraint `subject` and the entire `meta` object are not carried. Every arm is therefore scored
on one shared, versioned projection defined in the harness.
*Would be overturned by:* an upstream fix making the codec preserve the full IR, in which case the
projection narrows to identity and the result becomes stronger.

**D-015 · 2026-10-27 · Our extensions must not live in `meta`**
SILP keeps its only epistemic field, `confidence`, in `meta`, and `meta` does not survive a decode:
`priority` 1 becomes 0, `confidence` 0.9 becomes 1.0, `seq` is emptied and `req_id` is regenerated.
E1-E4 therefore go into the semantic body or into an extension the codec demonstrably carries. A
protocol that loses its own confidence field cannot be used to measure calibration.
*Would be overturned by:* a codec that preserves `meta` byte for byte.

**D-016 · 2026-10-27 · Payload minimalism is an economic requirement, and the skill file is how it is paid for**
A twelve-exchange pilot (docs/08-pilot.md) showed the naive typed arm costing 2.4x the tokens and 2.7x
the wall clock of natural language, and the cause was instruction density, not syntax: 1,951 mean
reasoning tokens against 595. Conventions therefore move out of the per-call prompt and into a short,
versioned skill document loaded once. A field that cannot be explained in one sentence is a field that
will be misread.
*Would be overturned by:* a payload whose conventions fit in two lines of prompt with no measurable
reasoning overhead.

**D-017 · 2026-10-27 · Qualifier loss is measured on the text, not on the receiver's self-report**
In the pilot, one receiver wrote "as of the latest extract date" and then declared `qualifier=no`. The
declared status is recorded but never trusted alone; a rubric scores the text, and disagreements are
adjudicated.

**D-018 · 2026-10-27 · The skill is a behaviour mechanism, not a cost mechanism, and EXPAND needs a contract**
A five-model probe (`09-skill-probe.md`) found the skill condition produced no wrong answers (5 of 5
produced answers preserved the qualifier) but 3 of 8 exchanges returned empty content, all
`finish_reason=length` with the reasoning budget exhausted. `max_tokens` therefore becomes a
per-condition parameter and an empty completion is never scored as a behavioural failure. `!EXPAND`
appeared in 3 of 4 deferred cases and spuriously in 2 of 4 non-deferred ones, so the receiver's output
becomes a validated decision object rather than prose.
*Would be overturned by:* a probe with n>=20 per cell in which the skill condition is cheaper and
equally accurate in a one-message session.
