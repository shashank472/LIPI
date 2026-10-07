#!/usr/bin/env bash
# When Qwen3 raw embeddings exist, stop the main job (skip Qwen3 translit for now) so the
# English gloss/qtrans views run next; afterwards embed Qwen3 translit.
cd /home/claude/cmmem
while [ ! -f results/emb/Qwen3-Emb-0.6B/raw.npz ]; do sleep 20; done
pkill -f "src/embed.py --models mE5-base IndicSBERT" || true
sleep 5
while pgrep -f "run_views_after.sh" > /dev/null || pgrep -f "src/embed.py --views gloss_en qtrans" > /dev/null; do sleep 30; done
python3 src/embed.py --models Qwen3-Emb-0.6B --views translit > logs/embed_qwen_translit.log 2>&1
