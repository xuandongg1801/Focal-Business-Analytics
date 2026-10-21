"""Adversarial leakage and target tests; no model training on test import."""
import unittest
import numpy as np
import pandas as pd

from .config import FEATURES, BLACKLIST, OUTPUT, validate_feature_names
from .data import build_features
from .target import is_present, read_source_fields, item_labels, aggregate_target
from .registry import MODEL_REGISTRY


class TargetTests(unittest.TestCase):
    @staticmethod
    def label(product, quantity, unit):
        return item_labels(pd.DataFrame(dict(raw_product=[product], raw_quantity=[quantity], raw_unit=[unit]))).item_target.iloc[0]

    def test_ten_confirmed_presence_cases(self):
        cases = [('FTTH02','100','KM',1), ('KM','12.3','KM',1), ('M .)','1634','M',1),
                 ('','100','KM',0), ('FTTH02','','KM',0), ('FTTH02','100','',0),
                 ('   ','100','KM',0), ('FTTH02','not numeric','KM',1), ('FTTH02','0','KM',1),
                 ('FTTH02','100','OUTSIDE_LIST',1)]
        for product, quantity, unit, expected in cases:
            with self.subTest(product=product, quantity=quantity, unit=unit):
                self.assertEqual(self.label(product,quantity,unit), expected)

    def test_null_and_whitespace_are_absent_in_each_component(self):
        for missing in [None, np.nan, pd.NA, '', '  ', '\t\n', '\u00a0']:
            for column in range(3):
                values = ['FE12', '12', 'KM']
                values[column] = missing
                with self.subTest(missing=missing, column=column):
                    self.assertFalse(is_present(missing))
                    self.assertEqual(self.label(*values),0)
        self.assertEqual(self.label(None,None,None),0)

    def test_quantity_validity_does_not_decide_label(self):
        for quantity in [0, '0', -1, np.inf, -np.inf, 'abc', 'NaN', 'NULL', 'N/A', False]:
            with self.subTest(quantity=quantity):
                self.assertTrue(is_present(quantity))
                self.assertEqual(self.label('FE12',quantity,'KM'),1)

    def test_product_quality_does_not_decide_label(self):
        for product in ['DA48','FE','7X0.33','FTHH02 CHẶT','KM','M','M .)','BÁO GIÁ',
                        'QUẤN LẠI CÁP','VNTT GIAO BÌNH DƯƠNG','???','NA','NULL']:
            with self.subTest(product=product):
                self.assertEqual(self.label(product,12,'KM'),1)

    def test_unit_quality_does_not_decide_label(self):
        for unit in ['KM','X','unknown','N/A',0]:
            with self.subTest(unit=unit):
                self.assertEqual(self.label('FE12',12,unit),1)

    def test_order_requires_all_source_lines(self):
        for values, expected in [([1,1,1],1),([1,0,1],0),([0],0),([1],1),([],0)]:
            with self.subTest(values=values):
                self.assertEqual(aggregate_target(pd.Series(values,dtype='int64')), expected)

    def test_derived_quality_and_mapping_cannot_change_label(self):
        d = pd.DataFrame(dict(raw_product=['M .)','FTTH02'], raw_quantity=['abc','0'], raw_unit=['X','M']))
        before = item_labels(d)
        changed = d.assign(product_valid=0, quantity_valid=0, unit_valid=0, parsed_product_token=None,
                           canonical_product_code=None, parse_status='unmapped', so_luong=np.nan,
                           so_luong_km=np.nan, don_vi=None, item_text_raw='', master_match=False,
                           wo='secret', so_hop_dong=None, price=99999)
        pd.testing.assert_series_equal(before.item_target,item_labels(changed).item_target)
        self.assertEqual(before.item_target.tolist(),[1,1])

    def test_cleaned_fields_cannot_substitute_for_original_cells(self):
        with self.assertRaises(KeyError):
            item_labels(pd.DataFrame(dict(item_text_raw=['FE12'],so_luong=[1],don_vi=['KM'])))

    def test_original_excel_values_preserve_literal_text_and_zero(self):
        import tempfile
        from pathlib import Path
        from openpyxl import Workbook
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            workbook = Workbook()
            sheet = workbook.active
            sheet.title = 'DATA_CHUAN_HOA'
            sheet.append(['Title'])
            sheet.append(['SẢN PHẨM','SỐ LƯỢNG','ĐƠN VỊ'])
            for row in [('M .)','not numeric','X'),('NULL',0,'N/A'),('   ','100','KM'),('FE12',None,'KM')]:
                sheet.append(row)
            workbook.save(root/'sample.xlsx')
            workbook.close()
            items = pd.DataFrame(dict(item_id=range(1,5),source_file=['sample.xlsx']*4,
                source_sheet=['DATA_CHUAN_HOA']*4,source_excel_row=range(3,7),so_luong=[np.nan]*4))
            attached = read_source_fields(items,root)
            self.assertEqual(attached.raw_quantity.iloc[0],'not numeric')
            self.assertEqual(attached.raw_product.iloc[1],'NULL')
            self.assertEqual(attached.raw_unit.iloc[1],'N/A')
            self.assertEqual(item_labels(attached).item_target.tolist(),[1,1,0,0])
            with self.assertRaisesRegex(ValueError,'lineage'):
                read_source_fields(pd.concat([items,items.iloc[:1]]),root)

    def test_master_codes_irrelevant_for_every_source_item(self):
        from .config import SOURCE
        d = read_source_fields(pd.read_csv(SOURCE/'fact_order_items.csv'))
        before = item_labels(d)
        changed = d.assign(parsed_product_token=None, canonical_product_code=None, master_match=False)
        pd.testing.assert_series_equal(before.item_target,item_labels(changed).item_target)

    def test_no_target_features_in_matrix(self):
        self.assertFalse(set(FEATURES) & BLACKLIST)
        for name in ['product_present','quantity_present','unit_present','line_complete','order_complete']:
            self.assertIn(name, BLACKLIST)
            self.assertNotIn(name, FEATURES)

    def test_forbidden_lineage_cannot_enter_schema(self):
        validate_feature_names(FEATURES)
        for name in BLACKLIST | {'log_quantity','product_missing_scaled','customer_full_period_score'}:
            with self.subTest(name=name):
                with self.assertRaises(ValueError):
                    validate_feature_names(FEATURES + [name])
        with self.assertRaises(ValueError):
            validate_feature_names(FEATURES[::-1])


