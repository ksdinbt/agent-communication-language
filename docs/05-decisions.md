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
