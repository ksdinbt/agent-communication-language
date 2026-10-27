#!/usr/bin/env python3
"""Overhead probe: how much does it cost to teach the conventions, and can that be cut?

The length probe found a fixed per-session overhead: 2,826 reasoning tokens per turn at T=1,
against 296 for prose. The convention block and the JSON contract are re-read on every call, so
the overhead is a property of their size and shape, not of the task.

Four variants, same payloads, same questions:

  v0  long skill (3.2k chars)   + prose contract (schema keys + rules)
  v1  compact skill (1.2k)      + prose contract
  v2  compact skill (1.2k)      + example-based contract (three JSON examples, no key list)
  v3  no skill                  + example-based contract (payload itself is the only teacher)

Measured: prompt tokens (the direct size of the overhead), reasoning tokens, billed cost,
contract validity, qualifier retention, EXPAND correctness.

Run: python3 overhead_probe.py [--reps 2]
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
SKILL_LONG = (ROOT / "skills" / "typed-payload-v0" / "SKILL.md").read_text()
SKILL_SHORT = (ROOT / "skills" / "typed-payload-v1" / "SKILL.md").read_text()
OUT = ROOT / "results" / "overhead-probe-2026-10-27"
MODELS = ["xiaomi/mimo-v2.6-flash", "openai/gpt-6-luna"]

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
PAYLOAD_DEFERRED = PAYLOAD_PARTIAL + "defer r1 table granularity=[weekly,daily] cost=1200\n"

INSTANCES = {
    "partial": {"payload": PAYLOAD_PARTIAL, "needs_expand": False,
                "question": "Compare sports turnover in 2026-W41 with 2026-W40."},
    "deferred": {"payload": PAYLOAD_DEFERRED, "needs_expand": True,
                 "question": "Is the 2026-W41 decline uniform across days, or driven by one day?"},
}

CONTRACT_PROSE = """Reply with ONE JSON object and nothing outside it. Schema:
{"act": "!REPORT" | "!EXPAND" | "!CANNOT_EXPAND", "ref": null | "r1",
 "granularity": null | "weekly" | "daily", "value": null | number,
 "epistemic": "OBSERVED" | "DERIVED" | "ASSUMED" | "PREDICTED" | "UNKNOWN",
 "qualifier": "none" | "partial_period" | "stale_extract" | "definition_changed" | "sample_too_small" | "other",
 "answer": "one or two sentences", "missing": []}
Rules: act=!EXPAND only when a deferral blocks you, then give ref and granularity.
Carry the payload's qualifier while it still applies. If the payload cannot support the question,
act=!REPORT with epistemic=UNKNOWN and name the gap in `missing`."""

CONTRACT_EXAMPLE = """Reply with one JSON object, shaped like this:

{"act":"!REPORT","ref":null,"granularity":null,"value":890000,"epistemic":"OBSERVED",
 "qualifier":"partial_period","answer":"W41 is 890k against 1.24M in W40; W41 is a partial week.",
 "missing":[]}

If a deferral blocks you: {"act":"!EXPAND","ref":"r1","granularity":"daily","value":null,
"epistemic":"UNKNOWN","qualifier":"none","answer":"Need the daily split.","missing":[]}

