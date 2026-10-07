# Native-speaker validation kit

Two sheets, one per language. Each holds 72 facts (3 per relation type, sampled at random with seed 5) x 6 fields = 432 rows.

How to use:
1. Give `hindi_review_sheet.csv` to a native Hindi speaker and `kannada_review_sheet.csv` to a native Kannada speaker who also chats in English. Both open in Excel or Google Sheets.
2. For each row, the reviewer reads the English reference and the text, then fills three ratings and an optional correction:
   - **Natural (1-5):** would a real person type this in a chat? 5 = completely natural.
   - **Same meaning (Y/N):** does it say the same thing as the English?
   - **Spelling/script OK (Y/N):** for `*_rom` fields, casual Latin spelling is fine. For `*_nat` fields, check the Devanagari or Kannada spelling.
3. Report in the paper (Section 3.4 has a TODO box):
   - the mean naturalness;
   - the % of Y answers for meaning and for spelling;
   - how many corrections were applied.

To apply corrections:
- Edit the matching field in `data/raw/facts_b*.jsonl`.
- Re-run `python3 scripts/validate_facts.py`, `python3 scripts/build_benchmark.py`, and the experiment commands in the top-level README.
- If more than about 5% of rows need fixes, also re-run the gloss step for the edited memories.

Field meanings:
- `cm_rom`: code-mixed, Latin script.
- `cm_nat`: same words, native script for Hindi/Kannada words.
- `mono_nat`: pure Hindi/Kannada in native script.
- `mono_rom`: the same words in Latin script.
- `q_*`: questions.
