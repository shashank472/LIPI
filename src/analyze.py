"""Aggregate per-fact ranks into the paper's tables, macros and summary CSVs."""
import json, os, sys
import numpy as np, pandas as pd
from scipy.stats import binomtest
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import P, MODELS
ORDER_M = ["bm25", "MiniLM-en", "mMiniLM", "mE5-small", "mE5-base", "LaBSE", "BGE-M3", "Qwen3-Emb-0.6B", "IndicSBERT", "Vyakyarth"]
MULTI = ["mMiniLM", "mE5-small", "mE5-base", "LaBSE", "BGE-M3", "Qwen3-Emb-0.6B", "IndicSBERT", "Vyakyarth"]
SUF = ["en", "cm_rom", "cm_nat", "mono_nat", "mono_rom"]
LAB = {"en": "EN", "cm_rom": "CM-R", "cm_nat": "CM-N", "mono_nat": "MO-N", "mono_rom": "MO-R"}
rng = np.random.default_rng(0)

def fcol(L, s): return "en" if s == "en" else f"{L}_{s}"

def boot_ci(x, n=2000):
    x = np.asarray(x, float); idx = rng.integers(0, len(x), (n, len(x)))
    m = x[idx].mean(1); return np.percentile(m, 2.5), np.percentile(m, 97.5)

def mcnemar(a, b):
    a = np.asarray(a, bool); b = np.asarray(b, bool)
    n01 = int((~a & b).sum()); n10 = int((a & ~b).sum())
    return 1.0 if n01 + n10 == 0 else binomtest(min(n01, n10), n01 + n10, 0.5).pvalue * 1.0

def load_ranks():
    d = pd.read_csv(P("results/ranks.csv"))
    d = d.drop_duplicates(["model", "view", "lang", "form", "qform", "fact_id"], keep="last")
    for k in (1, 5, 10): d[f"r{k}"] = (d["rank"] <= k).astype(float)
    d["rr"] = 1.0 / d["rank"]
    return d

def macro(name, val): return f"\\newcommand{{\\{name}}}{{{val}}}"

def mname(m): return {"bm25": "BM", "MiniLM-en": "MiniEn", "mMiniLM": "mMini", "mE5-small": "mEsmall", "mE5-base": "mEbase", "LaBSE": "LaBSE",
                      "BGE-M3": "BGE", "Qwen3-Emb-0.6B": "Qwen", "IndicSBERT": "IndSB", "Vyakyarth": "Vyak"}[m]
def fname(L, s): return ("Hi" if L == "hi" else "Kn") + {"en": "En", "cm_rom": "CmR", "cm_nat": "CmN", "mono_nat": "MoN", "mono_rom": "MoR"}[s]


