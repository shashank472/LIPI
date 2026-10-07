"""Assign 6 distinct relation types to each of 40 synthetic users so that every relation
appears exactly 10 times. Users come in blocks of 4; each block splits a fresh random
permutation of the 24 relations into 4 disjoint sets of 6. Deterministic (seeded)."""
import json, random
RELATIONS = [
 "home_city", "hometown", "employer", "job_role", "pet_name", "sibling_name",
 "partner_name", "allergy", "diet", "favorite_food", "learning_instrument", "weekend_sport",
 "vehicle", "trip_destination", "exam_prep", "injury", "workout_time", "favorite_singer",
 "language_learning", "child_name", "commute_mode", "favorite_team", "college", "savings_goal",
]
rng = random.Random(13)
users = []
for block in range(10):
    perm = RELATIONS[:]
    rng.shuffle(perm)
    for k in range(4):
        users.append(sorted(perm[6 * k: 6 * k + 6], key=RELATIONS.index))
genders = ["m", "f"] * 20
rng.shuffle(genders)
out = [{"user_id": f"u{u+1:02d}", "gender": genders[u], "relations": users[u]} for u in range(40)]
json.dump(out, open("data/raw/user_relations.json", "w"), indent=1)
from collections import Counter
c = Counter(r for x in out for r in x["relations"])
assert set(c.values()) == {10} and all(len(set(x["relations"])) == 6 for x in out)
for x in out: print(x["user_id"], x["gender"], ", ".join(x["relations"]))
