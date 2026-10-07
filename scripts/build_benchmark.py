"""Build CM-Recall: merge drafted facts, sample distractor banks, and build per-user
memory pools that are identical across needle forms (only the target needles change)."""
import json, glob, random, re
from collections import defaultdict

SEED = 2026
LANGS = ["hi", "kn"]
NEEDLE_FORMS = {L: ["en", f"{L}_cm_rom", f"{L}_cm_nat", f"{L}_mono_nat", f"{L}_mono_rom"] for L in LANGS}
QUERY_FORMS = {L: ["q_en", f"q_{L}_cm_rom", f"q_{L}_mono_nat"] for L in LANGS}
BANK = 600            # distractor bank size per (source, script)
PER_USER = 100        # distractors per user per source/script
HARD_NEG = 30         # other users' needles per pool

# Relation keyword filters: distractors that mention the relation's topic are dropped from
# that user's pool so that no distractor contradicts or answers one of the user's questions.
KW = {
 "home_city": r"live in|living in|moved to|shift(ed)? to|relocat|रहता|रहती|rehta|rehti|ವಾಸ|irtini",
 "hometown": r"grew up|hometown|i'?m from|i am from|originally from|native place|पैदा|ऊरು|ಹುಟ್ಟೂರು|ooru",
 "employer": r"work (at|for)|company|employer|joined|कंपनी|ಕಂಪನಿ",
 "job_role": r"work as|my job|i am an? |i'?m an? |profession|नौकरी|naukri|ಕೆಲಸ|kelsa",
 "pet_name": r"\bdog|\bcat\b|puppy|kitten|\bpet|parrot|rabbit|कुत्त|बिल्ली|kutt|billi|ನಾಯಿ|ಬೆಕ್ಕು|naayi|bekku",
 "sibling_name": r"sister|brother|sibling|बहन|भाई|behen|bhai|ಅಕ್ಕ|ತಂಗಿ|ಅಣ್ಣ|ತಮ್ಮ|akka|tangi|anna\b|tamma",
 "partner_name": r"wife|husband|fianc|married|spouse|पत्नी|पति|patni|pati\b|ಹೆಂಡತಿ|ಗಂಡ|hendati|ganda",
 "allergy": r"allerg|एलर्जी|ಅಲರ್ಜಿ",
 "diet": r"vegan|vegetarian|keto|diet|fasting|gluten|शाकाहार|ಸಸ್ಯಾಹಾರ",
 "favorite_food": r"favou?rite (food|dish|meal)|love (to )?eat",
 "learning_instrument": r"guitar|piano|violin|drum|flute|sitar|tabla|ukulele|veena|harmonium|instrument|गिटार|ಗಿಟಾರ್",
 "weekend_sport": r"cricket|football|soccer|tennis|badminton|swim|basketball|volleyball|kabaddi|squash|sport|खेल|ಆಟ",
 "vehicle": r"\bcar\b|bike|scooter|motorcycle|bought a|गाड़ी|gaadi|ಗಾಡಿ|ಕಾರು",
 "trip_destination": r"\btrip|travel|vacation|holiday|visit|यात्रा|ಪ್ರವಾಸ",
 "exam_prep": r"\bexam|\btest\b|preparing|परीक्षा|ಪರೀಕ್ಷೆ",
 "injury": r"injur|hurt|pain|sprain|fractur|चोट|dard|ನೋವು|ಪೆಟ್ಟು",
 "workout_time": r"gym|workout|exercise|कसरत|जिम|ವ್ಯಾಯಾಮ|ಜಿಮ್",
 "favorite_singer": r"singer|band|favou?rite (artist|song)|गायक|ಗಾಯಕ",
 "language_learning": r"learning (spanish|french|german|japanese|korean|italian|russian|arabic|mandarin|tamil|chinese)|language|भाषा|bhasha|ಭಾಷೆ",
 "child_name": r"\bson\b|daughter|\bkid|children|बेटा|बेटी|beta\b|beti|ಮಗ|maga",
 "commute_mode": r"commute|metro|\bbus\b|train|\bcab\b|drive to work|मेट्रो|ಮೆಟ್ರೋ|ಬಸ್",
 "favorite_team": r"\bteam|fan of|support|\bipl\b|club|टीम|ತಂಡ",
 "college": r"college|universit|graduat|alma mater|कॉलेज|विश्वविद्यालय|ಕಾಲೇಜು|ವಿಶ್ವವಿದ್ಯಾಲಯ",
 "savings_goal": r"saving|save money|बचत|ಉಳಿತಾಯ",
}
KW = {k: re.compile(v, re.I) for k, v in KW.items()}

