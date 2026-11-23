#!/usr/bin/env python3
"""Recompute the per-tier Pareto picks for every box in machines.json.

Axes: decode (up); memory = weights (resident size where an export streams a table) + f16 KV at the tier context (down);
context tier (the largest of 1M/512K/256K/128K/32K the row fits on its box with 10% headroom); coding capability =
the model's highest vendor-reported SWE-bench Verified score from the frozen candidate list (Terminal-Bench 2.1 vendor
when no row in the tier has SWE-bench). A row without a score cannot be shown dominated on capability. Pick = front
member (decode >= 5 tok/s) with the best score, ties within 1 point decided on decode; an incumbent pick with NO score
stays beside it; an incumbent with a lower score loses its pick. Writes pick/class and a dated head to each box note
between <!--picks--> markers.  usage: pareto.py DATE [--write]
"""
import json, re, sys
ROOT = "/Users/yijun/yijunyu.github.io"
DATE = sys.argv[1]; WRITE = "--write" in sys.argv
M = json.load(open(f"{ROOT}/local-mind/machines.json"))
CD = json.load(open(f"{ROOT}/flashrsi/local-mind-catalog/candidates-2026-11-22.json"))
cand = {c["id"]: c for c in CD["candidates"]}
CAP = {"m1u": 115.4, "m2max": 55.6, "m4mini": 12.7, "gb10": 128, "amd395": 130, "a2": 512}
TIERS = [("1M", 1048576), ("512K", 524288), ("256K", 262144), ("128K", 131072), ("32K", 32768)]
TK = {"1M": "t1m", "512K": "t512k", "256K": "t256k", "128K": "t128k", "32K": "t32k"}
ROWMAP = json.load(open(f"{ROOT}/flashrsi/local-mind-catalog/rowmap.json"))
import os
EXTRA = json.load(open(f"{ROOT}/flashrsi/local-mind-catalog/extra-scores.json")) if os.path.exists(f"{ROOT}/flashrsi/local-mind-catalog/extra-scores.json") else {}
RESIDENT = {"DeepSeek-V4.1-Flash Coder": 72.0, "Qwen3.8-Flash-Next MTP": 48.3, "Qwen3.8-Flash-Next|Strata": 60.0}
def size_gb(s):
    m = re.search(r"([\d.]+)\s*(GiB|GB)", s or "")
    return None if not m else float(m.group(1)) * (1.073741824 if m.group(2) == "GiB" else 1)
def num(s):
    m = re.search(r"([\d.]+)", str(s or "")); return float(m.group(1)) if m else None
def scores(name, bench):
    c = cand.get(ROWMAP.get(name, ""))
    pool = list((c or {}).get("coding_agent", {}).get("published_scores", []) or []) + [
        dict(s, variant_or_setting=s.get("setting")) for s in EXTRA.get(name, []) if s.get("source_class", "primary") == "primary"]
    if not pool: return None
    v = [float(s["value"]) for s in pool
         if "vendor" in (s.get("reported_by") or "") and (
             ("SWE-bench Verified" in s["benchmark"]) if bench == "swe" else ("Terminal" in s["benchmark"] and "2.1" in (s["benchmark"] + " " + (s.get("variant_or_setting") or ""))))]
    return max(v) if v else None
def kv(name):
    if name.startswith("Inkling-2-Mini"): return 32768, 0.17
    c = cand.get(ROWMAP.get(name, ""))
    k = c and c["fit"].get("kv_f16_bytes_per_token")
    return (k, 0.0) if k else None
