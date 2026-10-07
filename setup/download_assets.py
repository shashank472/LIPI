"""Download the encoders and datasets used in the experiments into ./assets (needs Hugging Face access)."""
import sys
from pathlib import Path
from huggingface_hub import HfApi, hf_hub_download, snapshot_download
ROOT = Path(__file__).resolve().parent.parent; ASSETS = ROOT / "assets"; api = HfApi()
MODELS = ["sentence-transformers/all-MiniLM-L6-v2", "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
          "intfloat/multilingual-e5-small", "intfloat/multilingual-e5-base", "BAAI/bge-m3", "sentence-transformers/LaBSE",
          "l3cube-pune/indic-sentence-similarity-sbert", "krutrim-ai-labs/Vyakyarth"]
def files(repo):
    fs = api.list_repo_files(repo); st = any(f.endswith(".safetensors") for f in fs)
    return [f for f in fs if not f.startswith(("onnx/", "openvino/")) and not f.endswith((".h5", ".msgpack", ".ot", ".onnx", ".pt"))
            and not (f.endswith(".bin") and st)]
failures = []
for repo in MODELS:
    try: snapshot_download(repo_id=repo, local_dir=ASSETS / "models" / repo.replace("/", "__"), allow_patterns=files(repo))
    except Exception as e: print("FAILED", repo, e); failures.append(repo)
for fn in ["hindi/hindi.jsonl", "kannada/kannada.jsonl"]:
    hf_hub_download("LingoIITGN/IndicTalk", fn, repo_type="dataset", local_dir=ASSETS / "data" / "IndicTalk")
snapshot_download("google/Synthetic-Persona-Chat", repo_type="dataset", local_dir=ASSETS / "data" / "Synthetic-Persona-Chat", allow_patterns=["data/*"])
print("done" if not failures else f"failures: {failures}"); sys.exit(1 if failures else 0)
