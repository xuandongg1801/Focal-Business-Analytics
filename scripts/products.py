"""Conservative product parsing and explicit quantity allocation; no fuzzy matching."""
from __future__ import annotations

from dataclasses import dataclass
import re
import unicodedata

import numpy as np
import pandas as pd


def normalize_product_text(value: object) -> str:
    if pd.isna(value):
        return ''
    text = unicodedata.normalize('NFKC', str(value)).upper()
    text = re.sub(r'[–—−]', '-', text)
    return ' '.join(text.split()).replace('ADDS', 'ADSS')


# Specific forms precede generic forms. The boundaries reject embedded/prefix codes.
CODE = re.compile(
    r'(?<![\w])(?:'
    r'FTTH\s*(?:SQ\s*\d{1,2}(?:\s*FO)?|\d{1,2}(?:\s*FO)?(?:\s*[-_/]\s*(?:LT|SQ))?)'
    r'|ADSS\s*\d{1,3}(?:\s*[-/ ]\s*(?:S|KV)?\s*\d{2,4})?'
    r'|(?:FEAM|FEM|FEA|FE|DUAM|DUM|DUA|DU|AAC|DAC|DB|FC|CORE)\s*[- ]?\s*\d{1,3}'
    r'|(?:(?:ÉP|EP)\s+)?CHẶT\s*\d{1,2}(?:\s*FO)?'
    r')(?![\w]|\s*-\s*[A-Z0-9])')
QUANTITY = re.compile(r'^\s*[:=]?\s*(\d+(?:[.,]\d{1,2})?)\s*(KM|M|KG|CÁI|BỘ|LICENSE|TẤN)\b')


@dataclass(frozen=True)
class ProductParse:
    codes: tuple[str, ...]
    parse_status: str
    allocation_status: str
    allocations: tuple[tuple[str, float | None], ...]
    reason: str


def _canonical(token: str, context: str) -> str | None:
    digits = re.findall(r'\d+', token)
    if token.startswith('FTTH') or 'CHẶT' in token:
        loose = bool(re.search(r'\bLT\b|LỎNG', context))
        tight = bool(re.search(r'\bSQ\b|CHẶT', context))
        if loose and tight:
            return None
        suffix = '-LT' if loose else '-SQ' if tight else ''
        return f'FTTH{int(digits[0]):02d}{suffix}'
    if token.startswith('ADSS'):
        return f'ADSS{int(digits[0]):02d}' + (f'-S{int(digits[1])}' if len(digits) == 2 else '')
    family = re.match(r'[A-Z]+', token)[0]
    return f'{family}{int(digits[0]):02d}'


def parse_product(value: object, quantity: float | None, unit: object,
                  reference_codes: set[str] | None = None) -> ProductParse:
    """Allocate only explicit amounts whose sum matches the numeric source total.

    Without a reference, recognized syntax is useful for isolated unit tests. In the
    pipeline, reference codes are mandatory; bare FTTH with a referenced variant
    remains a recognized specification with no invented LT/SQ variant or price.
    """
    text = normalize_product_text(value)
    if reference_codes is not None and text in reference_codes:
        return ProductParse((text,), 'exact_reference', 'single', ((text, quantity),), 'Exact reference code')
    matches = list(CODE.finditer(text))
    codes = []
    contexts = []
    for n, match in enumerate(matches):
        end = matches[n + 1].start() if n + 1 < len(matches) else len(text)
        context = text[match.start():end]
        codes.append(_canonical(match[0], context))
        contexts.append(text[match.end():end])
    if not codes:
        return ProductParse((), 'unmapped', 'unresolved', (), 'No supported product code')
    if None in codes:
        return ProductParse(tuple(c for c in codes if c), 'ambiguous', 'unresolved', (), 'Conflicting semantic qualifiers')
    distinct = tuple(dict.fromkeys(codes))
    if reference_codes is not None:
        supported = set(reference_codes) | {c.split('-')[0] for c in reference_codes if c.startswith('FTTH')}
        unknown = set(codes) - supported
        if unknown:
            return ProductParse(distinct, 'unmapped', 'unresolved', (), 'Unreferenced code: ' + ', '.join(sorted(unknown)))
    if len(matches) == 1:
        status = 'exact_reference' if reference_codes is not None and codes[0] in reference_codes else 'recognized_generic'
        return ProductParse(distinct, status, 'single', ((codes[0], quantity),), 'Single supported product')
    # Repeated-code, alternative-code or print-code descriptions need source confirmation too.
    if len(codes) != len(distinct):
        return ProductParse(distinct, 'ambiguous', 'unresolved', (), 'Repeated code in source description')
    quantities = [QUANTITY.match(context) for context in contexts]
    source_unit = normalize_product_text(unit)
    if pd.isna(quantity) or not all(quantities):
        return ProductParse(distinct, 'unresolved_multiple', 'unresolved', (), 'Multiple codes without explicit per-product amounts')
    allocated = []
    for code, match in zip(codes, quantities):
        amount = float(match[1].replace(',', '.'))
        product_unit = match[2]
        if product_unit != source_unit:
            if {product_unit, source_unit} == {'KM', 'M'}:
                amount *= 1000 if source_unit == 'M' else .001
            else:
                return ProductParse(distinct, 'unresolved_multiple', 'unresolved', (), 'Incompatible allocation units')
        allocated.append((code, amount))
    if not np.isclose(sum(amount for _, amount in allocated), quantity, rtol=1e-10, atol=1e-8):
        return ProductParse(distinct, 'unresolved_multiple', 'unresolved', (), 'Explicit allocation does not equal source total')
    return ProductParse(distinct, 'allocated_multiple', 'split', tuple(allocated), 'Explicit quantities reconcile to source total')


