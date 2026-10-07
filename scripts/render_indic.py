"""Render every piece of Devanagari/Kannada text used in the paper as a small vector PDF
(XeLaTeX + Noto Serif, Latin Modern for Latin text), so the paper itself compiles with
pdfLaTeX and the unmodified TMLR style. Output: paper/indic/<name>.pdf"""
import json, os, re, subprocess, sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "paper", "indic"); os.makedirs(OUT, exist_ok=True)
DEV = re.compile(r"([\u0900-\u097F][\u0900-\u097F\s\u0964,.!?'\-]*[\u0900-\u097F\u0964]|[\u0900-\u097F])")
KAN = re.compile(r"([\u0C80-\u0CFF][\u0C80-\u0CFF\s,.!?'\-]*[\u0C80-\u0CFF]|[\u0C80-\u0CFF])")
def tex_escape(s): return s.replace("&", "\\&").replace("%", "\\%").replace("_", "\\_").replace("#", "\\#")
def wrap(s):
    s = tex_escape(s)
    s = DEV.sub(lambda m: "{\\devafont " + m.group(1) + "}", s)
    s = KAN.sub(lambda m: "{\\kanfont " + m.group(1) + "}", s)
    return s
PRE = r"""\usepackage{fontspec}
\newfontfamily\devafont{NotoSerifDevanagari.ttf}[Path=%(f)s/, Script=Devanagari, Scale=0.95]
\newfontfamily\kanfont{NotoSerifKannada.ttf}[Path=%(f)s/, Script=Kannada, Scale=0.95]
"""
def render(name, text, mode):
    fonts = os.path.join(ROOT, "paper", "fonts")
    if mode == "cell":
        doc = "\\documentclass[varwidth=10.6cm,border=0pt,10pt]{standalone}\n" + PRE % {"f": fonts} + \
              "\\begin{document}\\small\\raggedright\\strut " + wrap(text) + "\\strut\\end{document}\n"
    else:
        doc = "\\documentclass[border=0pt,10pt]{standalone}\n" + PRE % {"f": fonts} + \
              "\\begin{document}\\strut " + wrap(text) + "\\end{document}\n"
    tex = os.path.join(OUT, name + ".tex")
    open(tex, "w", encoding="utf-8").write(doc)
    r = subprocess.run(["xelatex", "-interaction=nonstopmode", "-halt-on-error", name + ".tex"], cwd=OUT, capture_output=True, text=True)
    if r.returncode != 0: print("FAILED", name, r.stdout[-600:]); sys.exit(1)
    for ext in (".aux", ".log"): 
        try: os.remove(os.path.join(OUT, name + ext))
        except FileNotFoundError: pass

if __name__ == "__main__":
    facts = {f["fact_id"]: f for f in json.load(open(os.path.join(ROOT, "data/built/facts.json"), encoding="utf-8"))}
    f = facts["u02_f1"]
    for fld in ["hi_cm_nat", "hi_mono_nat", "kn_cm_nat", "kn_mono_nat"]:
        render("ex_" + fld, f[fld], "cell")
    render("ex_q_hi", f["q_hi_cm_rom"] + " / " + f["q_hi_mono_nat"], "cell")
    render("ex_q_kn", f["q_kn_cm_rom"] + " / " + f["q_kn_mono_nat"], "cell")
    render("lipi_hi", "लिपि", "inline"); render("lipi_kn", "ಲಿಪಿ", "inline")
    print("rendered", sorted(x for x in os.listdir(OUT) if x.endswith(".pdf")))
