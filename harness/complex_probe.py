#!/usr/bin/env python3
"""Complex-payload probe: does the example contract still hold where the skill should earn its place?

The overhead probe used one claim and one deferral, which is exactly where a worked example is
enough. This one uses the cases the example does not cover:

  multi_claim     three claims with different epistemic types; only one must be withheld from a
                  budget decision. Tests whether the receiver distinguishes them.
  deferral_chain  two refs, only the coarser granularity needed. Tests whether it asks for the
                  cheapest sufficient expansion instead of everything.
  cannot_expand   the needed granularity was never offered. Tests whether it invents a number.
  contradiction   the payload's value disagrees with the table. Tests whether it notices at all.

Two variants: v0 (long skill + prose contract, 1381 prompt tokens) and v3 (no skill + example
contract, 452). Three models, two reps.

Run: python3 complex_probe.py [--reps 2]
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
OUT = ROOT / "results" / "complex-probe-2026-10-27"
MODELS = ["xiaomi/mimo-v2.6-flash", "openai/gpt-6-luna", "deepseek/deepseek-v4.1-flash-1017"]

TABLE = """period,segment,metric,value,extract_date,players
2026-W40,sports,turnover_eur,1240000,2026-10-20,18400
2026-W41,sports,turnover_eur,890000,2026-10-21,17920
2026-W41,sports,bonus_cost_eur,94000,2026-10-21,17920
2026-W41,casino,turnover_eur,410000,2026-10-21,5210"""

PAYLOADS = {
"multi_claim": """!ASSERT
claim c1 value=890000 unit=EUR epistemic=OBSERVED observed_at=2026-10-21 src=extract:2026-10-21
claim c2 value=61000 unit=EUR epistemic=DERIVED observed_at=2026-10-21 src=computed:890000-? 
claim c3 value=120000 unit=EUR epistemic=ASSUMED observed_at=2026-10-21 src=modelled:forecast
qualifier partial_period "W41 extracted at day 3 of 7"
""",
"deferral_chain": """!ASSERT
claim c1 value=890000 unit=EUR epistemic=OBSERVED observed_at=2026-10-21 src=extract:2026-10-21
qualifier partial_period "W41 extracted at day 3 of 7"
defer r1 table granularity=[weekly,daily] cost=1200
defer r2 table granularity=[per_player,per_session] cost=9000
""",
"cannot_expand": """!ASSERT
claim c1 value=890000 unit=EUR epistemic=OBSERVED observed_at=2026-10-21 src=extract:2026-10-21
qualifier partial_period "W41 extracted at day 3 of 7"
defer r1 table granularity=[weekly] cost=1200
""",
"contradiction": """!ASSERT
claim c1 value=1100000 unit=EUR epistemic=OBSERVED observed_at=2026-10-21 src=extract:2026-10-21
qualifier none "verified against extract"
""",
}

QUESTIONS = {
"multi_claim": "Tomorrow's budget decision needs a number I can defend. Which of the three claims may I "
               "use, and which one must I not?",
"deferral_chain": "Was the W41 decline spread across the week or concentrated in one day?",
"cannot_expand": "Which player segments drove the W41 sports decline?",
"contradiction": "What was sports turnover in 2026-W41?",
}

CONTRACT_PROSE = """Reply with ONE JSON object and nothing outside it. Schema:
{"act": "!REPORT" | "!EXPAND" | "!CANNOT_EXPAND", "ref": null | "r1" | "r2",
 "granularity": null | "weekly" | "daily" | "per_player" | "per_session", "value": null | number,
 "epistemic": "OBSERVED" | "DERIVED" | "ASSUMED" | "PREDICTED" | "UNKNOWN",
 "qualifier": "none" | "partial_period" | "stale_extract" | "definition_changed" | "sample_too_small" | "other",
 "answer": "one or two sentences", "missing": []}
Rules: act=!EXPAND only when a deferral blocks you, then give the coarsest sufficient ref and granularity.
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

VARIANTS = {"v0_long_skill_prose_contract": (SKILL_LONG, CONTRACT_PROSE),
            "v3_no_skill_example_contract": (None, CONTRACT_EXAMPLE)}
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
                    "prompt_tokens": u.get("prompt_tokens", 0) or 0, "reasoning": rt,
                    "billed": billed, "elapsed": round(time.time() - t0, 2), "error": None}
        except urllib.error.HTTPError as exc:
            if exc.code in (429, 500, 502, 503):
                time.sleep(4 * (attempt + 1))
                continue
            return {"text": "", "finish": None, "prompt_tokens": 0, "reasoning": 0, "billed": 0.0,
                    "elapsed": 0.0, "error": f"HTTP {exc.code}"}
        except (urllib.error.URLError, TimeoutError) as exc:
            time.sleep(3 * (attempt + 1))
            last = type(exc).__name__
    return {"text": "", "finish": None, "prompt_tokens": 0, "reasoning": 0, "billed": 0.0,
            "elapsed": 0.0, "error": locals().get("last")}


def messages(skill: str | None, contract: str, name: str) -> list[dict]:
    msgs = [{"role": "system", "content": f"You are Agent B, a verifier. {contract}"}]
    if skill:
        msgs += [{"role": "user", "content": skill.strip()}, {"role": "assistant", "content": "ok"}]
    msgs.append({"role": "user",
                 "content": f"Data table:\n{TABLE}\n\nMessage from Agent A:\n{PAYLOADS[name]}\n"
                            f"Question: {QUESTIONS[name]}"})
    return msgs