def normalize_product_token(value: object) -> str | None:
    result = parse_product(value, None, None)
    return result.codes[0] if result.allocation_status == 'single' else None



PRODUCT_STATUSES = frozenset({'exact_reference', 'recognized_generic', 'unmapped',
                              'ambiguous', 'unresolved_multiple', 'allocated_multiple'})


def reference_codes(directory) -> set[str]:
    """Authoritative code membership; price codes can cover several technical variants."""
    return (set(pd.read_csv(directory/'dim_product.csv').ma_san_pham.dropna())
            | set(pd.read_csv(directory/'dim_price_list.csv').ky_ma_hieu.dropna()))


def product_semantics(token: str | None, status: str, references: set[str]) -> dict:
    """A normalized token is not evidence of a fully specified reference product."""
    token = None if pd.isna(token) else token
    exact = status == 'exact_reference'
    if exact and (token is None or token not in references):
        raise ValueError('Exact product requires authoritative code membership')
    return {'canonical_product_code': token if exact else None,
            'is_reference_product_code': exact,
            'product_family_code': token.split('-')[0] if token else None}


def validate_product_semantics(frame: pd.DataFrame, references: set[str]) -> None:
    if not frame.parse_status.isin(PRODUCT_STATUSES).all():
        raise ValueError('Unknown product match status')
    exact = frame.parse_status.eq('exact_reference')
    if not frame.is_reference_product_code.eq(exact).all():
        raise ValueError('Reference flag disagrees with product match status')
    if frame.loc[~exact, 'canonical_product_code'].notna().any():
        raise ValueError('Non-reference row contains an authoritative product code')
    if not frame.loc[exact, 'canonical_product_code'].isin(references).all():
        raise ValueError('Authoritative product code is absent from references')
    if not frame.loc[exact, 'canonical_product_code'].eq(frame.loc[exact, 'parsed_product_token']).all():
        raise ValueError('Reference code differs from normalized source token')
    generic = frame.parse_status.eq('recognized_generic')
    supported_generic = {c.split('-')[0] for c in references if c.startswith('FTTH')} - references
    if not frame.loc[generic, 'parsed_product_token'].isin(supported_generic).all():
        raise ValueError('Generic specification is unsupported by reference families')
    if frame.loc[generic, 'parsed_product_token'].isin(references).any():
        raise ValueError('Exact reference was incorrectly classified as generic')
    unresolved = frame.allocation_status.eq('unresolved')
    if frame.loc[unresolved, 'parsed_product_token'].notna().any():
        raise ValueError('Unresolved source row cannot have a single assigned token')
    expected_family = frame.parsed_product_token.astype('string').str.split('-').str[0]
    actual_family = frame.product_family_code.astype('string')
    if not (actual_family.eq(expected_family) | (actual_family.isna() & expected_family.isna())).fillna(False).all():
        raise ValueError('Product family does not match the resolved token')


def validate_allocation(source: pd.DataFrame, products: pd.DataFrame) -> pd.DataFrame:
    """Check each source row (including missing amounts), then reconcile by unit."""
    if source.item_id.isna().any() or not source.item_id.is_unique:
        raise ValueError('Source item key is null/duplicated')
    if products.product_item_id.isna().any() or not products.product_item_id.is_unique:
        raise ValueError('Product item key is null/duplicated')
    if not set(products.item_id) <= set(source.item_id):
        raise ValueError('Orphan product allocation')
    if products.parsed_product_token.isna().any() or products.duplicated(['item_id', 'parsed_product_token']).any():
        raise ValueError('Canonical grain must be one source/product pair')
    sums = products.groupby('item_id').so_luong.sum(min_count=1)
    allocated = source.item_id.map(sums)
    resolved = source.allocation_status.isin(['single', 'split'])
    if set(products.item_id) != set(source.loc[resolved, 'item_id']):
        raise ValueError('Missing/extra resolved allocation rows')
    if not np.allclose(allocated[resolved], source.loc[resolved, 'so_luong'], equal_nan=True, rtol=1e-10, atol=1e-8):
        raise ValueError('Per-source quantity conservation failed')
    original_units = products.item_id.map(source.set_index('item_id').don_vi)
    if not (products.don_vi.eq(original_units) | (products.don_vi.isna() & original_units.isna())).all():
        raise ValueError('Allocation unit differs from source unit')
    ledger = source.assign(resolved_quantity=allocated.where(resolved),
                           unresolved_quantity=source.so_luong.where(~resolved))
    report = ledger.groupby('don_vi', dropna=False).agg(
        source_rows=('item_id', 'size'), original_quantity=('so_luong', lambda s: s.sum(min_count=1)),
        resolved_quantity=('resolved_quantity', lambda s: s.sum(min_count=1)),
        unresolved_quantity=('unresolved_quantity', lambda s: s.sum(min_count=1)),
        missing_quantity=('so_luong', lambda s: s.isna().sum())).reset_index()
    # Zero is used only for an empty contribution to a known aggregate, never for missing source amounts.
    known = report.original_quantity.notna()
    actual = report.resolved_quantity.fillna(0) + report.unresolved_quantity.fillna(0)
    if not np.allclose(actual[known], report.loc[known, 'original_quantity']):
        raise ValueError('Unit-level quantity conservation failed')
    return report
