"""Deterministic 'casual' romanization of Devanagari / Kannada text (write-time fix W1).

Uses indic_transliteration (ITRANS) and then simplifies to chat-style Latin spelling:
lower-case, no diacritics, anusvara -> n, Hindi word-final schwa deletion. Latin-script
tokens (English words inside code-mixed text) pass through unchanged."""
import re, unicodedata
from indic_transliteration import sanscript
from indic_transliteration.sanscript import transliterate

DEV = re.compile(r"[ऀ-ॿ]+")
KAN = re.compile(r"[ಀ-೿]+")

_SIMPLE = [  # ITRANS -> casual
    ("~N", "n"), ("~n", "n"), ("N^", "n"), ("JN", "gy"), ("GY", "gy"),
    ("chh", "chh"), ("Ch", "chh"), ("sh", "sh"), ("Sh", "sh"),
    (".N", "n"), (".n", "n"), ("M", "n"), (".m", "n"), ("H", "h"), (".a", ""),
    ("RRi", "ri"), ("R^i", "ri"), ("RRI", "ri"), ("LLi", "li"),
    ("A", "aa"), ("I", "ee"), ("U", "oo"), ("ii", "ee"), ("uu", "oo"),
    ("T", "t"), ("D", "d"), ("N", "n"), ("L", "l"), ("q", "k"), ("K", "kh"), ("G", "gh"),
    ("z", "z"), ("f", "f"), (".D", "d"), (".Dh", "dh"), ("^", ""), ("~", ""), (".", ""),
]

def _simplify(s):
    for a, b in _SIMPLE:
        s = s.replace(a, b)
    s = unicodedata.normalize("NFD", s)
    s = "".join(c for c in s if unicodedata.category(c) != "Mn")
    return s.lower()

def _hindi_word(w):
    r = _simplify(transliterate(w, sanscript.DEVANAGARI, sanscript.ITRANS))
    # word-final schwa deletion: ghara -> ghar, kamala -> kamal (keep short words and long vowels)
    if len(r) > 3 and r.endswith("a") and not r.endswith("aa") and r[-2] not in "aeiou":
        r = r[:-1]
    return r

def _kannada_word(w):
    return _simplify(transliterate(w, sanscript.KANNADA, sanscript.ITRANS))

def romanize(text):
    text = text.replace("।", ".").replace("‌", "").replace("‍", "")
    text = DEV.sub(lambda m: _hindi_word(m.group(0)), text)
    text = KAN.sub(lambda m: _kannada_word(m.group(0)), text)
    return re.sub(r"\s+", " ", text).strip()

if __name__ == "__main__":
    for t in ["Finally last week पुणे shift हो गई, office से दस minute पे flat मिल गया।",
              "आखिरकार पिछले हफ्ते पुणे आ गई, दफ्तर से दस मिनट की दूरी पर घर मिल गया।",
              "मैं किस शहर में रहती हूँ?",
              "ಕೊನೆಗೂ ಕಳೆದ ವಾರ ಪುಣೆಗೆ ಬಂದೆ, ಕಚೇರಿಯಿಂದ ಹತ್ತು ನಿಮಿಷದ ದೂರದಲ್ಲಿ ಮನೆ ಸಿಕ್ಕಿತು.",
              "ನಾನು ಈಗ ಯಾವ ನಗರದಲ್ಲಿ ವಾಸಿಸುತ್ತಿದ್ದೇನೆ?"]:
        print(romanize(t))
