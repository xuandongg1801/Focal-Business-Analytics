"""Integration checks using real artifacts; does not train or modify business data."""
import json
import unittest
from unittest.mock import patch

import numpy as np
import pandas as pd
from streamlit.testing.v1 import AppTest

from approval_prediction.config import FEATURES, OUTPUT, ROOT
from approval_prediction.data import build_features, private_id
from approval_prediction.app.utils.feature_builder import build_transaction, customer_summary
from approval_prediction.registry import MODEL_REGISTRY
from approval_prediction.app.utils.prediction import predict, validate_features, compare_all_models
from approval_prediction.app.utils.data_loader import ArtifactError, validate_bundle, _check_bundle


class InferenceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.history = pd.read_csv(OUTPUT/'tables/target_audit.csv').fillna({'customer_id': ''})
        cls.history = cls.history[cls.history.include.eq(True)]
        cls.dataset = pd.read_csv(OUTPUT/'tables/modeling_dataset.csv').fillna({'customer_id': ''})
        cls.contract = json.loads((OUTPUT/'models/model_schema.json').read_text())

    def test_all_rows_feature_parity(self):
        data = self.dataset.set_index('order_id')
        rebuilt = build_features(self.history).set_index('order_id')
        np.testing.assert_allclose(data[FEATURES],rebuilt.loc[data.index,FEATURES],equal_nan=True,atol=1e-12)
        inferred = pd.concat([build_transaction(r.customer_id,r.order_date,self.history) for r in self.dataset.itertuples()],ignore_index=True)
        np.testing.assert_allclose(inferred,self.dataset[FEATURES],equal_nan=True,atol=1e-12)

    def test_temporal_boundary_and_unknown(self):
        row = self.dataset[self.dataset.prior_order_count.gt(0)].iloc[-1]
        full = build_transaction(row.customer_id,row.order_date,self.history)
        past = self.history[self.history.order_month.lt(row.order_month)]
        pd.testing.assert_frame_equal(full,build_transaction(row.customer_id,row.order_date,past))
        altered = self.history.assign(chot_don=999,quantity_valid=1,unit_valid=1,product_valid=1,
            product_present=1,quantity_present=1,unit_present=1,line_complete=1,order_complete=1)
        pd.testing.assert_frame_equal(full,build_transaction(row.customer_id,row.order_date,altered))
        missing = build_transaction('',row.order_date,self.history).iloc[0]
        self.assertEqual(missing.prior_order_count,0)
        self.assertTrue(pd.isna(missing.recency_months))
        self.assertEqual(missing.customer_is_known,0)
        new = build_transaction('UNIT_TEST_UNSEEN',row.order_date,self.history).iloc[0]
        self.assertEqual(new.prior_order_count,0)
        self.assertEqual(new.customer_is_known,1)

    def test_saved_models_match_every_test_probability(self):
        test = self.dataset[self.dataset.split.eq('test')]
        expected = pd.read_csv(OUTPUT/'tables/transaction_approval_predictions.csv').set_index('order_id').loc[test.order_id]
        names=list(self.contract['thresholds'])
        actual = predict(test[FEATURES],names)
        for name in names:
            got=actual[actual.model.eq(name)]
            np.testing.assert_allclose(got.probability,expected[f'prob_{name}'],atol=1e-7,rtol=1e-6)
            np.testing.assert_array_equal(got.prediction,expected[f'pred_{name}'])

    def test_schema_and_bundle_guards(self):
        self.assertTrue(validate_bundle())
        frame=self.dataset[FEATURES].head(1)
        with self.assertRaises(ArtifactError): validate_features(frame[FEATURES[::-1]],self.contract)
        with self.assertRaises(ArtifactError): validate_features(frame.assign(year=np.inf),self.contract)
        with self.assertRaises(ArtifactError): validate_features(frame.assign(month=np.nan),self.contract)
        with self.assertRaises(ArtifactError):
            _check_bundle.__wrapped__((((str(OUTPUT/'models/selection.json'),0,0),'bad-hash'),),self.contract)

    def test_selected_model_matches_comparison_for_all_four(self):
        row = self.dataset[self.dataset.split.eq('test')].iloc[-1]
        frame = build_transaction(row.customer_id, row.order_date, self.history)
        comparison = predict(frame, list(MODEL_REGISTRY)).set_index('model')
        self.assertEqual(set(comparison.index), set(MODEL_REGISTRY))
        for name in MODEL_REGISTRY:
            selected = predict(frame, [name]).iloc[0]
            reference = comparison.loc[name]
            self.assertEqual(selected.model, name)
            self.assertAlmostEqual(selected.probability, reference.probability, places=7)
            self.assertEqual(selected.threshold, reference.threshold)
            self.assertEqual(selected.predicted_class, reference.predicted_class)
            self.assertEqual(selected.prediction, int(selected.probability >= selected.threshold))
            self.assertIn(selected.predicted_class, ['WIN', 'LOST'])
            self.assertTrue(0 <= selected.probability <= 1)
            self.assertTrue(0 <= selected.threshold <= 1)
        with self.assertRaises(ArtifactError): predict(frame, ['unsupported'])

    def test_history_statistics_use_strict_month_cutoff(self):
        history = pd.DataFrame(dict(customer_id=['X']*4+['Y'],
            order_date=['2025-01-02','2025-02-05','2025-03-01','2026-01-01','2025-01-03'],
            order_month=['2025-01','2025-02','2025-03','2026-01','2025-01'], chot_don=[1,0,1,1,1]))
        got = customer_summary('X','2025-03-12',history)
        self.assertEqual(got['total_orders'],2)
        self.assertEqual(got['win_count'],1)
        self.assertEqual(got['lost_count'],1)
        self.assertEqual(got['win_rate'],.5)
        changed = history.copy()
        changed.loc[changed.order_month.ge('2025-03'), 'chot_don'] = 0
        self.assertEqual(got,customer_summary('X','2025-03-12',changed))
        empty = customer_summary('','2026-11-01',history)
        self.assertEqual(empty['total_orders'],0)
        self.assertTrue(np.isnan(empty['win_rate']))

    def test_per_model_metadata_and_neural_network_architecture(self):
        from .utils.model_loader import model
        from copy import deepcopy
        self.assertEqual(set(self.contract['models']), set(MODEL_REGISTRY))
        for name, expected in MODEL_REGISTRY.items():
            info = self.contract['models'][name]
            self.assertEqual(info['artifact'], expected['artifact'])
            self.assertEqual(info['feature_schema'], FEATURES)
            self.assertEqual(info['decision_threshold'], self.contract['thresholds'][name])
            corrupt = deepcopy(self.contract)
            corrupt['models'][name]['decision_threshold'] = -1
            with self.assertRaises(ArtifactError):
                _check_bundle.__wrapped__((),corrupt)
        mlp = model('mlp')
        dense = [layer for layer in mlp.layers if layer.__class__.__name__ == 'Dense']
        self.assertEqual([layer.units for layer in dense],[64,32,1])
        self.assertEqual([layer.activation.__name__ for layer in dense],['relu','relu','sigmoid'])
        self.assertEqual(sum(layer.__class__.__name__ == 'Dropout' for layer in mlp.layers),2)


    def test_partial_inference_preserves_successes_and_names_failure(self):
        from .utils.model_loader import model as real_model
        frame=self.dataset[FEATURES].head(1)
        expected=predict(frame,list(MODEL_REGISTRY)).set_index('model')
        def broken(name):
            if name=='random_forest':
                raise RuntimeError('Inference unavailable')
            return real_model(name)
        with patch('approval_prediction.app.utils.prediction.model',side_effect=broken):
            results,errors=compare_all_models(frame)
            with self.assertRaisesRegex(ArtifactError,'Random Forest'):
                predict(frame,['random_forest'])
        self.assertEqual(set(errors),{'random_forest'})
        self.assertIn('Random Forest',errors['random_forest'])
        self.assertEqual(set(results.model),set(MODEL_REGISTRY)-{'random_forest'})
        for row in results.itertuples():
            reference=expected.loc[row.model]
            self.assertAlmostEqual(row.probability,reference.probability,places=7)
            self.assertEqual(row.threshold,reference.threshold)
            self.assertEqual(row.predicted_class,reference.predicted_class)
        with patch('approval_prediction.app.utils.prediction.model',side_effect=RuntimeError('Unavailable')):
            results,errors=compare_all_models(frame)
        self.assertTrue(results.empty)
        self.assertEqual(set(errors),set(MODEL_REGISTRY))


