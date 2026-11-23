#!/usr/bin/env python3
"""Write each machines.json row's 'coding' (published benchmark scores, max two) and 'probes' (our own checks).

coding: from the frozen candidate list's coding_agent.published_scores for the row's upstream model (rowmap.json),
then from extra-scores.json (primary sources found later); SWE-bench Verified first (vendor before third-party,
highest value), then Terminal-Bench 2.1. Each entry keeps benchmark, value, setting, source_url, source_date,
reported_by and source_class ('primary' | 'verified-from-session' | 'unverified-session'); an unverified-session
entry is shown in italics with a marker and never feeds the Pareto rule. probes: from probes.json.
usage: coding_cells.py [--write]   prints per-class counts
"""
import json, os, sys
ROOT = "/Users/yijun/yijunyu.github.io"; FD = f"{ROOT}/flashrsi/local-mind-catalog"
M = json.load(open(f"{ROOT}/local-mind/machines.json"))
CD = json.load(open(f"{FD}/candidates-2026-11-22.json"))
cand = {c["id"]: c for c in CD["candidates"]}
rowmap = json.load(open(f"{FD}/rowmap.json"))
extra = json.load(open(f"{FD}/extra-scores.json")) if os.path.exists(f"{FD}/extra-scores.json") else {}
probes = json.load(open(f"{FD}/probes.json"))
def pick(scores):
    def norm(s, cls):
        return {"benchmark": s["benchmark"], "value": s["value"], "setting": s.get("variant_or_setting") or s.get("setting") or "",
                "source_url": s.get("source_url"), "source_date": s.get("source_date"), "reported_by": s.get("reported_by"),
                "source_class": s.get("source_class", cls)}
    vend = lambda s: 0 if "vendor" in (s.get("reported_by") or "") else 1
    out = []
    swe = [s for s in scores if "SWE-bench Verified" in s["benchmark"] or "SWE-Bench Verified" in s["benchmark"]]
    if swe: out.append(norm(sorted(swe, key=lambda s: (vend(s), -float(s["value"])))[0], "primary"))
    tb = [s for s in scores if "Terminal" in s["benchmark"] and "2.1" in (s["benchmark"] + " " + (s.get("variant_or_setting") or s.get("setting") or ""))]
    if tb: out.append(norm(sorted(tb, key=lambda s: (vend(s), -float(s["value"])))[0], "primary"))
    if len(out) < 2:
        used = {o["benchmark"].split(" (")[0] for o in out}
        rest = [s for s in scores if s not in swe and s not in tb]
        for s in sorted(rest, key=lambda s: (vend(s), -float(s["value"]))):
            if len(out) >= 2: break
            key = s["benchmark"].split(" (")[0]
            if key in used: continue
            used.add(key); out.append(norm(s, "primary"))
    return out
counts = {"rows": 0, "with_score": 0, "primary": 0, "verified-from-session": 0, "unverified-session": 0, "no_score": 0, "with_probe": 0}
for b in M["boxes"]:
    for r in b["rows"]:
        counts["rows"] += 1
        cid = rowmap.get(r["name"])
        scores = list((cand.get(cid, {}).get("coding_agent") or {}).get("published_scores") or []) if cid else []
        scores += extra.get(r["name"], [])
        cells = pick(scores)
        if cells:
            r["coding"] = cells; counts["with_score"] += 1
            for c in cells: counts[c["source_class"]] += 1
        else:
            r.pop("coding", None); counts["no_score"] += 1
        p = probes.get(b["id"], {}).get(r["name"])
        if p: r["probes"] = p; counts["with_probe"] += 1
        else: r.pop("probes", None)
print(json.dumps(counts))
if "--write" in sys.argv: open(f"{ROOT}/local-mind/machines.json", "w").write(json.dumps(M, indent=2, ensure_ascii=True))
