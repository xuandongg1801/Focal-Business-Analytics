"""Regression tests. Mutations are in-memory test inputs, never production data."""
import importlib.util
from pathlib import Path
import sys
import unittest
from datetime import datetime, timezone
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'scripts'))
sys.path.insert(0, str(ROOT))
from config import FORECAST_HORIZON, CONFIRMED_PROJECT_ORDERS
from data_rules import monthly_series, observation_months, fit_item_outlier_threshold, item_outlier_mask, abc_labels
from forecasting import run_forecast, temporal_plan, prepare_split, wape
from prospective import freeze_record, evaluate_record


def load_script(name):
    spec = importlib.util.spec_from_file_location(name, ROOT/'scripts'/f'{name}.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class PipelineTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.clean = load_script('02_clean_orders')
        cls.validate = load_script('06_validate_pipeline')
        cls.raw = cls.clean.load_raw_orders()
        cls.h = pd.read_csv(ROOT/'data/processed/fact_order_header.csv')
        cls.i = pd.read_csv(ROOT/'data/processed/fact_order_items.csv')
        cls.m = pd.read_csv(ROOT/'data/processed/mart_order_items.csv')

    def test_normalized_items_preserve_rows(self):
        self.assertEqual(len(self.clean.build_items(self.raw)), len(self.raw))

    def test_invalid_normalization(self):
        for flag in (False, None, 'True'):
            raw = self.raw.head(2).copy()
            raw['raw_item_already_normalized'] = flag
            with self.assertRaisesRegex(ValueError, 'normalized'):
                self.clean.build_items(raw)
        with self.assertRaises(ValueError):
            self.clean.build_items(self.raw.drop(columns='raw_item_already_normalized'))

    def test_invalid_quantity(self):
        for value in (-1, np.inf, 'bad-number'):
            raw = self.raw.head(1).copy()
            raw['so_luong'] = value
            with self.assertRaises(ValueError):
                self.clean.build_items(raw)

    def test_duplicate_source_id_rejected(self):
        raw = pd.concat([self.raw.head(1)]*2, ignore_index=True)
        with self.assertRaises(ValueError):
            self.clean.build_items(raw)

    def test_missing_date_is_not_mismatch(self):
        raw = self.raw.head(3).copy()
        year = int(raw.iloc[0]['nam_file'])
        raw['ngay'] = pd.Series([None, f'01/02/{year+1}', 'not-a-date'], index=raw.index)
        result = self.clean.clean_header(raw)
        self.assertEqual(result['ngay_bi_thieu'].tolist(), [True, False, False])
        self.assertEqual(result['ngay_nam_khong_khop_file'].tolist(), [False, True, False])
        self.assertEqual(result['ngay_khong_hop_le'].tolist(), [False, False, True])

    def test_header_rejects_unresolvable_month(self):
        for date in (None, 'not-a-date'):
            with self.subTest(date=date):
                raw = self.raw.head(1).copy()
                raw['so_xac_nhan_don_hang'] = 'INVALID_TEST_CODE'
                raw['ngay'] = date
                with self.assertRaisesRegex(ValueError, 'order_month rỗng.*INVALID_TEST_CODE'):
                    self.clean.clean_header(raw)

    def test_header_month_fallbacks(self):
        for code, date, expected in (
            ('INVALID_TEST_CODE', '01/02/2026', '2026-02'),
            ('CA-001/2603/TEST', None, '2026-03'),
            ('CA-001/2603/TEST', 'not-a-date', '2026-03'),
            ('CA-001/2603/TEST', '01/02/2026', '2026-02'),
        ):
            with self.subTest(code=code, date=date):
                raw = self.raw.head(1).copy()
                raw['nam_file'] = 2026
                raw['so_xac_nhan_don_hang'] = code
                raw['ngay'] = date
                result = self.clean.clean_header(raw)
                self.assertEqual(result['order_month'].iloc[0], expected)
                self.assertEqual(result['order_year'].iloc[0], '2026')

    def test_mart_rejects_missing_month_or_year(self):
        mart = load_script('03_build_mart')
        for column in ('order_month', 'order_year'):
            with self.subTest(column=column):
                header = self.h.copy()
                header[column] = None
                with self.assertRaisesRegex(ValueError, 'order_month/order_year rỗng'):
                    mart.build_mart(self.i, header, pd.DataFrame(), pd.DataFrame())

    def test_integrity(self):
        self.validate.validate_integrity(self.h, self.i, self.m)

    def test_duplicate_header_rejected(self):
        with self.assertRaises(AssertionError):
            self.validate.validate_integrity(pd.concat([self.h,self.h.head(1)]), self.i,self.m)

    def test_orphan_rejected(self):
        items = self.i.copy()
        items.loc[0,'order_row_id'] = -1
        with self.assertRaises(AssertionError):
            self.validate.validate_integrity(self.h,items,self.m)

    def test_merge_multiplication_rejected(self):
        with self.assertRaises(AssertionError):
            self.validate.validate_integrity(self.h,self.i,pd.concat([self.m,self.m.head(1)]))

    def test_item_grain_threshold(self):
        mask = self.m['la_don_ban_hang'] & self.m['so_luong_km'].notna() & ~self.m['so_xac_nhan_don_hang'].isin(CONFIRMED_PROJECT_ORDERS)
        vals = np.log1p(self.m.loc[mask,'so_luong_km'])
        q1,q3 = vals.quantile([.25,.75])
        self.assertAlmostEqual(fit_item_outlier_threshold(self.m), np.expm1(q3+3*(q3-q1)))
        self.assertAlmostEqual(fit_item_outlier_threshold(self.m),fit_item_outlier_threshold(self.m.sample(frac=1,random_state=7)))
        self.assertTrue(item_outlier_mask(self.m,fit_item_outlier_threshold(self.m)).equals(self.m['nghi_ngo_outlier']))

    def test_confirmed_values(self):
        self.validate.validate_business(self.m)

    def test_forecast_dynamic_horizon(self):
        for h in (1,FORECAST_HORIZON,9):
            result = run_forecast(self.m,h)
            self.assertEqual(len(result['future']),h)
            self.assertEqual(result['future'][0],monthly_series(self.m).index[-1]+1)

    def test_extended_history_and_project_only_last_month(self):
        # Shift genuine rows in a test copy only; no source/output dataset changes.
        tail = self.m[self.m['so_xac_nhan_don_hang'].isin(CONFIRMED_PROJECT_ORDERS)].head(1).copy()
        tail['order_month'] = '2026-09'
        result = run_forecast(pd.concat([self.m,tail],ignore_index=True))
        self.assertEqual(str(result['future'][0]),'2026-10')
        self.assertEqual(str(result['future'][-1]),'2027-03')

    def test_holdout_cannot_change_selection(self):
        original = run_forecast(self.m)
        changed = self.m.copy()
        mask = changed['order_month'].ge(original['metrics']['test_start'])
        changed.loc[mask,'so_luong_km'] *= 17
        changed.loc[mask,'nghi_ngo_outlier'] = ~changed.loc[mask,'nghi_ngo_outlier']
        other = run_forecast(changed)
        pd.testing.assert_frame_equal(original['detail'],other['detail'])
        pd.testing.assert_frame_equal(original['comparison'],other['comparison'])
        self.assertEqual(original['metrics']['selected_model'],other['metrics']['selected_model'])

    def test_future_does_not_enter_training_or_threshold(self):
        idx = monthly_series(self.m).index
        origin = temporal_plan(len(idx))[0][0]
        a = prepare_split(self.m,idx,origin,6)
        changed = self.m.copy()
        changed.loc[changed['order_month'].ge(str(idx[origin])),'so_luong_km'] *= 100
        b = prepare_split(changed,idx,origin,6)
        np.testing.assert_array_equal(a[0],b[0])
        self.assertEqual(a[2],b[2])

    def test_full_mart_flags_not_used_for_forecast(self):
        changed = self.m.copy()
        changed['nghi_ngo_outlier'] = ~changed['nghi_ngo_outlier']
        a,b = run_forecast(self.m),run_forecast(changed)
        pd.testing.assert_frame_equal(a['detail'],b['detail'])
        np.testing.assert_array_equal(a['forecast'],b['forecast'])

    def test_temporal_plan_short_history(self):
        for n in (5,8,12,18,24,36,45):
            origins,test,h = temporal_plan(n)
            self.assertTrue(all(o > 0 and o+h <= test for o in origins))
            self.assertEqual(test+h,n)
        with self.assertRaises(ValueError):
            temporal_plan(4)

    def test_wape_zero_is_undefined(self):
        self.assertTrue(np.isnan(wape(np.zeros(3),np.ones(3))))
        self.assertTrue(np.isnan(wape(np.full(3,1e-15),np.ones(3))))

    def test_missing_months_are_zero_and_short_run_is_explicit(self):
        original = self.m[self.m['order_month'].between('2023-01','2023-08')].copy()
        original = original[original['order_month'].ne('2023-04')]
        series = monthly_series(original)
        self.assertEqual(series.loc[pd.Period('2023-04')],0)
        result = run_forecast(original)
        self.assertEqual(len(result['future']),FORECAST_HORIZON)
        self.assertTrue(any('Short history' in text for text in result['metrics']['limitations']))

    def test_zero_series_reports_null_test_wape(self):
        zero = self.m.copy()
        zero['so_luong_km'] = 0.0
        result = run_forecast(zero)
        self.assertIsNone(result['metrics']['test_wape_pct'])
        self.assertTrue(np.isfinite(result['forecast']).all())

    def test_price_ranges_reject_invalid_numbers(self):
        mart = load_script('03_build_mart')
        price = pd.read_csv(ROOT/'data/processed/dim_price_list.csv')
        price.loc[0,'gia_cap_1'] = -1
        with self.assertRaises(ValueError):
            mart.price_ranges(price)

    def test_abc_dominant_item_is_a(self):
        self.assertEqual(abc_labels(pd.Series([90,6,4])).tolist(),['A','B','C'])

    def test_import_all_stages(self):
        before = set(ROOT.glob('outputs/**/*'))
        for path in (ROOT/'scripts').glob('[0-9][0-9]_*.py'):
            load_script(path.stem)
        self.assertEqual(before, set(ROOT.glob('outputs/**/*')))

    def test_observation_calendar_includes_outlier_only_last_month(self):
        tail = self.m[self.m['nghi_ngo_outlier']].head(1).copy()
        tail['order_month'] = '2026-09'
        extended = pd.concat([self.m,tail],ignore_index=True)
        result = run_forecast(extended)
        self.assertEqual(str(observation_months(extended)[-1]), '2026-09')
        self.assertEqual(str(result['future'][0]), '2026-10')
        self.assertEqual(result['baseline'].iloc[-1], 0)

    def test_monthly_series_excludes_non_sales(self):
        sales = self.m[self.m['la_don_ban_hang']]
        pd.testing.assert_series_equal(monthly_series(self.m),monthly_series(sales))

    def test_all_candidates_share_validation_and_test_windows(self):
        result = run_forecast(self.m)
        self.assertIn('Historical Mean', set(result['comparison']['mo_hinh']))
        grouped = result['detail'].groupby('diem_cat')
        self.assertTrue(grouped['actual_km'].nunique().eq(1).all())
        self.assertTrue(grouped['outlier_threshold_km'].nunique().eq(1).all())
        self.assertEqual(set(result['comparison']['mo_hinh']),set(result['holdout_comparison']['mo_hinh']))
        self.assertFalse(result['metrics']['holdout_used_for_tuning'])

    def test_prospective_rejects_retroactive_and_incomplete_months(self):
        forecast = pd.DataFrame({'thang':['2026-01','2026-02'], 'du_bao_km':[1.0,1.0]})
        method = {'history_end':'2025-12','selected_model':'test fixture','final_threshold_km':1e6,
                  'confirmed_project_orders':[]}
        record = freeze_record(forecast,method,datetime(2026,2,10,tzinfo=timezone.utc))
        rows,status = evaluate_record(record,self.m,'2026-02',datetime(2026,3,1,tzinfo=timezone.utc))
        self.assertTrue(rows.empty)
        self.assertEqual(status['status'],'NO_COMPLETED_PROSPECTIVE_MONTHS')
        with self.assertRaises(ValueError):
            evaluate_record(record,self.m,'2026-03',datetime(2026,3,1,tzinfo=timezone.utc))

    def test_prospective_uses_frozen_rule_without_refitting(self):
        # Only test copies are shifted; no fabricated actuals enter project files.
        forecast = pd.DataFrame({'thang':['2026-02'],'du_bao_km':[2.0]})
        method = {'history_end':'2025-12','selected_model':'test fixture','final_threshold_km':10,
                  'confirmed_project_orders':[]}
        record = freeze_record(forecast,method,datetime(2026,1,1,tzinfo=timezone.utc))
        actual = self.m[self.m['la_don_ban_hang']].head(2).copy()
        actual['order_month'] = '2026-02'
        actual['so_luong_km'] = [5.0,100.0]
        rows,status = evaluate_record(record,actual,'2026-02',datetime(2026,3,1,tzinfo=timezone.utc))
        self.assertEqual(rows['actual_baseline_km'].iloc[0],5)
        self.assertAlmostEqual(status['wape_pct'],60)

    def test_unmatched_customer_and_unconfirmed_price_year(self):
        mart = load_script('03_build_mart')
        header = self.h.copy()
        header['ma_khach'] = 'UNKNOWN_TEST_CODE'
        header['order_year'] = 2099
        built = mart.build_mart(self.i,header,
            pd.read_csv(ROOT/'data/processed/dim_customer.csv'),pd.read_csv(ROOT/'data/processed/dim_price_list.csv'))
        self.assertFalse(built['co_ma_khach_chinh_thuc'].any())
        self.assertTrue(built['ma_khach_nhom'].notna().all())
        self.assertTrue(built['gia_tri_uoc_tinh'].isna().all())
        np.testing.assert_allclose(built['so_luong_km'],self.i['so_luong_km'],equal_nan=True)


if __name__ == '__main__':
    unittest.main()
