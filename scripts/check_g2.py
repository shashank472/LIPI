"""Check translation outputs: every id present, no native script left, no placeholders,
and Latin-script names/numbers from the source carried into the translation."""
import re, sys
PH = re.compile(r"personal message|message or comment|reflection about|a message about|general (comment|message)|\[missing|missing translation|translation (here|pending)|the user (is|says)|^this is a", re.I)
def keep_tokens(src):
    toks = set(re.findall(r"\b\d+[\d:]*\b", src))
    toks |= {w for w in re.findall(r"\b[A-Z][a-zA-Z]{2,}\b", src) if w.lower() not in {"finally","last","next","sunday","monday","saturday","friday","full","long","daily","eega","aaj","naanu","main","mera","meri","ivattu","yaar","guru","ab","the"}}
    return toks
for name in sys.argv[1:]:
    rows = [l.rstrip("\n").split("\t", 1) for l in open(f"data/views/g2_in/{name}.tsv", encoding="utf-8") if l.strip()]
    try: out = [l.rstrip("\n").split("\t", 1) for l in open(f"data/views/g2_out/{name}.tsv", encoding="utf-8") if l.strip()]
    except FileNotFoundError: print(name, "NO OUTPUT"); continue
    got = {x[0]: x[1].strip() for x in out if len(x) == 2 and x[1].strip()}
    problems = []
    for k, src in rows:
        g = got.get(k)
        if g is None: problems.append((k, "missing")); continue
        if re.search(r"[ऀ-ॿಀ-೿]", g): problems.append((k, "native script left")); continue
        if PH.search(g) or len(g.split()) < 4: problems.append((k, "placeholder/too short")); continue
        lost = [t for t in keep_tokens(src) if t.lower() not in g.lower()]
        if len(lost) >= 2: problems.append((k, "lost names/numbers: " + ", ".join(lost)))
    print(f"{name}: in={len(rows)} got={len(got)} problems={len(problems)}" + (" OK" if not problems else ""))
    for k, why in problems[:12]: print("  ", k, why)
