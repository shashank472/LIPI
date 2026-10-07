#!/usr/bin/env bash
# Downloads about 10 GB of encoders and datasets into ./assets
set -euo pipefail
cd "$(dirname "$0")/.."
python3 -m venv .venv-dl && source .venv-dl/bin/activate
pip install -q --upgrade pip "huggingface_hub>=0.25"
python setup/download_assets.py
