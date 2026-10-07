# Style guide for drafting CM-Recall facts

Each line of a `facts_bNN.jsonl` file is one personal fact about one synthetic user. The fact is written as a chat message the user sends to an AI assistant. It appears in 9 parallel *forms* plus questions, so that retrieval differences can be traced to language, script and code-mixing alone.

## Fields (all required, in this order)
| field | content |
|---|---|
| `fact_id` | `uXX_fK`, where K = 1..6 follows the order of relations given for the user |
| `user_id` | `uXX` |
| `relation` | the relation type, as given |
| `answer` | canonical short answer (Latin script) |
| `aliases` | list of strings that count as a correct answer, matched case-insensitively as substrings (see rules below) |
| `en` | English statement |
| `q_en` | English question |
| `hi_cm_rom` | Hindi-English code-mixed, Latin script ("Hinglish") |
| `hi_cm_nat` | **same words** as `hi_cm_rom`; Hindi words in Devanagari, English words in Latin |
| `hi_mono_nat` | fluent Hindi, Devanagari only |
| `hi_mono_rom` | **same words** as `hi_mono_nat`, casual Latin script |
| `q_hi_cm_rom` | code-mixed Hindi question, Latin script |
| `q_hi_mono_nat` | pure Hindi question, Devanagari |
| `kn_cm_rom` | Kannada-English code-mixed, Latin script |
| `kn_cm_nat` | **same words** as `kn_cm_rom`; Kannada words in Kannada script, English words in Latin |
| `kn_mono_nat` | fluent Kannada, Kannada script only |
| `kn_mono_rom` | **same words** as `kn_mono_nat`, casual Latin script |
| `q_kn_cm_rom` | code-mixed Kannada question, Latin script |
| `q_kn_mono_nat` | pure Kannada question, Kannada script |

## Rules
1. **Statement content.**
   - Write a first-person, casual chat message of 12–30 words.
   - It states the fact plus one bit of everyday context.
   - It must not mention any other answer value of the same user, or any other city, person name, etc. that could be mistaken for an answer to another question.
   - All 9 forms convey the same content.
2. **EN.** Natural English. Where it reads naturally, avoid reusing the question's key words (for example, the statement says "shifted to Pune", the question asks "Which city do I live in now?").
3. **Code-mixed, Latin script (`*_cm_rom`).**
   - The matrix language is Hindi (or Kannada).
   - Roughly 30–50% of content words are English: nouns, plus verbs like *shift, join, book, start*.
   - Use casual chat spelling without diacritics.
   - Hindi examples: `hai, nahi, mein, kya, yaar, ho gaya/gayi, kar raha/rahi hoon`.
   - Kannada (colloquial Bengaluru) examples: `naanu, nanna, ide, illa, alli, maadide, hogtini, aaytu, tagonde, kaltidini`.
4. **Code-mixed, native script (`*_cm_nat`).** Use exactly the same words as the `_cm_rom` version, changing only the script:
   - Hindi/Kannada words go in native script.
   - All **person, pet and place names** go in native script (पुणे / ಪುಣೆ, आदित्य / ಆದಿತ್ಯ).
   - English common words and **brand / company / team / product / institution names written in English** (Infosys, RCB, Royal Enfield, Delhi University) stay in Latin script.
5. **Monolingual, native script (`*_mono_nat`).**
   - Write fluent, natural Hindi (or standard written Kannada).
   - Replace English words with native words wherever a common native word exists.
   - Unavoidable loanwords and brand names are still written in native script (जिम, एथर, ಇನ್ಫೋಸಿಸ್).
   - Latin characters are allowed only for codes like `A1` or `450X`, or for quoted foreign words.
6. **Monolingual, Latin script (`*_mono_rom`).**
   - Use exactly the same words as `_mono_nat`, romanized casually with no diacritics.
   - Names, brands and loanwords use their usual English spelling (Pune, Infosys, gym, violin).
7. **Hindi gender.** First-person verbs agree with the user's gender: `m` → `raha hoon, gaya, karta`; `f` → `rahi hoon, gayi, karti`. Kannada first person is not gendered.
8. **Questions.**
   - Each one asks for the answer, must not contain the answer, and fits the user's gender.
   - `q_en` follows the relation's usual form, for example:
     - "Which city do I live in now?"
     - "Where am I originally from?"
     - "Which company do I work for?"
     - "What do I do for a living?"
     - "What is my dog's name?"
     - "What is my sister's name?"
     - "What is my husband's name?"
     - "What am I allergic to?"
     - "What kind of diet do I follow?"
     - "What is my favourite dish?"
     - "Which instrument am I learning?"
     - "Which sport do I play on weekends?"
     - "Which vehicle did I buy recently?"
     - "Where am I going on my next trip?"
     - "Which exam am I preparing for?"
     - "Which part of my body did I hurt?"
     - "What time do I usually work out?"
     - "Who is my favourite singer?"
     - "Which language am I learning?"
     - "What is my son's name?"
     - "How do I get to work?"
     - "Which team do I support?"
     - "Which college did I study at?"
     - "What am I saving money for?"
   - Reuse the exact question wording from the example files for the same relation when it fits.
9. **Aliases.** List every string that would count as a correct answer:
   - Lower-case Latin spellings and common variants.
   - The Devanagari **and** Kannada-script spellings.
   - The stems that actually appear in each form. Inflected forms count, for example `biriyaani` for `biriyaaniya`.
   - The validator checks that at least one alias appears in each of the 9 forms, so make sure it does.
   - Do not add very short or generic aliases that would match wrong answers (avoid "a", "the", single digits).
10. **JSON.**
    - One object per line, UTF-8.
    - Use `ensure_ascii=False`-style raw Unicode, not `\u` escapes.
    - No ASCII double quotes inside strings; use apostrophes.
    - No trailing commas.

See `data/raw/facts_b01.jsonl` and `data/raw/facts_b02.jsonl` for 36 finished examples. Match their style and quality.

Validate with: `python3 scripts/validate_facts.py data/raw/facts_bNN.jsonl` (run from `/home/claude/cmmem`).