def load_facts():
    spec = {}
    for l in open("data/raw/value_spec.tsv", encoding="utf-8"):
        u, g, r, v, n = l.rstrip("\n").split("\t"); spec.setdefault(u, []).append((g, r, v))
    rel = {x["user_id"]: x for x in json.load(open("data/raw/user_relations.json"))}
    facts = []
    for p in sorted(glob.glob("data/raw/facts_b*.jsonl")):
        for l in open(p, encoding="utf-8"):
            if l.strip(): facts.append(json.loads(l))
    for f in facts:
        u = f["user_id"]; f["gender"] = rel[u]["gender"]
        k = int(f["fact_id"].split("_f")[1])
        if u in spec and f["answer"].lower() != spec[u][k-1][2].lower():
            f["aliases"] = sorted(set(f["aliases"] + [f["answer"].lower()]))
            f["answer"] = spec[u][k-1][2]
    facts.sort(key=lambda f: f["fact_id"])
    assert len(facts) == 240 and len({f["fact_id"] for f in facts}) == 240
    return facts

def main():
    rng = random.Random(SEED)
    facts = load_facts()
    by_user = defaultdict(list)
    for f in facts: by_user[f["user_id"]].append(f)
    units = {}
    for f in facts:
        for L in LANGS:
            for F in NEEDLE_FORMS[L]: units[f"N|{f['fact_id']}|{F}"] = {"text": f[F], "kind": "needle", "form": F}
            for Q in QUERY_FORMS[L]: units[f"Q|{f['fact_id']}|{Q}"] = {"text": f[Q], "kind": "query", "form": Q}
    # distractor banks
    banks = {}
    en = [json.loads(l) for l in open("data/distractors/distractors_en.jsonl", encoding="utf-8")]
    en = [r for r in en if len(r["text"].split()) >= 12]  # match needle length (median ~21 words)
    rng.shuffle(en); banks["en"] = en[:BANK]
    for L, name in [("hi", "hindi"), ("kn", "kannada")]:
        rows = [json.loads(l) for l in open(f"data/distractors/distractors_{name}.jsonl", encoding="utf-8")]
        for s in ["rom", "nat"]:
            rs = [r for r in rows if r["script"] == s]; rng.shuffle(rs); banks[f"{L}_{s}"] = rs[:BANK]
    for b, rs in banks.items():
        for i, r in enumerate(rs):
            units[f"D|{b}|{i:04d}"] = {"text": r["text"], "kind": "distractor", "form": b, "src": r["src"]}
    # pools
    pools = {}
    for L in LANGS:
        pools[L] = {}
        for u, fs in sorted(by_user.items()):
            rels = {f["relation"] for f in fs}
            aliases = [a.lower() for f in fs for a in f["aliases"] if len(a) >= 4]
            def ok(text):
                t = text.lower()
                return not any(a in t for a in aliases) and not any(KW[r].search(text) for r in rels)
            dis = []
            for b in ["en", f"{L}_rom", f"{L}_nat"]:
                cand = [f"D|{b}|{i:04d}" for i, r in enumerate(banks[b]) if ok(r["text"])]
                assert len(cand) >= PER_USER, (L, u, b, len(cand))
                dis += rng.sample(cand, PER_USER)
            others = [g for g in facts if g["user_id"] != u and g["relation"] not in rels
                      and all(ok(g[F]) for F in NEEDLE_FORMS[L])]
            hn = rng.sample(others, HARD_NEG)
            forms = (NEEDLE_FORMS[L] * (HARD_NEG // 5 + 1))[:HARD_NEG]; rng.shuffle(forms)
            pools[L][u] = {"hard_neg": [f"N|{g['fact_id']}|{F}" for g, F in zip(hn, forms)], "distractors": dis}
    json.dump(facts, open("data/built/facts.json", "w", encoding="utf-8"), ensure_ascii=False, indent=0)
    json.dump(units, open("data/built/units.json", "w", encoding="utf-8"), ensure_ascii=False)
    json.dump(pools, open("data/built/pools.json", "w"), indent=0)
    meta = {"seed": SEED, "needle_forms": NEEDLE_FORMS, "query_forms": QUERY_FORMS, "bank": BANK,
            "per_user_per_source": PER_USER, "hard_neg": HARD_NEG, "pool_size": 6 + HARD_NEG + 3 * PER_USER}
    json.dump(meta, open("data/built/meta.json", "w"), indent=1)
    kinds = defaultdict(int)
    for x in units.values(): kinds[x["kind"]] += 1
    print("units:", dict(kinds), "total", len(units), "| pool size", meta["pool_size"])
    import statistics as st
    for b in banks: print(b, "median words", st.median(len(r["text"].split()) for r in banks[b]))

if __name__ == "__main__":
    main()
