"""Descriptive data-quality checks; never used to construct WIN/LOST."""
import unicodedata
import pandas as pd
from .config import INVALID_PRODUCT_EXACT, INVALID_PRODUCT_PATTERNS, AMBIGUOUS_PRODUCT_EXACT


def normalize_text(text):
    return '' if pd.isna(text) else ' '.join(unicodedata.normalize('NFC', str(text)).upper().split())


def classify_product(text):
    """Description validity is independent of normalized tokens and master matches."""
    t = normalize_text(text)
    if not t:
        return 'PLACEHOLDER', 'Missing product description'
    if t in INVALID_PRODUCT_EXACT:
        return 'PLACEHOLDER', 'Observed unit-only text, generic request or non-product note'
    for pattern in INVALID_PRODUCT_PATTERNS:
        if pattern in t:
            return 'PLACEHOLDER', f'Observed non-specific request pattern: {pattern}'
    if t in AMBIGUOUS_PRODUCT_EXACT or not any(c.isalnum() for c in t):
        return 'AMBIGUOUS', 'Operational note or malformed text; actual goods cannot be established'
    return 'VALID_PRODUCT', 'Product description present; standardized code/master match is irrelevant'
