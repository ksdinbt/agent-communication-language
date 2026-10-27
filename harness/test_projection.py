"""Conformance tests for the semantic projection (harness/projection.py).

Run: python3 -m pytest harness/test_projection.py -q
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))
from projection import PROJECTION_VERSION, compare, norm_value, project  # noqa: E402

BASE = {
    "silp": "v1",
    "version": "ir-v0.1",
    "intent": "!CANCEL",
    "entities": [
        {"id": "act", "value": "flight", "action": "!CANCEL"},
        {"id": "notify", "value": "zhangsan", "action": "!EMAIL"},
    ],
    "constraints": [{"type": "loc", "value": "Beijing", "time": "t+1am", "subject": "me"}],
    "alternatives": [],
    "meta": {"req_id": "a3f9", "priority": 1, "confidence": 0.9, "seq": ["reason_first"],
             "out": "natural", "next_agent": None, "session_id": None},
}


def test_value_normalisation_agrees_across_encodings():
    for raw in (890000, "890000", "890,000", "890 000", "\u20ac890000", "890_000"):
        assert norm_value(raw) == 890000.0, raw
    assert norm_value("90%") == "90%"
    assert norm_value("200ms") == "200ms"
    assert norm_value(" Beijing ") == "beijing"


def test_meta_is_excluded_so_a_regenerated_req_id_does_not_fail_comparison():
    other = json.loads(json.dumps(BASE))
    other["meta"] = {"req_id": "1383", "priority": 0, "confidence": 1.0, "seq": [],
                     "out": "natural", "next_agent": None, "session_id": None}
    equal, diffs = compare(BASE, other)
    assert equal, diffs


def test_secondary_entity_id_is_excluded_but_values_and_actions_are_not():
    other = json.loads(json.dumps(BASE))
    other["entities"][1]["id"] = "act"  # what the code frontend does on decode
    assert compare(BASE, other)[0]

    other["entities"][1]["value"] = "lisi"
    equal, diffs = compare(BASE, other)
    assert not equal and "entities" in diffs


def test_constraint_subject_and_time_are_compared():
    for field, value in (("subject", "you"), ("time", "t+2"), ("operator", ">=")):
        other = json.loads(json.dumps(BASE))
        other["constraints"][0][field] = value
        equal, diffs = compare(BASE, other)
        assert not equal, field
        assert "constraints" in diffs, field


def test_order_does_not_matter():
    other = json.loads(json.dumps(BASE))
    other["entities"].reverse()
    assert compare(BASE, other)[0]


def test_absent_quality_fields_compare_equal_to_explicit_nones():
    a = json.loads(json.dumps(BASE))
    b = json.loads(json.dumps(BASE))
    b["ext"] = {}
    assert compare(a, b)[0]


def test_quality_fields_are_compared_when_present():
    a = json.loads(json.dumps(BASE))
    a["ext"] = {"epistemic": "OBSERVED", "authority": "PROPOSE",
                "qualifier": {"type": "partial_period"},
                "precision": {"refs": [{"id": "r1", "kind": "table",
                                        "granularity": ["daily", "player"]}]}}
    b = json.loads(json.dumps(a))
    assert compare(a, b)[0]

    b["ext"]["qualifier"]["type"] = "none"
    equal, diffs = compare(a, b)
    assert not equal and diffs["quality"]["actual"]["qualifier"] == "none"

    b = json.loads(json.dumps(a))
    b["ext"]["precision"]["refs"][0]["granularity"] = ["daily"]
    equal, diffs = compare(a, b)
    assert not equal and "refs" in diffs


def test_flat_quality_spelling_is_accepted():
    flat = json.loads(json.dumps(BASE))
    flat["ext"] = {"epistemic": "DERIVED", "authority": "REQUEST", "qualifier": "stale_extract"}
    nested = json.loads(json.dumps(BASE))
    nested["ext"] = {"claim": {"epistemic": "DERIVED"}, "authority": "REQUEST",
                     "qualifier": {"type": "stale_extract"}}
    # qualifier typing differs by spelling; epistemic and authority must agree
    assert project(flat)["quality"]["epistemic"] == project(nested)["quality"]["epistemic"]
    assert project(flat)["quality"]["authority"] == project(nested)["quality"]["authority"]


def test_projection_is_versioned():
    assert project(BASE)["projection_version"] == PROJECTION_VERSION


def test_bundled_silp_examples_project_without_error():
    repo = Path.home() / "Projects" / "polyglotIR-probe" / "examples"
    if not repo.exists():
        pytest.skip("polyglotIR-probe not present")
    for path in sorted(repo.glob("*.json")):
        p = project(json.loads(path.read_text()))
        assert p["intent"], path.name