def extra_tables(d, models, mm):
    fw = d[(d.qform == "q_en")]
    raw = fw[fw.view == "raw"]
    # full metrics
    t = ["\\begin{table}[h]", "\\centering", "\\small", "\\caption{All metrics for English questions (Raw indexing). EN: facts stored in English (mean of the two pools); non-EN: mean over the eight Hindi and Kannada forms.}",
         "\\label{tab:full}", "\\begin{tabular}{@{}l cccc cccc@{}}", "\\toprule",
         " & \\multicolumn{4}{c}{EN} & \\multicolumn{4}{c}{non-EN} \\\\", "\\cmidrule(lr){2-5}\\cmidrule(lr){6-9}",
         "Retriever & R@1 & R@5 & R@10 & MRR & R@1 & R@5 & R@10 & MRR \\\\", "\\midrule"]
    for m in models:
        a = raw[(raw.model == m) & (raw.form == "en")]; b = raw[(raw.model == m) & (raw.form != "en")]
        cells = [f"{100*a[c].mean():.1f}" for c in ["r1", "r5", "r10"]] + [f"{a.rr.mean():.3f}"] + [f"{100*b[c].mean():.1f}" for c in ["r1", "r5", "r10"]] + [f"{b.rr.mean():.3f}"]
        t.append(f"{m} & " + " & ".join(cells) + " \\\\")
    t += ["\\bottomrule", "\\end{tabular}", "\\end{table}"]
    open(P("paper/tables/full_metrics.tex"), "w").write("\n".join(t) + "\n")
    # per relation (avg multilingual encoders)
    facts = {f["fact_id"]: f["relation"] for f in json.load(open(P("data/built/facts.json"), encoding="utf-8"))}
    x = fw[fw.model.isin(mm)].copy(); x["relation"] = x.fact_id.map(facts)
    rows = []
    for r, g in x.groupby("relation"):
        en = 100 * g[(g.view == "raw") & (g.form == "en")].r5.mean()
        ne = 100 * g[(g.view == "raw") & (g.form != "en")].r5.mean()
        gl = 100 * g[(g.view == "gloss") & (g.form != "en")].r5.mean() if "gloss" in set(g.view) else float("nan")
        rows.append((r, en, ne, gl))
    rows.sort(key=lambda z: z[1] - z[2], reverse=True)
    t = ["\\begin{table}[h]", "\\centering", "\\small", "\\caption{Recall@5 (\\%) by relation type, English questions, mean of the seven multilingual and Indic encoders. Sorted by the EN$-$non-EN gap under Raw indexing.}",
         "\\label{tab:relation}", "\\begin{tabular}{@{}l ccc@{}}", "\\toprule", "Relation & EN (Raw) & non-EN (Raw) & non-EN (Gloss) \\\\", "\\midrule"]
    for r, en, ne, gl in rows:
        t.append(f"{r.replace('_', ' ')} & {en:.1f} & {ne:.1f} & {gl:.1f} \\\\")
    t += ["\\bottomrule", "\\end{tabular}", "\\end{table}"]
    open(P("paper/tables/per_relation.tex"), "w").write("\n".join(t) + "\n")
    # gloss quality
    import re as _re
    gloss = json.load(open(P("data/views/gloss_en.json"), encoding="utf-8"))
    fx = {f["fact_id"]: f for f in json.load(open(P("data/built/facts.json"), encoding="utf-8"))}
    from collections import defaultdict
    keep = defaultdict(list)
    for uid, g in gloss.items():
        if uid.startswith("N|"):
            _, fid, form = uid.split("|")
            al = [a.lower() for a in fx[fid]["aliases"] if _re.fullmatch(r"[a-z0-9 .:'&-]+", a.lower()) and len(a) >= 3] + [fx[fid]["answer"].lower()]
            keep[form].append(any(a in g.lower() for a in al))
    order = ["hi_cm_rom", "hi_cm_nat", "hi_mono_nat", "hi_mono_rom", "kn_cm_rom", "kn_cm_nat", "kn_mono_nat", "kn_mono_rom"]
    t = ["\\begin{table}[h]", "\\centering", "\\small", "\\caption{Share of fact glosses (Claude Haiku 4.5) that contain a Latin-script alias of the answer, by source form. Misses are mostly spelling variants (e.g.\\ \\emph{Kartik} for \\emph{Karthik}) or paraphrases (\\emph{lower back} for \\emph{back}); some are genuine translation errors.}",
         "\\label{tab:gloss}", "\\begin{tabular}{@{}l" + "c" * len(order) + "@{}}", "\\toprule",
         " & " + " & ".join(o.replace("_cm_rom", "-CM-R").replace("_cm_nat", "-CM-N").replace("_mono_nat", "-MO-N").replace("_mono_rom", "-MO-R") for o in order) + " \\\\", "\\midrule",
         "Answer kept & " + " & ".join(f"{100*sum(keep[o])/len(keep[o]):.1f}" for o in order) + " \\\\", "\\bottomrule", "\\end{tabular}", "\\end{table}"]
    open(P("paper/tables/gloss_quality.tex"), "w").write("\n".join(t) + "\n")
    # reverse-direction macros: avg multilingual, raw and gloss+qt, by memory form x question form
    out = []
    for L in ["hi", "kn"]:
        for q, qn in [("q_en", "QEn"), (f"q_{L}_cm_rom", "QCm"), (f"q_{L}_mono_nat", "QMo")]:
            for v, vn in [("raw", "Raw"), ("gloss+qt", "GlQt"), ("qt", "Qt")]:
                sub = d[(d.model.isin(mm)) & (d.lang == L) & (d.qform == q) & (d.view == v)]
                if len(sub) == 0: continue
                for sfx in SUF:
                    val = 100 * sub[sub.form == fcol(L, sfx)].r5.mean()
                    out.append(macro(f"Rev{fname(L, sfx)}{qn}{vn}", f"{val:.1f}"))
    return out

