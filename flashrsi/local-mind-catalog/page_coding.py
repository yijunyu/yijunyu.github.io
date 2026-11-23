#!/usr/bin/env python3
"""Insert (or refresh) one numeric column (or row) per published benchmark in the per-model pages, from machines.json
row.coding and _coding_benchmarks.
Content sits between <!--coding--> markers so a rerun replaces it.  usage: page_coding.py"""
import html, json, re
ROOT = "/Users/yijun/yijunyu.github.io/local-mind"
M = json.load(open(f"{ROOT}/machines.json"))
rows = {}
for b in M["boxes"]:
    for r in b["rows"]: rows.setdefault(r["name"], r)
PAGES = {"deepseek-v4-1-flash.html": "DeepSeek-V4.1-Flash", "deepseek-v4-pro-qwen35-4b.html": "DeepSeek-V4-Pro-Qwen3.5-4B",
         "maxwell-v1-flash.html": "Maxwell-V1-Flash", "nemotron-3.5-lightning.html": "Nemotron 3.5 Lightning",
         "qwen35-9b-defiant.html": "Qwen3.5-9B Defiant", "sage-s2-1-flash.html": "Sage-S2.1-Flash", "sensenova-loop-9b.html": "SenseNova-Loop-9B"}
BENCH = {b["key"]: b for b in M.get("_coding_benchmarks", [])}
NUM = 'style="text-align:right;font-variant-numeric:tabular-nums;white-space:nowrap"'
def value(s):
    tip = html.escape(f"{s['benchmark']} ({s.get('setting') or ''}) · {s.get('reported_by') or ''} · {s.get('source_date') or 'date not shown'}", quote=True)
    third = "" if "vendor" in (s.get("reported_by") or "") else "<sup>3p</sup>"
    t = f"{float(s['value']):g}{third}"
    a = f'<a href="{html.escape(s["source_url"] or "", quote=True)}" title="{tip}">{t}</a>' if s.get("source_url") else f'<span title="{tip}">{t}</span>'
    return f"<em>{a}<sup>&dagger;</sup></em>" if s.get("source_class") == "unverified-session" else a
def head(s):   # header text and tooltip for one benchmark column
    b = BENCH.get(s["bench"], {"label": s["benchmark"], "name": s["benchmark"], "unit": "%"})
    return b["label"], html.escape(f"{b['name']}, {b['unit']}; published for the full-precision model, not measured on the quantised file", quote=True)
NONE = '<span style="color:var(--mut,#666)">no published score</span>'
for page, name in PAGES.items():
    p = f"{ROOT}/{page}"; h = open(p).read()
    h = re.sub(r"<!--coding-->.*?<!--/coding-->\n?", "", h, flags=re.S)
    cs = (rows.get(name) or {}).get("coding") or []
    i = h.find("<table"); j = h.find("</table>", i)
    tbl = h[i:j]
    if "<th>quantisation</th>" in tbl:   # a column table: one numeric column per benchmark, same model-level value in every row
        ths = "".join(f'<th {NUM} title="{head(s)[1]}">{head(s)[0]} (published)</th>' for s in cs) or "<th>Coding (published)</th>"
        tds = "".join(f"<td {NUM}>{value(s)}</td>" for s in cs) or f"<td>{NONE}</td>"
        tbl = tbl.replace("<th>shards</th></tr>", f"<th>shards</th><!--coding-->{ths}<!--/coding--></tr>", 1)
        tbl = re.sub(r"(<tr><td>[^<]+</td><td>[^<]+</td><td>\d+</td>)(</tr>)", lambda m: m.group(1) + f"<!--coding-->{tds}<!--/coding-->" + m.group(2), tbl)
    else:                                 # a key/value table: one row per benchmark
        trs = "".join(f'<tr><th title="{head(s)[1]}">{html.escape(BENCH.get(s["bench"], {}).get("name", s["benchmark"]))} (published, %)</th><td {NUM}>{value(s)}</td></tr>' for s in cs) \
              or f"<tr><th>Coding (published)</th><td>{NONE}</td></tr>"
        tbl = tbl + f"<!--coding-->{trs}<!--/coding-->\n"
    h = h[:i] + tbl + h[j:]
    open(p, "w").write(h)
    print(page, "->", ", ".join(f"{s['bench']}={s['value']}" for s in cs) or "none")
