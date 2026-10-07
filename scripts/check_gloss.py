import json, re, sys
for b in sys.argv[1:]:
    inp = [json.loads(l) for l in open(f"data/views/gloss_in/{b}.jsonl", encoding="utf-8")] if not b.startswith("qtrans") else [json.loads(l) for l in open("data/views/qtrans_in.jsonl", encoding="utf-8")]
    path = f"data/views/gloss_out/{b}.jsonl" if not b.startswith("qtrans") else "data/views/qtrans_out.jsonl"
    try: out = [json.loads(l) for l in open(path, encoding="utf-8") if l.strip()]
    except Exception as e: print(b, "UNREADABLE", e); continue
    ids_in = [x["id"] for x in inp]; got = {x["id"]: x.get("gloss", "") for x in out}
    missing = [i for i in ids_in if not got.get(i, "").strip()]
    native = [i for i in ids_in if re.search(r"[ऀ-ॿಀ-೿]", got.get(i, ""))]
    print(f"{b}: in={len(inp)} out={len(out)} missing={len(missing)} native_left={len(native)}", "OK" if not missing and not native else "")
