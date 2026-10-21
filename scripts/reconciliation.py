"""Full-key, full-field raw-to-processed reconciliation before target creation."""
from io import StringIO

import pandas as pd


def reconcile_table(expected: pd.DataFrame, actual: pd.DataFrame,
                    keys: list[str], name: str) -> None:
    """Compare CSV-facing representations, including key coverage on both sides."""
    for side, frame in [('raw', expected), ('processed', actual)]:
        missing = set(keys) - set(frame)
        if missing:
            raise ValueError(f'{name}: {side} missing key columns: {sorted(missing)}')
        bad = frame[keys].isna().any(axis=1) | frame.duplicated(keys, keep=False)
        if bad.any():
            raise ValueError(f'{name}: {side} null/duplicate keys count={bad.sum()}; sample={frame.loc[bad, keys].head(3).to_dict("records")}')
    if set(expected) != set(actual):
        raise ValueError(f'{name}: schema mismatch; missing={sorted(set(expected)-set(actual))}; extra={sorted(set(actual)-set(expected))}')
    expected = pd.read_csv(StringIO(expected.to_csv(index=False)))
    compared = expected.merge(actual, on=keys, how='outer', validate='one_to_one',
                              suffixes=('_raw', '_processed'), indicator=True)
    missing = compared._merge.ne('both')
    if missing.any():
        counts = compared.loc[missing, '_merge'].value_counts().to_dict()
        sample = compared.loc[missing, keys+['_merge']].head(3).to_dict('records')
        raise ValueError(f'{name}: key coverage mismatch (left_only=missing processed, right_only=extra processed); counts={counts}; sample={sample}')
    for column in expected.columns.difference(keys):
        left, right = compared[f'{column}_raw'], compared[f'{column}_processed']
        same = left.eq(right) | (left.isna() & right.isna())
        if not same.all():
            sample = compared.loc[~same, keys+[f'{column}_raw', f'{column}_processed']].head(3).to_dict('records')
            raise ValueError(f'{name}: field mismatch {column}; count={(~same).sum()}; sample={sample}')


def reconcile_orders(cleaner, raw: pd.DataFrame, header: pd.DataFrame,
                     items: pd.DataFrame) -> int:
    if raw.duplicated(['source_file', 'source_sheet', 'source_excel_row']).any():
        raise ValueError('raw: duplicate physical source row key')
    expected_header, expected_items = cleaner.build_order_tables(raw)
    reconcile_table(expected_header, header, ['so_xac_nhan_don_hang'], 'headers')
    reconcile_table(expected_items, items, ['source_file', 'source_sheet', 'source_excel_row'], 'items')
    return len(expected_items)
