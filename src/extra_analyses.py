"""Robustness analyses: memory-pool size, regression with fact-clustered SEs, tokenizer
fertility by form, and recall conditioned on gloss fidelity."""
import json, os, re, sys
import numpy as np, pandas as pd
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import P, load, MODELS
from eval_retrieval import EmbStore
from analyze import MULTI, load_ranks, macro
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt

facts, units, pools, meta = load()
users = sorted({f["user_id"] for f in facts})
rng = np.random.default_rng(1)
out_macros = []

def pool_variants(L, u):
    """Small (36+30), default (336) and large (all admissible bank distractors) pools."""
    base = pools[L][u]
    dist = base["distractors"]
    # large: every bank distractor admissible for this user (same filter as build_benchmark)
    import importlib.util
    spec = importlib.util.spec_from_file_location("bb", P("scripts/build_benchmark.py")); bb = importlib.util.module_from_spec(spec); spec.loader.exec_module(bb)
    fs = [f for f in facts if f["user_id"] == u]; rels = {f["relation"] for f in fs}
    aliases = [a.lower() for f in fs for a in f["aliases"] if len(a) >= 4]
    def ok(t): return not any(a in t.lower() for a in aliases) and not any(bb.KW[r].search(t) for r in rels)
    large = [i for i, x in units.items() if x["kind"] == "distractor" and x["form"] in ("en", f"{L}_rom", f"{L}_nat") and ok(x["text"])]
    small = list(rng.choice(dist, 30, replace=False))
    return {"66": small, "336": dist, "large": large}

def pool_scaling():
    rows = []
    cache = {(L, u): pool_variants(L, u) for L in ["hi", "kn"] for u in users}
    for m in MULTI:
        es = EmbStore(m)
        try: E = es.get("raw"); G = es.get("gloss_en")
        except FileNotFoundError: continue
        for L in ["hi", "kn"]:
            for u in users:
                pv = cache[(L, u)]
                for size, dist in pv.items():
                    for F in meta["needle_forms"][L]:
                        ids = [f"N|{u}_f{k}|{F}" for k in range(1, 7)] + pools[L][u]["hard_neg"] + list(dist)
                        M = np.stack([E[i] for i in ids]); Mg = np.stack([G[i] for i in ids])
                        for k in range(1, 7):
                            q = E[f"Q|{u}_f{k}|q_en"]; s = M @ q; sg = np.maximum(s, Mg @ q)
                            for view, sc in [("raw", s), ("gloss", sg)]:
                                rank = 1 + int((sc > sc[k - 1]).sum())
                                rows.append((m, L, size, len(ids), F, view, rank <= 5))
    d = pd.DataFrame(rows, columns=["model", "lang", "size", "n", "form", "view", "r5"])
    d.to_csv(P("results/pool_scaling.csv"), index=False)
    d["en"] = np.where(d.form == "en", "EN", "non-EN")
    t = d.groupby(["size", "view", "en"]).r5.mean().unstack(["view", "en"]) * 100
    nmed = d.groupby("size").n.median()
    # figure: colour = indexing, line style = EN vs non-EN (two validated categorical slots)
    order = ["66", "336", "large"]; xs = [nmed[s] for s in order]
    fig, ax = plt.subplots(figsize=(3.4, 2.3))
    for view, col in [("raw", "#2a78d6"), ("gloss", "#1baf7a")]:
        for en, ls, mk in [("EN", "-", "o"), ("non-EN", "--", "s")]:
            ys = [t.loc[s, (view, en)] for s in order]
            ax.plot(xs, ys, ls, color=col, marker=mk, markersize=4, linewidth=1.6, label=f"{'Raw' if view=='raw' else 'Gloss'}, {en} facts")
    ax.set_xscale("log"); ax.set_xticks(xs, [str(int(x)) for x in xs]); ax.minorticks_off()
    ax.set_xlabel("memories per user (log scale)", fontsize=7); ax.set_ylabel("Recall@5 (%)", fontsize=7)
    ax.tick_params(labelsize=6.5); ax.grid(color="#e4e3df", linewidth=0.5)
    for sp in ("top", "right"): ax.spines[sp].set_visible(False)
    ax.legend(fontsize=6, frameon=False, loc="upper right")
    fig.tight_layout(); fig.savefig(P("paper/figures/fig_poolsize.pdf"), bbox_inches="tight"); plt.close(fig)
    for s in order:
        for view in ["raw", "gloss"]:
            for en in ["EN", "non-EN"]:
                out_macros.append(macro(f"Pool{ {'66':'Small','336':'Default','large':'Large'}[s] }{view.capitalize()}{en.replace('-', '')}", f"{t.loc[s, (view, en)]:.1f}"))
        out_macros.append(macro(f"PoolN{ {'66':'Small','336':'Default','large':'Large'}[s] }", f"{int(nmed[s])}"))
    print(t.round(1))

