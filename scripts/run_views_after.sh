#!/usr/bin/env bash
# wait for the raw/translit embedding job, then embed the LLM views (glosses, query translations)
cd /home/claude/cmmem
while pgrep -f "src/embed.py --models mE5-base" > /dev/null; do sleep 30; done
python3 src/embed.py --views gloss_en qtrans > logs/embed_views.log 2>&1
