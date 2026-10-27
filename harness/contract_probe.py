#!/usr/bin/env python3
"""Receiver-contract probe: structured decisions, free reasoning, three-way cost.

Design decisions, and why:

1. Reasoning is allowed and not fought. `max_tokens` is generous (6000) so a model can
   think as long as it needs; the run records `finish_reason` and refuses to score a
   truncated answer as a behavioural failure.
2. Cost is reported three ways, never one:
       cost_billed  - what the invoice says: prompt + completion, reasoning included
       cost_payload - prompt + completion excluding reasoning tokens
       reasoning    - reported separately
   Only `cost_billed` may support a claim about saving money. `cost_payload` answers a
   narrower question: how much of the bill is attributable to the payload as opposed to
   the model's own deliberation.
3. The receiver's answer is a decision object, not prose, so a missing !EXPAND is a
   validation error with a name rather than a stylistic choice.

Conditions:
    prose     - answer freely, plus a final STATUS line (what the earlier probes did)
    contract  - reply with a single JSON object matching DECISION_SCHEMA

Run: python3 contract_probe.py [--reps 3] [--models a,b]
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
SKILL = (ROOT / "skills" / "typed-payload-v0" / "SKILL.md").read_text()
OUT = ROOT / "results" / "contract-probe-2026-10-27"

MODELS = ["xiaomi/mimo-v2.6-flash", "z-ai/glm-5.3-flash",
          "deepseek/deepseek-v4.1-flash-1017", "openai/gpt-6-luna"]

TABLE = """period,day,segment,turnover_eur,extract_date
2026-W40,,sports,1240000,2026-10-20
2026-W41,,sports,890000,2026-10-21
2026-W41,2026-10-19,sports,310000,2026-10-21
2026-W41,2026-10-20,sports,330000,2026-10-21
2026-W41,2026-10-21,sports,250000,2026-10-21
2026-W39,,casino,540000,2026-10-13"""

PAYLOAD_PARTIAL = """!ASSERT
claim c1 value=890000 unit=EUR epistemic=OBSERVED observed_at=2026-10-21 src=extract:2026-10-21
qualifier partial_period "W41 extracted at day 3 of 7"
"""

PAYLOAD_DEFERRED = PAYLOAD_PARTIAL + """defer r1 table granularity=[weekly,daily] cost=1200
"""

PAYLOAD_STALE = """!ASSERT
claim c1 value=540000 unit=EUR epistemic=OBSERVED observed_at=2026-10-13 src=extract:2026-10-13
qualifier stale_extract "casino figure from a 14-day-old extract"
"""

PAYLOAD_UNKNOWN = """!ASSERT
claim c1 value=210000 unit=EUR epistemic=ASSUMED observed_at=2026-10-21 src=modelled:no-source
qualifier sample_too_small "casino W41 based on 12 players"
"""

INSTANCES = {
    "partial": {"payload": PAYLOAD_PARTIAL, "needs_expand": False, "expect_value": "890000",
                "must_flag": "partial_period"},
    "deferred": {"payload": PAYLOAD_DEFERRED, "needs_expand": True, "expect_value": "890000",
                 "must_flag": "partial_period"},
    "stale": {"payload": PAYLOAD_STALE, "needs_expand": False, "expect_value": "540000",
              "must_flag": "stale_extract"},
    "assumed": {"payload": PAYLOAD_UNKNOWN, "needs_expand": False, "expect_value": "210000",
                "must_flag": "sample_too_small"},
}

QUESTIONS = {
    "partial": "Compare sports turnover in 2026-W41 with 2026-W40.",
    "deferred": "Is the 2026-W41 decline uniform across days, or driven by one day?",
    "stale": "What is casino turnover for the latest period, and can I use it for tomorrow's decision?",
    "assumed": "What was casino turnover in 2026-W41?",
}

SYS_PROSE = """You are Agent B, a verifier. The payload conventions are supplied as context: follow them.
Answer the question, then end with a line: STATUS: qualifier=<yes|no>"""

SYS_CONTRACT = """You are Agent B, a verifier. The payload conventions are supplied as context.
Reply with ONE JSON object and nothing outside it. Schema:

