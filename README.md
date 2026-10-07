# LIPI: cross-script recall in LLM-agent memory

Code, data and paper for **"Lost in Transliteration: Script and Code-Mixing Break Long-Term Memory Retrieval in LLM Agents"**.

**The question.** Does an agent's long-term memory still work if a user states a fact in Hinglish, Kannada-English, or native-script Hindi/Kannada, and later asks about it in English?

**The benchmark (LIPI).**
- 240 facts about 40 synthetic users.
- Each fact is written in 9 parallel forms: English, plus {code-mixed, monolingual} x {Latin, native script} for both Hindi and Kannada.
- Each user's memory pool has 336 utterances.
- Questions come in English, code-mixed and native-script forms.

## Layout
```
data/raw/           drafted facts (facts_b*.jsonl), relation assignment, value spec
data/STYLE_GUIDE.md rules used to draft the 9 forms
data/built/         facts.json, units.json (all texts), pools.json (per-user pools), meta.json
data/distractors/   sampled IndicTalk / Synthetic-Persona-Chat utterances
data/views/         LLM outputs: gloss_en.json (write-time English glosses), qtrans.json (question translations), prompts
data/audit/         LLM-review findings and the corrections applied
data/e2e/           reader items, answers and keys
src/                translit.py, embed.py, eval_retrieval.py, analyze.py, extra_analyses.py, figures.py, e2e_*.py
scripts/            validators, builders, Indic-script rendering for the paper
results/            ranks.csv (every per-fact rank), summaries, e2e and pool-size results
paper/              TMLR LaTeX source: submission.tex (anonymous), preprint.tex (named)
validation/         native-speaker review sheets
setup/              asset download script
```

## Reproduce the numbers
```bash
pip install torch sentence-transformers transformers indic-transliteration wordfreq pandas scipy statsmodels matplotlib
bash setup/download_assets.sh                 # encoders + IndicTalk + Synthetic-Persona-Chat
mkdir -p models && cp -r assets/models/* models/
python3 scripts/validate_facts.py             # data checks (scripts, pairing, gender agreement, aliases)
python3 src/embed.py --views raw translit gloss_en qtrans
python3 src/eval_retrieval.py --views raw translit gloss qt gloss+qt
python3 src/e2e_score.py --model mE5-base     # reader answers are cached in data/e2e/
python3 src/analyze.py && python3 src/extra_analyses.py && python3 src/figures.py
```
`data/built/pools.json` fixes every memory pool, so the build step is not needed. To rebuild from scratch, run `scripts/build_benchmark.py`.

The LLM steps (glosses, question translations, reader answers) were run with Claude Haiku 4.5. Their outputs are cached, so every number is reproducible without API access. To regenerate them with another model, use the prompts in `data/views/GLOSS_PROMPT.md` and `data/e2e/READER_PROMPT.md`.

## Build the paper (pdfLaTeX, official TMLR style)
```bash
cd paper
pdflatex submission && bibtex submission && pdflatex submission && pdflatex submission   # anonymous, for review
pdflatex preprint   && bibtex preprint   && pdflatex preprint   && pdflatex preprint     # named, for arXiv
```
The few Devanagari/Kannada snippets are pre-rendered vector PDFs in `paper/indic/` (`scripts/render_indic.py`, needs XeLaTeX), so the paper itself needs only pdfLaTeX.

## Licences
- Code: MIT (see `LICENSE`).
- LIPI data: CC-BY-4.0.
- IndicTalk and Synthetic-Persona-Chat: CC-BY-4.0.
- Noto fonts in `paper/fonts`: OFL.