def e2e_table():
    path = P("results/e2e_mE5-base.csv")
    if not os.path.exists(path): return []
    d = pd.read_csv(path)
    order = ["en", "hi_cm_rom", "hi_cm_nat", "hi_mono_nat", "hi_mono_rom", "kn_cm_rom", "kn_cm_nat", "kn_mono_nat", "kn_mono_rom"]
    lab = lambda f: "EN" if f == "en" else f[:2] + "-" + LAB[f[3:]]
    t = ["\\begin{table}[t]", "\\centering", "\\small",
         "\\caption{End-to-end answer accuracy (\\%) of an LLM reader (Claude Haiku 4.5) given five memories, for 48 facts (two per relation) and English questions. Raw/Gloss: top-5 memories retrieved by mE5-base under Raw or Gloss indexing; in parentheses, how often the target memory was among them. Oracle: target memory plus four random pool memories.}",
         "\\label{tab:e2e}", "\\begin{tabular}{@{}l ccc@{}}", "\\toprule", "Stored form & Raw & Gloss & Oracle \\\\", "\\midrule"]
    out = []
    for f in order:
        g = d[d.form == f]
        if len(g) == 0: continue
        cells = []
        for c in ["raw", "gloss", "oracle"]:
            x = g[g.cond == c]
            acc = 100 * x.correct.mean(); hit = 100 * x.needle_in.mean()
            cells.append(f"{acc:.1f}" + (f" ({hit:.0f})" if c != "oracle" else ""))
        t.append(f"\\form{{{lab(f)}}} & " + " & ".join(cells) + " \\\\")
        if f in ("en", "hi_mono_rom"): t.append("\\midrule")
    ne = d[d.form != "en"]
    for c, n in [("raw", "Raw"), ("gloss", "Gloss"), ("oracle", "Oracle")]:
        out.append(macro(f"EtoE{n}NonEn", f"{100*ne[ne.cond == c].correct.mean():.1f}"))
        out.append(macro(f"EtoE{n}En", f"{100*d[(d.form == 'en') & (d.cond == c)].correct.mean():.1f}"))
    t += ["\\midrule", "non-EN mean & " + " & ".join(f"{100*ne[ne.cond == c].correct.mean():.1f}" for c in ["raw", "gloss", "oracle"]) + " \\\\",
          "\\bottomrule", "\\end{tabular}", "\\end{table}"]
    open(P("paper/tables/e2e.tex"), "w").write("\n".join(t) + "\n")
    return out

def avg_macros(d, mm):
    out = []
    fw = d[(d.qform == "q_en") & (d.model.isin(mm))]
    for v, n in [("raw", "Raw"), ("translit", "Translit"), ("gloss", "Gloss")]:
        x = fw[fw.view == v]
        if len(x) == 0: continue
        out.append(macro(f"MitAvg{n}", f"{100*x[x.form != 'en'].r5.mean():.1f}"))
        out.append(macro(f"EnAvg{n}", f"{100*x[x.form == 'en'].r5.mean():.1f}"))
        for L, Ln in [("hi", "Hi"), ("kn", "Kn")]:
            out.append(macro(f"MitAvg{n}{Ln}", f"{100*x[(x.lang == L) & (x.form != 'en')].r5.mean():.1f}"))
    # reverse direction: non-English questions over non-English memories
    rv = d[(d.qform != "q_en") & (d.model.isin(mm)) & (d.form != "en")]
    for v, n in [("raw", "Raw"), ("qt", "Qt"), ("gloss", "Gloss"), ("gloss+qt", "GlQt")]:
        x = rv[rv.view == v]
        if len(x): out.append(macro(f"RevAvg{n}", f"{100*x.r5.mean():.1f}"))
    # same-form question and memory (e.g. CM-R question, CM-R memory)
    same = []
    for L in ["hi", "kn"]:
        same.append(d[(d.model.isin(mm)) & (d.view == "raw") & (d.lang == L) & (d.qform == f"q_{L}_cm_rom") & (d.form == f"{L}_cm_rom")])
        same.append(d[(d.model.isin(mm)) & (d.view == "raw") & (d.lang == L) & (d.qform == f"q_{L}_mono_nat") & (d.form == f"{L}_mono_nat")])
    sm = pd.concat(same)
    if len(sm): out.append(macro("SameFormRaw", f"{100*sm.r5.mean():.1f}"))
    # best / worst cells
    raw = fw[fw.view == "raw"]
    out.append(macro("NumMulti", str(len(mm))))
    return out

