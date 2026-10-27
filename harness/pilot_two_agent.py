#!/usr/bin/env python3
"""Two-agent pilot: natural language vs a typed payload.

Purpose is EFFORT SIZING, not evidence. Two arms only, six instances, one seed,
one model. It answers three questions before we build a real harness:

  1. How long does one two-hop exchange take end to end?
  2. What does it cost, in tokens and in money?
  3. Does a planted qualifier survive the hop, and does the receiver's own
     self-report about that match reality?

The "ir" arm is an IR-lite payload, NOT a SILP implementation. It carries the
four properties as plain labelled fields so the pilot can measure whether the
receiver uses them at all. Anything we learn about SILP specifically comes from
docs/07-silp-runnability.md, not from here.

Usage: OPENROUTER_API_KEY=... python3 pilot_two_agent.py
"""

from __future__ import annotations

import json
import os
import re
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

MODEL = "deepseek/deepseek-v4.1-flash"
ENDPOINT = "https://openrouter.ai/api/v1/chat/completions"
OUT_DIR = Path(__file__).resolve().parent.parent / "results" / "pilot-2026-10-27"

# --------------------------------------------------------------------------
# Instances: two clean, two with a partial period, two with a stale extract.
# The trap instances are where a qualifier must survive the hop.
# --------------------------------------------------------------------------

TABLE = """period,segment,turnover_eur,extract_date
2026-W39,sports,1180000,2026-10-20
2026-W40,sports,1240000,2026-10-20
2026-W41,sports,890000,2026-10-21
2026-W41,casino,410000,2026-10-21"""

INSTANCES = [
    {
        "id": "clean-1", "kind": "clean",
        "question": "What was sports turnover in 2026-W40?",
        "expect_value": "1240000", "qualifier": None,
    },
    {
        "id": "clean-2", "kind": "clean",
        "question": "What was casino turnover in 2026-W41?",
        "expect_value": "410000", "qualifier": None,
    },
    {
        "id": "partial-1", "kind": "partial",
        "question": "What was sports turnover in 2026-W41, and how does it compare with 2026-W40?",
        "expect_value": "890000",
        "qualifier": ["partial", "incomplete", "in progress", "not complete",
                      "cut", "through day", "up to day", "mid-week", "partial week"],
    },
    {
        "id": "partial-2", "kind": "partial",
        "question": "What was sports turnover in 2026-W41, and what is the week-over-week change?",
        "expect_value": "890000",
        "qualifier": ["partial", "incomplete", "in progress", "not complete",
                      "cut", "through day", "up to day", "mid-week", "partial week"],
    },
    {
        "id": "stale-1", "kind": "stale",
        "question": "What is sports turnover for 2026-W41 right now?",
        "expect_value": "890000",
        "qualifier": ["2026-10-21", "stale", "as of", "extract", "not current",
                      "old", "snapshot"],
    },
    {
        "id": "stale-2", "kind": "stale",
        "question": "Give me the latest sports turnover figure.",
        "expect_value": "890000",
        "qualifier": ["2026-10-21", "stale", "as of", "extract", "not current",
                      "old", "snapshot"],
    },
]

# --------------------------------------------------------------------------
# Arm definitions
# --------------------------------------------------------------------------

NL_A = """You are Agent A, a data analyst. You have a table. You do not answer the
question yourself: you delegate it to Agent B, a verifier, by writing one short
natural-language message. Be accurate and complete but do not pad."""

NL_B = """You are Agent B, a verifier. Agent A sends you a natural-language message and
the data table. Answer the question, using the table. If the data cannot support
a clean answer, say so explicitly in the answer. End your reply with a line:
STATUS: qualifier=<yes|no>"""

IR_A = """You are Agent A, a data analyst. You have a table. You do not answer the
question yourself: you delegate it to Agent B, a verifier, by writing one message
in the TYPED payload format below. No prose outside the payload.

Format (one field per line, pipes separate values):
DELEGATE req=<id> to=verifier
CLAIM metric=<name> period=<period> value=<number> epistemic=<OBSERVED|DERIVED|ASSUMED|
      PREDICTED|UNKNOWN> src=<source> observed_at=<date>
QUALIFIER type=<partial_period|stale_extract|none> note=<short text>
ASK <what the verifier must return, including the epistemic status of its result>

Rules: epistemic=OBSERVED only if the figure comes straight from the table;
DERIVED if computed; QUALIFIER type=none only if neither partiality nor staleness
applies."""

IR_B = """You are Agent B, a verifier. Agent A sends you a message in the TYPED
payload format below, plus the data table. Interpret the payload, verify the claim
against the table, and reply in this format:

RESULT value=<number> epistemic=<OBSERVED|DERIVED|ASSUMED|PREDICTED|UNKNOWN>
QUALIFIER type=<partial_period|stale_extract|none> note=<short text>
ANSWER <one or two sentences for the human>
STATUS: qualifier=<yes|no>

Treat a QUALIFIER of type other than none as something you must carry into your
own answer. Do not invent figures that are not in the table."""

ARMS = {
    "nl": (NL_A, NL_B),
    "ir": (IR_A, IR_B),
}

# --------------------------------------------------------------------------
# API plumbing
# --------------------------------------------------------------------------


