"""Apply the LLM-audit corrections to the raw fact files and to the built units/facts
(pools are left unchanged: corrections only touch wording, not answers or aliases)."""
import json, glob, re
fixes = {}
for p in ["data/audit/out_hi_0.jsonl", "data/audit/out_kn_1.jsonl"]:
    for l in open(p, encoding="utf-8"):
        if l.strip():
            r = json.loads(l); fixes[(r["fact_id"], r["field"])] = r["fixed"]
changed = []
for p in sorted(glob.glob("data/raw/facts_b*.jsonl")):
    rows = [json.loads(l) for l in open(p, encoding="utf-8") if l.strip()]
    for r in rows:
        for (fid, fld), txt in fixes.items():
            if r["fact_id"] == fid and r[fld] != txt:
                r[fld] = txt; changed.append((fid, fld))
    open(p, "w", encoding="utf-8").write("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows))
facts = json.load(open("data/built/facts.json", encoding="utf-8"))
units = json.load(open("data/built/units.json", encoding="utf-8"))
for f in facts:
    for (fid, fld), txt in fixes.items():
        if f["fact_id"] == fid: f[fld] = txt
ids = []
for fid, fld in changed:
    uid = (f"Q|{fid}|{fld}" if fld.startswith("q_") else f"N|{fid}|{fld}")
    if uid in units: units[uid]["text"] = fixes[(fid, fld)]; ids.append(uid)
json.dump(facts, open("data/built/facts.json", "w", encoding="utf-8"), ensure_ascii=False, indent=0)
json.dump(units, open("data/built/units.json", "w", encoding="utf-8"), ensure_ascii=False)
json.dump(ids, open("data/audit/changed_units.json", "w"))
print("changed units:", ids)
