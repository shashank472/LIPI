"""Generate LaTeX tables that do not depend on results: the nine-form example and the retriever list."""
import json, sys
sys.path.insert(0, "src")
from common import load, MODELS
facts, units, pools, meta = load()
f = {x["fact_id"]: x for x in facts}["u02_f1"]
def tex_escape(s): return s.replace("&", "\\&").replace("%", "\\%").replace("_", "\\_").replace("#", "\\#")
import re
def wrap(s):
    s = tex_escape(s)
    s = re.sub(r"([\u0900-\u097F][\u0900-\u097F\s\u0964,.!?]*[\u0900-\u097F\u0964])", r"\\dev{\1}", s)
    s = re.sub(r"([\u0C80-\u0CFF][\u0C80-\u0CFF\s,.!?]*[\u0C80-\u0CFF])", r"\\kan{\1}", s)
    return s
rows = [("EN", "English", "en"), ("hi-CM-R", "code-mixed, Latin", "hi_cm_rom"), ("hi-CM-N", "code-mixed, native", "hi_cm_nat"),
        ("hi-MO-N", "monolingual, native", "hi_mono_nat"), ("hi-MO-R", "monolingual, Latin", "hi_mono_rom"),
        ("kn-CM-R", "code-mixed, Latin", "kn_cm_rom"), ("kn-CM-N", "code-mixed, native", "kn_cm_nat"),
        ("kn-MO-N", "monolingual, native", "kn_mono_nat"), ("kn-MO-R", "monolingual, Latin", "kn_mono_rom")]
def cell(fld):
    if fld in ("hi_cm_nat", "hi_mono_nat", "kn_cm_nat", "kn_mono_nat", "q_hi", "q_kn"):
        return "\\adjustbox{valign=t}{\\includegraphics{indic/ex_" + fld + ".pdf}}"
    return tex_escape(f[fld])
out = ["\\begin{table}[t]", "\\centering", "\\small",
       "\\caption{One \\lipi{} fact (user u02, relation \\emph{home city}, answer \\emph{Pune}) in its nine parallel forms, with its questions. \\form{CM-R} and \\form{CM-N} (likewise \\form{MO-N} and \\form{MO-R}) use the same words in different scripts.}",
       "\\label{tab:example}", "\\begin{tabular}{@{}l l >{\\raggedright\\arraybackslash}p{10.6cm}@{}}", "\\toprule", "Form & Type & Memory text \\\\", "\\midrule"]
for a, b, fld in rows:
    out.append(f"\\form{{{a}}} & {b} & {cell(fld)} \\\\")
    if a in ("EN", "hi-MO-R"): out.append("\\midrule")
out += ["\\midrule", f"Question & EN & {tex_escape(f['q_en'])} \\\\", "Question & hi-CM-R / hi-MO-N & " + cell("q_hi") + " \\\\",
        "Question & kn-CM-R / kn-MO-N & " + cell("q_kn") + " \\\\", "\\bottomrule", "\\end{tabular}", "\\end{table}"]
open("paper/tables/example.tex", "w", encoding="utf-8").write("\n".join(out) + "\n")
names = {"bm25": ("BM25", "lexical", "--", "\\citet{robertson2009bm25}"),
 "MiniLM-en": ("all-MiniLM-L6-v2", "English-only", "23M", "A-Mem default"),
 "mMiniLM": ("paraphrase-multilingual-MiniLM-L12-v2", "multilingual", "118M", "50+ languages"),
 "mE5-small": ("multilingual-e5-small", "multilingual", "118M", "\\texttt{query:}/\\texttt{passage:} prefixes"),
 "mE5-base": ("multilingual-e5-base", "multilingual", "278M", "\\texttt{query:}/\\texttt{passage:} prefixes"),
 "LaBSE": ("LaBSE", "multilingual", "471M", "translation-pair trained"),
 "BGE-M3": ("bge-m3 (dense)", "multilingual", "568M", "XLM-R large backbone"),
 "IndicSBERT": ("indic-sentence-similarity-sbert", "Indic", "238M", "L3Cube; 10 Indic languages"),
 "Vyakyarth": ("Vyakyarth", "Indic", "278M", "Krutrim; XLM-R based")}
t = ["\\begin{table}[t]", "\\centering", "\\small", "\\setlength{\\tabcolsep}{4pt}", "\\caption{Retrievers evaluated. Parameter counts are approximate.}", "\\label{tab:retrievers}",
     "\\begin{tabular}{@{}l l l l l@{}}", "\\toprule", "Short name & Model & Type & Params & Notes \\\\", "\\midrule"]
for k, (m, typ, p, note) in names.items():
    t.append(f"{k} & \\texttt{{{tex_escape(m)}}} & {typ} & {p} & {note} \\\\")
t += ["\\bottomrule", "\\end{tabular}", "\\end{table}"]
open("paper/tables/retrievers.tex", "w").write("\n".join(t) + "\n")
print("ok")
