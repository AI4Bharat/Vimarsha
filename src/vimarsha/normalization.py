"""Text normalization shared by lattice construction and scoring."""

from __future__ import annotations

import re
import string
import unicodedata

from indicnlp.normalize.indic_normalize import IndicNormalizerFactory

LANGUAGE_CODES = {
    "assamese": "as",
    "bengali": "bn",
    "bodo": "brx",
    "dogri": "doi",
    "gujarati": "gu",
    "hindi": "hi",
    "kannada": "kn",
    "kashmiri": "ks",
    "konkani": "kok",
    "maithili": "mai",
    "malayalam": "ml",
    "manipuri": "mni",
    "marathi": "mr",
    "nepali": "ne",
    "odia": "or",
    "punjabi": "pa",
    "sanskrit": "sa",
    "santali": "sat",
    "sindhi": "sd",
    "tamil": "ta",
    "telugu": "te",
    "urdu": "ur",
}

NO_INDIC_NORMALIZATION = {"ur", "kok", "mai", "doi", "sat", "mni", "brx", "ks", "sd"}

_REPLACEMENTS = {
    "॥": " ",
    "।": " ",
    "۔": " ",
    "‘": "",
    "’": " ",
    "ʼ": "",
    "–": " ",
    "—": " ",
    "‑": " ",
    "\u200b": "",
    "\u200c": "",
    "\u200d": "",
    "\u200e": "",
    "\u200f": "",
    "“": "",
    "”": "",
}
for _character in string.punctuation:
    _REPLACEMENTS.setdefault(_character, " ")
_TRANSLATION = str.maketrans(_REPLACEMENTS)


def resolve_language(language: str) -> str:
    """Return an ISO 639 code from a supported language name or code."""
    value = language.strip().lower()
    if value in LANGUAGE_CODES:
        return LANGUAGE_CODES[value]
    if value in LANGUAGE_CODES.values():
        return value
    supported = ", ".join(sorted(LANGUAGE_CODES))
    raise ValueError(f"Unsupported language {language!r}. Use an ISO code or one of: {supported}")


def normalize_text(text: str, language: str) -> str:
    """Apply the normalization used by the released OIWER implementation."""
    if not isinstance(text, str):
        raise TypeError(f"Expected text to be str, got {type(text).__name__}")

    language_code = resolve_language(language)
    value = text.translate(_TRANSLATION)
    if language_code not in NO_INDIC_NORMALIZATION:
        value = IndicNormalizerFactory().get_normalizer(language_code).normalize(value)
    value = unicodedata.normalize("NFC", value)
    return re.sub(r"\s+", " ", value).strip()
