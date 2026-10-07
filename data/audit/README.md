# LLM review of the Hindi and Kannada strings (Section 3.4)

| File | Contents |
|---|---|
| `in_{hi,kn}_{0,1}.jsonl` | Review batches given to the reviewer model (Claude Sonnet, prompted as a Hindi or Kannada linguist). Each line is one fact with all of its forms. |
| `out_hi_0.jsonl`, `out_kn_1.jsonl` | Every string the reviewer flagged, with the problem it found and a corrected string. |
| `changed_units.json` | The 10 benchmark units changed by `scripts/apply_audit_fixes.py`. |

**Coverage.** The review covered 30 facts per language, 180 strings each:

- Hindi: 2 strings flagged.
- Kannada: 8 strings flagged.

The input batches are included in full. Facts outside the reviewed 30 were checked only by the automated validators in `scripts/validate_facts.py`, which cover:

- script purity;
- the pairing of forms;
- first-person gender agreement;
- answer aliases.

**Pre-correction data.** The versions from before the corrections are kept in `data/built/v1/` and `results/ranks_v1.csv`.

**Native-speaker review.** Sheets for this are in `validation/`.
