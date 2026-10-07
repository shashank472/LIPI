"""Score reader answers by alias match and report accuracy per form x condition."""
import argparse, glob, json, os, re, sys
import pandas as pd
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import P, load
ap = argparse.ArgumentParser(); ap.add_argument("--model", required=True); a = ap.parse_args()
facts = {f["fact_id"]: f for f in load()[0]}
key = json.load(open(P(f"data/e2e/key_{a.model}.json")))
ans = {}
for p in glob.glob(P(f"data/e2e/out_{a.model}_*.txt")):
    for l in open(p, encoding="utf-8"):
        if "\t" in l:
            i, v = l.rstrip("\n").split("\t", 1); ans[i] = v.strip()
def norm(s): return re.sub(r"[^a-z0-9ऀ-ॿಀ-೿ ]", " ", s.lower())
rows = []
for cell, iid in key["key"].items():
    fid, L, F, c = cell.split("|")
    out = ans.get(iid)
    al = [norm(x).strip() for x in facts[fid]["aliases"] + [facts[fid]["answer"]] if len(x) >= 2]
    ok = out is not None and any(re.search(r"(^| )" + re.escape(x) + r"( |$)", " " + norm(out) + " ") for x in al if x)
    rows.append({"fact_id": fid, "lang": L, "form": F, "cond": c, "answered": out is not None, "correct": bool(ok),
                 "needle_in": key["needle_in"][iid]})
d = pd.DataFrame(rows)
d.to_csv(P(f"results/e2e_{a.model}.csv"), index=False)
print("answered:", d.answered.mean().round(3))
print(d.pivot_table(index="form", columns="cond", values="correct", aggfunc="mean").round(3))
print(d.pivot_table(index="form", columns="cond", values="needle_in", aggfunc="mean").round(3))