def regression():
    import statsmodels.formula.api as smf
    d = load_ranks()
    x = d[(d.view == "raw") & (d.qform == "q_en") & (d.model.isin(MULTI)) & (d.form != "en")].copy()
    x["kannada"] = (x.lang == "kn").astype(int)
    x["codemixed"] = x.form.str.contains("_cm_").astype(int)
    x["native"] = x.form.str.endswith("_nat").astype(int)
    x["y"] = (x["rank"] <= 5).astype(int)
    mod = smf.logit("y ~ codemixed * native + kannada + C(model)", data=x).fit(disp=0, cov_type="cluster", cov_kwds={"groups": pd.factorize(x.fact_id)[0]})
    rows = []
    for term, name in [("codemixed", "Code-mixed (vs.\\ monolingual)"), ("native", "Native script (vs.\\ Latin)"),
                       ("codemixed:native", "Code-mixed $\\times$ native"), ("kannada", "Kannada (vs.\\ Hindi)")]:
        b, se, p = mod.params[term], mod.bse[term], mod.pvalues[term]
        lo, hi = mod.conf_int().loc[term]
        rows.append(f"{name} & {b:+.2f} & {se:.2f} & {np.exp(b):.2f} [{np.exp(lo):.2f}, {np.exp(hi):.2f}] & {'$<$0.001' if p < 1e-3 else f'{p:.3f}'} \\\\")
        out_macros.append(macro("OR" + {"codemixed": "Mix", "native": "Nat", "codemixed:native": "Int", "kannada": "Kan"}[term], f"{np.exp(b):.2f}"))
    t = ["\\begin{table}[t]", "\\centering", "\\small",
         f"\\caption{{Logistic regression of Recall@5 success on the properties of the stored form ({len(x):,} retrieval outcomes: 240 facts $\\times$ 8 non-English forms $\\times$ {x.model.nunique()} multilingual and Indic encoders; Raw indexing, English questions). Retriever fixed effects are included; standard errors are clustered by fact. OR: odds ratio with 95\\% CI.}}",
         "\\label{tab:regression}", "\\begin{tabular}{@{}l c c c c@{}}", "\\toprule", "Term & $\\beta$ & SE & OR [95\\% CI] & $p$ \\\\", "\\midrule"] + rows + ["\\bottomrule", "\\end{tabular}", "\\end{table}"]
    open(P("paper/tables/regression.tex"), "w").write("\n".join(t) + "\n")
    print(mod.summary().tables[1])