class AppFlowTests(unittest.TestCase):
    def assert_healthy(self,app):
        self.assertFalse(list(app.exception),list(app.exception))
        self.assertFalse(list(app.error),[e.value for e in app.error])

    def test_three_pages_controls_and_real_prediction(self):
        app=AppTest.from_file(str(ROOT/'approval_prediction/app/app.py'),default_timeout=90).run()
        self.assert_healthy(app)
        self.assertEqual(app.radio(key='navigation').options,['Overview','EDA','Prediction'])
        app.multiselect(key='analysis_types').set_value([]).run()
        self.assert_healthy(app)
        self.assertTrue(any('Không có đơn' in message.value for message in app.info))
        app.radio(key='navigation').set_value('EDA').run()
        self.assert_healthy(app)
        self.assertTrue(any('Không có dữ liệu' in message.value for message in app.info))
        app.radio(key='navigation').set_value('Prediction').run()
        self.assert_healthy(app)
        self.assertIsNone(app.selectbox(key='customer').value)
        self.assertEqual(app.selectbox(key='prediction_model').options, [m['display_name'] for m in MODEL_REGISTRY.values()])
        metadata=json.loads((OUTPUT/'models/selection.json').read_text())
        self.assertEqual(app.selectbox(key='prediction_model').value,metadata['selected_model'])
        source=pd.read_csv(ROOT/'data/processed/fact_order_header.csv')
        codes=sorted(source.loc[source.la_don_ban_hang.eq(True),'ma_khach'].dropna().unique())
        self.assertEqual(app.selectbox(key='customer').options,codes+['Không có mã khách nguồn'])
        customer=private_id(codes[0],'C_')
        app.selectbox(key='customer').set_value(customer).run()
        app.selectbox(key='prediction_month').set_value(6).run()
        app.number_input(key='prediction_year').set_value(2025).run()
        with patch('approval_prediction.app.pages.predict.build_transaction', wraps=build_transaction) as builder, \
             patch('approval_prediction.app.pages.predict.compare_all_models', wraps=compare_all_models) as inference:
            next(b for b in app.button if b.label=='Phân tích giao dịch').click().run()
            self.assert_healthy(app)
            self.assertEqual(builder.call_count,1)
            self.assertEqual(inference.call_count,1)
            analysis=app.session_state['prediction_analysis']
            self.assertEqual(analysis['identity'][:2],(customer,'2025-06-01'))
            self.assertFalse(any(b.label=='So sánh 4 mô hình' for b in app.button))
            self.assertEqual(len(analysis['results']),4)
            self.assertEqual(set(analysis['results'].model),set(MODEL_REGISTRY))
            initial_comparison=analysis['results'].set_index('model')
            self.assertTrue(any('Ngưỡng phân loại' in d.value.columns for d in app.dataframe))
            for name in MODEL_REGISTRY:
                app.selectbox(key='prediction_model').set_value(name).run()
                self.assert_healthy(app)
                # Selecting a model reuses the context; no second action or inference.
                self.assertEqual(builder.call_count,1)
                self.assertEqual(inference.call_count,1)
                comparison=app.session_state['prediction_analysis']['results'].set_index('model')
                pd.testing.assert_frame_equal(comparison,initial_comparison)
                expected=comparison.loc[name]
                self.assertTrue(any(m.label=='Khả năng WIN' and m.value==f'{expected.probability:.1%}' for m in app.metric))
                self.assertTrue(any(c.value==MODEL_REGISTRY[name]['display_name'] for c in app.caption))
                self.assertTrue(any(f'Dự đoán: {expected.predicted_class}' in m.value and f'{expected.threshold:.1%}' in m.value for m in app.markdown))
                table=next(d.value for d in app.dataframe if 'Ngưỡng phân loại' in d.value.columns)
                shown=table[table['Mô hình'].eq(MODEL_REGISTRY[name]['display_name'])].iloc[0]
                self.assertAlmostEqual(shown['Khả năng WIN'],expected.probability,places=7)
                self.assertEqual(shown['Ngưỡng phân loại'],expected.threshold)
                self.assertEqual(shown['Dự đoán'],expected.predicted_class)
        app.selectbox(key='prediction_month').set_value(9).run()
        self.assertNotIn('prediction_analysis',app.session_state)
        self.assertFalse(any(b.label=='Tải kết quả CSV' for b in app.get('download_button')))
        self.assertFalse(any(m.label=='Khả năng WIN' for m in app.metric))
        self.assertFalse(any('Ngưỡng phân loại' in d.value.columns for d in app.dataframe))
        next(b for b in app.button if b.label=='Phân tích giao dịch').click().run()
        self.assertEqual(app.session_state['prediction_analysis']['identity'][1],'2025-09-01')
        self.assertEqual(len(app.session_state['prediction_analysis']['results']),4)
        app.number_input(key='prediction_year').set_value(2026).run()
        self.assertNotIn('prediction_analysis',app.session_state)
        app.selectbox(key='prediction_month').set_value(11).run()
        self.assertTrue(any(w.value=='Thời điểm dự đoán nằm ngoài kỳ dữ liệu lịch sử hiện có.' for w in app.warning))
        self.assertFalse(any(m.label=='Khả năng WIN' for m in app.metric))
        next(b for b in app.button if b.label=='Phân tích giao dịch').click().run()
        self.assert_healthy(app)
        app.selectbox(key='customer').set_value('').run()
        self.assertNotIn('prediction_analysis',app.session_state)
        self.assertFalse(any(b.label=='Tải kết quả CSV' for b in app.get('download_button')))
        self.assertFalse(any(m.label=='Khả năng WIN' for m in app.metric))
        next(b for b in app.button if b.label=='Phân tích giao dịch').click().run()
        self.assert_healthy(app)
        self.assertTrue(any('Chưa có lịch sử' in i.value for i in app.info))
        for phase in ['Validation','Test']:
            next(r for r in app.radio if r.label=='Giai đoạn đánh giá').set_value(phase).run()
            for name in ['logistic','random_forest','xgboost','mlp']:
                next(s for s in app.selectbox if s.label=='Mô hình').set_value(name).run()
                self.assert_healthy(app)
        app.slider(key='forecast_horizon').set_value(1).run()
        self.assert_healthy(app)
        # A new artifact context invalidates saved results without another inference.
        contract=json.loads((OUTPUT/'models/model_schema.json').read_text())
        contract['artifact_sha256']={**contract['artifact_sha256'],'context_test':'changed'}
        with patch('approval_prediction.app.pages.predict.schema',return_value=contract):
            app.run()
            self.assert_healthy(app)
            self.assertNotIn('prediction_analysis',app.session_state)
            self.assertFalse(any(m.label=='Khả năng WIN' for m in app.metric))
            self.assertFalse(any('Ngưỡng phân loại' in d.value.columns for d in app.dataframe))

    def test_runtime_failure_keeps_history_and_other_models(self):
        from .utils.model_loader import model as real_model
        app=AppTest.from_file(str(ROOT/'approval_prediction/app/app.py'),default_timeout=90).run()
        app.radio(key='navigation').set_value('Prediction').run()
        app.selectbox(key='customer').set_value('').run()
        app.selectbox(key='prediction_model').set_value('random_forest').run()
        def broken(name):
            if name=='random_forest':
                raise RuntimeError('Inference unavailable')
            return real_model(name)
        with patch('approval_prediction.app.utils.prediction.model',side_effect=broken):
            next(b for b in app.button if b.label=='Phân tích giao dịch').click().run()
        self.assertFalse(list(app.exception))
        self.assertTrue(any('Random Forest' in e.value for e in app.error))
        self.assertFalse(any(m.label=='Khả năng WIN' for m in app.metric))
        self.assertTrue(any(m.label=='Tổng đơn lịch sử' for m in app.metric))
        table=next(d.value for d in app.dataframe if 'Ngưỡng phân loại' in d.value.columns)
        self.assertEqual(len(table),3)
        self.assertNotIn('Random Forest',table['Mô hình'].tolist())
        app.selectbox(key='prediction_model').set_value('logistic').run()
        self.assertTrue(any(m.label=='Khả năng WIN' for m in app.metric))

    def test_missing_artifact_has_friendly_message(self):
        with patch('approval_prediction.app.utils.data_loader.validate_bundle',side_effect=ArtifactError('Không tìm thấy model artifact. Hãy chạy pipeline training trước.')):
            app=AppTest.from_file(str(ROOT/'approval_prediction/app/app.py'),default_timeout=30).run()
            self.assertFalse(list(app.exception))
            self.assertIn('Không tìm thấy model artifact',app.error[0].value)


