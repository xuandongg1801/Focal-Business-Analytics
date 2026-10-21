"""Regenerate public-safe Markdown docs from reviewed templates and aggregate artifacts.

This script intentionally never exports source/customer/order/price-level values.
It expects to be run from the full project checkout, with docs_templates/ installed.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
TEMPLATES = ROOT / 'docs_templates'
DOCS = ROOT / 'docs'
TABLES = ROOT / 'outputs' / 'tables'
CLASS = ROOT / 'outputs' / 'approval_prediction'
TOKENS = re.compile(r'\{\{([A-Z0-9_]+)\}\}')
EXPECTED = {f'{idx:02d}_{name}.md' for idx, name in [
    (1,'project_overview'), (2,'data_dictionary'), (3,'data_pipeline'),
    (4,'data_quality'), (5,'eda'), (6,'rfv_analysis'),
    (7,'forecasting'), (8,'approval_prediction'),
    (9,'streamlit_app'), (10,'reproducibility')]}


def read_json(path: Path):
    return json.loads(path.read_text(encoding='utf-8'))


def pct(value: float) -> str:
    return f'{float(value)*100:.2f}%'


def md_table(headers, data):
    def safe(value):
        return str(value).replace('|','/').replace('\n',' ').strip()
    return ('| ' + ' | '.join(map(safe,headers)) + ' |\n'
            + '| ' + ' | '.join('---' for _ in headers) + ' |\n'
            + '\n'.join('| ' + ' | '.join(map(safe,row)) + ' |' for row in data))


def generate():
    missing = EXPECTED - {p.name for p in TEMPLATES.glob('*.md')}
    unexpected = {p.name for p in TEMPLATES.glob('*.md')} - EXPECTED
    if missing or unexpected:
        raise RuntimeError(f'Documentation templates mismatch: missing={sorted(missing)} extra={sorted(unexpected)}')

    quality = read_json(TABLES/'pipeline_validation.json')
    eda = read_json(TABLES/'eda_summary.json')
    forecast = read_json(TABLES/'forecast_methodology.json')
    selection = read_json(CLASS/'models'/'selection.json')
    schema = read_json(CLASS/'models'/'model_schema.json')
    splits = pd.read_csv(CLASS/'tables'/'split_audit.csv')
    model = pd.read_csv(CLASS/'tables'/'model_comparison.csv')
    rfv = pd.read_csv(TABLES/'customer_rfm_segments.csv')
    if not (set(splits['split']) == {'train','validation','test'}):
        raise ValueError('Expected three temporal dataset splits')
    if rfv.empty:
        raise ValueError('RFV summary is empty; no documented cohort available')
    if set(model['model']) != {'logistic','random_forest','xgboost','mlp'}:
        raise ValueError('Unexpected set of candidate classifiers')
    if not ((splits.class_1 + splits.class_0) == splits.n).all():
        raise ValueError('Model split audit counts do not reconcile')
    if int(splits.n.sum()) != int(model.train_size.iloc[0]+model.validation_size.iloc[0]+model.test_size.iloc[0]):
        raise ValueError('Model dataset size disagreement')

    split_order=['train','validation','test']
    split_idx=splits.set_index('split').loc[split_order]
    split_table=md_table(['Tập','Khoảng tháng','Số đơn','WIN','LOST','Tỷ lệ WIN'],
        [(name, f"{r.first_month} – {r.last_month}", int(r.n), int(r.class_1), int(r.class_0), pct(r.class_1_rate))
            for name,r in split_idx.iterrows()])

    model_idx=model.set_index('model').loc[['logistic','random_forest','xgboost','mlp']]
    display={'logistic':'Logistic Regression','random_forest':'Random Forest',
             'xgboost':'XGBoost','mlp':'MLP Neural Network'}
    model_table=md_table(['Mô hình','Val Macro-F1','Val ROC-AUC','Test Macro-F1','Test ROC-AUC','Threshold'],
        [(('**'+display[name]+'**') if name==selection['selected_model'] else display[name],
          f'{r.validation_macro_f1:.4f}',f'{r.validation_roc_auc:.4f}',
          f'{r.test_macro_f1:.4f}',f'{r.test_roc_auc:.4f}',f'{r.threshold:.2f}')
            for name,r in model_idx.iterrows()])
    selected=selection['selected_model']
    selected_row=model_idx.loc[selected]
    best_test=model_idx['test_macro_f1'].idxmax()
    counts=rfv.groupby('phan_khuc',sort=False).size()
    segment_names=['Gần đây, thường xuyên, lượng cao','Tần suất cao','Ít giao dịch gần đây','Nhóm còn lại']
    if set(counts.index) != set(segment_names):
        raise ValueError('RFV segment set changed; revise documentation before publishing')
    rfv_table=md_table(['Phân khúc','Số khách','Tỷ lệ trong mẫu RFV'],
        [(seg,int(counts[seg]),pct(counts[seg]/len(rfv))) for seg in segment_names])

    reg=int(eda['so_khach_hang_dang_ky'])
    n_rfv=len(rfv)
    if reg < n_rfv or not n_rfv or len(rfv.ma_khach.unique()) != len(rfv):
        raise ValueError('RFV customer count not unique or exceeds registered customers')
    known_eda=int(eda['so_khach_hang_co_ma_chinh_thuc_phat_sinh_don_cap'])
    if n_rfv != known_eda:
        raise ValueError('RFV vs EDA official-customer count changed; revise wording and scope')

    tokens={
        'ORDERS':quality['orders'], 'ITEMS':quality['items'],
        'CANONICAL_ROWS':quality['canonical_product_rows'],
        'EXACT_ROWS':quality['exact_product_rows'], 'GENERIC_ROWS':quality['generic_product_rows'],
        'UNRESOLVED_ROWS':quality['unresolved_rows'], 'UNRESOLVED_MULTI_ROWS':quality['unresolved_multi_product_rows'],
        'UNMAPPED_ROWS':quality['unmapped_product_rows'], 'MONTH_CONFLICTS':quality['month_conflict_orders'],
        'MISSING_QTY':quality['missing_quantity'], 'MISSING_CUST':quality['missing_customer_code'],
        'OUTLIER_ROWS':quality['outlier_rows'], 'DUP_ORDERS':quality['duplicate_order_ids'],
        'DUP_ITEMS':quality['duplicate_item_ids'], 'DUP_CANDIDATES':quality['duplicate_item_candidate_rows'],
        'RFV_SNAPSHOT':str(rfv.snapshot_month.iloc[0]), 'REGISTERED_CUSTOMERS':reg,
        'RFV_CUSTOMERS':n_rfv, 'RFV_COVERAGE':pct(n_rfv/reg),
        'INFERRED_GROUPS':int(eda['so_nhom_suy_dien_tu_ma_don_khong_co_ma_khach']),
        'INFERRED_KM_SHARE':f"{float(eda['ty_trong_km_nhom_suy_dien_pct']):.2f}%",
        'RFV_SEGMENT_TABLE':rfv_table,
        'FORECAST_HISTORY':f"{forecast['history_start']} – {forecast['history_end']}",
        'FORECAST_VALIDATION':f"{forecast['validation_start']} – {forecast['validation_end']}",
        'FORECAST_FOLDS':forecast['validation_folds'],
        'FORECAST_TEST':f"{forecast['test_start']} – {forecast['test_end']}",
        'FORECAST_MODEL':str(forecast['selected_model']).replace('alpha=','alpha = '),
        'FORECAST_VAL_WAPE':f"{forecast['validation_wape_pct']:.2f}%",
        'FORECAST_TEST_WAPE':f"{forecast['test_wape_pct']:.2f}%",
        'FORECAST_HORIZON':f"{forecast['forecast_start']} – {forecast['forecast_end']}",
        'CLASS_N':int(splits.n.sum()),'CLASS_WIN':int(splits.class_1.sum()),
        'CLASS_LOST':int(splits.class_0.sum()),'CLASS_SPLIT_TABLE':split_table,
        'TRAIN_WIN_RATE':pct(split_idx.loc['train','class_1_rate']),
        'VAL_WIN_RATE':pct(split_idx.loc['validation','class_1_rate']),
        'TEST_WIN_RATE':pct(split_idx.loc['test','class_1_rate']),
        'CLASS_MODEL_TABLE':model_table, 'CLASS_SELECTED_MODEL':display[selected],
        'CLASS_SELECTED_VAL_F1':f'{selected_row.validation_macro_f1:.4f}',
        'CLASS_SELECTED_THRESHOLD':f'{float(schema["threshold"]):.2f}',
        'CLASS_TEST_BEST':display[best_test],
        'CLASS_TEST_BEST_F1':f'{model_idx.loc[best_test,"test_macro_f1"]:.4f}',
        'CLASS_TN':int(selected_row.test_tn), 'CLASS_FP':int(selected_row.test_fp),
        'CLASS_FN':int(selected_row.test_fn), 'CLASS_TP':int(selected_row.test_tp),
    }
    if int(quality['canonical_product_rows'])+int(quality['unresolved_rows'])!=int(quality['items']):
        raise ValueError('Quality row-count conservation invariant failed')
    if int(selected_row.test_tn + selected_row.test_fp + selected_row.test_fn + selected_row.test_tp)!=int(split_idx.loc['test','n']):
        raise ValueError('Confusion matrix does not sum to test population')

    DOCS.mkdir(parents=True,exist_ok=True)
    output={}
    for name in sorted(EXPECTED):
        source=(TEMPLATES/name).read_text(encoding='utf-8')
        unknown = set(TOKENS.findall(source)) - set(tokens)
        if unknown:
            raise ValueError(f'Unknown documentation variables in {name}: {sorted(unknown)}')
        result = TOKENS.sub(lambda match: str(tokens[match.group(1)]),source)
        if TOKENS.search(result):
            raise ValueError(f'Unrendered variables remain in {name}')
        output[name]=result.strip()+'\n'
    for name,body in output.items():
        (DOCS/name).write_text(body,encoding='utf-8')
    print(f'Wrote {len(output)} public-safe documentation pages (derived aggregates only)')


if __name__=='__main__':
    generate()
