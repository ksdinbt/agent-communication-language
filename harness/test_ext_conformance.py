"""Conformance tests for spec/ir-extension-v0.1.md.

Every rule in the specification is exercised by at least one vector, and every vector has a
declared expectation in spec/conformance/expectations.json. A rule without a vector is a rule
nobody can check; a vector without an expectation is decoration.

Run: python3 -m pytest harness/test_ext_conformance.py -q
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))
from validate_ext import degraded_validates, validate  # noqa: E402

CONF = Path(__file__).resolve().parent.parent / "spec" / "conformance"
EXPECT = json.loads((CONF / "expectations.json").read_text())


@pytest.mark.parametrize("name,expected", sorted(EXPECT.items()))
def test_vector_matches_expectation(name: str, expected: bool) -> None:
    doc = json.loads((CONF / name).read_text())
    errors = validate(doc)
    assert (not errors) is expected, f"{name}: expected valid={expected}, errors={errors}"


@pytest.mark.parametrize("name", sorted(EXPECT))
def test_every_vector_strips_to_a_valid_plain_message(name: str) -> None:
    """Section 2: removing `ext` must leave a usable SILP message, valid or not."""
    doc = json.loads((CONF / name).read_text())
    assert degraded_validates(doc), name


def test_invalid_constraint_deferral_is_named_in_the_error() -> None:
    doc = json.loads((CONF / "defer-invalid-constraint.json").read_text())
    errors = validate(doc)
    assert any("may not be deferred" in e for e in errors), errors


def test_expand_must_be_a_request() -> None:
    doc = json.loads((CONF / "expand-request.json").read_text())
    assert not validate(doc)
    doc["ext"]["authority"] = "PROPOSE"
    assert any("!EXPAND must carry authority=REQUEST" in e for e in validate(doc))


def test_duplicate_claim_ids_rejected() -> None:
    doc = json.loads((CONF / "defer-valid.json").read_text())
    doc["ext"]["claims"].append(dict(doc["ext"]["claims"][0]))
    assert any("duplicate claim id" in e for e in validate(doc))


def test_projection_keeps_deferral_and_degraded_apart() -> None:
    """The extension changes meaning, so the two documents must not compare equal."""
    from projection import compare

    full = json.loads((CONF / "defer-valid.json").read_text())
    degraded = {k: v for k, v in full.items() if k != "ext"}
    equal, diffs = compare(full, degraded)
    assert not equal
    assert "refs" in diffs and "quality" in diffs