class AnalyticsTests(unittest.TestCase):
    def test_filters_conservation_and_empty_charts(self):
        from .utils.analytics import load_analytics, filtered, kpis, monthly, product_totals, observations
        from .components.analytics_charts import trend, ranking, forecast
        data = load_analytics()
        types = data.orders.loc[data.orders.la_don_ban_hang, 'loai_don'].unique().tolist()
        all_data = filtered(data,'2023-01','2025-12',[],types)
        self.assertEqual(kpis(all_data)['orders'],data.orders.la_don_ban_hang.sum())
        m = monthly(all_data,'2023-01','2025-12')
        self.assertAlmostEqual(m[['Nền','Dự án xác nhận','Cực trị thống kê']].sum().sum(), kpis(all_data)['km'])
        self.assertGreaterEqual(len(observations(all_data)),3)
        self.assertTrue(len(trend(m).data))
        empty = filtered(data,'2023-01','2025-12',[],[])
        self.assertEqual(kpis(empty)['orders'],0)
        self.assertTrue(pd.isna(kpis(empty)['km']))
        self.assertEqual(observations(empty),[])
        self.assertEqual(monthly(empty,'2023-01','2025-12')['Số đơn'].sum(),0)
        self.assertEqual(len(ranking(product_totals(empty),'canonical_product_code','KM','Empty').data),0)
        self.assertEqual(len(trend(m.iloc[:0]).data),0)
        self.assertEqual(len(forecast(pd.DataFrame(),pd.DataFrame()).data),0)
        for customer in all_data.orders.ma_khach.dropna().unique()[:3]:
            selected = filtered(data,'2023-01','2025-12',[customer],types)
            self.assertTrue(selected.orders.ma_khach.eq(customer).all())
            self.assertEqual(set(selected.items.order_row_id), set(selected.orders.order_row_id))


if __name__ == '__main__': unittest.main()
