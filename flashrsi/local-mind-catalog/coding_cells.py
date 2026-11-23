#!/usr/bin/env python3
"""Write each machines.json row's 'coding' (published benchmark scores, one per benchmark column) and 'probes' (our own checks).

coding: from the frozen candidate list's coding_agent.published_scores for the row's upstream model (rowmap.json),
then from extra-scores.json (primary sources found later); one numeric score per benchmark column (BENCHES; a
version-split benchmark gets one column per version, since versions are not comparable), vendor before third-party,
then highest value. The column list is written to machines.json _coding_benchmarks. Each entry keeps bench (the
column key), benchmark, value (a number), setting, source_url, source_date,
reported_by and source_class ('primary' | 'verified-from-session' | 'unverified-session'); an unverified-session
entry is shown in italics with a marker and never feeds the Pareto rule. probes: from probes.json.
usage: coding_cells.py [--write]   prints per-class counts
"""
import json, os, re, sys
ROOT = "/Users/yijun/yijunyu.github.io"; FD = f"{ROOT}/flashrsi/local-mind-catalog"
M = json.load(open(f"{ROOT}/local-mind/machines.json"))
CD = json.load(open(f"{FD}/candidates-2026-11-22.json"))
cand = {c["id"]: c for c in CD["candidates"]}
rowmap = json.load(open(f"{FD}/rowmap.json"))
extra = json.load(open(f"{FD}/extra-scores.json")) if os.path.exists(f"{FD}/extra-scores.json") else {}
probes = json.load(open(f"{FD}/probes.json"))
BENCHES = [  # column order on the pages; a column is shown only where some row carries a score for it
    {"key": "swe_v",   "label": "SWE-V",     "name": "SWE-bench Verified", "unit": "% resolved"},
    {"key": "swe_pro", "label": "SWE-Pro",   "name": "SWE-bench Pro", "unit": "% resolved"},
    {"key": "swe_ml",  "label": "SWE-ML",    "name": "SWE-bench Multilingual", "unit": "% resolved"},
    {"key": "tb4_0",   "label": "TB 4.0",    "name": "Terminal-Bench 4.0", "unit": "% tasks solved"},
    {"key": "tb2_1",   "label": "TB 2.1",    "name": "Terminal-Bench 2.1", "unit": "% tasks solved"},
    {"key": "tb2_0",   "label": "TB 2.0",    "name": "Terminal-Bench 2.0", "unit": "% tasks solved"},
    {"key": "tb_nv",   "label": "TB (v?)",   "name": "Terminal-Bench, version not stated", "unit": "% tasks solved"},
    {"key": "lcb_v6",  "label": "LCB v6",    "name": "LiveCodeBench v6", "unit": "% pass@1"},
    {"key": "lcb_v5",  "label": "LCB v5",    "name": "LiveCodeBench v5 (2024.10-2025.02)", "unit": "% pass@1"},
    {"key": "lcb_nv",  "label": "LCB (v?)",  "name": "LiveCodeBench, version not stated", "unit": "% pass@1"},
    {"key": "aider",   "label": "Aider",     "name": "Aider polyglot", "unit": "% correct"},
]
def bench_key(s):
    b = s["benchmark"]; st = b + " " + (s.get("variant_or_setting") or s.get("setting") or "")
    if re.search(r"SWE-?bench Pro", b, re.I): return "swe_pro"
    if re.search(r"SWE-?bench Multilingual", b, re.I): return "swe_ml"
    if re.search(r"SWE-?bench Verified", b, re.I): return "swe_v"
    if "Terminal" in b:
        m = re.search(r"Terminal-?Bench\s*(\d+)\.(\d+)", st, re.I)
        k = f"tb{m.group(1)}_{m.group(2)}" if m else "tb_nv"
        return k if any(x["key"] == k for x in BENCHES) else None
    if "LiveCodeBench" in b:
        m = re.search(r"\b(?:LCB|LiveCodeBench)[- ]?v(\d+)", st, re.I)
        return {"5": "lcb_v5", "6": "lcb_v6"}.get(m.group(1)) if m else "lcb_nv"
    if re.search(r"Aider", b, re.I): return "aider"
    return None
def pick(scores):
    # One score per benchmark column. Where a source gives several settings of the same benchmark the vendor's
    # figure wins, then the highest (the rule pareto.py uses for capability), and the chosen setting is kept.
    def norm(s, cls, key):
        return {"bench": key, "benchmark": s["benchmark"], "value": float(s["value"]),
                "setting": s.get("variant_or_setting") or s.get("setting") or "",
                "source_url": s.get("source_url"), "source_date": s.get("source_date"), "reported_by": s.get("reported_by"),
                "source_class": s.get("source_class", cls)}
    vend = lambda s: 0 if "vendor" in (s.get("reported_by") or "") else 1
    by = {}
    for s in scores:
        k = bench_key(s)
        if k: by.setdefault(k, []).append(s)
    return [norm(sorted(by[b["key"]], key=lambda s: (vend(s), -float(s["value"])))[0], "primary", b["key"]) for b in BENCHES if b["key"] in by]
counts = {"rows": 0, "per_bench": {}, "with_score": 0, "primary": 0, "verified-from-session": 0, "unverified-session": 0, "no_score": 0, "with_probe": 0}
for b in M["boxes"]:
    for r in b["rows"]:
        counts["rows"] += 1
        cid = rowmap.get(r["name"])
        scores = list((cand.get(cid, {}).get("coding_agent") or {}).get("published_scores") or []) if cid else []
        scores += extra.get(r["name"], [])
        cells = pick(scores)
        if cells:
            r["coding"] = cells; counts["with_score"] += 1
            for c in cells:
                counts[c["source_class"]] += 1; counts["per_bench"][c["bench"]] = counts["per_bench"].get(c["bench"], 0) + 1
        else:
            r.pop("coding", None); counts["no_score"] += 1
        p = probes.get(b["id"], {}).get(r["name"])
        if p: r["probes"] = p; counts["with_probe"] += 1
        else: r.pop("probes", None)
used = {k for k in counts["per_bench"]}
M["_coding_benchmarks"] = [dict(b, rows=counts["per_bench"][b["key"]]) for b in BENCHES if b["key"] in used]
M = {k: M[k] for k in ["_comment", "_provenance", "_coding_benchmarks"] + [k for k in M if k not in ("_comment", "_provenance", "_coding_benchmarks")]}
print(json.dumps(counts))
if "--write" in sys.argv: open(f"{ROOT}/local-mind/machines.json", "w").write(json.dumps(M, indent=2, ensure_ascii=True))
