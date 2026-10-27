"""Minimal validator for the E4 extension (spec/ir-extension-v0.1.md).

Implements the sender rules of section 4 and the receiver-contract shape of section 3.1,
plus the degradation rule from section 2. Deliberately small: every rule here is one that
the conformance vectors in spec/conformance/ exercise, and nothing else. A validator that
grows beyond its vectors is a validator nobody can test.

Usage:
    python3 validate_ext.py spec/conformance/defer-valid.json
Exit code 0 if the document is valid, 1 otherwise, 2 on unreadable input.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Any

EPISTEMIC = {"OBSERVED", "DERIVED", "ASSUMED", "PREDICTED", "UNKNOWN"}
AUTHORITY = {"INFORM", "PROPOSE", "REQUEST", "AUTHORISE", "EXECUTE_REPORT"}
QUALIFIER = {"none", "partial_period", "stale_extract", "definition_changed",
             "sample_too_small", "other"}
REF_KIND = {"table", "metric_definition", "segment", "period", "evidence", "codebook"}
RESOLUTION = {"inline", "deferred"}
ACTS = {"!ASSERT", "!ASK", "!REQUEST", "!OFFER", "!ACCEPT", "!REJECT", "!DELEGATE",
        "!REPORT", "!CANCEL", "!EXPAND", "!CANNOT_EXPAND"}
DEFERRABLE = REF_KIND  # only evidentiary detail may be deferred, never constraints
ROOT_REQUIRED = ("silp", "version", "intent", "meta")


def _err(errors: list[str], where: str, msg: str) -> None:
    errors.append(f"{where}: {msg}")


def validate(doc: dict[str, Any]) -> list[str]:
    """Return a list of errors. Empty list means valid."""
    errors: list[str] = []

    for field in ROOT_REQUIRED:
        if field not in doc:
            _err(errors, "root", f"missing required field '{field}'")
    if doc.get("intent") not in ACTS:
        _err(errors, "root.intent", f"{doc.get('intent')!r} is not a known act")

    ext = doc.get("ext")
    if ext is None:
        # Degraded form: a plain SILP message is valid by definition.
        return errors
    if not isinstance(ext, dict):
        _err(errors, "root.ext", "must be an object")
        return errors

    ver = ext.get("ext_version", "")
    if not re.fullmatch(r"e4-v\d+\.\d+", str(ver)):
        _err(errors, "ext.ext_version", f"{ver!r} does not match ^e4-v\\d+\\.\\d+$")

    auth = ext.get("authority", "INFORM")
    if auth not in AUTHORITY:
        _err(errors, "ext.authority", f"{auth!r} is not one of {sorted(AUTHORITY)}")

    claims = ext.get("claims") or []
    if doc.get("intent") in {"!ASSERT", "!REPORT"} and not claims:
        _err(errors, "ext.claims", "at least one claim is required for !ASSERT / !REPORT")
    seen_ids: set[str] = set()
    for i, claim in enumerate(claims):
        w = f"ext.claims[{i}]"
        cid = claim.get("id")
        if not cid:
            _err(errors, w, "missing 'id'")
        elif cid in seen_ids:
            _err(errors, w, f"duplicate claim id {cid!r}")
        else:
            seen_ids.add(cid)
        if "epistemic" not in claim:
            _err(errors, w, "missing 'epistemic' (mandatory, no default)")
        elif claim["epistemic"] not in EPISTEMIC:
            _err(errors, w, f"{claim['epistemic']!r} is not a valid epistemic type")
        if claim.get("epistemic") in {"OBSERVED", "DERIVED"} and not claim.get("observed_at"):
            _err(errors, w, "OBSERVED/DERIVED claims require 'observed_at'")
        if "value" in claim and not isinstance(claim["value"], (str, int, float)):
            _err(errors, w, "'value' must be a string or a number")

    qual = ext.get("qualifier") or {}
    if qual:
        if qual.get("type") not in QUALIFIER:
            _err(errors, "ext.qualifier.type", f"{qual.get('type')!r} is not a valid qualifier type")
        elif qual["type"] == "none" and not str(qual.get("note", "")).strip():
            _err(errors, "ext.qualifier", "qualifier type 'none' requires a note saying why it was dropped")

    # Rule 4.6 (added after docs/10-contract-probe.md): a numeric report must carry its number
    # in the machine-readable field, not only in prose. A null value with a figure in the text
    # lets a wrong number hide where no validator looks.
    if doc.get("intent") == "!REPORT":
        for i, claim in enumerate(claims):
            if claim.get("value") in (None, ""):
                _err(errors, f"ext.claims[{i}]", "numeric !REPORT requires a non-null 'value'")

    precision = ext.get("precision") or {}
    resolution = precision.get("resolution", "inline")
    if resolution not in RESOLUTION:
        _err(errors, "ext.precision.resolution", f"{resolution!r} is not one of {sorted(RESOLUTION)}")
    refs = precision.get("refs") or []
    if resolution == "deferred" and not refs:
        _err(errors, "ext.precision.refs", "resolution=deferred requires at least one ref")
    if resolution == "inline" and refs:
        _err(errors, "ext.precision.refs", "resolution=inline must not carry refs")
    ref_ids: set[str] = set()
    for i, ref in enumerate(refs):
        w = f"ext.precision.refs[{i}]"
        rid = ref.get("id")
        if not rid:
            _err(errors, w, "missing 'id'")
        elif rid in ref_ids:
            _err(errors, w, f"duplicate ref id {rid!r}")
        else:
            ref_ids.add(rid)
        if ref.get("kind") not in REF_KIND:
            _err(errors, w, f"{ref.get('kind')!r} is not a valid ref kind")
        gran = ref.get("granularity") or []
        if not gran:
            _err(errors, w, "a resolvable ref must declare at least one granularity")

    # Rule 4.5: AUTHORISE requires a named source.
    if auth == "AUTHORISE" and not any(c.get("source") for c in claims):
        _err(errors, "ext.authority", "AUTHORISE requires a claim with a 'source' naming the authoriser")

    if doc.get("intent") == "!EXPAND":
        ents = {e.get("id"): e.get("value") for e in (doc.get("entities") or [])}
        if "ref" not in ents:
            _err(errors, "entities", "!EXPAND requires an entity with id='ref'")
        if "granularity" not in ents:
            _err(errors, "entities", "!EXPAND requires an entity with id='granularity'")
        if auth != "REQUEST":
            _err(errors, "ext.authority", "!EXPAND must carry authority=REQUEST")

    if doc.get("intent") == "!CANNOT_EXPAND" and not qual:
        _err(errors, "ext.qualifier", "!CANNOT_EXPAND requires a qualifier explaining why")

    # Rule 4.1: constraints are never deferred.
    if resolution == "deferred":
        for i, ref in enumerate(refs):
            if ref.get("deferring") in {"constraint", "entity", "intent"}:
                _err(errors, f"ext.precision.refs[{i}]",
                     f"'{ref['deferring']}' may not be deferred; only evidentiary detail may be")

    return errors


def degraded_validates(doc: dict[str, Any]) -> bool:
    """True if stripping `ext` leaves a document that still satisfies the root contract."""
    stripped = {k: v for k, v in doc.items() if k != "ext"}
    return all(f in stripped for f in ROOT_REQUIRED) and stripped.get("intent") in ACTS


def _main(argv: list[str]) -> int:
    if len(argv) != 2:
        print("usage: validate_ext.py <ir.json>", file=sys.stderr)
        return 2
    path = Path(argv[1])
    try:
        doc = json.loads(path.read_text())
    except (OSError, json.JSONDecodeError) as exc:
        print(f"cannot read {path}: {exc}", file=sys.stderr)
        return 2
    errors = validate(doc)
    if errors:
        print(f"INVALID {path.name}")
        for e in errors:
            print(f"  - {e}")
        return 1
    print(f"VALID {path.name}" + ("" if "ext" not in doc else
                                  f" (ext present, strips to valid: {degraded_validates(doc)})"))
    return 0


if __name__ == "__main__":
    raise SystemExit(_main(sys.argv))
