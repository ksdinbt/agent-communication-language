#!/usr/bin/env python3
"""Aggregate results/contract-probe-*/runs.jsonl into the tables used in docs/10.

Prints: per model x condition behaviour rates, cost split, and the reasoning share.
No statistics beyond counts and means: the probe is n=3 per cell.
"""

from __future__ import annotations

import json
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def load(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def pct(n: int, d: int) -> str:
    return f"{n}/{d}" if d else "-"


def main() -> None:
    path = Path(sys.argv[1]) if len(sys.argv) > 1 else (
        ROOT / "results" / "contract-probe-2026-10-27" / "runs.jsonl")
    rows = load(path)
    valid = [r for r in rows if not r.get("error")]

    print(f"rows={len(rows)} valid={len(valid)} empty={sum(r['empty'] for r in rows)} "
          f"truncated={sum(r['finish_reason'] == 'length' for r in rows)}")

    print("\n## Behaviour by model and condition")
    print(f"{'model':22}{'cond':10}{'contract':>10}{'expand ok':>11}{'qualifier':>11}{'value':>8}")
    for (model, cond), sub in sorted(defaultdict(list, {
            k: [r for r in valid if (r["model"], r["condition"]) == k]
            for k in {(r["model"], r["condition"]) for r in valid}}).items()):
        if cond == "contract":
            cv = pct(sum(r["contract_valid"] for r in sub), len(sub))
            ex = pct(sum(bool(r["expand_correct"]) for r in sub), len(sub))
        else:
            cv, ex = "n/a", "n/a"
        print(f"{model.split('/')[-1][:20]:22}{cond:10}{cv:>10}{ex:>11}"
              f"{pct(sum(r['qualifier_in_text'] for r in sub), len(sub)):>11}"
              f"{pct(sum(r['value_correct'] for r in sub), len(sub)):>8}")

    print("\n## Cost split (USD, mean per call)")
    print(f"{'model':22}{'cond':10}{'billed':>11}{'payload':>11}{'reasoning share':>17}")
    for key in sorted({(r["model"], r["condition"]) for r in valid}):
        sub = [r for r in valid if (r["model"], r["condition"]) == key]
        b = sum(r["cost_billed"] for r in sub) / len(sub)
        p = sum(r["cost_payload"] for r in sub) / len(sub)
        share = (1 - p / b) * 100 if b else 0
        print(f"{key[0].split('/')[-1][:20]:22}{key[1]:10}{b:11.6f}{p:11.6f}{share:16.0f}%")

    tot_b = sum(r["cost_billed"] for r in rows)
    tot_p = sum(r["cost_payload"] for r in rows)
    print(f"\ntotal billed ${tot_b:.4f} | total payload ${tot_p:.4f} | "
          f"reasoning {100 * (1 - tot_p / tot_b) if tot_b else 0:.0f}% of the bill")


if __name__ == "__main__":
    main()
