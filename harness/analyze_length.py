#!/usr/bin/env python3
"""Aggregate results/length-probe-*/runs.jsonl.

Answers two questions:
  1. Is the per-turn cost of a session lower with the typed payload than with prose, and does
     that difference grow with length (slope) or stay flat (intercept)?
  2. Do the planted qualifiers survive to the final answer, and does survival depend on length?

Per-session billing is linear in turns within a session, so the meaningful comparison is
cost per turn, not cost per session: an 8-turn session costs roughly eight times a 1-turn one
by construction, which tells us nothing about format.
"""

from __future__ import annotations

import json
import statistics as st
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def main() -> None:
    path = Path(sys.argv[1]) if len(sys.argv) > 1 else (
        ROOT / "results" / "length-probe-2026-10-27" / "runs.jsonl")
    rows = [json.loads(line) for line in path.read_text().splitlines() if line.strip()]
    ok = [r for r in rows if not r["errors"]]

    print(f"sessions={len(rows)} clean={len(ok)} truncated_calls={sum(r['truncated'] for r in rows)}")
    print(f"total billed ${sum(r['billed'] for r in rows):.4f} | payload "
          f"${sum(r['payload_cost'] for r in rows):.4f}")

    print("\n## Cost per turn (this is the comparable number)")
    print(f"{'arm':10}{'len':>4}{'n':>4}{'billed/turn':>13}{'payload/turn':>14}{'reasoning/turn':>16}")
    for (arm, length) in sorted({(r["arm"], r["length"]) for r in ok}):
        sub = [r for r in ok if (r["arm"], r["length"]) == (arm, length)]
        print(f"{arm:10}{length:>4}{len(sub):>4}"
              f"{st.mean(r['billed'] / r['turns'] for r in sub):13.6f}"
              f"{st.mean(r['payload_cost'] / r['turns'] for r in sub):14.6f}"
              f"{st.mean(r['reasoning'] / r['turns'] for r in sub):16.1f}")

    print("\n## Per-turn cost, first turn vs later turns (does it drift?)")
    for (arm, length) in sorted({(r["arm"], r["length"]) for r in ok if r["length"] > 1}):
        sub = [r for r in ok if (r["arm"], r["length"]) == (arm, length) and r["per_turn_billed"]]
        first = st.mean(s["per_turn_billed"][0] for s in sub)
        last = st.mean(s["per_turn_billed"][-1] for s in sub)
        print(f"{arm:10}T={length}  first=${first:.6f}  last=${last:.6f}  "
              f"drift={100 * (last - first) / first if first else 0:+.0f}%")

    print("\n## Behaviour")
    print(f"{'arm':10}{'len':>4}{'qualifier partial':>18}{'qualifier stale':>17}{'weakest right':>15}")
    for (arm, length) in sorted({(r["arm"], r["length"]) for r in ok}):
        sub = [r for r in ok if (r["arm"], r["length"]) == (arm, length)]
        print(f"{arm:10}{length:>4}"
              f"{sum(r['qualifier_partial'] for r in sub):>10}/{len(sub):<7}"
              f"{sum(r['qualifier_stale'] for r in sub):>10}/{len(sub):<6}"
              f"{sum(r['weakest_correct'] for r in sub):>9}/{len(sub)}")

    print("\n## By model (billed per turn, T=8)")
    per = defaultdict(list)
    for r in ok:
        if r["length"] == 8:
            per[(r["model"].split("/")[-1], r["arm"])].append(r["billed"] / r["turns"])
    for (model, arm), vals in sorted(per.items()):
        print(f"  {model[:24]:26}{arm:9}{st.mean(vals):.6f}")


if __name__ == "__main__":
    main()
