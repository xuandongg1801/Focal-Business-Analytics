"""Independent invariants; frozen regressions apply only to the original source."""
import hashlib
import json
import numpy as np
import pandas as pd
from config import ROOT, RAW, PROC, TAB, FIXTURES, CONFIRMED, PRICE_COLS, FORECAST_HORIZON, WAPE_EPSILON, HISTORICAL_EXTERNAL_EXPOSURE
from data_rules import sales_km, observation_months, unpriced_metrics, fit_item_outlier_threshold, item_outlier_mask
from reporting import write_json
from products import validate_allocation, validate_product_semantics, reference_codes
from reconciliation import reconcile_orders
import importlib


def validate_integrity(h: pd.DataFrame, i: pd.DataFrame, m: pd.DataFrame) -> None:
    """Structural invariants independent of the original dataset size."""
    for df, key in ((h, 'order_row_id'), (h, 'so_xac_nhan_don_hang'),
                    (i, 'item_id'), (i, 'order_source_row_id'), (m, 'item_id')):
        assert df[key].notna().all() and df[key].is_unique, f'Invariant: {key} null/duplicate'
    assert i['order_row_id'].notna().all()
    assert set(i['order_row_id']) == set(h['order_row_id']), 'Invariant: orphan item/header'
    assert len(m) == len(i) and set(m['item_id']) == set(i['item_id']), 'Invariant: merge multiplication/loss'
    for col in ('so_luong', 'so_luong_km'):
        for df in (i, m):
            values = df[col].dropna()
            assert np.isfinite(values).all() and values.ge(0).all(), f'Invariant: invalid {col}'
    for column in ('order_row_id', 'so_luong', 'so_luong_km', 'don_vi'):
        pd.testing.assert_series_equal(i.set_index('item_id')[column].sort_index(),
                                       m.set_index('item_id')[column].sort_index())
    assert h['order_month'].notna().all()
    periods = pd.PeriodIndex(h['order_month'], freq='M')
    assert not periods.hasnans
    assert (h['order_year'].astype(str).to_numpy() == periods.year.astype(str)).all()
    dates = pd.to_datetime(h['ngay_dt'], errors='raise')
    assert h['ngay_bi_thieu'].equals(h['ngay'].isna())
    assert h['ngay_nam_khong_khop_file'].equals(dates.notna() & dates.dt.year.ne(h['nam_file']))
    assert not (h['ngay_bi_thieu'] & h['ngay_nam_khong_khop_file']).any()
    assert not h['ngay_khong_hop_le'].any(), 'Invariant: invalid supplied date'


def validate_business(m: pd.DataFrame) -> pd.DataFrame:
    """Validate fixed confirmations, price semantics, item filtering and KM conservation."""
    for order, expected in CONFIRMED.items():
        sub = m[m['so_xac_nhan_don_hang'].eq(order)]
        assert len(sub) == len(expected), f'Confirmed business rows: {order}'
        assert dict(zip(sub['parsed_product_token'], sub['so_luong_km'])) == expected, f'Confirmed KM: {order}'
        assert not sub['nghi_ngo_outlier'].any()
    unpriced = m['so_luong_km'].notna() & ~m['co_don_gia_tham_khao']
    for col in [c for c in m if c.startswith('gia_tri_')]:
        assert m.loc[unpriced, col].isna().all(), f'Unpriced rows generated {col}'
    for col in [c for c in m if c.endswith(('_min', '_max'))] + ['don_gia_tham_khao']:
        vals = m[col].dropna()
        assert np.isfinite(vals).all() and vals.ge(0).all(), f'Invalid price/value: {col}'
    for tier in PRICE_COLS:
        for bound in ('min', 'max'):
            np.testing.assert_allclose(m[f'gia_tri_{tier}_{bound}'], m['so_luong_km'] * m[f'{tier}_{bound}'], equal_nan=True)
    assert m['ma_khach_nhom'].notna().all() and m['ten_khach_hang_nhom'].notna().all()
    assert m['co_ma_khach_chinh_thuc'].equals(m['ma_khach'].notna() & m['ma_khach_hang'].notna())
    threshold = fit_item_outlier_threshold(m)
    np.testing.assert_allclose(m['outlier_stat_threshold_km'], threshold)
    assert m['nghi_ngo_outlier'].equals(item_outlier_mask(m, threshold))
    cable = m[sales_km(m) & ~m['nghi_ngo_outlier']]
    assert np.isclose(cable.groupby(['ma_khach_nhom', 'ten_khach_hang_nhom'])['so_luong_km'].sum().sum(), cable['so_luong_km'].sum())
    return cable


