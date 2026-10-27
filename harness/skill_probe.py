#!/usr/bin/env python3
"""Probe: does a loaded skill change receiver behaviour compared with an in-prompt format block?

Two conditions, same payload, same model:
  prompt_spec : the format block lives in the system prompt (what the pilot's `ir` arm did)
  skill       : a two-line system prompt, plus the skill document supplied once as context

Two instances:
  partial   : the figure is a partial week; a qualifier must survive the hop
  deferred  : the sender can only supply an aggregate; the receiver must either
              act on what it has or issue one !EXPAND

What is measured: qualifier preserved in the receiver's text (rubric, not self-report),
whether the receiver used !EXPAND where the payload invited it, tokens, empty completions.

This is a probe about adoption, not a benchmark. n = 2 instances, one seed.

Usage: python3 skill_probe.py [--models a,b,c]
"""

from __future__ import annotations

import argparse
import json
import os
import re
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ENDPOINT = "https://openrouter.ai/api/v1/chat/completions"
ROOT = Path(__file__).resolve().parent.parent
SKILL_PATH = ROOT / "skills" / "typed-payload-v0" / "SKILL.md"
OUT_DIR = ROOT / "results" / "skill-probe-2026-10-27"

DEFAULT_MODELS = [
    "z-ai/glm-5.3-flash",
    "deepseek/deepseek-v4.1-flash-1017",
    "openai/gpt-6-luna",
    "nvidia/nemotron-3-ultra-550b-a55b:free",
    "xiaomi/mimo-v2.6-flash",
]

TABLE = """period,day,segment,turnover_eur,extract_date
2026-W40,,sports,1240000,2026-10-20
2026-W41,,sports,890000,2026-10-21
2026-W41,2026-10-19,sports,310000,2026-10-21
2026-W41,2026-10-20,sports,330000,2026-10-21
2026-W41,2026-10-21,sports,250000,2026-10-21"""

PAYLOAD_PARTIAL = """!ASSERT
claim c1 value=890000 unit=EUR epistemic=OBSERVED observed_at=2026-10-21 src=extract:2026-10-21
qualifier partial_period "W41 extracted at day 3 of 7"
"""

PAYLOAD_DEFERRED = """!ASSERT
claim c1 value=890000 unit=EUR epistemic=OBSERVED observed_at=2026-10-21 src=extract:2026-10-21
qualifier partial_period "W41 extracted at day 3 of 7"
defer r1 table granularity=[weekly,daily] cost=1200
"""

INSTANCES = {
    "partial": {
        "payload": PAYLOAD_PARTIAL,
        "question": "Compare sports turnover in 2026-W41 with 2026-W40.",
        "needs_expand": False,
    },
    "deferred": {
        "payload": PAYLOAD_DEFERRED,
        "question": "Is the 2026-W41 decline uniform across days, or driven by one day?",
        "needs_expand": True,
    },
}

QUALIFIER_MARKERS = ["partial", "incomplete", "in progress", "day 3", "3 of 7", "mid-week",
                     "not complete", "cut off", "through 2026-10-21", "only three days"]
EXPAND_RE = re.compile(r"!EXPAND|EXPAND\b", re.I)

SYS_PROMPT_SPEC = """You are Agent B, a verifier. You receive a message from Agent A in this format:

    <act>
    claim <id> value=<n> unit=<u> epistemic=<OBSERVED|DERIVED|ASSUMED|PREDICTED|UNKNOWN> observed_at=<date> src=<id>
    qualifier <type> "<note>"          (optional)
    defer <refid> <kind> granularity=[...] cost=<n>   (optional)

Rules: an ASSUMED or PREDICTED claim is not actable; ask with !EXPAND if a deferral blocks you;
UNKNOWN is a real answer when the data cannot decide. Answer the question, then end with
STATUS: qualifier=<yes|no>"""

SYS_PROMPT_SKILL = """You are Agent B, a verifier. The conventions for the payload format are supplied
as context: follow them. Answer the question, then end with STATUS: qualifier=<yes|no>"""


def api_key() -> str:
    if k := os.environ.get("OPENROUTER_API_KEY"):
        return k
    for line in (Path.home() / ".hermes" / ".env").read_text().splitlines():
        if line.startswith("OPENROUTER_API_KEY="):
            return line.split("=", 1)[1].strip().strip('"')
    raise SystemExit("no OPENROUTER_API_KEY")


