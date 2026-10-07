"""Re-embed only the given unit ids (raw and translit views) and patch the cached npz files."""
import json, os, sys
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import P, load, MODELS
from translit import romanize
import torch; torch.set_num_threads(2)
from sentence_transformers import SentenceTransformer
ids = json.load(open(P("data/audit/changed_units.json")))
_, units, _, _ = load()
for m, (d, qp, pp, _) in MODELS.items():
    if m == "bm25" or not os.path.exists(P(f"results/emb/{m}/raw.npz")): continue
    model = SentenceTransformer(P("models", d), device="cpu"); model.max_seq_length = 128
    for view in ["raw", "translit"]:
        path = P(f"results/emb/{m}/{view}.npz"); z = np.load(path)
        all_ids = list(z["ids"]); vecs = z["vecs"].astype(np.float32)
        texts = [units[i]["text"] if view == "raw" else romanize(units[i]["text"]) for i in ids]
        inp = [(qp if i.startswith("Q|") else pp) + t for i, t in zip(ids, texts)]
        new = model.encode(inp, normalize_embeddings=True, convert_to_numpy=True)
        for i, v in zip(ids, new):
            if view == "translit" and romanize(units[i]["text"]) == units[i]["text"] and i not in all_ids:
                continue  # translit file only stores texts that differ from raw
            if i in all_ids: vecs[all_ids.index(i)] = v
            else: all_ids.append(i); vecs = np.vstack([vecs, v[None]])
        np.savez_compressed(path, ids=np.array(all_ids), vecs=vecs.astype(np.float16))
    print("updated", m, flush=True)
