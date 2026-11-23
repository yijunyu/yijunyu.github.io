#!/usr/bin/env python3
"""Read a model's declared context window off its own files.

usage: ctx_reader.py PATH_OR_URL   (a .gguf file, a config.json, a model directory, or an https URL to a config.json)
prints: <tokens> <key path>   or   'none' when no key declares it.

Order: GGUF <arch>.context_length; then config.json keys max_position_embeddings,
text_config.max_position_embeddings, text_config.model_max_length, model_max_length,
then any other nested *.max_position_embeddings (e.g. mtp_config), reported with its path.
"""
import json, os, struct, sys, urllib.request

def gguf_ctx(p):
    f = open(p, "rb")
    if f.read(4) != b"GGUF": return None
    f.read(4); _, nkv = struct.unpack("<QQ", f.read(16))
    def rs():
        n, = struct.unpack("<Q", f.read(8)); return f.read(n).decode("utf8", "replace")
    SZ = {0:1,1:1,2:2,3:2,4:4,5:4,6:4,7:1,10:8,11:8,12:8}
    FMT = {0:"<B",1:"<b",2:"<H",3:"<h",4:"<I",5:"<i",6:"<f",7:"<?",10:"<Q",11:"<q",12:"<d"}
    def rv(t):
        if t == 8: return rs()
        if t == 9:
            et, = struct.unpack("<I", f.read(4)); n, = struct.unpack("<Q", f.read(8))
            if et == 8:
                for _ in range(n): rs()
            else: f.read(SZ[et] * n)
            return None
        return struct.unpack(FMT[t], f.read(SZ[t]))[0]
    for _ in range(nkv):
        k = rs(); t, = struct.unpack("<I", f.read(4)); v = rv(t)
        if k.endswith(".context_length"): return v, k
    return None

def walk(d, path=""):
    for k, v in d.items():
        p = f"{path}.{k}" if path else k
        if isinstance(v, dict): yield from walk(v, p)
        elif k == "max_position_embeddings" and isinstance(v, int): yield v, p

def cfg_ctx(d):
    tc = d.get("text_config") or {}
    for v, p in ((d.get("max_position_embeddings"), "max_position_embeddings"),
                 (tc.get("max_position_embeddings"), "text_config.max_position_embeddings"),
                 (tc.get("model_max_length"), "text_config.model_max_length"),
                 (d.get("model_max_length"), "model_max_length")):
        if isinstance(v, int): return v, p
    return next(walk(d), None)

a = sys.argv[1]
if a.startswith("http"):
    r = cfg_ctx(json.load(urllib.request.urlopen(urllib.request.Request(a, headers={"User-Agent": "catalog-client"}))))
elif a.endswith(".gguf"):
    r = gguf_ctx(a)
else:
    r = cfg_ctx(json.load(open(os.path.join(a, "config.json") if os.path.isdir(a) else a)))
print(f"{r[0]} {r[1]}" if r else "none")
