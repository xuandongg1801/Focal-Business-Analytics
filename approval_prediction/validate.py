"""Independent output gates, usable without retraining."""
import argparse
import json
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from PIL import Image
from sklearn.impute import SimpleImputer

from .registry import MODEL_REGISTRY
from .config import OUTPUT, SOURCE, FEATURES, BLACKLIST, TARGET_VERSION, validate_feature_names


def validate_outputs(out):
    required_tables = ['modeling_dataset.csv', 'target_audit.csv', 'modeling_population_audit.csv',
        'class_distribution.csv', 'feature_dictionary.csv', 'model_comparison.csv',
        'threshold_analysis.csv', 'transaction_approval_predictions.csv',
        'false_positive_cases.csv', 'false_negative_cases.csv', 'feature_importance.csv',
        'product_text_audit.csv','unit_audit.csv','quantity_parse_audit.csv',
        'temporal_performance.csv','temporal_population_profile.csv','data_completeness_by_period.csv']
    required_figures = ['class_distribution.png', 'win_rate_by_year.png', 'roc_curve_models.png',
        'precision_recall_curve_models.png', 'model_comparison.png', 'threshold_curve.png',
        'feature_importance.png'] + [f'confusion_matrix_{n}.png' for n in ['logistic','random_forest','xgboost','mlp']]
    expected_models = {'selection.json', 'model_schema.json', 'preprocessor.joblib'} | {Path(m['artifact']).name for m in MODEL_REGISTRY.values()}
    assert {p.name for p in (out/'models').iterdir() if p.is_file()} == expected_models
    assert all((out/'tables'/n).is_file() for n in required_tables)
    assert all((out/'figures'/n).is_file() for n in required_figures)
    d = pd.read_csv(out/'tables/modeling_dataset.csv', keep_default_na=True)
    pred = pd.read_csv(out/'tables/transaction_approval_predictions.csv')
    comp = pd.read_csv(out/'tables/model_comparison.csv')
    selection = json.loads((out/'models/selection.json').read_text(encoding='utf-8'))
    assert selection['target_version'] == TARGET_VERSION
    dictionary = pd.read_csv(out/'tables/feature_dictionary.csv')
    assert {'feature_name','description','source','available_at_prediction_time','used_in_model','leakage_risk','reason'} <= set(dictionary)
    assert dictionary.loc[dictionary.used_in_model, 'feature_name'].tolist() == FEATURES
    edge = pd.read_csv(out/'tables/target_edge_case_review.csv')
    assert edge.product_present.eq(1).all()
    assert edge.chot_don.isin([0, 1]).all()
    target = pd.read_csv(out/'tables/target_audit.csv')
    assert target.chot_don.isin([0, 1]).all()
    # Rebuild labels from source-line fields; saved labels cannot validate themselves.
    from .target import read_source_fields, item_labels, aggregate_target
    from .data import private_id
    source_items = pd.read_csv(SOURCE/'fact_order_items.csv')
    rebuilt_items = item_labels(read_source_fields(source_items)).set_index('item_id')
    saved_items = pd.read_csv(out/'tables/item_target_audit.csv').set_index('item_id')
    assert saved_items.index.is_unique and set(saved_items.index) == set(rebuilt_items.index)
    columns = ['product_present', 'quantity_present', 'unit_present', 'line_complete', 'item_target']
    np.testing.assert_array_equal(saved_items.loc[rebuilt_items.index, columns], rebuilt_items[columns])
    headers = pd.read_csv(SOURCE/'fact_order_header.csv')
    rebuilt_target = rebuilt_items.groupby('order_row_id').item_target.agg(aggregate_target)
    headers['order_id'] = headers.so_xac_nhan_don_hang.map(lambda value: private_id(value, 'O_'))
    headers['expected_target'] = headers.order_row_id.map(rebuilt_target)
    expected = headers.set_index('order_id').expected_target
    assert target.order_id.is_unique and set(target.order_id) == set(expected.index)
    np.testing.assert_array_equal(target.chot_don, expected.loc[target.order_id])
    assert len(d) == int(target.include.sum())
    validate_feature_names(FEATURES)
    assert d.order_id.is_unique and d.order_id.notna().all()
    assert d.chot_don.notna().all() and set(d.chot_don) == {0, 1}
    assert not (set(FEATURES) & BLACKLIST)
    assert selection['features'] == FEATURES
    assert set(d.columns) == set(FEATURES + ['order_id', 'order_date', 'order_month', 'customer_id',
                                          'chot_don', 'split', 'history_latest_month'])
    splits = {n: d[d.split.eq(n)] for n in ['train', 'validation', 'test']}
    tr, va, te = [splits[n] for n in ['train', 'validation', 'test']]
    assert tr.order_month.max() < va.order_month.min() <= va.order_month.max() < te.order_month.min()
    assert tr.order_date.max() < va.order_date.min() <= va.order_date.max() < te.order_date.min()
    for a, b in [('train', 'validation'), ('train', 'test'), ('validation', 'test')]:
        assert set(splits[a].order_id).isdisjoint(splits[b].order_id)
    hist = d.history_latest_month.notna()
    assert (d.loc[hist, 'history_latest_month'] < d.loc[hist, 'order_month']).all()
    # Recompute counts independently from the full order population.
    audit = pd.read_csv(out/'tables/target_audit.csv').fillna({'customer_id': ''})
    sales = audit[audit.include.eq(True)]
    for row in d.fillna({'customer_id': ''}).itertuples():
        past = sales[sales.customer_id.eq(row.customer_id) & sales.order_month.lt(row.order_month)] if row.customer_id else sales.iloc[:0]
        assert row.prior_order_count == len(past)
        assert row.customer_active_months_before == past.order_month.nunique()
        assert row.customer_is_known == bool(row.customer_id)
        p = pd.Period(row.order_month, freq='M')
        periods = pd.PeriodIndex(past.order_month, freq='M')
        n3, n6 = int((periods >= p-3).sum()), int((periods >= p-6).sum())
        assert row.orders_last_3m == n3 and row.orders_last_6m == n6
        assert np.isclose(row.prior_monthly_order_trend, (2*n3-n6)/3)
        if len(past):
            assert row.recency_months == (p - periods.max()).n
        else:
            assert pd.isna(row.recency_months)
    prep = joblib.load(out/'models/preprocessor.joblib')
    fresh = SimpleImputer(strategy='median', keep_empty_features=True).fit(tr[FEATURES])
    np.testing.assert_allclose(prep['impute'].statistics_, fresh.statistics_, equal_nan=True)
    np.testing.assert_allclose(prep['scale'].mean_, fresh.transform(tr[FEATURES]).mean(axis=0), atol=1e-12)
    assert prep['scale'].n_samples_seen_ == len(tr)
    assert list(prep.feature_names_in_) == FEATURES
    fit_ids = pd.read_csv(out/'tables/preprocessor_fit_orders.csv')
    assert set(fit_ids.order_id) == set(tr.order_id)
    assert len(pred) == len(te) and pred.order_id.is_unique and set(pred.order_id) == set(te.order_id)
    truth = te.set_index('order_id').chot_don.reindex(pred.order_id).to_numpy()
    np.testing.assert_array_equal(truth, pred.actual_chot_don)
    required = set(MODEL_REGISTRY)
    assert set(comp.model) == required and len(comp) == 4 and comp.model.is_unique
    assert set(selection['selection']) == required
    for name in comp.model:
        prob = pred[f'prob_{name}'].to_numpy()
        assert np.isfinite(prob).all() and ((prob >= 0) & (prob <= 1)).all()
        threshold = selection['selection'][name]['threshold']
        np.testing.assert_array_equal(pred[f'pred_{name}'], (prob >= threshold).astype(int))
        if name != 'mlp':
            loaded = joblib.load(out/MODEL_REGISTRY[name]['artifact'])
            np.testing.assert_allclose(loaded.predict_proba(prep.transform(te[FEATURES]))[:, 1], prob,
                                       rtol=1e-6, atol=1e-7)
    from .modeling import choose_threshold, metrics
    validation_preds = pd.read_csv(out/'tables/validation_predictions.csv')
    assert set(validation_preds.order_id) == set(va.order_id)
    for name in required:
        threshold, _ = choose_threshold(validation_preds.chot_don, validation_preds[f'prob_{name}'])
        assert np.isclose(threshold, selection['selection'][name]['threshold'])
    selected = max(selection['selection'], key=lambda n: (selection['selection'][n]['macro_f1'], selection['selection'][n]['roc_auc']))
    assert selected == selection['selected_model']
    for row in comp.itertuples():
        expected = metrics(pred.actual_chot_don, pred[f'prob_{row.model}'], row.threshold)
        for key, value in expected.items():
            assert np.isclose(getattr(row, key), value)
            assert np.isclose(getattr(row, f'test_{key}'), value)
            assert np.isclose(getattr(row, f'validation_{key}'), selection['selection'][row.model][key])
    temporal = pd.read_csv(out/'tables/temporal_performance.csv')
    for row in comp.itertuples():
        for split in ['validation','test']:
            record = temporal[temporal.model.eq(row.model) & temporal.scope.eq('split') & temporal.split.eq(split)].iloc[0]
            for key in ['accuracy','precision','recall','f1','macro_f1','roc_auc','pr_auc','specificity']:
                assert np.isclose(record[key], getattr(row,f'{split}_{key}'))
    assert selection['preprocessing_fit_split'] == 'train'
    for path in (out/'figures').glob('*.png'):
        with Image.open(path) as image:
            assert min(image.size) >= 1000
            image.verify()
    docs = ['model_card.md', 'data_contract.md', 'leakage_audit.md']
    assert all((out/'docs'/name).is_file() for name in docs)
    report = dict(status='PASS', order_grain=True, target_binary=True, target_recomputed_from_source=True, allowlist=True,
                  temporal_splits=True, independently_recomputed_history=True,
                  preprocessing_train_only=True, thresholds_validation_only=True,
                  prediction_count=len(pred), four_models=True, figures_verified=True)
    (out/'validation.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(__doc__)
    parser.add_argument('--output', type=Path, default=OUTPUT)
    print(validate_outputs(parser.parse_args().output))
