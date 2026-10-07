"""Reassemble a staged model: copy direct files, concatenate split parts, verify sha256."""
import hashlib, os, shutil, sys
UP = "/mnt/user-data/uploads/AgentMemoryPaper/assets"
DST = "/home/claude/cmmem/models"
def sha(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 24), b""): h.update(b)
    return h.hexdigest()
def assemble(m):
    man = f"{UP}/_chunks/{m}/MANIFEST.tsv"
    ok = True
    for line in open(man):
        kind, rel, size, digest = line.rstrip("\n").split("\t")
        out = f"{DST}/{m}/{rel}"
        if rel.startswith(("imgs/", ".eval_results/")) or rel.endswith((".jpg", ".webp", ".DS_Store", "README.md", ".gitattributes", "train_script.py", "data_config.json")):
            continue
        os.makedirs(os.path.dirname(out), exist_ok=True)
        if kind == "direct":
            src = f"{UP}/models/{m}/{rel}"
            if not os.path.exists(src): print("  MISSING", rel); ok = False; continue
            shutil.copyfile(src, out)
        else:
            d = os.path.dirname(f"{UP}/_chunks/{m}/{rel}")
            base = os.path.basename(rel)
            parts = sorted(p for p in os.listdir(d) if p.startswith(base + ".part"))
            with open(out, "wb") as w:
                for p in parts:
                    with open(os.path.join(d, p), "rb") as r: shutil.copyfileobj(r, w, 1 << 24)
            if os.path.getsize(out) != int(size) or sha(out) != digest:
                print(f"  BAD {rel}: size {os.path.getsize(out)} vs {size}"); ok = False
        if kind == "direct" and os.path.getsize(out) != int(size):
            print(f"  BAD size {rel}"); ok = False
    print(m, "OK" if ok else "FAILED")
for m in sys.argv[1:]: assemble(m)