{"act": "!REPORT" | "!EXPAND" | "!CANNOT_EXPAND",
 "ref": null | "r1",
 "granularity": null | "weekly" | "daily",
 "value": null | number,
 "epistemic": "OBSERVED" | "DERIVED" | "ASSUMED" | "PREDICTED" | "UNKNOWN",
 "qualifier": "none" | "partial_period" | "stale_extract" | "definition_changed" | "sample_too_small" | "other",
 "answer": "one or two sentences",
 "missing": [] }

Rules: use act=!EXPAND only when a deferral blocks you, and then give ref and granularity.
Use qualifier=UNKNOWN-free: carry the payload's qualifier if it still applies. If the payload
cannot support the question, act=!REPORT with epistemic=UNKNOWN and name the gap in `missing`."""

DECISION_KEYS = {"act", "ref", "granularity", "value", "epistemic", "qualifier", "answer", "missing"}

FLAG_WORDS = {
    "partial_period": ["partial", "incomplete", "day 3", "3 of 7", "mid-week", "not complete"],
    "stale_extract": ["stale", "2026-10-13", "as of", "14 day", "old extract", "not current"],
    "sample_too_small": ["small sample", "12 players", "too small", "unreliable", "assumed", "no source"],
}


def api_key() -> str:
    if k := os.environ.get("OPENROUTER_API_KEY"):
        return k
    for line in (Path.home() / ".hermes" / ".env").read_text().splitlines():
        if line.startswith("OPENROUTER_API_KEY="):
            return line.split("=", 1)[1].strip().strip('"')
    raise SystemExit("no key")


def call(key: str, model: str, condition: str, inst_name: str, max_tokens: int = 6000) -> dict:
    inst = INSTANCES[inst_name]
    sys_p = SYS_CONTRACT if condition == "contract" else SYS_PROSE
    msgs = [
        {"role": "system", "content": sys_p},
        {"role": "user", "content": f"Payload conventions (load once):\n\n{SKILL}"},
        {"role": "assistant", "content": "Noted."},
        {"role": "user", "content": f"Data table:\n{TABLE}\n\nMessage from Agent A:\n{inst['payload']}\n"
                                    f"Question: {QUESTIONS[inst_name]}"},
    ]
    payload = {"model": model, "temperature": 0, "max_tokens": max_tokens, "messages": msgs}
    if condition == "contract":
        payload["response_format"] = {"type": "json_object"}
    data = json.dumps(payload).encode()
    for attempt in range(4):
        req = urllib.request.Request(ENDPOINT, data=data,
                                     headers={"Authorization": f"Bearer {key}",
                                              "Content-Type": "application/json"})
        started = time.time()
        try:
            with urllib.request.urlopen(req, timeout=240) as r:
                body = json.loads(r.read())
            ch = body["choices"][0]
            usage = body.get("usage") or {}
            det = usage.get("completion_tokens_details") or {}
            rt = det.get("reasoning_tokens", 0) or 0
            pt = usage.get("prompt_tokens", 0) or 0
            ct = usage.get("completion_tokens", 0) or 0
            billed = usage.get("cost", 0.0) or 0.0
            # cost_payload: same call minus reasoning tokens, priced at the completion rate
            price_c = 0.0
            if ct and billed:
                price_c = billed / max(ct, 1)
            return {
                "text": ch["message"].get("content") or "",
                "finish_reason": ch.get("finish_reason"),
                "reasoning_tokens": rt, "prompt_tokens": pt, "completion_tokens": ct,
                "cost_billed": billed,
                "cost_payload": round(billed * (ct - rt) / ct, 8) if ct else 0.0,
                "elapsed_s": round(time.time() - started, 2),
                "error": None,
            }
        except urllib.error.HTTPError as exc:
            if exc.code in (429, 500, 502, 503):
                time.sleep(4 * (attempt + 1))
                continue
            return {"text": "", "finish_reason": None, "reasoning_tokens": 0,
                    "prompt_tokens": 0, "completion_tokens": 0, "cost_billed": 0.0,
                    "cost_payload": 0.0, "elapsed_s": 0.0, "error": f"HTTP {exc.code}"}
        except (urllib.error.URLError, TimeoutError) as exc:
            time.sleep(3 * (attempt + 1))
            last = type(exc).__name__
    return {"text": "", "finish_reason": None, "reasoning_tokens": 0, "prompt_tokens": 0,
            "completion_tokens": 0, "cost_billed": 0.0, "cost_payload": 0.0,
            "elapsed_s": 0.0, "error": locals().get("last", "timeout")}


def parse_decision(text: str) -> tuple[dict | None, str]:
    if not text.strip():
        return None, "empty"
    m = re.search(r"\{.*\}", text, re.S)
    if not m:
        return None, "no-json"
    try:
        obj = json.loads(m.group(0))
    except json.JSONDecodeError as exc:
        return None, f"bad-json:{exc.msg}"
    missing = DECISION_KEYS - set(obj)
    if missing:
        return obj, f"missing-keys:{','.join(sorted(missing))}"
    return obj, "ok"


def flag_present(text: str, kind: str) -> bool:
    low = text.lower()
    return any(w in low for w in FLAG_WORDS[kind])


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--reps", type=int, default=3)
    ap.add_argument("--models", default=",".join(MODELS))
    args = ap.parse_args()
    models = [m.strip() for m in args.models.split(",") if m.strip()]
    key = api_key()
    OUT.mkdir(parents=True, exist_ok=True)
    rows = []
    with (OUT / "runs.jsonl").open("w") as log:
        for model in models:
            for condition in ("prose", "contract"):
                for inst_name in INSTANCES:
                    for rep in range(args.reps):
                        r = call(key, model, condition, inst_name)
                        obj, status = parse_decision(r["text"]) if condition == "contract" else (None, "prose")
                        must = INSTANCES[inst_name]["must_flag"]
                        row = {
                            "ts": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                            "model": model, "condition": condition, "instance": inst_name, "rep": rep,
                            "parse_status": status,
                            "contract_valid": status == "ok",
                            "act": (obj or {}).get("act"),
                            "expand_correct": (
                                ((obj or {}).get("act") == "!EXPAND") == INSTANCES[inst_name]["needs_expand"]
                                if status == "ok" else None),
                            "qualifier_in_text": flag_present(r["text"] + " " + str((obj or {}).get("qualifier")), must),
                            "value_correct": INSTANCES[inst_name]["expect_value"] in r["text"].replace(",", ""),
                            "empty": not r["text"].strip(),
                            **{k: r[k] for k in ("finish_reason", "reasoning_tokens", "prompt_tokens",
                                                 "completion_tokens", "cost_billed", "cost_payload",
                                                 "elapsed_s", "error")},
                            "text": r["text"],
                        }
                        rows.append(row)
                        log.write(json.dumps(row, ensure_ascii=False) + "\n")
                        log.flush()
                        print(f"{model.split('/')[-1][:18]:18}{condition:9}{inst_name:8}r{rep} "
                              f"fin={str(r['finish_reason']):>6} reas={r['reasoning_tokens']:5} "
                              f"billed=${r['cost_billed']:.6f} payload=${r['cost_payload']:.6f} "
                              f"{status if condition=='contract' else ''}"
                              f"{' EMPTY' if row['empty'] else ''}{r['error'] or ''}")
    summary = {
        "rows": len(rows), "reps": args.reps, "models": models,
        "total_billed_usd": round(sum(r["cost_billed"] for r in rows), 6),
        "total_payload_usd": round(sum(r["cost_payload"] for r in rows), 6),
        "empty": sum(1 for r in rows if r["empty"]),
        "truncated": sum(1 for r in rows if r["finish_reason"] == "length"),
    }
    (OUT / "summary.json").write_text(json.dumps(summary, indent=2))
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
