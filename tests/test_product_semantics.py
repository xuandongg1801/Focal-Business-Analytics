"""Reference-code semantics and dtype portability regressions."""
import importlib
from pathlib import Path
import sys
import unittest
import warnings
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'scripts'))
from products import parse_product, product_semantics, validate_product_semantics, reference_codes
from data_contract import semantic_dtype


class ProductSemanticTests(unittest.TestCase):
    references = {'FTTH02-LT', 'FTTH02-SQ', 'FE06'}

    def test_exact_master_match(self):
        p = parse_product('FE06', 2, 'KM', self.references)
        self.assertEqual(p.parse_status, 'exact_reference')
        self.assertEqual(product_semantics(p.codes[0], p.parse_status, self.references)['canonical_product_code'], 'FE06')

    def test_bare_spec_never_selects_a_variant(self):
        for refs in [self.references, {'FTTH02-LT'}]:
            p = parse_product('FTTH02', 2, 'KM', refs)
            self.assertEqual(p.parse_status, 'recognized_generic')
            fields = product_semantics(p.codes[0], p.parse_status, refs)
            self.assertIsNone(fields['canonical_product_code'])
            self.assertFalse(fields['is_reference_product_code'])
            self.assertEqual(fields['product_family_code'], 'FTTH02')

    def test_unique_explicit_normalization(self):
        for raw, expected in [('ftth 2 / lt', 'FTTH02-LT'), ('FTTH02 (LỎNG)', 'FTTH02-LT'), ('FTTH SQ 2FO', 'FTTH02-SQ')]:
            p = parse_product(raw, 2, 'KM', self.references)
            self.assertEqual(p.parse_status, 'exact_reference')
            self.assertEqual(p.codes, (expected,))

    def test_unknown_and_conflicting_qualifiers(self):
        self.assertEqual(parse_product('FTTH99', 2, 'KM', self.references).parse_status, 'unmapped')
        p = parse_product('FTTH02-LT (CHẶT)', 2, 'KM', self.references)
        self.assertEqual(p.parse_status, 'ambiguous')
        self.assertFalse(p.allocations)

    def test_unresolved_multiple_is_not_reference(self):
        p = parse_product('FE06 FTTH02-LT', 2, 'KM', self.references)
        self.assertEqual(p.parse_status, 'unresolved_multiple')
        self.assertEqual(p.allocations, ())
        self.assertIsNone(product_semantics(None, p.parse_status, self.references)['canonical_product_code'])

    def test_split_references_and_generic_keep_separate_levels(self):
        p = parse_product('FE06: 2 KM; FTTH02: 3 KM', 5, 'KM', self.references)
        self.assertEqual(p.allocations, (('FE06', 2), ('FTTH02', 3)))
        self.assertEqual(p.parse_status, 'allocated_multiple')
        cleaner = importlib.import_module('02_clean_orders')
        items = pd.read_csv(ROOT/'data/processed/fact_order_items.csv').head(1).copy()
        items['item_text_raw'] = 'FE06: 2 KM; FTTH02: 3 KM'
        items['so_luong'] = 5.; items['don_vi'] = 'KM'; items['allocation_status'] = 'split'
        products = cleaner.build_product_items(items)
        self.assertEqual(products.parse_status.tolist(), ['exact_reference', 'recognized_generic'])
        self.assertEqual(products.so_luong.sum(), 5)
        self.assertTrue(pd.isna(products.canonical_product_code.iloc[1]))
        validate_product_semantics(products, reference_codes(ROOT/'data/processed'))

    def test_generic_cannot_leak_into_reference_rankings(self):
        from approval_prediction.app.utils.analytics import AnalyticsData, product_totals
        products = pd.DataFrame({'canonical_product_code':['FE06', None], 'parsed_product_token':['FE06','FTTH02'],
            'product_family_code':['FE06','FTTH02'], 'nhom_san_pham_don_hang':['FE','FTTH'],
            'is_reference_product_code':[True, False], 'parse_status':['exact_reference','recognized_generic'], 'so_luong_km':[2.,100.]})
        data = AnalyticsData(pd.DataFrame(), pd.DataFrame(), products, pd.DataFrame())
        self.assertEqual(product_totals(data).KM.sum(), 2.)
        self.assertEqual(product_totals(data,'generic').KM.sum(), 100.)
        self.assertEqual(product_totals(data,'family').KM.sum(), 102.)

    def test_actual_contract_and_corrupted_generic(self):
        items = pd.read_csv(ROOT/'data/processed/fact_product_items.csv')
        refs = reference_codes(ROOT/'data/processed')
        validate_product_semantics(items, refs)
        idx = items.index[items.parse_status.eq('recognized_generic')][0]
        broken = items.copy(); broken.loc[idx,'canonical_product_code'] = 'FTTH02-LT'
        with self.assertRaisesRegex(ValueError,'Non-reference'):
            validate_product_semantics(broken, refs)

    def test_all_null_codes_have_string_semantics(self):
        self.assertEqual(semantic_dtype('canonical_product_code'), 'string')
        self.assertEqual(semantic_dtype('parsed_product_token'), 'string')
        for file in (ROOT/'data/processed').glob('*.csv'):
            for column in pd.read_csv(file,nrows=0):
                self.assertIsInstance(semantic_dtype(column),str)

    def test_month_cleaning_with_missing_codes_has_no_downcast_warning(self):
        cleaner = importlib.import_module('02_clean_orders')
        raw = cleaner.load_raw_orders().head(3).copy()
        raw['so_xac_nhan_don_hang'] = ['not a date code']*3
        raw['ngay'] = ['15/01/2023']*3
        raw['nam_file'] = 2023
        with warnings.catch_warnings():
            warnings.simplefilter('error', FutureWarning)
            result = cleaner.clean_header(raw)
        self.assertEqual(result.order_month.tolist(), ['2023-01']*3)
        self.assertEqual(str(result.order_month.dtype), 'string')

    def test_trend_contract_accepts_decreasing_orders(self):
        from approval_prediction.config import FEATURE_DOMAINS
        self.assertIn('signed', FEATURE_DOMAINS['prior_monthly_order_trend'][0])
        self.assertIn('<0 decreasing', FEATURE_DOMAINS['prior_monthly_order_trend'][0])


    def test_reference_abc_and_conserved_denominator(self):
        import numpy as np
        mart = pd.read_csv(ROOT/'data/processed/mart_product_items.csv')
        subset = mart[mart.la_don_ban_hang & ~mart.nghi_ngo_outlier & mart.is_reference_product_code]
        abc = pd.read_csv(ROOT/'outputs/tables/abc_product_code.csv')
        self.assertEqual(set(abc.canonical_product_code),set(subset.loc[subset.so_luong_km.notna(),'canonical_product_code']))
        self.assertTrue(np.isclose(abc.so_luong_km.sum(),subset.so_luong_km.sum()))
        ledger = pd.read_csv(ROOT/'data/processed/mart_order_items.csv')
        total = ledger.loc[ledger.la_don_ban_hang & ~ledger.nghi_ngo_outlier,'so_luong_km'].sum()
        generic = mart.loc[mart.la_don_ban_hang & ~mart.nghi_ngo_outlier & ~mart.is_reference_product_code, 'so_luong_km'].sum()
        unresolved = ledger.loc[ledger.la_don_ban_hang & ~ledger.nghi_ngo_outlier & ledger.allocation_status.eq('unresolved'), 'so_luong_km'].sum()
        excluded = generic + unresolved
        self.assertTrue(np.isclose(total,abc.so_luong_km.sum()+excluded))
