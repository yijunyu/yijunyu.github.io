#!/usr/bin/env python3
"""KPI reader for the local-mind-catalog campaign.

C = covered / candidates over the newest frozen candidates-<date>.json in this
directory. A candidate's status is its newest coverage_after_round<N> field.
Also prints the secondary KPIs it can read without a GPU: GB of model weights
left on the internal disk under the paths this campaign inventories.
"""
import glob, json, os, re, subprocess, sys

here = os.path.dirname(os.path.abspath(__file__))
files = sorted(glob.glob(os.path.join(here, "candidates-*.json")))
if not files:
    sys.exit("no frozen candidates file")
doc = json.load(open(files[-1]))
cands = doc["candidates"]

def status(c):
    keys = sorted((k for k in c if re.match(r"coverage_after_round\d+$", k)),
                  key=lambda k: int(k.rsplit("round", 1)[1]))
    return c[keys[-1]] if keys else c.get("coverage_baseline", "not covered")

covered = [c["id"] for c in cands if status(c) == "covered"]
print(f"frozen list: {os.path.basename(files[-1])} ({len(cands)} candidates)")
print(f"C = {len(covered)}/{len(cands)} = {len(covered)/len(cands):.3f}")

paths = ["~/models", "~/.cache/huggingface", "~/.cache/tqllm", "~/.ollama/models"]
total = 0
for p in paths:
    p = os.path.expanduser(p)
    if not os.path.exists(p):
        continue
    out = subprocess.run(["find", p, "-type", "f", "-size", "+100M"], capture_output=True, text=True).stdout.split()
    total += sum(os.path.getsize(f) for f in out if not os.path.islink(f))
print(f"weights on internal disk under {', '.join(paths)}: {total/1e9:.1f} GB")
