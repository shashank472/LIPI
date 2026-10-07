"""Embed every memory/query text under a given 'view' (raw text, transliterated, LLM gloss)
with each encoder; cache to results/emb/<model>/<view>.npz."""
import argparse, json, os, sys, time
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import P, load, MODELS
from translit import romanize

def view_texts(view, units):
    if view == "raw":
        return {k: v["text"] for k, v in units.items()}
    if view == "translit":
        return {k: romanize(v["text"]) for k, v in units.items()}
    path = P(f"data/views/{view}.json")          # e.g. gloss_en (LLM outputs), qtrans
    return json.load(open(path, encoding="utf-8"))

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--models", nargs="+", default=[m for m in MODELS if m != "bm25"])
    ap.add_argument("--views", nargs="+", default=["raw", "translit"])
    ap.add_argument("--threads", type=int, default=2)
    a = ap.parse_args()
    import torch
    torch.set_num_threads(a.threads)
    from sentence_transformers import SentenceTransformer
    _, units, _, _ = load()
    for m in a.models:
        d, qp, pp, _ = MODELS[m]
        model = None
        for view in a.views:
            out = P(f"results/emb/{m}/{view}.npz")
            if os.path.exists(out): print("skip", out); continue
            texts = view_texts(view, units)
            ids = sorted(texts)
            if view != "raw" and os.path.exists(P(f"results/emb/{m}/raw.npz")):
                raw = view_texts("raw", units)  # only embed texts that differ from raw
                ids = [i for i in ids if i not in raw or texts[i] != raw[i]]
            if model is None:
                model = SentenceTransformer(P("models", d), device="cpu", trust_remote_code=False)
                model.max_seq_length = 128
            t0 = time.time()
            is_q = [i.startswith("Q|") for i in ids]
            inp = [(qp if q else pp) + texts[i] for i, q in zip(ids, is_q)]
            vecs = model.encode(inp, batch_size=32, normalize_embeddings=True, show_progress_bar=False, convert_to_numpy=True)
            os.makedirs(os.path.dirname(out), exist_ok=True)
            np.savez_compressed(out, ids=np.array(ids), vecs=vecs.astype(np.float16))
            print(f"{m} {view}: {len(ids)} texts in {time.time()-t0:.0f}s", flush=True)
        del model

if __name__ == "__main__":
    main()