def fertility():
    from transformers import AutoTokenizer
    tok = {"XLM-R (mE5, BGE-M3)": AutoTokenizer.from_pretrained(P("models/intfloat__multilingual-e5-base")),
           "BERT-en (MiniLM-en)": AutoTokenizer.from_pretrained(P("models/sentence-transformers__all-MiniLM-L6-v2"))}
    forms = [("en", "EN")] + [(f"{L}_{s}", f"{L}-{lab}") for L in ["hi", "kn"] for s, lab in [("cm_rom", "CM-R"), ("cm_nat", "CM-N"), ("mono_nat", "MO-N"), ("mono_rom", "MO-R")]]
    rows = []
    for name, tk in tok.items():
        vals = []
        for f, lab in forms:
            n_tok = np.mean([len(tk.tokenize(x[f])) / max(1, len(x[f].split())) for x in facts])
            unk = np.mean([sum(t == tk.unk_token for t in tk.tokenize(x[f])) / max(1, len(tk.tokenize(x[f]))) for x in facts])
            vals.append((n_tok, unk))
        rows.append((name, vals))
        for (f, lab), (n_tok, unk) in zip(forms, vals):
            out_macros.append(macro("Fert" + ("X" if "XLM" in name else "B") + re.sub(r"[^A-Za-z]", "", lab.title()), f"{n_tok:.1f}"))
    t = ["\\begin{table}[t]", "\\centering", "\\small", "\\setlength{\\tabcolsep}{4pt}",
         "\\caption{Tokeniser fertility (subword tokens per whitespace word) of each stored form, averaged over the 240 facts; in parentheses, share of tokens mapped to \\texttt{[UNK]}.}",
         "\\label{tab:fertility}", "\\begin{tabular}{@{}l c cccc cccc@{}}", "\\toprule",
         " & & \\multicolumn{4}{c}{Hindi} & \\multicolumn{4}{c}{Kannada} \\\\", "\\cmidrule(lr){3-6}\\cmidrule(lr){7-10}",
         "Tokeniser & EN & " + " & ".join(lab.split("-", 1)[1] for _, lab in forms[1:]) + " \\\\", "\\midrule"]
    for name, vals in rows:
        t.append(name + " & " + " & ".join(f"{a:.1f}" + (f" ({100*b:.0f}\\%)" if b > 0.005 else "") for a, b in vals) + " \\\\")
    t += ["\\bottomrule", "\\end{tabular}", "\\end{table}"]
    open(P("paper/tables/fertility.tex"), "w").write("\n".join(t) + "\n")
    for name, vals in rows: print(name, [round(a, 2) for a, _ in vals], [round(b, 3) for _, b in vals])

def gloss_conditioned():
    d = load_ranks()
    gloss = json.load(open(P("data/views/gloss_en.json"), encoding="utf-8"))
    fx = {f["fact_id"]: f for f in facts}
    def kept(fid, form):
        g = gloss.get(f"N|{fid}|{form}", "")
        al = [a.lower() for a in fx[fid]["aliases"] if re.fullmatch(r"[a-z0-9 .:'&-]+", a.lower()) and len(a) >= 3] + [fx[fid]["answer"].lower()]
        return any(a in g.lower() for a in al)
    x = d[(d.view == "gloss") & (d.qform == "q_en") & (d.model.isin(MULTI)) & (d.form != "en")].copy()
    x["kept"] = [kept(f, fm) for f, fm in zip(x.fact_id, x.form)]
    r = x.groupby("kept")["rank"].apply(lambda s: 100 * (s <= 5).mean())
    out_macros.append(macro("GlossKeptRfive", f"{r.get(True, float('nan')):.1f}"))
    out_macros.append(macro("GlossLostRfive", f"{r.get(False, float('nan')):.1f}"))
    print("gloss R@5 by answer kept:", r.round(1).to_dict())

if __name__ == "__main__":
    for fn in sys.argv[1:] or ["pool_scaling", "regression", "fertility", "gloss_conditioned"]:
        globals()[fn]()
    old = open(P("paper/tables/numbers_extra.tex")).read().splitlines() if os.path.exists(P("paper/tables/numbers_extra.tex")) else []
    keep = {l.split("}")[0]: l for l in old}
    for l in out_macros: keep[l.split("}")[0]] = l
    open(P("paper/tables/numbers_extra.tex"), "w").write("\n".join(sorted(keep.values())) + "\n")