def call(key: str, model: str, messages: list[dict], max_tokens: int = 2000) -> dict:
    payload = {"model": model, "temperature": 0, "max_tokens": max_tokens, "messages": messages}
    data = json.dumps(payload).encode()
    last = None
    for attempt in range(4):
        req = urllib.request.Request(
            ENDPOINT, data=data,
            headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"})
        started = time.time()
        try:
            with urllib.request.urlopen(req, timeout=180) as r:
                body = json.loads(r.read())
            ch = body["choices"][0]
            usage = body.get("usage", {}) or {}
            det = usage.get("completion_tokens_details") or {}
            return {
                "text": ch["message"].get("content") or "",
                "finish_reason": ch.get("finish_reason"),
                "reasoning_tokens": det.get("reasoning_tokens", 0),
                "tokens": usage.get("total_tokens", 0),
                "cost_usd": usage.get("cost", 0.0),
                "elapsed_s": round(time.time() - started, 2),
            }
        except urllib.error.HTTPError as exc:
            last = f"HTTP {exc.code}"
            if exc.code in (429, 500, 502, 503):
                time.sleep(4 * (attempt + 1))
                continue
            return {"error": last, "text": "", "tokens": 0, "cost_usd": 0.0,
                    "elapsed_s": 0.0, "finish_reason": None, "reasoning_tokens": 0}
        except (urllib.error.URLError, TimeoutError) as exc:
            last = type(exc).__name__
            time.sleep(3 * (attempt + 1))
    return {"error": last, "text": "", "tokens": 0, "cost_usd": 0.0,
            "elapsed_s": 0.0, "finish_reason": None, "reasoning_tokens": 0}


def build_messages(condition: str, skill_text: str, inst: dict) -> list[dict]:
    if condition == "prompt_spec":
        msgs = [{"role": "system", "content": SYS_PROMPT_SPEC}]
    else:
        msgs = [{"role": "system", "content": SYS_PROMPT_SKILL},
                {"role": "user", "content": f"Payload conventions (load once):\n\n{skill_text}"},
                {"role": "assistant", "content": "Noted. Send the payload and the question."}]
    msgs.append({"role": "user",
                 "content": f"Data table:\n{TABLE}\n\nMessage from Agent A:\n{inst['payload']}\n"
                            f"Question: {inst['question']}"})
    return msgs


def qualifier_in_text(text: str) -> bool:
    low = text.lower()
    return any(m in low for m in QUALIFIER_MARKERS)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--models", default=",".join(DEFAULT_MODELS))
    args = ap.parse_args()
    models = [m.strip() for m in args.models.split(",") if m.strip()]
    skill_text = SKILL_PATH.read_text()
    key = api_key()
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    log = (OUT_DIR / "runs.jsonl").open("w")
    rows = []
    for model in models:
        for condition in ("prompt_spec", "skill"):
            for name, inst in INSTANCES.items():
                r = call(key, model, build_messages(condition, skill_text, inst))
                row = {
                    "ts": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                    "model": model, "condition": condition, "instance": name,
                    "needs_expand": inst["needs_expand"],
                    "expand_used": bool(EXPAND_RE.search(r["text"])),
                    "qualifier_preserved": qualifier_in_text(r["text"]),
                    "empty": not r["text"].strip(),
                    **{k: r[k] for k in ("finish_reason", "reasoning_tokens", "tokens",
                                         "cost_usd", "elapsed_s")},
                    "error": r.get("error"),
                    "text": r["text"],
                }
                rows.append(row)
                log.write(json.dumps(row, ensure_ascii=False) + "\n")
                log.flush()
                print(f"{model.split('/')[-1][:22]:22} {condition:11} {name:9} "
                      f"q={str(row['qualifier_preserved']):5} expand={str(row['expand_used']):5} "
                      f"tok={row['tokens']:5} {row['elapsed_s']:5.1f}s "
                      f"{'EMPTY' if row['empty'] else ''}{row['error'] or ''}")
    log.close()
    summary = {"models": models, "rows": len(rows),
               "total_cost_usd": round(sum(r["cost_usd"] for r in rows), 6)}
    (OUT_DIR / "summary.json").write_text(json.dumps(summary, indent=2))
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
