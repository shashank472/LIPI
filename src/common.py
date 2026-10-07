import json, re, os
import numpy as np
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
def P(*a): return os.path.join(ROOT, *a)
def load():
    facts = json.load(open(P("data/built/facts.json"), encoding="utf-8"))
    units = json.load(open(P("data/built/units.json"), encoding="utf-8"))
    pools = json.load(open(P("data/built/pools.json")))
    meta = json.load(open(P("data/built/meta.json")))
    return facts, units, pools, meta
TOK = re.compile(r"[^\s\.,!?;:'\"()\[\]{}।|–—\-/]+")
def tokenize(t): return [w.lower() for w in TOK.findall(t)]
def pool_ids(pools, L, u, form):
    """Memory pool for user u in language L when the user's own facts are written in `form`."""
    own = [f"N|{u}_f{k}|{form}" for k in range(1, 7)]
    return own + pools[L][u]["hard_neg"] + pools[L][u]["distractors"]
MODELS = {  # short name -> (dir, query prefix, passage prefix, params in M)
 "bm25": (None, "", "", 0),
 "MiniLM-en": ("sentence-transformers__all-MiniLM-L6-v2", "", "", 23),
 "mMiniLM": ("sentence-transformers__paraphrase-multilingual-MiniLM-L12-v2", "", "", 118),
 "mE5-small": ("intfloat__multilingual-e5-small", "query: ", "passage: ", 118),
 "mE5-base": ("intfloat__multilingual-e5-base", "query: ", "passage: ", 278),
 "LaBSE": ("sentence-transformers__LaBSE", "", "", 471),
 "IndicSBERT": ("l3cube-pune__indic-sentence-similarity-sbert", "", "", 238),
 "Vyakyarth": ("krutrim-ai-labs__Vyakyarth", "", "", 278),
 "BGE-M3": ("BAAI__bge-m3", "", "", 568),
 "Qwen3-Emb-0.6B": ("Qwen__Qwen3-Embedding-0.6B",
                    "Instruct: Given a question a user asks about themselves, retrieve the user's earlier chat message that answers it\nQuery: ", "", 596),
}