def snapshot_regression(h, i, m):
    """Original fixture values are immutable; additional source data disable only this snapshot."""
    before = FIXTURES
    expected = json.loads((before / 'expectations.json').read_text(encoding='utf-8'))
    manifest = json.loads((before / 'source_manifest.json').read_text(encoding='utf-8'))
    current = {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in RAW.glob('*.xlsx')}
    if current != manifest:
        print('[INFO] Current dataset regression: NOT APPLICABLE (source changed); invariants/business checks still required')
        return 'NOT_APPLICABLE_SOURCE_CHANGED'
    assert len(h) == expected['orders'], 'Current dataset regression expectation: orders'
    assert len(i) == expected['items'], 'Current dataset regression expectation: items'
    old_h = pd.read_csv(before / 'fact_order_header.csv')
    old_i = pd.read_csv(before / 'fact_order_items.csv')
    protected = [c for c in old_h.columns if c != 'ngay_nam_khong_khop_file']
    pd.testing.assert_frame_equal(h[protected], old_h[protected], check_dtype=False)
    # Frozen source fields remain invariant. Parser-derived codes/prices are verified
    # against independent semantic regression cases, independently of derived fixture columns.
    source_columns = ['item_id', 'order_row_id', 'order_source_row_id', 'item_text_raw', 'parsed', 'so_luong', 'don_vi', 'so_luong_km']
    pd.testing.assert_frame_equal(i[source_columns], old_i[source_columns], check_dtype=False)
    old_m = pd.read_csv(before / 'mart_order_items.csv')
    for column in ('so_luong_km', 'nghi_ngo_outlier', 'ma_khach_nhom'):
        pd.testing.assert_series_equal(m[column], old_m[column], check_dtype=False)
    rates = h[h['loai_don'].eq('Đơn khách hàng - Cáp quang')].groupby(h['order_year'].astype(str))['wo'].apply(lambda s: round(s.notna().mean()*100,1)).to_dict()
    assert rates == expected['wo_rate_by_year'], 'Current dataset regression expectation: WO rates'
    assert h['loai_don_tu_so_hop_dong'].sum() == expected['orders_classified_from_contract']
    return 'PASS'