def api_key() -> str:
    key = os.environ.get("OPENROUTER_API_KEY")
    if key:
        return key
    env = Path.home() / ".hermes" / ".env"
    for line in env.read_text().splitlines():
        if line.startswith("OPENROUTER_API_KEY="):
            return line.split("=", 1)[1].strip().strip('"')
    raise SystemExit("no OPENROUTER_API_KEY in env or ~/.hermes/.env")


def call(key: str, system: str, user: str, max_tokens: int = 1500) -> dict:
    payload = {
        "model": MODEL,
        "temperature": 0,
        "max_tokens": max_tokens,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
    }
    data = json.dumps(payload).encode()
    req = urllib.request.Request(
        ENDPOINT, data=data,
        headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
    )
    started = time.time()
    for attempt in range(3):
        try:
            with urllib.request.urlopen(req, timeout=120) as r:
                body = json.loads(r.read())
            break
        except (urllib.error.URLError, TimeoutError) as exc:
            if attempt == 2:
                raise
            time.sleep(2 * (attempt + 1))
            req = urllib.request.Request(
                ENDPOINT, data=data,
                headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
            )
    elapsed = time.time() - started
    choice = body["choices"][0]
    text = choice["message"].get("content") or ""
    usage = body.get("usage", {})
    details = usage.get("completion_tokens_details") or {}
    return {
        "text": text,
        "finish_reason": choice.get("finish_reason"),
        "reasoning_tokens": details.get("reasoning_tokens", 0),
        "elapsed_s": round(elapsed, 2),
        "prompt_tokens": usage.get("prompt_tokens", 0),
        "completion_tokens": usage.get("completion_tokens", 0),
        "total_tokens": usage.get("total_tokens", 0),
        "cost_usd": usage.get("cost", 0.0),
    }


# --------------------------------------------------------------------------
# Scoring
# --------------------------------------------------------------------------

STATUS_RE = re.compile(r"STATUS:\s*qualifier\s*=\s*(yes|no)", re.I)


def declared_qualifier(text: str) -> str | None:
    m = STATUS_RE.search(text)
    return m.group(1).lower() if m else None


def heuristic_qualifier(text: str, keywords: list[str]) -> bool:
    low = text.lower()
    return any(k.lower() in low for k in keywords)


def answer_has_value(text: str, value: str) -> bool:
    digits = text.replace(",", "").replace(" ", "").replace("_", "")
    return value in digits or value in text.replace(",", "").replace(" ", "")


def main() -> None:
    key = api_key()
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    log_path = OUT_DIR / "runs.jsonl"
    rows = []

    with log_path.open("w") as log:
        for inst in INSTANCES:
            for arm, (sys_a, sys_b) in ARMS.items():
                # Turn 1: A composes the delegation
                a = call(key, sys_a, f"Data table:\n{TABLE}\n\nQuestion: {inst['question']}")
                # Turn 2: B interprets and answers, same table, fixed schedule
                b = call(
                    key, sys_b,
                    f"Data table:\n{TABLE}\n\nMessage from Agent A:\n{a['text']}\n\n"
                    f"Original question: {inst['question']}",
                )
                declared = declared_qualifier(b["text"])
                heuristic = (
                    heuristic_qualifier(b["text"], inst["qualifier"])
                    if inst["qualifier"] else not heuristic_qualifier(b["text"], [])
                )
                row = {
                    "ts": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                    "instance": inst["id"], "kind": inst["kind"], "arm": arm,
                    "a_text": a["text"], "b_text": b["text"],
                    "a_elapsed_s": a["elapsed_s"], "b_elapsed_s": b["elapsed_s"],
                    "tokens_a": a["total_tokens"], "tokens_b": b["total_tokens"],
                    "tokens_total": a["total_tokens"] + b["total_tokens"],
                    "finish_a": a["finish_reason"], "finish_b": b["finish_reason"],
                    "reasoning_a": a["reasoning_tokens"], "reasoning_b": b["reasoning_tokens"],
                    "cost_usd": round(a.get("cost_usd", 0.0) + b.get("cost_usd", 0.0), 8),
                    "elapsed_total_s": round(a["elapsed_s"] + b["elapsed_s"], 2),
                    "value_present": answer_has_value(b["text"], inst["expect_value"]),
                    "declared_qualifier": declared,
                    "heuristic_qualifier": bool(heuristic),
                    "needs_qualifier": bool(inst["qualifier"]),
                }
                rows.append(row)
                log.write(json.dumps(row, ensure_ascii=False) + "\n")
                log.flush()
                print(f"{inst['id']:10} {arm:3} tokens={row['tokens_total']:5} "
                      f"{row['elapsed_total_s']:6.1f}s value={row['value_present']} "
                      f"decl={declared} heur={row['heuristic_qualifier']}")

    summary = {
        "model": MODEL,
        "instances": len(INSTANCES), "arms": list(ARMS), "exchanges": len(rows),
        "tokens_total": sum(r["tokens_total"] for r in rows),
        "wall_clock_s": round(sum(r["elapsed_total_s"] for r in rows), 1),
    }
    (OUT_DIR / "summary.json").write_text(json.dumps(summary, indent=2))
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
