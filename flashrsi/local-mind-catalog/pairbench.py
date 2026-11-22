import json, sys, time, urllib.request, statistics
url = sys.argv[1]; model = sys.argv[2]; pairs = int(sys.argv[3]) if len(sys.argv) > 3 else 5
def req(msg, n):
    body = json.dumps({"model": model, "messages": [{"role": "user", "content": msg}], "max_tokens": n,
                       "temperature": 0, "stream": False, "ignore_eos": True}).encode()
    r = urllib.request.Request(url + "/v1/chat/completions", body, {"Content-Type": "application/json"})
    t = time.perf_counter(); d = json.loads(urllib.request.urlopen(r, timeout=900).read()); dt = time.perf_counter() - t
    return dt, d
story = "Write a long story about a lighthouse keeper who finds a message in a bottle."
req(story, 8)  # warm-up, discarded
est = []
for i in range(pairs):
    order = [(1, 129), (129, 1)][i % 2]   # A/B then B/A
    res = {}
    for n in order:
        dt, d = req(story, n); res[n] = (dt, d["usage"]["completion_tokens"])
    (t1, c1), (t129, c129) = res[1], res[129]
    est.append((c129 - c1) / (t129 - t1))
    print(f"pair {i}: 1-tok {t1:.3f}s ({c1}), 129-tok {t129:.3f}s ({c129}) -> {est[-1]:.2f} tok/s", flush=True)
para = ("The quick brown fox jumps over the lazy dog while the committee reviews the quarterly budget. " * 26)
pf = []
for i in range(3):
    dt, d = req(f"Note {i*7919}: " + para + " Summarise this in one word.", 1)
    pf.append(d["usage"]["prompt_tokens"] / dt)
    print(f"prefill {i}: {d['usage']['prompt_tokens']} tokens in {dt:.3f}s -> {pf[-1]:.1f} t/s (includes request overhead)", flush=True)
_, d = req("What is 17 times 23? Answer briefly.", 300)
print("probe:", json.dumps(d["choices"][0]["message"])[:400])
print(f"DECODE median {statistics.median(est):.2f} range {min(est):.2f}-{max(est):.2f} n={len(est)}; PREFILL median {statistics.median(pf):.1f} range {min(pf):.1f}-{max(pf):.1f}")
