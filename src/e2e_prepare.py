"""Build reader (QA) items: for a subset of facts, give an LLM reader the top-k memories
retrieved under a condition and the English question. Items are shuffled and given opaque
ids so the reader cannot tell conditions apart."""
import argparse, json, os, random, sys
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import P, load, pool_ids
from eval_retrieval import EmbStore

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", required=True)
    ap.add_argument("--n_facts", type=int, default=96)
    ap.add_argument("--k", type=int, default=5)
    ap.add_argument("--batches", type=int, default=8)
    a = ap.parse_args()
    facts, units, pools, meta = load()
    rng = random.Random(11)
    # stratified subset: 4 facts per relation (24 relations -> 96 facts)
    byrel = {}
    for f in facts: byrel.setdefault(f["relation"], []).append(f)
    subset = [f for r in sorted(byrel) for f in rng.sample(byrel[r], a.n_facts // len(byrel))]
    es = EmbStore(a.model); E = es.get("raw"); G = es.get("gloss_en")
    items, key = [], {}
    for f in subset:
        u = f["user_id"]; k = int(f["fact_id"].split("_f")[1])
        for L in ["hi", "kn"]:
            for F in meta["needle_forms"][L]:
                if F == "en" and L == "kn": continue       # English needles evaluated once
                ids = pool_ids(pools, L, u, F)
                M = np.stack([E[i] for i in ids]); Mg = np.stack([G[i] for i in ids])
                q = E[f"Q|{f['fact_id']}|q_en"]
                s_raw = M @ q; s_gl = np.maximum(s_raw, Mg @ q)
                target = k - 1
                conds = {
                    "raw": [ids[j] for j in np.argsort(-s_raw)[:a.k]],
                    "gloss": [ids[j] for j in np.argsort(-s_gl)[:a.k]],
                }
                others = [i for j, i in enumerate(ids) if j != target]
                conds["oracle"] = rng.sample(others, a.k - 1) + [ids[target]]
                seen = {}
                for c, mem in conds.items():
                    mem = list(mem)
                    if c == "oracle": rng.shuffle(mem)
                    sig = tuple(sorted(mem))
                    if sig in seen:            # identical memory set -> reuse the same reader call
                        key[f"{f['fact_id']}|{L}|{F}|{c}"] = seen[sig]; continue
                    iid = f"x{len(items):05d}"; seen[sig] = iid
                    key[f"{f['fact_id']}|{L}|{F}|{c}"] = iid
                    items.append({"id": iid, "question": f["q_en"], "memories": [units[i]["text"] for i in mem],
                                  "needle_in": f"N|{f['fact_id']}|{F}" in mem})
    rng.shuffle(items)
    os.makedirs(P("data/e2e"), exist_ok=True)
    json.dump({"model": a.model, "k": a.k, "facts": [f["fact_id"] for f in subset], "key": key,
               "needle_in": {it["id"]: it["needle_in"] for it in items}}, open(P(f"data/e2e/key_{a.model}.json"), "w"), indent=0)
    nb = a.batches; size = (len(items) + nb - 1) // nb
    for b in range(nb):
        with open(P(f"data/e2e/in_{a.model}_{b}.txt"), "w", encoding="utf-8") as f:
            for it in items[b*size:(b+1)*size]:
                mem = " | ".join(f"[{j+1}] {t}" for j, t in enumerate(it["memories"]))
                f.write(f"{it['id']}\tQ: {it['question']}\tMEMORIES: {mem}\n")
    print(len(subset), "facts ->", len(items), "reader items in", nb, "batches;", len(key), "condition cells")

if __name__ == "__main__":
    main()
