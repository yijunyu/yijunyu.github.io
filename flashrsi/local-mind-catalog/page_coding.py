#!/usr/bin/env python3
"""Insert (or refresh) a 'Coding (published)' row/column in the per-model pages, from machines.json row.coding.
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
def label(s):
    b = s["benchmark"]; st = b + " " + (s.get("setting") or "")
    if re.search(r"SWE-?bench Verified", b, re.I): return "SWE-V"
    if "Terminal" in b:
        m = re.search(r"(\d+\.\d+)", st); return f"TB{m.group(1)}" if m else "TB (version not stated)"
    if "LiveCodeBench" in b:
        m = re.search(r"v\d+", st, re.I); return f"LCB {m.group(0)}" if m else "LiveCodeBench"
    return b
def cell(r):
    cs = (r or {}).get("coding") or []
    if not cs: return '<span style="color:var(--mut,#666)">no published score</span>'
    out = []
    for s in cs:
        tip = html.escape(f"{s['benchmark']} ({s.get('setting') or ''}) · {s.get('reported_by') or ''} · {s.get('source_date') or 'date not shown'}", quote=True)
        third = "" if "vendor" in (s.get("reported_by") or "") else "<sup>3p</sup>"
        t = f"{label(s)} {s['value']}{third}"
        a = f'<a href="{html.escape(s["source_url"] or "", quote=True)}" title="{tip}">{t}</a>' if s.get("source_url") else f'<span title="{tip}">{t}</span>'
        out.append(f"<em>{a}<sup>&dagger;</sup></em>" if s.get("source_class") == "unverified-session" else a)
    return " &middot; ".join(out) + ' <span style="color:var(--mut,#666);font-size:.85em">(published, full-precision model)</span>'
for page, name in PAGES.items():
    p = f"{ROOT}/{page}"; h = open(p).read()
    h = re.sub(r"<!--coding-->.*?<!--/coding-->", "", h, flags=re.S)
    c = cell(rows.get(name))
    i = h.find("<table"); j = h.find("</table>", i)
    tbl = h[i:j]
    if "<th>quantisation</th>" in tbl:   # a column table: one column, same model-level value in every row
        tbl = tbl.replace("<th>shards</th></tr>", "<th>shards</th><!--coding--><th>Coding (published)</th><!--/coding--></tr>", 1)
        tbl = re.sub(r"(<tr><td>[^<]+</td><td>[^<]+</td><td>\d+</td>)(</tr>)", lambda m: m.group(1) + f"<!--coding--><td>{c}</td><!--/coding-->" + m.group(2), tbl)
    else:                                 # a key/value table: one more row
        tbl = tbl + f"<!--coding--><tr><th>Coding (published)</th><td>{c}</td></tr><!--/coding-->\n"
    h = h[:i] + tbl + h[j:]
    open(p, "w").write(h)
    print(page, "->", re.sub("<[^>]+>", "", c)[:90])