changes, heads = [], {}
for b in M["boxes"]:
    rows = []
    for i, r in enumerate(b["rows"]):
        dec, w = num(r.get("decode")), size_gb(r.get("size"))
        if dec is None or w is None or not r.get("modes") or r.get("retired"): continue
        if re.search(r"not published|does not start|token id 0", r.get("engine") or ""): continue
        key = "Qwen3.8-Flash-Next|Strata" if r["name"] == "Qwen3.8-Flash-Next" and "Strata" in r["engine"] else r["name"]
        w = RESIDENT.get(key, w)
        k = kv(r["name"]); ssd = "ssd" in r["modes"]; hyb = "hyb" in r["modes"]
        x = dict(i=i, r=r, name=r["name"], dec=dec, w=w, swe=scores(r["name"], "swe"), tb=scores(r["name"], "tb"), tier=None)
        for t, T in TIERS:
            if not r.get("ctx_tokens") or r["ctx_tokens"] < T: continue
            m = w + ((k[0] * T / 1e9 + k[1]) if k else 0)
            if ssd or (not hyb and m * 1.1 <= CAP[b["id"]]): x["tier"], x["mem"] = t, m; break
        if not x["tier"] and (hyb or not r.get("ctx_tokens")):
            x["tier"], x["mem"] = "32K", w + ((k[0] * 32768 / 1e9) if k else 0)
        if x["tier"]: rows.append(x)
    keep, lines = {}, []
    label = lambda x: x["name"] + (f" ({'Strata' if 'Strata' in x['r']['engine'] else 'llama.cpp'})" if x["name"] == "Qwen3.8-Flash-Next" else "")
    for t, _ in TIERS:
        xs = [x for x in rows if x["tier"] == t]
        if not xs: continue
        for x in xs:
            x["dom"] = [o for o in xs if o is not x and o["dec"] >= x["dec"] and o["mem"] <= x["mem"] and x["swe"] is not None
                        and o["swe"] is not None and o["swe"] >= x["swe"] and (o["dec"] > x["dec"] or o["mem"] < x["mem"] or o["swe"] > x["swe"])]
        front = [x for x in xs if not x["dom"] and x["dec"] >= 5]
        basis, pick = None, None
        ws = sorted([x for x in front if x["swe"] is not None], key=lambda x: (-x["swe"], -x["dec"]))
        if ws:
            basis = "SWE-bench Verified"; top = ws[0]["swe"]; pick = max([x for x in ws if top - x["swe"] <= 1], key=lambda x: x["dec"])
        else:
            wt = sorted([x for x in front if x["tb"] is not None], key=lambda x: (-x["tb"], -x["dec"]))
            if wt: basis, pick = "Terminal-Bench 2.1", wt[0]
            else:
                pick = next((x for x in front if x["r"].get("pick")), None); basis = "kept" if pick else None
        sc = (lambda x: x["swe"]) if basis == "SWE-bench Verified" else (lambda x: x["tb"])
        inc = [x for x in front if x["r"].get("pick") and x is not pick and (basis == "kept" or sc(x) is None)]
        picks = [p for p in [pick] + inc if p]
        for p in picks: keep[p["i"]] = t
        if not picks:
            lines.append(f"<b>{t}:</b> no pick &mdash; {', '.join(map(label, xs))} {'have' if len(xs) > 1 else 'has'} no published coding-agent score, so nothing in this tier is recommended on capability."); continue
        s = f"<b>{t}:</b> "
        if pick:
            s += f"{label(pick)} ({pick['dec']}&nbsp;tok/s, {pick['mem']:.1f}&nbsp;GB with the cache at {t}" + (f", {basis} {sc(pick)}" if basis != "kept" else "") + ")"
            s += " stays: nothing in this tier has a published score" if basis == "kept" else f" has the highest vendor-reported {basis} score on the front"
            beaten = [o for o in xs if pick in o["dom"]]
            if beaten: s += ", and dominates " + ", ".join(f"{label(o)} ({o['dec']}&nbsp;tok/s, {o['mem']:.1f}&nbsp;GB, {o['swe']})" for o in beaten) + " on all four axes"
            if basis != "kept":
                oth = [o for o in front if o is not pick and sc(o) is not None]
                if oth: s += "; also on the front, not picked: " + "; ".join(f"{label(o)} ({o['dec']}&nbsp;tok/s, {o['mem']:.1f}&nbsp;GB, {sc(o)}" + (", the same score but slower" if sc(o) >= sc(pick) else ", a lower score") + ")" for o in oth)
        if inc: s += f". {' and '.join(map(label, inc))} {'remain picks' if len(inc) > 1 else 'remains a pick'} beside it: on the front with no {basis} score, so capability cannot separate {'them' if len(inc) > 1 else 'it'} from the pick"
        dropped = [x for x in xs if x["r"].get("pick") and x not in picks]
        if dropped: s += ". Pick removed: " + ", ".join(label(x) + (f" (dominated by {', '.join(map(label, x['dom']))})" if x["dom"] else " (a lower score than the pick)") for x in dropped)
        lines.append(s + ".")
    for i, r in enumerate(b["rows"]):
        t = keep.get(i)
        if t:
            if not r.get("pick") or r.get("class") != TK[t]: changes.append(f"{b['id']}: + {r['name']} -> {t}" + (f" (was {r.get('class')})" if r.get("pick") else " (new)"))
            r["pick"], r["class"] = True, TK[t]
        elif r.get("pick"):
            changes.append(f"{b['id']}: - {r['name']} (was {r.get('class')})"); r.pop("pick", None); r.pop("class", None)
    if lines:
        head = (f"<!--picks--><strong>Our picks ({DATE}), recomputed per context tier on the Pareto front.</strong> Axes: decode; memory as weights plus the f16 cache at the tier's context "
                "(each row sits in the largest tier it fits on this machine with 10% headroom); context; and coding capability as the model's highest vendor-reported SWE-bench Verified score, "
                "or Terminal-Bench 2.1 where no row in the tier has one. Vendors use different harnesses, so a gap of a point or less is a tie, decided on decode, and a row with no published "
                "score cannot be shown dominated on capability. Script: flashrsi/local-mind-catalog/pareto.py. " + " ".join(lines) + "<!--/picks--> ")
        note = b["note"]
        if "<!--picks-->" in note: note = re.sub(r"<!--picks-->.*?<!--/picks--> ", "", note, flags=re.S)
        b["note"] = head + note
        heads[b["id"]] = head
print("\n".join(changes) or "no pick changes")
if WRITE: open(f"{ROOT}/local-mind/machines.json", "w").write(json.dumps(M, indent=2, ensure_ascii=True))
