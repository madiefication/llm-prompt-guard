"""
Prompt Preprocessing Engine: normalization pipeline before classification.
"""

import html
import re
import ssl
import unicodedata

# Lazy NLTK import — downloaded on first use
_nltk_ready = False
_use_simple_tokenizer = False


def _ensure_nltk():
    global _nltk_ready, _use_simple_tokenizer
    if _nltk_ready or _use_simple_tokenizer:
        return
    try:
        import nltk
        # Bypass SSL verification for environments with cert issues
        try:
            _create_unverified_https_context = ssl._create_unverified_context
        except AttributeError:
            pass
        else:
            ssl._create_default_https_context = _create_unverified_https_context

        for pkg in ("punkt", "punkt_tab"):
            try:
                nltk.data.find(f"tokenizers/{pkg}")
            except LookupError:
                try:
                    nltk.download(pkg, quiet=True)
                except Exception:
                    pass
        # Verify punkt_tab actually works
        from nltk.tokenize import word_tokenize
        word_tokenize("test")
        _nltk_ready = True
    except Exception:
        _use_simple_tokenizer = True


# Zero-width and invisible Unicode characters
_ZERO_WIDTH = re.compile(r"[​‌‍‎‏﻿­]")
# Repeated whitespace
_MULTI_SPACE = re.compile(r"\s{2,}")


def strip_html(text: str) -> str:
    text = html.unescape(text)
    return re.sub(r"<[^>]+>", " ", text)


def remove_zero_width(text: str) -> str:
    return _ZERO_WIDTH.sub("", text)


def normalize_unicode(text: str) -> str:
    return unicodedata.normalize("NFKC", text)


def normalize_whitespace(text: str) -> str:
    return _MULTI_SPACE.sub(" ", text).strip()


def _simple_tokenize(text: str) -> list[str]:
    """Regex-based fallback tokenizer when NLTK is unavailable."""
    return re.findall(r"\b\w+\b", text.lower())


def tokenize(text: str) -> list[str]:
    _ensure_nltk()
    if _use_simple_tokenizer:
        return _simple_tokenize(text)
    try:
        from nltk.tokenize import word_tokenize
        return word_tokenize(text)
    except Exception:
        return _simple_tokenize(text)


def preprocess(text: str) -> dict:
    """
    Full preprocessing pipeline.
    Returns a dict with both the cleaned text (for classifiers) and tokens.
    """
    raw = text

    # 1. HTML stripping
    cleaned = strip_html(raw)
    # 2. Zero-width removal (done before lower so rule classifier still sees originals)
    cleaned = remove_zero_width(cleaned)
    # 3. Unicode normalization
    cleaned = normalize_unicode(cleaned)
    # 4. Whitespace normalization
    cleaned = normalize_whitespace(cleaned)
    # 5. Lowercase for ML model
    lowered = cleaned.lower()

    tokens = tokenize(lowered)

    return {
        "original": raw,
        "cleaned": cleaned,       # preserves case — for rule matching
        "normalized": lowered,    # lowercased — for ML model
        "tokens": tokens,
    }