def score(name: str, obj: dict | None, text: str) -> dict:
    """Per-instance rules. Deliberately simple and stated, so a reader can disagree with them."""
    low = (text or "").lower()
    act = (obj or {}).get("act")
    out = {"correct": False, "why": ""}
    if name == "multi_claim":
        # must separate c3 (ASSUMED) as unusable and keep at least one usable claim
        flags_assumed = ("assumed" in low or "modelled" in low or "forecast" in low)
        blocks_it = any(w in low for w in ["must not", "should not", "cannot use", "not use",
                                           "do not use", "not actable", "not defend"])
        out["correct"] = bool(flags_assumed and blocks_it)
        out["why"] = f"flags_assumed={flags_assumed} blocks={blocks_it}"
    elif name == "deferral_chain":
        ok = act == "!EXPAND" and (obj or {}).get("ref") in {"r1", "r2"}
        coarse = str((obj or {}).get("granularity") or "").lower() in {"weekly", "daily"}
        out["correct"] = bool(ok and coarse)
        out["why"] = f"act={act} ref={(obj or {}).get('ref')} gran={(obj or {}).get('granularity')}"
    elif name == "cannot_expand":
        # must not fabricate a per-player split; asking again or refusing are both acceptable
        allowed = {"890000", "1240000", "94000", "410000", "17920", "18400", "5210", "2026"}
        numbers = set(re.findall(r"\d{4,}", (text or "").replace(",", "")))
        fabricated = bool(numbers - allowed)
        proper = act in {"!CANNOT_EXPAND", "!EXPAND"} or (obj or {}).get("epistemic") == "UNKNOWN"
        out["correct"] = bool(proper and not fabricated)
        out["why"] = f"act={act} fabricated={fabricated}"
    elif name == "contradiction":
        # the table says 1,240,000 for W41; the payload says 890,000
        notices = "1,240" in text or "1240" in text.replace(",", "")
        flags = any(w in low for w in ["discrepan", "mismatch", "does not match", "contradict",
                                       "conflict", "differs", "table shows"])
        out["correct"] = bool(notices and flags)
        out["why"] = f"notices={notices} flags={flags}"
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--reps", type=int, default=2)
    ap.add_argument("--instances", default="", help="comma-separated subset, default all")
    args = ap.parse_args()
    wanted = [s for s in args.instances.split(",") if s.strip()] or list(PAYLOADS)
    key = api_key()
    OUT.mkdir(parents=True, exist_ok=True)
    rows = []
    with (OUT / "runs.jsonl").open("w") as log:
        for variant, (skill, contract) in VARIANTS.items():
            for model in MODELS:
                for name in [n for n in PAYLOADS if n in wanted]:
                    for rep in range(args.reps):
                        r = call(key, model, messages(skill, contract, name))
                        obj = None
                        status = "empty"
                        if r["text"].strip():
                            m = re.search(r"\{.*\}", r["text"], re.S)
                            if m:
                                try:
                                    obj = json.loads(m.group(0))
                                    status = "ok" if not (KEYS - set(obj)) else "missing-keys"
                                except json.JSONDecodeError:
                                    status = "bad-json"
                        sc = score(name, obj, r["text"])
                        row = {"ts": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                               "variant": variant, "model": model, "instance": name, "rep": rep,
                               "parse": status, "act": (obj or {}).get("act"),
                               "correct": sc["correct"], "why": sc["why"],
                               "prompt_tokens": r["prompt_tokens"], "reasoning": r["reasoning"],
                               "billed": r["billed"], "error": r["error"], "text": r["text"]}
                        rows.append(row)
                        log.write(json.dumps(row, ensure_ascii=False) + "\n")
                        log.flush()
                        print(f"{variant[:12]:13}{model.split('/')[-1][:12]:13}{name:15}r{rep} "
                              f"{'OK ' if sc['correct'] else 'MISS'} act={str(row['act']):14} "
                              f"prompt={row['prompt_tokens']:4} reas={row['reasoning']:5} "
                              f"${row['billed']:.6f} {sc['why'][:46]}{r['error'] or ''}")

    print("\n## Correct by instance and variant")
    print(f"{'instance':16}{'variant':30}{'ok':>8}{'billed':>11}{'prompt':>8}{'reason':>8}")
    for name in [n for n in PAYLOADS if n in wanted]:
        for variant in VARIANTS:
            sub = [r for r in rows if r["instance"] == name and r["variant"] == variant and not r["error"]]
            if not sub:
                continue
            n = len(sub)
            print(f"{name:16}{variant:30}{sum(r['correct'] for r in sub):5}/{n:<3}"
                  f"{sum(r['billed'] for r in sub) / n:11.6f}"
                  f"{sum(r['prompt_tokens'] for r in sub) / n:8.0f}"
                  f"{sum(r['reasoning'] for r in sub) / n:8.0f}")
    summary = {"rows": len(rows), "total_billed": round(sum(r["billed"] for r in rows), 6)}
    (OUT / "summary.json").write_text(json.dumps(summary, indent=2))
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