def factorial_table(d, models):
    raw = d[(d.qform == "q_en") & (d.view == "raw")]
    t = ["\\begin{table}[t]", "\\centering", "\\small",
         "\\caption{Decomposing the drop (Recall@5 points, English questions, Raw indexing). \\emph{Mixing} = mean(CM forms) $-$ mean(MO forms): positive means code-mixed memories are easier to find. \\emph{Script} = mean(native forms) $-$ mean(Romanized forms): positive means native script is easier. \\emph{EN gap} = EN $-$ mean of the four non-English forms. 95\\% bootstrap CIs over facts are given for the average row.}",
         "\\label{tab:factorial}", "\\begin{tabular}{@{}l ccc ccc@{}}", "\\toprule",
         " & \\multicolumn{3}{c}{Hindi} & \\multicolumn{3}{c}{Kannada} \\\\", "\\cmidrule(lr){2-4}\\cmidrule(lr){5-7}",
         "Retriever & Mixing & Script & EN gap & Mixing & Script & EN gap \\\\", "\\midrule"]
    for m in [x for x in models if x != "bm25"]:
        cells = []
        for L in ["hi", "kn"]:
            g = raw[(raw.model == m) & (raw.lang == L)].pivot_table(index="fact_id", columns="form", values="r5")
            if g.shape[1] < 5: cells += ["--"] * 3; continue
            cm = (g[f"{L}_cm_rom"] + g[f"{L}_cm_nat"]) / 2; mo = (g[f"{L}_mono_rom"] + g[f"{L}_mono_nat"]) / 2
            nat = (g[f"{L}_cm_nat"] + g[f"{L}_mono_nat"]) / 2; rom = (g[f"{L}_cm_rom"] + g[f"{L}_mono_rom"]) / 2
            cells += [f"{100*(cm-mo).mean():+.1f}", f"{100*(nat-rom).mean():+.1f}", f"{100*(g['en']-(cm+mo)/2).mean():+.1f}"]
        t.append(f"{m} & " + " & ".join(cells) + " \\\\")
    eff = json.load(open(P("results/factorial_effects.json")))
    def fmt(k): v = eff[k]; return f"{v[0]:+.1f} [{v[1]:.0f}, {v[2]:.0f}]"
    t += ["\\midrule", "Avg.\\ multilingual & " + " & ".join(fmt(f"{L}_{k}") for L in ["hi", "kn"] for k in ["mix", "script", "gap"]) + " \\\\",
          "\\bottomrule", "\\end{tabular}", "\\end{table}"]
    open(P("paper/tables/factorial.tex"), "w").write("\n".join(t) + "\n")

def more_macros(d, models, mm):
    out = []
    fw = d[(d.qform == "q_en")]
    raw = fw[fw.view == "raw"]
    # significance count (non-EN cells vs same retriever EN cell, McNemar p<0.01)
    nsig, ncell, nimp = 0, 0, 0
    for m in models:
        for L in ["hi", "kn"]:
            en = raw[(raw.model == m) & (raw.lang == L) & (raw.form == "en")].sort_values("fact_id").r5.values
            for s in SUF[1:]:
                x = raw[(raw.model == m) & (raw.lang == L) & (raw.form == fcol(L, s))].sort_values("fact_id").r5.values
                ncell += 1; nsig += int(mcnemar(en, x) < 0.01)
                g = fw[(fw.view == "gloss") & (fw.model == m) & (fw.lang == L) & (fw.form == fcol(L, s))].r5.mean()
                nimp += int(g > x.mean())
    out += [macro("NumSigCells", str(nsig)), macro("NumCells", str(ncell)), macro("NumCellsImproved", str(nimp))]
    gl = fw[fw.view == "gloss"]
    def gain(sel_m=None, suffix=None):
        a = raw[raw.form != "en"]; b = gl[gl.form != "en"]
        if sel_m: a = a[a.model.isin(sel_m)]; b = b[b.model.isin(sel_m)]
        if suffix: a = a[a.form.str.endswith(suffix)]; b = b[b.form.str.endswith(suffix)]
        return 100 * (b.r5.mean() - a.r5.mean())
    out += [macro("GainMoR", f"{gain(mm, 'mono_rom'):.0f}"), macro("GainmEbase", f"{gain(['mE5-base']):.0f}"), macro("GainMiniEn", f"{gain(['MiniLM-en']):.0f}")]
    def eff(m, L, kind):
        g = raw[(raw.model == m) & (raw.lang == L)].pivot_table(index="fact_id", columns="form", values="r5")
        cm = (g[f"{L}_cm_rom"] + g[f"{L}_cm_nat"]) / 2; mo = (g[f"{L}_mono_rom"] + g[f"{L}_mono_nat"]) / 2
        nat = (g[f"{L}_cm_nat"] + g[f"{L}_mono_nat"]) / 2; rom = (g[f"{L}_cm_rom"] + g[f"{L}_mono_rom"]) / 2
        return 100 * {"mix": (cm - mo), "script": (nat - rom), "gap": g["en"] - (cm + mo) / 2}[kind].mean()
    out += [macro("MixMiniEnHi", f"{eff('MiniLM-en','hi','mix'):.0f}"), macro("MixMiniEnKn", f"{eff('MiniLM-en','kn','mix'):.0f}"),
            macro("MixmEbaseHi", f"{eff('mE5-base','hi','mix'):.0f}"), macro("MixmEbaseKn", f"{eff('mE5-base','kn','mix'):.0f}"),
            macro("ScriptBGE", f"{(eff('BGE-M3','hi','script') + eff('BGE-M3','kn','script')) / 2:.0f}")]
    gaps = [eff(m, L, "gap") for m in ["IndicSBERT", "Vyakyarth"] for L in ["hi", "kn"]]
    out += [macro("IndicGapMin", f"{min(gaps):.0f}"), macro("IndicGapMax", f"{max(gaps):.0f}")]
    out.append(macro("GlossEnmEbaseHi", f"{100*gl[(gl.model=='mE5-base') & (gl.lang=='hi') & (gl.form=='en')].r5.mean():.1f}"))
    return out

