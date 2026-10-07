"""Rank the target needle inside each user's memory pool for every (language, needle form,
query form, retriever, view). Writes per-fact ranks (long format) for later analysis."""
import argparse, csv, math, os, sys, json
from collections import Counter
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import P, load, pool_ids, tokenize, MODELS
from translit import romanize

def load_emb(m, view):
    z = np.load(P(f"results/emb/{m}/{view}.npz"))
    return {i: v.astype(np.float32) for i, v in zip(z["ids"], z["vecs"])}

class EmbStore:
    def __init__(self, m):
        self.m = m; self.cache = {}
    def get(self, view):
        if view not in self.cache:
            d = dict(load_emb(self.m, "raw"))
            if view != "raw":
                d.update(load_emb(self.m, view))   # view file holds only texts that changed
            self.cache[view] = d
        return self.cache[view]

def bm25_scores(q_toks, docs_toks, k1=1.5, b=0.75):
    N = len(docs_toks); avgdl = sum(len(d) for d in docs_toks) / N
    df = Counter(t for d in docs_toks for t in set(d))
    idf = {t: math.log(1 + (N - n + 0.5) / (n + 0.5)) for t, n in df.items()}
    out = np.zeros(N)
    for j, d in enumerate(docs_toks):
        tf = Counter(d); L = len(d)
        out[j] = sum(idf.get(t, 0) * tf[t] * (k1 + 1) / (tf[t] + k1 * (1 - b + b * L / avgdl)) for t in q_toks if t in tf)
    return out

def text_view(view, units, gloss, qtr):
    """Text seen by BM25 under a view: memory side and query side."""
    def mem(i):
        t = units[i]["text"]
        if view == "translit": return romanize(t)
        if view in ("gloss", "gloss+qt"): return t + " " + gloss.get(i, "")
        return t
    def qry(i):
        t = units[i]["text"]
        if view == "translit": return romanize(t)
        if view in ("qt", "gloss+qt"): return t + " " + qtr.get(i, "")
        return t
    return mem, qry

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--models", nargs="+", default=list(MODELS))
    ap.add_argument("--views", nargs="+", default=["raw", "translit"])
    ap.add_argument("--out", default="results/ranks.csv")
    a = ap.parse_args()
    facts, units, pools, meta = load()
    gloss = json.load(open(P("data/views/gloss_en.json"), encoding="utf-8"))
    qtr = json.load(open(P("data/views/qtrans.json"), encoding="utf-8"))
    users = sorted({f["user_id"] for f in facts})
    rows = []
    for m in a.models:
        es = None if m == "bm25" else EmbStore(m)
        for view in a.views:
            if m != "bm25":
                try:
                    E = es.get("translit" if view == "translit" else "raw")
                    G = es.get("gloss_en") if view in ("gloss", "gloss+qt") else None
                    T = es.get("qtrans") if view in ("qt", "gloss+qt") else None
                except FileNotFoundError: print("missing", m, view); continue
            for L in ["hi", "kn"]:
                for F in meta["needle_forms"][L]:
                    for u in users:
                        ids = pool_ids(pools, L, u, F)
                        if m == "bm25":
                            mem, qry = text_view(view, units, gloss, qtr)
                            dt = [tokenize(mem(i)) for i in ids]
                        else:
                            M = np.stack([E[i] for i in ids])
                            if G is not None:
                                Mg = np.stack([G.get(i, E[i]) for i in ids])
                        for k in range(1, 7):
                            fid = f"{u}_f{k}"; target = 0 + (k - 1)
                            for Qf in meta["query_forms"][L]:
                                qid = f"Q|{fid}|{Qf}"
                                if m == "bm25":
                                    s = bm25_scores(tokenize(qry(qid)), dt)
                                else:
                                    qs = [E[qid]] + ([T[qid]] if T is not None and qid in T else [])
                                    s = np.max([M @ q for q in qs] + ([Mg @ q for q in qs] if G is not None else []), axis=0)
                                rank = 1 + int((s > s[target]).sum())
                                rows.append((m, view, L, F, Qf, fid, rank))
            print("done", m, view, flush=True)
    new = not os.path.exists(P(a.out))
    with open(P(a.out), "a", newline="") as f:
        w = csv.writer(f)
        if new: w.writerow(["model", "view", "lang", "form", "qform", "fact_id", "rank"])
        w.writerows(rows)
    print(len(rows), "rows ->", a.out)

if __name__ == "__main__":
    main()
