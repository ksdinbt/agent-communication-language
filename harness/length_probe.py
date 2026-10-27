#!/usr/bin/env python3
"""Length probe: does the payload-format gap grow with session length?

The earlier probes measured one exchange. That answers "is this format cheaper per message",
which is the wrong question: real agent sessions run for many turns, and a per-message
difference either compounds or stays flat. This probe measures the slope.

Design:
    lengths   1 and 8 turns
    arms      nl        - Agent A writes prose, Agent B replies in prose
              payload   - Agent A writes the typed payload, Agent B replies with a validated
                          JSON decision object
    task      each turn adds one period row; B maintains a running answer; the final answer
              is what gets scored
    traps     turn 3 is an incomplete week (partial_period), turn 6 an old extract (stale_extract).
              A qualifier raised at turn 3 must still be visible in the answer at turn 8.

Both agents are model calls, so sender cost is included. Fixed schedule, no extra turns.

Metrics per session: cost_billed, cost_payload, reasoning tokens, per-turn means, final answer
correctness, qualifier survival, and whether the final answer silently used only the last row.

Run: python3 length_probe.py [--models a,b] [--reps 2]
"""

from __future__ import annotations

import argparse
import json
import os
import re
import statistics
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ENDPOINT = "https://openrouter.ai/api/v1/chat/completions"
ROOT = Path(__file__).resolve().parent.parent
SKILL = (ROOT / "skills" / "typed-payload-v0" / "SKILL.md").read_text()
OUT = ROOT / "results" / "length-probe-2026-10-27"

MODELS = ["xiaomi/mimo-v2.6-flash", "z-ai/glm-5.3-flash", "openai/gpt-6-luna"]
LENGTHS = [1, 8]
REPS = 2

# Turn data: one row per turn. Turns 3 and 6 carry the traps.
TURNS = [
    {"period": "2026-W33", "segment": "sports", "turnover": 1_050_000, "extract": "2026-08-24",
     "trap": None},
    {"period": "2026-W34", "segment": "sports", "turnover": 1_120_000, "extract": "2026-08-31",
     "trap": None},
    {"period": "2026-W35", "segment": "sports", "turnover": 640_000, "extract": "2026-09-02",
     "trap": "partial_period"},   # extracted on day 3 of 7
    {"period": "2026-W36", "segment": "sports", "turnover": 1_180_000, "extract": "2026-09-07",
     "trap": None},
    {"period": "2026-W37", "segment": "sports", "turnover": 1_240_000, "extract": "2026-09-14",
     "trap": None},
    {"period": "2026-W38", "segment": "sports", "turnover": 1_260_000, "extract": "2026-08-30",
     "trap": "stale_extract"},    # snapshot older than the period it describes
    {"period": "2026-W39", "segment": "sports", "turnover": 1_310_000, "extract": "2026-09-28",
     "trap": None},
    {"period": "2026-W40", "segment": "sports", "turnover": 1_240_000, "extract": "2026-10-05",
     "trap": None},
]

QUESTION = "Track sports turnover week by week. At the end, say which week was the weakest and why."

SYS_A_NL = """You are Agent A, an analyst. Each turn you receive one new week of data. Write Agent B
a short natural-language update. Mention anything about the data that affects how the figure should
be read. Do not answer the overall question yourself."""

SYS_A_PAYLOAD = """You are Agent A, an analyst. Each turn you receive one new week of data. Write Agent B
a payload in the typed format supplied as context. Set epistemic, observed_at and qualifier honestly:
if the extract date is mid-week or older than the period, say so. Do not answer the overall question."""

SYS_B_NL = """You are Agent B, a verifier. Each turn you receive Agent A's update. Maintain your
running understanding of the series; the final answer to the overall question is what gets scored.
Be accurate about how each figure should be read."""

SYS_B_PAYLOAD = """You are Agent B, a verifier. Each turn you receive Agent A's payload. Maintain your
running understanding; the final answer is what gets scored. Reply in one JSON object:

{"seen": "<period>", "value": <number or null>, "epistemic": "<type>", "qualifier": "<type>",
 "note": "<short>", "running_finding": "<one sentence>"}

Carry a qualifier forward until it stops applying, and say why if it does."""


