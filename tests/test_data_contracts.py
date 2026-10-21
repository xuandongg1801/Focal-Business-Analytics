"""Adversarial integrity and semantic regression tests with unchanged real RAW."""
import importlib
from io import StringIO
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'scripts'))
from products import normalize_product_token, parse_product, validate_allocation
from reconciliation import reconcile_orders
from segmentation import relative_score, segment_labels, LABEL_RECENT, LABEL_INACTIVE, LABEL_FREQUENT, LABEL_OTHER


class ProductTests(unittest.TestCase):
    def test_ftth_semantic_variants(self):
        for core in [1, 2, 4, 6, 8, 12]:
            code = f'FTTH{core:02d}-LT'
            for value in [code, code.lower(), f' FTTH {core} / LT ', f'FTTH{core:02d} (LỎNG)', f'FTTH{core:02d} [lỏng]', f'FTTH{core:02d}—LT']:
                with self.subTest(value=value):
                    self.assertEqual(normalize_product_token(value), code)
            self.assertEqual(normalize_product_token(code), normalize_product_token(normalize_product_token(code)))
        self.assertEqual(normalize_product_token('FTTH SQ 2FO'), 'FTTH02-SQ')
        self.assertEqual(normalize_product_token('ÉP CHẶT 1'), 'FTTH01-SQ')
        self.assertIsNone(normalize_product_token('FTTH02-LT (CHẶT)'))

    def test_prefix_and_reference_boundaries(self):
        for value in ['XFTTH02', 'FTTH02XYZ', 'FTTH020', 'FTTH02-LTXYZ', 'XFEAM06', 'UNKNOWN123']:
            self.assertIsNone(normalize_product_token(value), value)
        self.assertEqual(normalize_product_token('FEAM06'), 'FEAM06')
        self.assertEqual(normalize_product_token('DUAM12'), 'DUAM12')
        self.assertEqual(parse_product('DU999', 5, 'KM', {'DU24'}).parse_status, 'unmapped')

    def test_multiple_codes_are_never_first_match(self):
        for text in ['FEM06 VÀ FEAM06', 'DU24 FTTH04', 'DU48 IN DU24 (BIN 4.500 + 3.000)', 'DUA12 (CÁP CŨ DUA24)']:
            result = parse_product(text, 40, 'KM')
            self.assertEqual(result.allocation_status, 'unresolved')
            self.assertEqual(result.allocations, ())
            self.assertIsNone(normalize_product_token(text))

    def test_explicit_allocation_conserves_and_normalizes_units(self):
        result = parse_product('FEM06: 2 KM; FEAM06: 3000 M', 5, 'KM')
        self.assertEqual(result.allocation_status, 'split')
        self.assertEqual(result.allocations, (('FEM06', 2), ('FEAM06', 3)))
        for amount in [4, 6, np.nan]:
            self.assertEqual(parse_product('FEM06: 2 KM; FEAM06: 3 KM', amount, 'KM').allocation_status, 'unresolved')
        self.assertEqual(parse_product('FEM06: 2 KG; FEAM06: 3 KM', 5, 'KM').allocation_status, 'unresolved')

    def test_conservation_catches_duplicate_loss_and_orphan(self):
        source = pd.DataFrame(dict(item_id=[1, 2, 3], so_luong=[5, 7, np.nan],
                                   don_vi=['KM']*3, allocation_status=['split', 'unresolved', 'single']))
        products = pd.DataFrame(dict(item_id=[1, 1, 3], product_item_id=['1:1', '1:2', '3:1'],
            parsed_product_token=['FE04', 'FE06', 'DU12'], so_luong=[2, 3, np.nan], don_vi=['KM']*3))
        result = validate_allocation(source, products).iloc[0]
        self.assertEqual(result.original_quantity, 12)
        self.assertEqual(result.resolved_quantity, 5)
        self.assertEqual(result.unresolved_quantity, 7)
        self.assertEqual(result.missing_quantity, 1)
        for bad in [products.iloc[1:], pd.concat([products, products.head(1)]), products.assign(item_id=99), products.assign(so_luong=10)]:
            with self.assertRaises(ValueError):
                validate_allocation(source, bad)


class ReconciliationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cleaner = importlib.import_module('02_clean_orders')
        cls.raw = cls.cleaner.load_raw_orders()
        h, i = cls.cleaner.build_order_tables(cls.raw)
        cls.h = pd.read_csv(StringIO(h.to_csv(index=False)))
        cls.i = pd.read_csv(StringIO(i.to_csv(index=False)))

    def check(self, raw=None, h=None, i=None):
        return reconcile_orders(self.cleaner, self.raw if raw is None else raw,
                                self.h if h is None else h, self.i if i is None else i)

    def test_complete_reconciliation(self):
        self.assertEqual(self.check(), len(self.raw))

    def test_missing_processed_row_changes_target_and_fails(self):
        from approval_prediction.target import read_source_fields, item_labels, aggregate_target
        item = self.i[self.i.item_id.eq(241)].iloc[0]
        original = read_source_fields(self.i[self.i.order_row_id.eq(item.order_row_id)])
        changed = original[original.item_id.ne(241)]
        self.assertNotEqual(aggregate_target(item_labels(original).item_target), aggregate_target(item_labels(changed).item_target))
        with self.assertRaisesRegex(ValueError, 'key coverage mismatch'):
            self.check(i=self.i[self.i.item_id.ne(241)])

    def test_extra_processed_row(self):
        extra = self.i.head(1).assign(item_id=99999, source_excel_row=99999)
        with self.assertRaisesRegex(ValueError, 'key coverage mismatch'):
            self.check(i=pd.concat([self.i, extra], ignore_index=True))

    def test_duplicate_physical_key(self):
        with self.assertRaisesRegex(ValueError, 'duplicate keys'):
            self.check(i=pd.concat([self.i, self.i.head(1)], ignore_index=True))

    def test_changed_raw_customer(self):
        raw = self.raw.copy()
        raw.loc[raw.so_xac_nhan_don_hang.eq(raw.iloc[0].so_xac_nhan_don_hang), 'ma_khach'] = 'KH_TEST'
        with self.assertRaisesRegex(ValueError, 'ma_khach'):
            self.check(raw=raw)

    def test_changed_product_quantity_unit_key_composition(self):
        for field, value in [('item_text_raw', 'BÁO GIÁ'), ('so_luong', 987654.),
                             ('don_vi', 'KG'), ('parsed_product_token', 'DU24'), ('order_row_id', 99999),
                             ('order_source_row_id', 99999), ('parsed', False)]:
            with self.subTest(field=field):
                changed = self.i.copy()
                changed.loc[0, field] = value
                with self.assertRaisesRegex(ValueError, 'field mismatch'):
                    self.check(i=changed)

    def test_changed_header_fields(self):
        for field, value in [('order_month', '2099-01'), ('ma_khach', 'KH_TEST'), ('la_don_ban_hang', False), ('ngay_dt', '2099-01-01')]:
            with self.subTest(field=field):
                changed = self.h.copy()
                changed.loc[0, field] = value
                with self.assertRaisesRegex(ValueError, 'field mismatch'):
                    self.check(h=changed)

    def test_integrity_gate_precedes_target_or_writes(self):
        from approval_prediction.data import build_target
        with patch('reconciliation.reconcile_orders', side_effect=ValueError('integrity failed')), patch('approval_prediction.data.item_labels') as labels:
            with self.assertRaisesRegex(ValueError, 'integrity failed'):
                build_target(ROOT/'.cache/nonexistent_test_output')
            labels.assert_not_called()

    def test_month_conflict_retains_both_and_rule(self):
        raw = self.raw.head(1).copy()
        raw['nam_file'] = 2025
        raw['ngay'] = '01/02/2025'
        raw['so_xac_nhan_don_hang'] = 'CA-01/2501/TEST'
        row = self.cleaner.clean_header(raw).iloc[0]
        self.assertEqual(row.order_month_from_code, '2025-01')
        self.assertEqual(row.order_month_from_date, '2025-02')
        self.assertEqual(row.order_month_canonical, '2025-02')
        self.assertTrue(row.order_month_conflict)
        self.assertEqual(row.order_month_rule, 'date_in_file_year')


class SegmentationTests(unittest.TestCase):
    def test_score_direction_and_ties(self):
        values = pd.Series([0, 1, 2, 3])
        self.assertEqual(relative_score(values, True).tolist(), [1, 2, 3, 4])
        self.assertEqual(relative_score(values, False).tolist(), [4, 3, 2, 1])
        self.assertEqual(relative_score(pd.Series([2, 2, 2]), True).nunique(), 1)
        self.assertEqual(relative_score(pd.Series([0]), False).iloc[0], 4)
        with self.assertRaises(ValueError): relative_score(pd.Series([-1]), True)

    def test_labels_at_boundaries(self):
        scores = pd.DataFrame({'r_score':[1, 2, 3, 4], 'f_score':[4, 3, 3, 2], 'v_score':[4, 4, 3, 4]})
        self.assertEqual(segment_labels(scores).tolist(), [LABEL_INACTIVE, LABEL_FREQUENT, LABEL_RECENT, LABEL_OTHER])


if __name__ == '__main__':
    unittest.main()
