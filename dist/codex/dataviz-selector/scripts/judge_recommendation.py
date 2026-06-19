#!/usr/bin/env python3
"""Lightweight heuristic judge for dataviz-selector recommendation text.
Scores whether a recommendation includes Karthik-style selection components.
Usage: judge_recommendation.py < recommendation.md
"""
import re, sys
text = sys.stdin.read().lower()
checks = {
    "has recommended visual": r"recommended visual|visual:",
    "has why": r"why:",
    "has encoding": r"encoding:|x\s*=|y\s*=",
    "has context layers": r"context layers:|annotation|threshold|counterfactual|event|highlight|facet|ribbon|marker",
    "has avoid section": r"avoid:",
    "mentions claim fit": r"claim|story|hypothesis|comparison|because|fit",
    "guards against misuse": r"avoid|mislead|axis|zero|regression|spaghetti|legend|map|stacked|log",
}
score = 0
for name, pat in checks.items():
    ok = bool(re.search(pat, text))
    print(f"{'PASS' if ok else 'FAIL'} {name}")
    score += ok
print(f"SCORE {score}/{len(checks)}")

# Optional task-aware checks via EXPECT env var: comma-separated keywords, at least one must appear.
import os
expected = [x.strip().lower() for x in os.environ.get("EXPECT", "").split(",") if x.strip()]
if expected:
    hit = [x for x in expected if x in text]
    print(("PASS" if hit else "FAIL") + " task-aware keyword: " + (", ".join(hit) if hit else ", ".join(expected)))
    if not hit:
        sys.exit(1)

if score < 6:
    sys.exit(1)