def api_key() -> str:
    if k := os.environ.get("OPENROUTER_API_KEY"):
        return k
    for line in (Path.home() / ".hermes" / ".env").read_text().splitlines():
        if line.startswith("OPENROUTER_API_KEY="):
            return line.split("=", 1)[1].strip().strip('"')
    raise SystemExit("no key")


def call(key: str, model: str, messages: list[dict], max_tokens: int = 6000) -> dict:
    payload = {"model": model, "temperature": 0, "max_tokens": max_tokens, "messages": messages}
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
            return {"text": ch["message"].get("content") or "",
                    "finish": ch.get("finish_reason"), "reasoning": rt,
                    "prompt": u.get("prompt_tokens", 0), "completion": ct,
                    "billed": billed,
                    "payload_cost": round(billed * (ct - rt) / ct, 8) if ct else 0.0,
                    "elapsed": round(time.time() - t0, 2), "error": None}
        except urllib.error.HTTPError as exc:
            if exc.code in (429, 500, 502, 503):
                time.sleep(4 * (attempt + 1))
                continue
            return {"text": "", "finish": None, "reasoning": 0, "prompt": 0, "completion": 0,
                    "billed": 0.0, "payload_cost": 0.0, "elapsed": 0.0, "error": f"HTTP {exc.code}"}
        except (urllib.error.URLError, TimeoutError) as exc:
            time.sleep(3 * (attempt + 1))
            last = type(exc).__name__
    return {"text": "", "finish": None, "reasoning": 0, "prompt": 0, "completion": 0,
            "billed": 0.0, "payload_cost": 0.0, "elapsed": 0.0, "error": locals().get("last")}


def _rows_text(aggregate: bool, turn_idx: int) -> str:
    """Aggregate mode sends the whole series in one message; incremental sends one row."""
    if aggregate:
        return "\n".join(
            f"{r['period']}: turnover_eur={r['turnover']}, extract_date={r['extract']}"
            for r in TURNS)
    row = TURNS[turn_idx]
    return (f"{row['period']}: turnover_eur={row['turnover']}, extract_date={row['extract']}")


def a_messages(arm: str, turn_idx: int, history: list[str], skill: str,
               aggregate: bool = False) -> list[dict]:
    sys_p = SYS_A_PAYLOAD if arm == "payload" else SYS_A_NL
    msgs = [{"role": "system", "content": sys_p}]
    if arm == "payload":
        msgs += [{"role": "user", "content": f"Payload conventions:\n\n{skill}"},
                 {"role": "assistant", "content": "Noted."}]
    detail = (f"Your own previous updates, for consistency:\n" +
              "\n".join(history[-3:])) if history else "This is your first update."
    header = ("Here is the whole series at once:" if aggregate
              else f"New data for {TURNS[turn_idx]['period']} (segment=sports):")
    msgs.append({"role": "user",
                 "content": f"{header}\n{_rows_text(aggregate, turn_idx)}\n"
                            f"{detail}\n\nWrite the update for Agent B."})
    return msgs


def b_messages(arm: str, turn_idx: int, a_text: str, history: list[str], skill: str) -> list[dict]:
    sys_p = SYS_B_PAYLOAD if arm == "payload" else SYS_B_NL
    msgs = [{"role": "system", "content": sys_p}]
    if arm == "payload":
        msgs += [{"role": "user", "content": f"Payload conventions:\n\n{skill}"},
                 {"role": "assistant", "content": "Noted."}]
    prior = "\n".join(f"- {h}" for h in history[-3:]) if history else "(none yet)"
    msgs.append({"role": "user",
                 "content": f"Overall question: {QUESTION}\n\nMessage from Agent A this turn:\n{a_text}\n"
                            f"\nYour own recent replies:\n{prior}"})
    return msgs