def validate_forecast(m: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    """Validate the final forecast and separation of validation/holdout outputs."""
    forecast = pd.read_csv(TAB / 'forecast.csv')
    detail = pd.read_csv(TAB / 'forecast_backtest.csv')
    comparison = pd.read_csv(TAB / 'forecast_model_comparison.csv')
    test = pd.read_csv(TAB / 'forecast_holdout.csv')
    method = json.loads((TAB / 'forecast_methodology.json').read_text(encoding='utf-8'))
    history_last = observation_months(m)[-1]
    assert forecast['thang'].tolist() == pd.period_range(history_last+1, periods=FORECAST_HORIZON, freq='M').astype(str).tolist()
    assert np.isfinite(forecast['du_bao_km']).all() and forecast['du_bao_km'].ge(0).all()
    assert detail['validation_end'].lt(method['test_start']).all()
    assert detail['diem_cat'].lt(detail['validation_start']).all()
    assert not method['holdout_used_for_tuning'] and not method['pipeline_holdout_leakage']
    assert method['historical_external_exposure'] == HISTORICAL_EXTERNAL_EXPOSURE
    assert comparison['folds'].nunique() == 1 and len(comparison) >= 2
    assert forecast['mo_hinh'].eq(comparison.iloc[0]['mo_hinh']).all()
    assert len(test) == method['evaluation_horizon'] and test['thang'].iloc[0] == method['test_start']
    denom = test['actual_km'].abs().sum()
    if denom > WAPE_EPSILON:
        assert np.isclose(method['test_wape_pct'], (test['actual_km']-test['prediction_km']).abs().sum()/denom*100)
    else:
        assert method['test_wape_pct'] is None
    holdout_comparison = pd.read_csv(TAB / 'forecast_holdout_comparison.csv')
    assert set(holdout_comparison['mo_hinh']) == set(comparison['mo_hinh'])
    assert holdout_comparison['selected_on_validation'].sum() == 1
    assert holdout_comparison.loc[holdout_comparison['selected_on_validation'],'mo_hinh'].iloc[0] == method['selected_model']
    return forecast, method


def main():
    h, i, m = [pd.read_csv(PROC / name) for name in ('fact_order_header.csv', 'fact_order_items.csv', 'mart_order_items.csv')]
    validate_integrity(h, i, m)
    cleaner = importlib.import_module('02_clean_orders')
    reconcile_orders(cleaner, cleaner.load_raw_orders(), h, i)
    products = pd.read_csv(PROC/'fact_product_items.csv')
    validate_allocation(i, products)
    for frame in [i, products]:
        validate_product_semantics(frame, reference_codes(PROC))
    product_mart = pd.read_csv(PROC/'mart_product_items.csv')
    assert set(product_mart.product_item_id) == set(products.product_item_id)
    assert product_mart.product_item_id.is_unique
    pd.testing.assert_frame_equal(product_mart[products.columns], products, check_dtype=False)
    expected_conflict = h.order_month_from_date.notna() & h.order_month_from_code.notna() & h.order_month_from_date.ne(h.order_month_from_code)
    assert h.order_month_conflict.equals(expected_conflict)
    assert h.order_month_canonical.equals(h.order_month)

    cable = validate_business(m)
    duplicate_candidates = m[m.duplicated(['order_row_id','item_text_raw','so_luong','don_vi'], keep=False)]
    duplicate_candidates.to_csv(TAB/'duplicate_item_candidates.csv',index=False,encoding='utf-8-sig')
    if not duplicate_candidates.empty:
        print(f'[WARNING] {len(duplicate_candidates)} item rows share order/text/quantity/unit; distinct source IDs retained pending business review.')
    snapshot = snapshot_regression(h, i, m)
    forecast, method = validate_forecast(m)
    eda = json.loads((TAB/'eda_summary.json').read_text(encoding='utf-8'))
    assert eda['tong_so_dong_don_hang'] == len(h)
    metrics = unpriced_metrics(m)
    assert np.isclose(metrics['unpriced_km_sales_total'], metrics['unpriced_km_sales_non_outlier']+metrics['unpriced_km_sales_outlier'])
    for key, val in metrics.items():
        assert eda[key] == val
    monthly = pd.read_csv(TAB/'monthly_km.csv')
    assert np.isclose(monthly['so_luong_km'].sum(), cable['so_luong_km'].sum())
    abc = pd.read_csv(TAB/'abc_product_code.csv')
    assert np.isclose(abc['so_luong_km'].sum(), product_mart.loc[sales_km(product_mart) & ~product_mart.nghi_ngo_outlier & product_mart.is_reference_product_code, 'so_luong_km'].sum())
    for fig in (ROOT/'outputs/figures').glob('*.png'):
        assert fig.stat().st_size > 1000
    checks = dict(status='PASS', data_invariants='PASS', business_validations='PASS',
                  current_dataset_regression=snapshot, orders=len(h), items=len(i),
                  canonical_product_rows=len(products),
                  exact_product_rows=int(products.is_reference_product_code.sum()),
                  generic_product_rows=int(products.parse_status.eq("recognized_generic").sum()),
                  ambiguous_product_rows=int(i.parse_status.eq("ambiguous").sum()), quantity_conservation='PASS per source row and unit',
                  unresolved_rows=int(i.allocation_status.eq('unresolved').sum()),
                  unresolved_multi_product_rows=int((i.allocation_status.eq('unresolved') & i.product_candidates.fillna('').str.contains(' | ', regex=False)).sum()),
                  unmapped_product_rows=int(i.parse_status.eq('unmapped').sum()),
                  month_conflict_orders=int(h.order_month_conflict.sum()),
                  duplicate_order_ids=int(h['order_row_id'].duplicated().sum()),
                  duplicate_item_ids=int(i['item_id'].duplicated().sum()), orphan_items=0,
                  duplicate_item_candidate_rows=len(duplicate_candidates),
                  missing_dates=int(h['ngay_bi_thieu'].sum()), invalid_dates=int(h['ngay_khong_hop_le'].sum()),
                  year_mismatches=int(h['ngay_nam_khong_khop_file'].sum()),
                  missing_quantity=int(i['so_luong'].isna().sum()), missing_customer_code=int(h['ma_khach'].isna().sum()),
                  missing_product_code=int(i['parsed_product_token'].isna().sum()),
                  outlier_grain='item', outlier_rows=int(m['nghi_ngo_outlier'].sum()),
                  outlier_orders=int(m.loc[m['nghi_ngo_outlier'],'order_row_id'].nunique()),
                  outlier_threshold_km=float(m['outlier_stat_threshold_km'].iloc[0]),
                  sales_km_raw=float(m.loc[sales_km(m),'so_luong_km'].sum()),
                  sales_km_non_outlier=float(cable['so_luong_km'].sum()),
                  forecast_total_km=float(forecast['du_bao_km'].sum()), forecast_methodology=method, **metrics)
    write_json(TAB/'pipeline_validation.json', checks)
    print('[PASS] Full pipeline validation')
    print(f'Orders={len(h)}, items={len(i)}, snapshot={snapshot}; details: pipeline_validation.json')


if __name__ == '__main__':
    main()