If the data cannot answer: {"act":"!REPORT","ref":null,"granularity":null,"value":null,
"epistemic":"UNKNOWN","qualifier":"none","answer":"Cannot decide.","missing":["daily W40 split"]}"""

VARIANTS = {
    "v0_long_skill_prose_contract": (SKILL_LONG, CONTRACT_PROSE),
    "v1_short_skill_prose_contract": (SKILL_SHORT, CONTRACT_PROSE),
    "v2_short_skill_example_contract": (SKILL_SHORT, CONTRACT_EXAMPLE),
    "v3_no_skill_example_contract": (None, CONTRACT_EXAMPLE),
}

FLAG = ["partial", "incomplete", "day 3", "3 of 7", "mid-week", "not complete", "only three days"]
KEYS = {"act", "ref", "granularity", "value", "epistemic", "qualifier", "answer", "missing"}


def api_key() -> str:
    if k := os.environ.get("OPENROUTER_API_KEY"):
        return k
    for line in (Path.home() / ".hermes" / ".env").read_text().splitlines():
        if line.startswith("OPENROUTER_API_KEY="):
            return line.split("=", 1)[1].strip().strip('"')
    raise SystemExit("no key")


def call(key: str, model: str, messages: list[dict], max_tokens: int = 4000) -> dict:
    payload = {"model": model, "temperature": 0, "max_tokens": max_tokens,
               "response_format": {"type": "json_object"}, "messages": messages}
    data = json.dumps(payload).encode()
    for attempt in range(4):
        req = urllib.request.Request(ENDPOINT, data=data,
                                     headers={"Authorization": f"Bearer {key}",
                                              "Content-Type": "application/json"})
        t0 = time.time()
        try:
            with urllib.request.urlopen(req, timeout=240) as r:
                body = json.loads(r.read())
            ch = body["choices"][0]
            u = body.get("usage") or {}
            det = u.get("completion_tokens_details") or {}
            ct = u.get("completion_tokens", 0) or 0
            rt = det.get("reasoning_tokens", 0) or 0
            billed = u.get("cost", 0.0) or 0.0
            return {"text": ch["message"].get("content") or "", "finish": ch.get("finish_reason"),
                    "prompt_tokens": u.get("prompt_tokens", 0) or 0, "completion_tokens": ct,
                    "reasoning": rt, "billed": billed,
                    "payload_cost": round(billed * (ct - rt) / ct, 8) if ct else 0.0,
                    "elapsed": round(time.time() - t0, 2), "error": None}
        except urllib.error.HTTPError as exc:
            if exc.code in (429, 500, 502, 503):
                time.sleep(4 * (attempt + 1))
                continue
            return {"text": "", "finish": None, "prompt_tokens": 0, "completion_tokens": 0,
                    "reasoning": 0, "billed": 0.0, "payload_cost": 0.0, "elapsed": 0.0,
                    "error": f"HTTP {exc.code}"}
        except (urllib.error.URLError, TimeoutError) as exc:
            time.sleep(3 * (attempt + 1))
            last = type(exc).__name__
    return {"text": "", "finish": None, "prompt_tokens": 0, "completion_tokens": 0, "reasoning": 0,
            "billed": 0.0, "payload_cost": 0.0, "elapsed": 0.0, "error": locals().get("last")}


def messages(skill: str | None, contract: str, inst: dict) -> list[dict]:
    msgs = [{"role": "system", "content": f"You are Agent B, a verifier. {contract}"}]
    if skill:
        msgs += [{"role": "user", "content": skill.strip()},
                 {"role": "assistant", "content": "ok"}]
    msgs.append({"role": "user",
                 "content": f"Data table:\n{TABLE}\n\nMessage from Agent A:\n{inst['payload']}\n"
                            f"Question: {inst['question']}"})
    return msgs


def parse(text: str) -> tuple[dict | None, str]:
    if not text.strip():
        return None, "empty"
    m = re.search(r"\{.*\}", text, re.S)
    if not m:
        return None, "no-json"
    try:
        obj = json.loads(m.group(0))
    except json.JSONDecodeError as exc:
        return None, f"bad-json:{exc.msg}"
    missing = KEYS - set(obj)
    return obj, ("ok" if not missing else f"missing:{','.join(sorted(missing))}")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--reps", type=int, default=2)
    args = ap.parse_args()
    key = api_key()
    OUT.mkdir(parents=True, exist_ok=True)
    rows = []
    with (OUT / "runs.jsonl").open("w") as log:
        for variant, (skill, contract) in VARIANTS.items():
            for model in MODELS:
                for name, inst in INSTANCES.items():
                    for rep in range(args.reps):
                        r = call(key, model, messages(skill, contract, inst))
                        obj, status = parse(r["text"])
                        row = {
                            "ts": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                            "variant": variant, "model": model, "instance": name, "rep": rep,
                            "skill_chars": len(skill or ""), "contract_chars": len(contract),
                            "parse": status, "valid": status == "ok",
                            "act": (obj or {}).get("act"),
                            "expand_correct": (((obj or {}).get("act") == "!EXPAND")
                                               == inst["needs_expand"]) if status == "ok" else None,
                            "qualifier": any(w in (r["text"] or "").lower() for w in FLAG),
                            "empty": not r["text"].strip(),
                            **{k: r[k] for k in ("prompt_tokens", "completion_tokens", "reasoning",
                                                 "billed", "payload_cost", "elapsed", "finish")},
                            "error": r["error"], "text": r["text"],
                        }
                        rows.append(row)
                        log.write(json.dumps(row, ensure_ascii=False) + "\n")
                        log.flush()
                        print(f"{variant:32}{model.split('/')[-1][:14]:15}{name:9}r{rep} "
                              f"prompt={row['prompt_tokens']:5} reas={row['reasoning']:5} "
                              f"billed=${row['billed']:.6f} valid={int(row['valid'])} "
                              f"q={int(row['qualifier'])} "
                              f"exp={row['expand_correct']}{row['error'] or ''}")

    print("\n## Per variant")
    print(f"{'variant':34}{'prompt':>8}{'reasoning':>11}{'billed':>11}{'valid':>8}{'qualif':>8}{'expand':>8}")
    for variant in VARIANTS:
        sub = [r for r in rows if r["variant"] == variant and not r["error"]]
        if not sub:
            print(f"{variant:34}{'no data':>8}")
            continue
        n = len(sub)
        print(f"{variant:34}{sum(r['prompt_tokens'] for r in sub) / n:8.0f}"
              f"{sum(r['reasoning'] for r in sub) / n:11.0f}"
              f"{sum(r['billed'] for r in sub) / n:11.6f}"
              f"{sum(r['valid'] for r in sub):5}/{n:<3}"
              f"{sum(r['qualifier'] for r in sub):5}/{n:<3}"
              f"{sum(bool(r['expand_correct']) for r in sub):5}/{n:<3}")

    summary = {"rows": len(rows), "total_billed": round(sum(r["billed"] for r in rows), 6),
               "variants": list(VARIANTS)}
    (OUT / "summary.json").write_text(json.dumps(summary, indent=2))
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
