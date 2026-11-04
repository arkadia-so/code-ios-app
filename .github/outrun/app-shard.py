#!/usr/bin/env python3
"""app-shard.py <shard 1|2> <durations.json> <tests dir> <ui seconds>: xcodebuild's test selection for one shard.

ARK-81 bench (outrun, workflow-level shard until outrun's xcode adapter lands). FlipcashTests'
top-level test types, longest first (LPT), go to the lighter of two shards; shard 2 starts loaded
with the UI smoke step it also runs. Shard 1 runs its types (-only-testing), shard 2 everything
else (-skip-testing shard 1's), so a type missing from the durations still runs, on shard 2.
Durations: per-type test time from a previous result bundle; an unknown type counts as the median.
"""
import json
import os
import re
import statistics
import sys

shard, durations_path, tests_dir, ui = int(sys.argv[1]), sys.argv[2], sys.argv[3], float(sys.argv[4])
known = json.load(open(durations_path))
types = set()
for root, _, files in os.walk(tests_dir):
    for f in files:
        if f.endswith(".swift"):
            text = open(os.path.join(root, f), encoding="utf-8", errors="replace").read()
            if "@Test" in text:
                types.update(re.findall(r"(?m)^(?:@\w+(?:\([^)]*\))?\s+)*(?:final\s+)?(?:struct|class|enum|extension)\s+(\w+)", text))
types &= set(known) | {t for t in types if t.endswith("Tests")}
median = statistics.median(known.values()) if known else 1.0
loads, first = [0.0, ui], []
for t in sorted(types, key=lambda t: (-known.get(t, median), t)):
    i = 0 if loads[0] <= loads[1] else 1
    loads[i] += known.get(t, median)
    if i == 0:
        first.append(t)
flag = "-only-testing" if shard == 1 else "-skip-testing"
print(" ".join(f"{flag}:FlipcashTests/{t}" for t in sorted(first)))
print(f"shard {shard}: {len(first)} types on shard 1; loads {loads[0]:.0f} s / {loads[1]:.0f} s", file=sys.stderr)
