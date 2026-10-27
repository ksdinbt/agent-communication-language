"""The semantic projection: the single comparison function used by every arm.

Why this exists (decision D-014): SILP's reference codec does not preserve the full IR.
Measured on polyglotIR commit 45e9550, `decode(compile(ir))` reproduces the whole IR in
0 of 54 combinations; secondary entity ids, constraint `subject` and the entire `meta`
object are dropped. Scoring arms on IR identity would therefore penalise any payload that
carries more than SILP does. Every arm is scored on the projection below instead.

What the projection keeps: things that change what a receiver should DO.
  - the communicative act (intent) and the action of each entity
  - entity values (normalised)
  - constraints: type, operator, normalised value, time, subject
  - alternatives: action, target, location
  - claim quality fields when present: epistemic type, authority, qualifier type,
    evidence references (id, kind, granularity) - these are the payload of E1-E4

What it drops, deliberately:
  - protocol metadata: req_id, session_id, priority, seq, out, next_agent, confidence.
    These are transport/session concerns, they are absent from every alternative encoding,
    and at least one of them (req_id) is regenerated on decode by the incumbent.
  - entity `id` for secondary actions. It is an addressing handle, not meaning: the code
    frontend encodes secondary entities positionally. Reference identity for E4 lives in
    `ext.precision.refs[].id`, which IS compared.

PROJECTION_VERSION is versioned with the harness. Changing what is compared changes what
the benchmark means, so a change here invalidates prior results by construction.
"""

from __future__ import annotations

import json
import re
import sys
from typing import Any

PROJECTION_VERSION = "1.0"

_UNIT_SUFFIX = re.compile(r"^(?P<num>[-+]?\d+(?:[.,]\d+)?)\s*(?P<unit>%|[a-zA-Z]{1,6})?$")
_SEPARATORS = ("_", " ", "'", "\u00a0", "\u202f")


def norm_value(raw: Any) -> Any:
    """Normalise a value so that '890,000', '890000', '€890 000' and 890000 agree.

    Numbers become floats, units are kept as a lowercase suffix, and anything that is not
    a number is returned as a lowercased, whitespace-collapsed string. Currency symbols are
    stripped: the unit is carried by the field name or by an explicit unit suffix, and
    '€890' vs '890 EUR' is an encoding difference, not a semantic one.
    """
    if raw is None:
        return None
    if isinstance(raw, (int, float)):
        return float(raw)
    s = str(raw).strip()
    for sym in ("€", "$", "£", "\u00a0"):
        s = s.replace(sym, "")
    for sep in _SEPARATORS:
        s = s.replace(sep, "")
    s = s.replace(",", "") if re.fullmatch(r"[-+]?\d{1,3}(,\d{3})+", s) else s
    m = _UNIT_SUFFIX.match(s)
    if m:
        num = float(m.group("num").replace(",", "."))
        unit = (m.group("unit") or "").lower()
        return f"{num:g}{unit}" if unit else float(f"{num:g}")
    return " ".join(s.lower().split())


def norm_action(action: Any, intent: Any) -> Any:
    """Treat a missing action as the intent, and normalise case and the '!' prefix."""
    a = intent if action in (None, "") else action
    return str(a).strip().upper()


def _entity_key(e: dict, intent: Any) -> tuple:
    return (norm_action(e.get("action"), intent), norm_value(e.get("value")))


def _constraint_key(c: dict) -> tuple:
    return (
        str(c.get("type", "")).strip().lower(),
        str(c.get("operator") or "").strip(),
        norm_value(c.get("value")),
        str(c.get("time") or "").strip().lower(),
        norm_value(c.get("subject")),
    )


def _alternative_key(a: dict) -> tuple:
    return (
        norm_action(a.get("action"), None),
        norm_value(a.get("target")),
        norm_value(a.get("location")),
    )


def _ref_key(r: dict) -> tuple:
    return (
        str(r.get("id", "")).strip(),
        str(r.get("kind", "")).strip().lower(),
        tuple(sorted(str(g).strip().lower() for g in (r.get("granularity") or []))),
    )


def project(ir: dict) -> dict:
    """Reduce an IR document to the comparison surface.

    Accepts a SILP-shaped IR as a dict, with or without our `ext` block, and is
    tolerant of the field spellings the frontends produce.
    """
    intent = ir.get("intent")
    entities = sorted((_entity_key(e, intent) for e in (ir.get("entities") or [])), key=repr)
    constraints = sorted((_constraint_key(c) for c in (ir.get("constraints") or [])), key=str)
    alternatives = sorted((_alternative_key(a) for a in (ir.get("alternatives") or [])), key=str)

    ext = ir.get("ext") or {}
    quality = {
        "epistemic": str(_nested(ext, "epistemic") or _nested(ext, "claim", "epistemic") or "").lower() or None,
        "authority": str(_nested(ext, "authority") or "").lower() or None,
        "qualifier": str(_nested(ext, "qualifier", "type") or "").lower() or None,
    }
    refs = sorted((_ref_key(r) for r in (_nested(ext, "precision", "refs") or [])), key=str)

    return {
        "projection_version": PROJECTION_VERSION,
        "intent": norm_action(intent, None),
        "entities": entities,
        "constraints": constraints,
        "alternatives": alternatives,
        "quality": quality,
        "refs": refs,
    }


def _nested(ext: dict, *path: str) -> Any:
    """Fetch a nested field from `ext`, accepting the flat spelling as a fallback.

    The pilot showed models emit both `{"ext": {"epistemic": "..."}}` and
    `{"ext": {"claim": {"epistemic": "..."}}}`, so tolerating both is a requirement,
    not a kindness.
    """
    node: Any = ext
    for key in path:
        if isinstance(node, dict) and key in node:
            node = node[key]
        elif isinstance(ext, dict) and path[-1] in ext:
            return ext[path[-1]]
        else:
            return None
    return node


def compare(a: dict, b: dict) -> tuple[bool, dict]:
    """Compare two IR documents on the projection. Returns (equal, differences)."""
    pa, pb = project(a), project(b)
    diffs: dict[str, Any] = {}
    for key in ("intent", "entities", "constraints", "alternatives", "quality", "refs"):
        if pa[key] != pb[key]:
            diffs[key] = {"expected": pa[key], "actual": pb[key]}
    return (not diffs), diffs


def _main(argv: list[str]) -> int:
    if len(argv) != 3:
        print("usage: projection.py <a.json> <b.json>", file=sys.stderr)
        return 2
    a = json.load(open(argv[1]))
    b = json.load(open(argv[2]))
    equal, diffs = compare(a, b)
    print(json.dumps({"equal": equal, "projection_version": PROJECTION_VERSION,
                      "differences": diffs}, indent=2, ensure_ascii=False))
    return 0 if equal else 1


if __name__ == "__main__":
    raise SystemExit(_main(sys.argv))
