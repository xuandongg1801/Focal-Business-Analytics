import pandas as pd
from approval_prediction.registry import MODEL_REGISTRY
METRICS = {'accuracy': 'Accuracy', 'precision': 'Precision', 'recall': 'Recall',
           'f1': 'F1', 'macro_f1': 'Macro-F1', 'roc_auc': 'ROC-AUC', 'pr_auc': 'PR-AUC'}
def model_name(name): return MODEL_REGISTRY.get(name, {}).get('display_name', name)
def pct(value): return 'Chưa có' if pd.isna(value) else f'{value:.1%}'
def number(value): return 'Chưa có' if pd.isna(value) else f'{value:,.0f}'
def date_label(value): return pd.Timestamp(value).strftime('%d/%m/%Y')
def selection_label(selection):
    metric=selection['selection_metric'].replace('validation ', '').replace('macro_f1', 'Macro-F1').replace('roc_auc', 'ROC-AUC').replace('tie-break', 'khi bằng điểm')
    return 'Chọn theo ' + metric + ' trên validation'
