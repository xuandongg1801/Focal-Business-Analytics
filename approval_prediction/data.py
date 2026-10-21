"""Target audit and strictly earlier-month order-arrival history."""
import hashlib
import importlib.util
import sys

import numpy as np
import pandas as pd

from .config import ROOT, SOURCE, VALID_UNITS, FEATURES, VALIDATION_START, TEST_START, validate_feature_names
from .target import read_source_fields, item_labels, aggregate_target
from .quality import normalize_text, classify_product


def load_cleaner():
    # Reuse the existing parser only for raw reconciliation, not for modeling.
    sys.path.insert(0, str(ROOT / 'scripts'))
    spec = importlib.util.spec_from_file_location('existing_order_cleaner', ROOT / 'scripts/02_clean_orders.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def private_id(value, prefix):
    return prefix + hashlib.sha256(str(value).encode('utf-8')).hexdigest()[:16]


def build_target(out):
    h = pd.read_csv(SOURCE / 'fact_order_header.csv')
    items = pd.read_csv(SOURCE / 'fact_order_items.csv')
    cleaner = load_cleaner()
    from reconciliation import reconcile_orders
    raw = cleaner.load_raw_orders()
    raw_rows_reconciled = reconcile_orders(cleaner, raw, h, items)
    audit = item_labels(read_source_fields(items))
    labels = audit.groupby('order_row_id').agg(chot_don=('item_target', aggregate_target),
                                             item_count=('item_id', 'size'))
    d = h.merge(labels, on='order_row_id', validate='one_to_one')
    d['order_id'] = d.so_xac_nhan_don_hang.map(lambda v: private_id(v, 'O_'))
    d['customer_id'] = d.ma_khach.map(lambda v: private_id(v, 'C_') if pd.notna(v) else '')
    d['order_date'] = pd.to_datetime(d.ngay_dt).dt.strftime('%Y-%m-%d')
    d['include'] = d.la_don_ban_hang.eq(True)
    d['customer_known'] = d.ma_khach.notna()
    d['population_reason'] = np.where(d.include, 'Customer sales; existing pipeline rule', 'Purchase/internal; excluded')
    population = d.groupby(['loai_don', 'include', 'population_reason'], dropna=False).size().reset_index(name='orders')
    population = population.rename(columns={'loai_don': 'type', 'orders': 'count', 'population_reason': 'reason'})
    population.to_csv(out/'tables/modeling_population_audit.csv', index=False, encoding='utf-8-sig')
    audit = audit.merge(d[['order_row_id', 'order_id', 'order_date', 'include']], on='order_row_id', validate='many_to_one')
    audit.to_csv(out/'tables/item_target_audit.csv', index=False, encoding='utf-8-sig')
    patterns = audit.groupby('item_text_raw', dropna=False).agg(
        rows=('item_id', 'size'), product_present=('product_present', 'first'),
        sales_rows=('include', 'sum')).reset_index()
    patterns.to_csv(out/'tables/observed_product_patterns.csv', index=False, encoding='utf-8-sig')
    audit.groupby('don_vi', dropna=False).size().rename('rows').to_csv(out/'tables/observed_units.csv')
    d[['order_id', 'order_date', 'order_month', 'order_year', 'customer_id', 'loai_don',
       'include', 'population_reason', 'customer_known', 'chot_don', 'item_count',
       'loai_don_tu_so_hop_dong']].to_csv(out/'tables/target_audit.csv', index=False, encoding='utf-8-sig')
    sales = d[d.include].copy()
    for field, name in [('order_year', 'year'), ('order_month', 'month'),
                        ('customer_id', 'customer'), ('loai_don', 'order_type'), ('customer_known', 'customer_known')]:
        sales.groupby(field, dropna=False).agg(total=('order_id', 'size'),
            win=('chot_don', 'sum'), win_rate=('chot_don', 'mean')).assign(
                lost=lambda x: x.total-x.win
            ).reset_index().to_csv(out/f'tables/target_by_{name}.csv', index=False, encoding='utf-8-sig')
    distribution = sales.chot_don.value_counts().rename_axis('chot_don').reset_index(name='orders')
    distribution['share'] = distribution.orders / len(sales)
    distribution.to_csv(out/'tables/class_distribution.csv', index=False)
    # Stratify reviewed examples over years and both business classes.
    samples = []
    for label in [0, 1]:
        candidates = sales[sales.chot_don.eq(label)].sort_values(['order_year', 'order_id'])
        idx = np.linspace(0, len(candidates)-1, min(24, len(candidates)), dtype=int)
        samples.append(candidates.iloc[idx])
    sample = pd.concat(samples)
    # Reconcile every raw row, providing stronger coverage than just the samples.
    # Distinct RAW values and frequencies, not a master-match audit.
    pa = raw.groupby('san_pham_raw', dropna=False).size().reset_index(name='count').rename(columns={'san_pham_raw': 'raw_product'})
    pa['normalized_product'] = pa.raw_product.map(normalize_text)
    classifications = pa.raw_product.map(classify_product)
    pa['classification'] = classifications.map(lambda v: v[0])
    pa['reason'] = classifications.map(lambda v: v[1])
    pa.to_csv(out/'tables/product_text_audit.csv', index=False, encoding='utf-8-sig')
    ua = raw.groupby('don_vi', dropna=False).size().reset_index(name='count').rename(columns={'don_vi': 'raw_unit'})
    ua['normalized_unit'] = ua.raw_unit.map(normalize_text)
    ua['is_valid'] = ua.normalized_unit.isin(VALID_UNITS)
    ua['reason'] = np.where(ua.is_valid, 'Observed business unit; not restricted to KM',
                           np.where(ua.normalized_unit.eq(''), 'Missing unit', 'Outside data-quality unit list; does not determine target'))
    ua.to_csv(out/'tables/unit_audit.csv', index=False, encoding='utf-8-sig')
    numeric = pd.to_numeric(audit.raw_quantity, errors='coerce')
    invalid_numeric = audit.quantity_present.eq(1) & (~np.isfinite(numeric) | numeric.le(0))
    qa = audit.loc[invalid_numeric, ['order_source_row_id', 'raw_quantity']]
    qa['reason'] = 'Non-numeric, non-finite or non-positive quantity; data quality only'
    qa.to_csv(out/'tables/quantity_parse_audit.csv', index=False, encoding='utf-8-sig')
    samples_out = audit[audit.order_row_id.isin(sample.order_row_id)].merge(
        sample[['order_row_id', 'chot_don', 'order_year']], on='order_row_id', validate='many_to_one')
    samples_out['raw_reconciled'] = True
    samples_out.to_csv(out/'tables/target_review_samples.csv', index=False, encoding='utf-8-sig')
    edge = audit[audit.item_text_raw.map(normalize_text).isin(['DA48', 'FE', '7X0.33', 'KM', 'M', 'M .)'])].merge(
        d[['order_id', 'chot_don']], on='order_id', validate='many_to_one')
    edge.to_csv(out/'tables/target_edge_case_review.csv', index=False, encoding='utf-8-sig')
    counts = dict(total_orders=len(h), duplicate_orders=int(h.order_row_id.duplicated().sum()),
                  missing_keys=int(h.order_row_id.isna().sum()), mean_items=float(labels.item_count.mean()),
                  min_items=int(labels.item_count.min()), max_items=int(labels.item_count.max()),
                  sales_orders=len(sales), excluded_orders=int((~d.include).sum()),
                  class_0=int(sales.chot_don.eq(0).sum()), class_1=int(sales.chot_don.eq(1).sum()),
                  raw_rows_reconciled=raw_rows_reconciled,
                  win_rate=float(sales.chot_don.mean()), invalid_raw_quantities=len(qa),
                  wo_order_coverage=float(h.wo.notna().mean()))
    return sales, audit, counts


def build_features(sales):
    """Only arrival counts; all orders in the current month are invisible to one another."""
    validate_feature_names(FEATURES)
    if not sales.order_id.is_unique or sales.order_id.isna().any():
        raise ValueError('Modeling population must have one non-null order_id per order')
    if not sales.chot_don.isin([0, 1]).all():
        raise ValueError('WIN/LOST target must be binary for every order')
    d = sales.sort_values(['order_month', 'order_id']).copy()
    d['_period'] = pd.PeriodIndex(d.order_month, freq='M').asi8
    return _feature_rows(d)


def _feature_rows(d):
    rows = []
    for _, row in d.iterrows():
        p = row['_period']
        prior = d[d.customer_id.eq(row.customer_id) & d['_period'].lt(p)] if row.customer_id else d.iloc[:0]
        features = history_features(row.customer_id, row.order_month, prior)
        rows.append({**row.drop(labels=['_period']).to_dict(), **features,
                     'history_latest_month': prior.order_month.max() if len(prior) else ''})
    result = pd.DataFrame(rows)
    result['split'] = np.where(result.order_month.lt(VALIDATION_START), 'train',
                      np.where(result.order_month.lt(TEST_START), 'validation', 'test'))
    columns = ['order_id', 'order_date', 'order_month', 'customer_id', 'chot_don',
               'split', 'history_latest_month'] + FEATURES
    return result.loc[:, columns].reset_index(drop=True)


def history_features(customer_id, order_month, history):
    """Shared training/inference features. Never use current-month arrivals or outcomes.

    History must contain sales arrivals regardless of WIN/LOST. Missing customer
    IDs do not share a synthetic history. This function also filters a full history
    input, making the temporal boundary explicit for callers outside training.
    """
    month_period = pd.Period(order_month, freq='M')
    p = month_period.ordinal
    known = pd.notna(customer_id) and bool(customer_id)
    prior = history.loc[history.customer_id.eq(customer_id) & history.order_month.lt(str(month_period))] if known else history.iloc[:0]
    periods = pd.PeriodIndex(prior.order_month, freq='M').asi8
    last3, last6 = int((periods >= p-3).sum()), int((periods >= p-6).sum())
    month = month_period.month
    return dict(customer_is_known=int(known), prior_order_count=len(prior),
        recency_months=p-periods.max() if len(prior) else np.nan,
        customer_active_months_before=prior.order_month.nunique(), orders_last_3m=last3,
        orders_last_6m=last6, prior_monthly_order_trend=(2*last3-last6)/3,
        year=month_period.year, month=month, quarter=(month-1)//3+1,
        month_sin=np.sin(2*np.pi*month/12), month_cos=np.cos(2*np.pi*month/12))
