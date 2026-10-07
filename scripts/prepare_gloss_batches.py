"""Select memory units that a write-time canonicaliser would gloss (not already English,
judged by a cheap English-word-ratio language ID) and split them into shuffled batches."""
import json, os, random, re, sys
sys.path.insert(0, "src")
from common import load, P
from wordfreq import zipf_frequency
NOT_EN = set("main mein hai hoon hain ki ka ke ko se par aur bhi nahi kya ab aaj kal ek woh yeh mera meri mere naanu nanna ide illa alli eega yaava enu tumba".split())
def english_ratio(t):
    if re.search(r"[ऀ-ॿಀ-೿]", t): return 0.0
    toks = [w.lower() for w in re.findall(r"[A-Za-z']+", t)]
    if not toks: return 0.0
    return sum(1 for w in toks if w not in NOT_EN and zipf_frequency(w, "en") >= 3.0) / len(toks)
facts, units, pools, meta = load()
mem_ids = [i for i, u in units.items() if u["kind"] in ("needle", "distractor")]
need = [i for i in mem_ids if english_ratio(units[i]["text"]) < 0.8]
skip = [i for i in mem_ids if i not in set(need)]
kinds = {}
for i in skip: kinds[units[i]["form"]] = kinds.get(units[i]["form"], 0) + 1
print("memory units", len(mem_ids), "to gloss", len(need), "| judged English (skipped) by form:", kinds)
random.Random(7).shuffle(need)
os.makedirs(P("data/views/gloss_in"), exist_ok=True); os.makedirs(P("data/views/gloss_out"), exist_ok=True)
B = 360
for b in range(0, len(need), B):
    with open(P(f"data/views/gloss_in/batch_{b//B:02d}.jsonl"), "w", encoding="utf-8") as f:
        for j, i in enumerate(need[b:b+B]):
            f.write(json.dumps({"n": j, "id": i, "text": units[i]["text"]}, ensure_ascii=False) + "\n")
print("batches:", (len(need) + B - 1) // B)
# queries for query-side translation (reverse direction)
qs = [i for i, u in units.items() if u["kind"] == "query" and u["form"] != "q_en"]
with open(P("data/views/qtrans_in.jsonl"), "w", encoding="utf-8") as f:
    for j, i in enumerate(qs): f.write(json.dumps({"n": j, "id": i, "text": units[i]["text"]}, ensure_ascii=False) + "\n")
print("queries to translate:", len(qs))
