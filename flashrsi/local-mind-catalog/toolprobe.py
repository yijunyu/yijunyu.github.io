#!/usr/bin/env python3
"""Streaming tool-call probe against an OpenAI-compatible server.
usage: toolprobe.py URL MODEL [API_KEY]   exit 0 = a tool call with JSON-parsable arguments; 2 = no tool call; 5 = transport error"""
import json, sys, urllib.request
url, model = sys.argv[1], sys.argv[2]; key = sys.argv[3] if len(sys.argv) > 3 else None
tools = [{"type": "function", "function": {"name": "get_weather", "description": "Current weather for a city",
          "parameters": {"type": "object", "properties": {"city": {"type": "string"}}, "required": ["city"]}}}]
body = {"model": model, "stream": True, "temperature": 0, "max_tokens": 1024, "tool_choice": "auto", "tools": tools,
        "messages": [{"role": "user", "content": "What is the weather in Paris right now? Use the tool."}]}
h = {"Content-Type": "application/json"}
if key: h["Authorization"] = "Bearer " + key
try:
    r = urllib.request.urlopen(urllib.request.Request(url + "/v1/chat/completions", json.dumps(body).encode(), h), timeout=600)
except Exception as e:
    print("transport:", e); sys.exit(5)
name, args = "", ""
for line in r:
    line = line.decode().strip()
    if not line.startswith("data:") or line == "data: [DONE]": continue
    try: ch = json.loads(line[5:])
    except Exception: continue
    for c in ch.get("choices", []):
        for tc in (c.get("delta", {}).get("tool_calls") or []):
            f = tc.get("function", {}); name += f.get("name") or ""; args += f.get("arguments") or ""
if not name:
    print("no tool call"); sys.exit(2)
try: a = json.loads(args or "{}")
except Exception: print(f"tool {name} with unparsable arguments: {args[:200]}"); sys.exit(2)
print(f"tool ok: {name}({json.dumps(a)})"); sys.exit(0)
