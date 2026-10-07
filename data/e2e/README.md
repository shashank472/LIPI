# End-to-end reading experiment (Section 5.6)

| File | Contents |
|---|---|
| `READER_PROMPT.md` | Instructions given to the reader (Claude Haiku 4.5). |
| `in_mE5-base_{0-7}.txt` | The 1,233 distinct reader items, one per line: `id`, the English question and five memories. Items that would be identical across conditions are asked once. Ids are opaque and items are shuffled. |
| `key_mE5-base.json` | Maps each of the 1,296 cells (fact × form × condition) to its item id. It also records whether the target memory was among the five shown. |
| `out_mE5-base_reused.txt`, `out_mE5-base_todo.txt` | The reader's answers, `id<TAB>answer`. |
| `v1/` | Inputs, key and answers of the run on the data before the 10 audit corrections (`data/audit`). |
| `discarded_run1/` | An earlier run, discarded because the reader returned "unknown" for most items without reading them. It is kept for transparency and is not used anywhere. |

**How the two answer files fit together.** After the audit corrections:

- 5 items had different inputs from `v1/`. These were answered again (`todo`).
- The other 1,228 items were unchanged, so their answers were carried over from `v1/` (`reused`).

The change log is `data/audit/changed_units.json`.

**Scoring.** `python3 src/e2e_score.py --model mE5-base` reads every `out_mE5-base_*.txt` file here. It marks an answer correct if it contains the gold answer or one of its aliases, and writes `results/e2e_mE5-base.csv`.
