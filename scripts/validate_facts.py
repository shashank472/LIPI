"""Sanity checks for drafted facts: keys, scripts, code-mixing ratios, answer presence."""
import json, re, sys, glob
from wordfreq import zipf_frequency

KEYS = ["fact_id","user_id","relation","answer","aliases","en","q_en",
        "hi_cm_rom","hi_cm_nat","hi_mono_nat","hi_mono_rom","q_hi_cm_rom","q_hi_mono_nat",
        "kn_cm_rom","kn_cm_nat","kn_mono_nat","kn_mono_rom","q_kn_cm_rom","q_kn_mono_nat"]
DEV = re.compile(r"[ऀ-ॿ]"); KAN = re.compile(r"[ಀ-೿]"); LAT = re.compile(r"[A-Za-z]")
# romanized Hindi/Kannada function words that are also (rare) English strings
NOT_EN = set("""main mein hai hoon hain ki ka ke ko se par aur bhi nahi kya kaun kaunsa kaunsi kab kahan
ab aaj kal ek do teen woh yeh mera meri mere apna apni tha thi the ho gaya gayi raha rahi rahe
naanu nanna nanage ide illa alli ge inda aagide eega yaava enu hege kooda tumba mane oota
""".split())

def counts(s):
    return len(DEV.findall(s)), len(KAN.findall(s)), len(LAT.findall(s))

def en_ratio(s):
    toks = [t.lower() for t in re.findall(r"[A-Za-z']+", s)]
    if not toks: return 0.0
    en = [t for t in toks if t not in NOT_EN and zipf_frequency(t, "en") >= 3.0]
    return len(en) / len(toks)

def norm(s): return re.sub(r"\s+", " ", s.lower())

def check(rec, problems):
    fid = rec.get("fact_id", "?")
    for k in KEYS:
        if k not in rec or (k != "aliases" and not str(rec[k]).strip()):
            problems.append(f"{fid}: missing {k}")
    if problems and problems[-1].startswith(fid): return
    for k in ["en","q_en","hi_cm_rom","hi_mono_rom","q_hi_cm_rom","kn_cm_rom","kn_mono_rom","q_kn_cm_rom"]:
        d, kn, l = counts(rec[k])
        if d or kn: problems.append(f"{fid}: {k} has native-script chars")
    for k, idx in [("hi_cm_nat", 0), ("kn_cm_nat", 1)]:
        c = counts(rec[k])
        if c[idx] == 0 or c[2] == 0: problems.append(f"{fid}: {k} should mix native + Latin")
        if k == "hi_cm_nat" and c[1]: problems.append(f"{fid}: {k} has Kannada chars")
        if k == "kn_cm_nat" and c[0]: problems.append(f"{fid}: {k} has Devanagari chars")
    for k, idx in [("hi_mono_nat", 0), ("q_hi_mono_nat", 0), ("kn_mono_nat", 1), ("q_kn_mono_nat", 1)]:
        c = counts(rec[k]); tot = sum(c) or 1
        if c[idx] / tot < 0.85: problems.append(f"{fid}: {k} native share {c[idx]/tot:.2f} < .85")
        other = c[1] if idx == 0 else c[0]
        if other: problems.append(f"{fid}: {k} contains the other Indic script")
    for lang in ["hi", "kn"]:
        rc, rm = en_ratio(rec[f"{lang}_cm_rom"]), en_ratio(rec[f"{lang}_mono_rom"])
        if rc <= rm: problems.append(f"{fid}: {lang} CM-R English ratio {rc:.2f} <= MONO-R {rm:.2f}")
    al = [norm(a) for a in rec["aliases"]]
    for k in ["en","hi_cm_rom","hi_cm_nat","hi_mono_nat","hi_mono_rom","kn_cm_rom","kn_cm_nat","kn_mono_nat","kn_mono_rom"]:
        txt = norm(rec[k])
        if not any(a in txt for a in al):
            problems.append(f"{fid}: no alias of '{rec['answer']}' found in {k}")

import sys as _s; _s.path.insert(0, "src")
from translit import romanize
M_ROM = re.compile(r"\b(raha|karta|gaya|sakta|chuka|leta|deta|jaata|rehta|khata|padhta|seekhta)\s+(hoon|hun|hu)\b", re.I)
F_ROM = re.compile(r"\b(rahi|karti|gayi|gai|sakti|chuki|leti|deti|jaati|rehti|khati|padhti|seekhti)\s+(hoon|hun|hu)\b", re.I)
M_DEV = re.compile(r"(रहा|करता|गया|सकता|चुका|लेता|देता|जाता|रहता|खाता|पढ़ता|सीखता)\s+(हूँ|हूं)")
F_DEV = re.compile(r"(रही|करती|गई|गयी|सकती|चुकी|लेती|देती|जाती|रहती|खाती|पढ़ती|सीखती)\s+(हूँ|हूं)")
GENDER = {}
try:
    GENDER = {x["user_id"]: x["gender"] for x in json.load(open("data/raw/user_relations.json"))}
except Exception: pass
def extra_checks(rec, problems):
    g = GENDER.get(rec["user_id"])
    for fld, (mp, fp) in {"hi_cm_rom": (M_ROM, F_ROM), "hi_mono_rom": (M_ROM, F_ROM), "q_hi_cm_rom": (M_ROM, F_ROM),
                          "hi_cm_nat": (M_DEV, F_DEV), "hi_mono_nat": (M_DEV, F_DEV), "q_hi_mono_nat": (M_DEV, F_DEV)}.items():
        if g == "f" and mp.search(rec[fld]): problems.append(f"{rec['fact_id']}: {fld} masculine first person for female user")
        if g == "m" and fp.search(rec[fld]): problems.append(f"{rec['fact_id']}: {fld} feminine first person for male user")
    for L in ["hi", "kn"]:
        for a, b in [(f"{L}_cm_rom", f"{L}_cm_nat"), (f"{L}_mono_rom", f"{L}_mono_nat")]:
            na, nb = len(rec[a].split()), len(romanize(rec[b]).split())
            if abs(na - nb) / max(na, nb) > 0.25: problems.append(f"{rec['fact_id']}: {a}/{b} word counts differ ({na} vs {nb})")

def main(paths):
    recs, problems = [], []
    for p in paths:
        for i, line in enumerate(open(p, encoding="utf-8")):
            if not line.strip(): continue
            try: recs.append(json.loads(line))
            except Exception as e: problems.append(f"{p}:{i+1} bad JSON: {e}")
    ids = [r.get("fact_id") for r in recs]
    dup = {x for x in ids if ids.count(x) > 1}
    if dup: problems.append(f"duplicate ids: {sorted(dup)}")
    for r in recs: check(r, problems); extra_checks(r, problems)
    stats = {}
    for lang in ["hi", "kn"]:
        stats[lang] = (sum(en_ratio(r[f"{lang}_cm_rom"]) for r in recs) / max(len(recs),1),
                       sum(en_ratio(r[f"{lang}_mono_rom"]) for r in recs) / max(len(recs),1))
    print(f"{len(recs)} facts checked; mean English-token ratio CM-R/MONO-R: hi={stats['hi'][0]:.2f}/{stats['hi'][1]:.2f} kn={stats['kn'][0]:.2f}/{stats['kn'][1]:.2f}")
    for p in problems: print("  WARN", p)
    print("OK" if not problems else f"{len(problems)} warnings")

if __name__ == "__main__":
    main(sys.argv[1:] or sorted(glob.glob("data/raw/facts_b*.jsonl")))
