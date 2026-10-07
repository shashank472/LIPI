import sys
for b in sys.argv[1:]:
    ids = [l.split("\t", 1)[0] for l in open(f"data/e2e/in_{b}.txt", encoding="utf-8") if l.strip()]
    try: out = dict(l.rstrip("\n").split("\t", 1) for l in open(f"data/e2e/out_{b}.txt", encoding="utf-8") if "\t" in l)
    except FileNotFoundError: print(b, "NO OUTPUT"); continue
    missing = [i for i in ids if not out.get(i, "").strip()]
    long_ = [i for i in ids if len(out.get(i, "").split()) > 8]
    unk = sum(1 for i in ids if out.get(i, "").strip().lower() == "unknown")
    print(f"{b}: in={len(ids)} answered={len(ids)-len(missing)} missing={len(missing)} too_long={len(long_)} unknown={unk}" + (" OK" if not missing and not long_ else ""))