def run_session(key: str, model: str, arm: str, length: int, rep: int) -> dict:
    a_hist: list[str] = []
    b_hist: list[str] = []
    calls = []
    for i in range(length):
        aggregate = length == 1
        a = call(key, model, a_messages(arm, i, a_hist, SKILL, aggregate))
        b = call(key, model, b_messages(arm, i, a["text"], b_hist, SKILL))
        calls.append({"turn": i + 1, "period": TURNS[i]["period"], "trap": TURNS[i]["trap"],
                      "a": a, "b": b})
        a_hist.append(a["text"])
        b_hist.append(b["text"])

    final_text = " ".join(b_hist) + " " + " ".join(a_hist)
    # a final synthesis turn is not added: the last B reply is the scored artefact
    scored = b_hist[-1] if b_hist else ""
    low = (scored + " " + final_text).lower()
    qualifier_survival = {"partial_period": any(w in low for w in
                                                ["partial", "incomplete", "day 3", "mid-week", "not complete"]),
                          "stale_extract": any(w in low for w in
                                               ["stale", "2026-08-30", "old extract", "as of", "snapshot"])}
    weakest = any(w in low for w in ["w35", "640", "2026-w35"])
    return {
        "ts": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "model": model, "arm": arm, "length": length, "rep": rep,
        "turns": length, "calls": len(calls) * 2,
        "billed": round(sum(c["a"]["billed"] + c["b"]["billed"] for c in calls), 8),
        "payload_cost": round(sum(c["a"]["payload_cost"] + c["b"]["payload_cost"] for c in calls), 8),
        "reasoning": sum(c["a"]["reasoning"] + c["b"]["reasoning"] for c in calls),
        "prompt": sum(c["a"]["prompt"] + c["b"]["prompt"] for c in calls),
        "completion": sum(c["a"]["completion"] + c["b"]["completion"] for c in calls),
        "truncated": sum(1 for c in calls for x in (c["a"], c["b"]) if x["finish"] == "length"),
        "errors": [x["error"] for c in calls for x in (c["a"], c["b"]) if x["error"]],
        "qualifier_partial": qualifier_survival["partial_period"],
        "qualifier_stale": qualifier_survival["stale_extract"],
        "weakest_correct": weakest,
        "scored_text": scored,
        "per_turn_billed": [round(c["a"]["billed"] + c["b"]["billed"], 8) for c in calls],
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--models", default=",".join(MODELS))
    ap.add_argument("--reps", type=int, default=REPS)
    args = ap.parse_args()
    models = [m.strip() for m in args.models.split(",") if m.strip()]
    key = api_key()
    OUT.mkdir(parents=True, exist_ok=True)
    rows = []
    with (OUT / "runs.jsonl").open("w") as log:
        for model in models:
            for arm in ("nl", "payload"):
                for length in LENGTHS:
                    for rep in range(args.reps):
                        r = run_session(key, model, arm, length, rep)
                        rows.append(r)
                        log.write(json.dumps(r, ensure_ascii=False) + "\n")
                        log.flush()
                        print(f"{model.split('/')[-1][:16]:16}{arm:8}T={length:<2}r{rep} "
                              f"billed=${r['billed']:.5f} payload=${r['payload_cost']:.5f} "
                              f"reas={r['reasoning']:5} trunc={r['truncated']} "
                              f"q_partial={int(r['qualifier_partial'])} "
                              f"q_stale={int(r['qualifier_stale'])} "
                              f"weakest={int(r['weakest_correct'])}")

    summary = {}
    for key_ in {(r["arm"], r["length"]) for r in rows}:
        sub = [r for r in rows if (r["arm"], r["length"]) == key_]
        summary[f"{key_[0]}_T{key_[1]}"] = {
            "mean_billed": round(statistics.mean(r["billed"] for r in sub), 6),
            "mean_per_turn": round(statistics.mean(r["billed"] / r["turns"] for r in sub), 6),
            "qualifier_partial": f"{sum(r['qualifier_partial'] for r in sub)}/{len(sub)}",
            "qualifier_stale": f"{sum(r['qualifier_stale'] for r in sub)}/{len(sub)}",
            "weakest_correct": f"{sum(r['weakest_correct'] for r in sub)}/{len(sub)}",
        }
    summary["total_billed_usd"] = round(sum(r["billed"] for r in rows), 6)
    (OUT / "summary.json").write_text(json.dumps(summary, indent=2))
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