class TemporalTests(unittest.TestCase):
    def source(self):
        return pd.DataFrame(dict(order_id=['a','b','c','d','e','f'], customer_id=['X','X','X','X','',''],
            order_date=['2023-01-01','2023-01-01','2023-02-05','2025-03-01','2023-01-01','2023-02-01'],
            order_month=['2023-01','2023-01','2023-02','2025-03','2023-01','2023-02'],
            chot_don=[1,0,1,0,1,1]))

    def test_same_month_unknown_customer_and_future(self):
        d = self.source()
        result = build_features(d).set_index('order_id')
        self.assertEqual(result.loc['a','prior_order_count'], 0)
        self.assertEqual(result.loc['b','prior_order_count'], 0)
        self.assertEqual(result.loc['c','prior_order_count'], 2)
        self.assertEqual(result.loc['f','prior_order_count'], 0)
        changed = d.copy()
        changed['chot_don'] = 1-changed.chot_don
        changed['so_luong'] = 1e12
        changed['item_text_raw'] = 'BÁO GIÁ'
        pd.testing.assert_frame_equal(result[FEATURES], build_features(changed).set_index('order_id')[FEATURES])
        truncated = build_features(d[d.order_id.ne('d')]).set_index('order_id')
        pd.testing.assert_frame_equal(result.loc[truncated.index, FEATURES], truncated[FEATURES])

    def test_nonbinary_or_duplicate_order_is_rejected(self):
        d = self.source()
        for bad in [None, 2, -1]:
            changed = d.copy()
            changed.loc[changed.order_id.eq('a'), 'chot_don'] = bad
            with self.assertRaisesRegex(ValueError, 'binary'):
                build_features(changed)
        with self.assertRaisesRegex(ValueError, 'one non-null order_id'):
            build_features(pd.concat([d, d.iloc[:1]]))

    def test_future_rows_do_not_change_prior_vectors(self):
        d = self.source()
        expected = build_features(d).set_index('order_id').loc[['a', 'b', 'c'], FEATURES]
        changed = d.copy()
        changed.loc[changed.order_id.eq('d'), ['customer_id', 'order_month', 'chot_don']] = ['Y', '2026-11', 1]
        changed = pd.concat([changed, changed.iloc[[3]].assign(order_id='new')], ignore_index=True)
        actual = build_features(changed).set_index('order_id').loc[expected.index, FEATURES]
        pd.testing.assert_frame_equal(actual, expected)


class OutputTests(unittest.TestCase):
    """Run after a clean module run; no silent skips for absent artifacts."""
    def test_all_output_gates(self):
        from .validate import validate_outputs
        self.assertEqual(validate_outputs(OUTPUT)['status'], 'PASS')

    def test_model_comparison_and_probability_contract(self):
        comp = pd.read_csv(OUTPUT/'tables/model_comparison.csv')
        self.assertEqual(set(comp.model), set(MODEL_REGISTRY))
        self.assertEqual(len(comp), 4)
        for prefix in ['validation','test']:
            for metric in ['accuracy','precision','recall','f1','macro_f1','roc_auc','pr_auc']:
                self.assertIn(f'{prefix}_{metric}', comp)
        p = pd.read_csv(OUTPUT/'tables/transaction_approval_predictions.csv').filter(like='prob_')
        self.assertTrue(np.isfinite(p).all().all())
        self.assertTrue(((p>=0)&(p<=1)).all().all())

    def test_no_order_duplicates_across_splits(self):
        d = pd.read_csv(OUTPUT/'tables/modeling_dataset.csv')
        self.assertTrue(d.order_id.is_unique)
        self.assertEqual(d.split.nunique(), 3)


if __name__ == '__main__':
    unittest.main()
