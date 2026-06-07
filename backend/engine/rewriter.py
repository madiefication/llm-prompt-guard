"""
Prompt Rewriter: strips injection keywords and rephrases suspicious prompts safely.
Only invoked for prompts classified as 'suspicious' (not malicious — those are blocked).
"""

import re

# Phrases to strip from suspicious prompts
_INJECTION_PHRASES = [
    r"ignore\s+(all\s+)?previous\s+instructions",
    r"disregard\s+(all\s+)?(previous|prior|your)\s+(instructions?|context|training)",
    r"forget\s+(everything|all|your|previous|prior).{0,40}(instruction|training|context|rule)",
    r"pretend\s+you\s+have\s+no\s+restrictions?",
    r"act\s+as\s+(if\s+)?you\s+(have\s+no|without\s+any)\s+(restriction|guideline|ethic|filter)",
    r"(you\s+are\s+now\s+)?in\s+(developer|debug|unrestricted|legacy|sandbox)\s+mode",
    r"without\s+(any\s+)?(restriction|limitation|filter|censorship|ethical|guideline)",
    r"(bypass|override|disable|circumvent)\s+.{0,30}(safety|filter|restriction|guideline|policy)",
    r"\bjailbreak\b",
    r"\bDAN\s*mode\b",
    r"no\s+ethical\s+guidelines?",
    r"(as\s+an?\s+)?(evil|malicious|unrestricted|unfiltered)\s+(ai|assistant|model|bot)",
    r"(system\s+prompt|hidden\s+instruction|secret\s+instruction)",
    r"reveal\s+(your|the)\s+(system|initial|original)\s+prompt",
]

_COMPILED = [re.compile(p, re.IGNORECASE | re.DOTALL) for p in _INJECTION_PHRASES]

# Filler replacements for stripped segments
_PLACEHOLDER = " [content removed] "


def rewrite(text: str) -> str:
    """Strip injection keywords and return a sanitized version of the prompt."""
    cleaned = text
    for pattern in _COMPILED:
        cleaned = pattern.sub(_PLACEHOLDER, cleaned)

    # Collapse multiple placeholders
    cleaned = re.sub(r"(\s*\[content removed\]\s*){2,}", _PLACEHOLDER, cleaned)
    # Remove leading/trailing cruft
    cleaned = re.sub(r"^\s*\[content removed\]\s*", "", cleaned)
    cleaned = re.sub(r"\s*\[content removed\]\s*$", "", cleaned)
    # Normalize whitespace
    cleaned = re.sub(r"\s{2,}", " ", cleaned).strip()

    if not cleaned or len(cleaned) < 10:
        return "Please rephrase your request in a constructive way."

    # Capitalize first letter
    if cleaned and cleaned[0].islower():
        cleaned = cleaned[0].upper() + cleaned[1:]

    return cleaned
