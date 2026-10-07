#!/usr/bin/env bash
cd /home/claude/cmmem
while [ ! -f results/emb/Qwen3-Emb-0.6B/raw.npz ]; do sleep 20; done
pkill -f "^python3 src/embed.py --models mE5-base IndicSBERT" ; sleep 5
python3 src/embed.py --views gloss_en qtrans > logs/embed_views.log 2>&1
python3 src/embed.py --models Qwen3-Emb-0.6B --views translit > logs/embed_qwen_translit.log 2>&1
echo done > logs/orchestrate.done