def main():
    d = load_ranks()
    models = [m for m in ORDER_M if m in set(d.model)]
    fw = d[d.qform == "q_en"]
    summ = fw.groupby(["model", "view", "lang", "form"])[["r1", "r5", "r10", "rr"]].mean().reset_index()
    summ.to_csv(P("results/summary_forward.csv"), index=False)
    macros = []
    # ---------- main table: Recall@5, raw view, English questions ----------
    raw = fw[fw.view == "raw"]
    lines = ["\\begin{table}[t]", "\\centering", "\\small", "\\setlength{\\tabcolsep}{4pt}",
             "\\caption{Recall@5 (\\%) of the target memory among 336 pooled memories, for English questions, when the fact was stored in each form (Raw indexing). Each cell averages 240 facts; 95\\% bootstrap CIs are about $\\pm$6 points. \\textbf{Bold}: best retriever per column. $^\\dagger$: not significantly different from the same retriever's \\form{EN} score (McNemar, $p\\ge 0.01$); all other non-EN cells differ significantly.}",
             "\\label{tab:main}", "\\begin{tabular}{@{}l ccccc ccccc@{}}", "\\toprule",
             " & \\multicolumn{5}{c}{Hindi pool} & \\multicolumn{5}{c}{Kannada pool} \\\\", "\\cmidrule(lr){2-6}\\cmidrule(lr){7-11}",
             "Retriever & " + " & ".join([LAB[s] for s in SUF] * 2) + " \\\\", "\\midrule"]
    best = {}
    for L in ["hi", "kn"]:
        for s in SUF:
            v = raw[(raw.lang == L) & (raw.form == fcol(L, s))].groupby("model").r5.mean()
            best[(L, s)] = v.max() if len(v) else None
    for m in models:
        cells = []
        for L in ["hi", "kn"]:
            en = raw[(raw.model == m) & (raw.lang == L) & (raw.form == "en")].sort_values("fact_id").r5.values
            for s in SUF:
                x = raw[(raw.model == m) & (raw.lang == L) & (raw.form == fcol(L, s))].sort_values("fact_id").r5.values
                if len(x) == 0: cells.append("--"); continue
                v = 100 * x.mean(); txt = f"{v:.1f}"
                if best[(L, s)] is not None and abs(x.mean() - best[(L, s)]) < 1e-9: txt = f"\\textbf{{{txt}}}"
                if s != "en" and len(en) == len(x) and mcnemar(en, x) >= 0.01: txt += "$^\\dagger$"
                cells.append(txt)
                macros.append(macro(f"R{mname(m)}{fname(L, s)}", f"{v:.1f}"))
        lines.append(f"{m} & " + " & ".join(cells) + " \\\\")
        if m in ("MiniLM-en", "BGE-M3"): lines.append("\\midrule")
    # average over multilingual encoders
    mm = [m for m in MULTI if m in models]
    cells = []
    for L in ["hi", "kn"]:
        for s in SUF:
            v = 100 * raw[(raw.model.isin(mm)) & (raw.lang == L) & (raw.form == fcol(L, s))].r5.mean()
            cells.append(f"{v:.1f}"); macros.append(macro(f"Ravg{fname(L, s)}", f"{v:.1f}"))
    lines += ["\\midrule", "Avg.\\ multilingual & " + " & ".join(cells) + " \\\\", "\\bottomrule", "\\end{tabular}", "\\end{table}"]
    open(P("paper/tables/main_r5.tex"), "w").write("\n".join(lines) + "\n")
    # ---------- factorial effects (avg over multilingual encoders) ----------
    eff = {}
    for L in ["hi", "kn"]:
        g = raw[(raw.model.isin(mm)) & (raw.lang == L)].pivot_table(index=["model", "fact_id"], columns="form", values="r5")
        cm = (g[f"{L}_cm_rom"] + g[f"{L}_cm_nat"]) / 2; mo = (g[f"{L}_mono_rom"] + g[f"{L}_mono_nat"]) / 2
        rom = (g[f"{L}_cm_rom"] + g[f"{L}_mono_rom"]) / 2; nat = (g[f"{L}_cm_nat"] + g[f"{L}_mono_nat"]) / 2
        nonen = (cm + mo) / 2
        for k, x in {"mix": cm - mo, "script": nat - rom, "gap": g["en"] - nonen}.items():
            lo, hi = boot_ci(x.values); eff[(L, k)] = (100 * x.mean(), 100 * lo, 100 * hi)
            macros.append(macro(f"Eff{('Hi' if L=='hi' else 'Kn')}{k.capitalize()}", f"{100*x.mean():.1f}"))
    json.dump({f"{L}_{k}": v for (L, k), v in eff.items()}, open(P("results/factorial_effects.json"), "w"), indent=1)
    # ---------- mitigation table: mean R@5 over the 8 non-EN forms, and the EN reference ----------
    views = [v for v in ["raw", "translit", "gloss"] if v in set(fw.view)]
    mt = ["\\begin{table}[t]", "\\centering", "\\small", "\\caption{Mitigations, English questions. Mean Recall@5 (\\%) over the eight non-English forms (four per language), and the gap to the same retriever's \\form{EN} score (averaged over the two pools). Translit: deterministic script unification. Gloss: LLM English gloss indexed next to each memory at write time.}",
          "\\label{tab:mitigation}", "\\begin{tabular}{@{}l c " + " ".join(["cc"] * len(views)) + "@{}}", "\\toprule",
          "Retriever & \\form{EN} & " + " & ".join([f"\\multicolumn{{2}}{{c}}{{{v.capitalize()}}}" for v in views]) + " \\\\",
          " & & " + " & ".join(["non-EN & gap"] * len(views)) + " \\\\", "\\midrule"]
    for m in models:
        sub = fw[fw.model == m]
        en = 100 * sub[(sub.view == "raw") & (sub.form == "en")].r5.mean()
        cells = [f"{en:.1f}"]
        for v in views:
            x = sub[(sub.view == v) & (sub.form != "en")].r5
            if len(x) == 0: cells += ["--", "--"]; continue
            env = 100 * sub[(sub.view == v) & (sub.form == "en")].r5.mean()
            cells += [f"{100*x.mean():.1f}", f"{100*x.mean()-env:+.1f}"]
            macros.append(macro(f"Mit{mname(m)}{v.capitalize()}", f"{100*x.mean():.1f}"))
            macros.append(macro(f"Gap{mname(m)}{v.capitalize()}", f"{env-100*x.mean():.1f}"))
        macros.append(macro(f"EnR{mname(m)}", f"{en:.1f}"))
        mt.append(f"{m} & " + " & ".join(cells) + " \\\\")
    mt += ["\\bottomrule", "\\end{tabular}", "\\end{table}"]
    open(P("paper/tables/mitigation.tex"), "w").write("\n".join(mt) + "\n")
    macros += extra_tables(d, models, mm)
    macros += e2e_table()
    macros += avg_macros(d, mm)
    factorial_table(d, models)
    macros += more_macros(d, models, mm)
    # gloss fidelity macro
    gk = json.load(open(P("results/gloss_fidelity.json"))) if os.path.exists(P("results/gloss_fidelity.json")) else {"overall": float("nan")}
    macros.append(macro("glossKeep", f"{100*gk['overall']:.1f}\\%"))
    open(P("paper/tables/numbers.tex"), "w").write("\n".join(sorted(set(macros))) + "\n")
    print("models:", models, "| views:", sorted(set(d.view)), "| macros:", len(set(macros)))
    print({k: tuple(round(x, 1) for x in v) for k, v in eff.items()})

if __name__ == "__main__":
    main()
