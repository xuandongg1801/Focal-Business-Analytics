"""Report fixed holdout results; never feed them back to model selection."""
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.metrics import (ConfusionMatrixDisplay, roc_curve, precision_recall_curve)
from .modeling import metrics


def save(fig, out, name):
    fig.tight_layout()
    fig.savefig(out/'figures'/name, dpi=300, bbox_inches='tight', metadata={'Software': 'approval_prediction'})
    plt.close(fig)


def export_evaluation(out, dataset, comparison, predictions, importance, frozen):
    plt.rcParams.update({'font.size': 10, 'axes.spines.top': False, 'axes.spines.right': False})
    dist = pd.read_csv(out/'tables/class_distribution.csv')
    fig, ax = plt.subplots(figsize=(6, 4))
    bars = ax.bar(dist.chot_don.map({0:'LOST', 1:'WIN'}), dist.orders, color='#296985')
    ax.bar_label(bars)
    ax.set(xlabel='WIN / LOST business label', ylabel='Orders', title='Sales order class distribution')
    save(fig, out, 'class_distribution.png')
    years = pd.read_csv(out/'tables/target_by_year.csv')
    fig, ax = plt.subplots(figsize=(6, 4))
    ax.bar(years.order_year.astype(str), years.win_rate, color='#296985')
    ax.set(ylim=(0, 1), ylabel='WIN / total sales orders', title='WIN rate by year')
    save(fig, out, 'win_rate_by_year.png')
    y = predictions.actual_chot_don
    for kind in ['roc', 'precision_recall']:
        fig, ax = plt.subplots(figsize=(7, 5))
        for name in comparison.model:
            p = predictions[f'prob_{name}']
            if kind == 'roc':
                xx, yy, _ = roc_curve(y, p)
            else:
                yy, xx, _ = precision_recall_curve(y, p)
            if kind == 'precision_recall':
                # Match Average Precision's step interpolation; a straight baseline
                # from (recall=0, precision=1) would exaggerate its apparent area.
                ax.step(xx, yy, where='post', label=name, linewidth=1.5)
            else:
                ax.plot(xx, yy, label=name, linewidth=1.5)
        ax.set(xlabel='False positive rate' if kind == 'roc' else 'Recall',
               ylabel='True positive rate' if kind == 'roc' else 'Precision',
               title='Test ROC curves' if kind == 'roc' else 'Test precision-recall curves (class 1)')
        ax.set_ylim(0, 1.05)
        ax.legend(fontsize=8)
        save(fig, out, f'{kind}_curve_models.png')
    for name in comparison.model:
        fig, ax = plt.subplots(figsize=(5, 4))
        ConfusionMatrixDisplay.from_predictions(y, predictions[f'pred_{name}'], labels=[0, 1], display_labels=['LOST', 'WIN'],
                                               ax=ax, colorbar=False, cmap='Blues')
        ax.set_title(f'Test: {name}')
        save(fig, out, f'confusion_matrix_{name}.png')
    fig, ax = plt.subplots(figsize=(9, 5))
    comparison.set_index('model')[['macro_f1', 'f1', 'roc_auc', 'pr_auc']].plot.bar(ax=ax)
    ax.set(ylim=(0, 1.05), ylabel='Score', xlabel='', title='Fixed test evaluation; selection uses validation')
    ax.tick_params(axis='x', rotation=20)
    save(fig, out, 'model_comparison.png')
    curves = pd.read_csv(out/'tables/threshold_analysis.csv')
    fig, axes = plt.subplots(2, 2, figsize=(10, 7), sharex=True, sharey=True)
    for ax, (name, frame) in zip(axes.flat, curves.groupby('model', sort=False)):
        for score in ['precision', 'recall', 'f1', 'macro_f1']:
            ax.plot(frame.threshold, frame[score], label=score)
        ax.axvline(frozen['selection'][name]['threshold'], color='black', linestyle='--', linewidth=1)
        ax.set(title=name, xlabel='Threshold', ylabel='Validation score', ylim=(0, 1.05))
    axes.flat[0].legend(fontsize=7)
    save(fig, out, 'threshold_curve.png')
    fig, ax = plt.subplots(figsize=(9, 5))
    imp = importance.iloc[::-1]
    ax.barh(imp.feature, imp.importance, xerr=imp['std'], color='#296985')
    ax.set(xlabel='Validation ROC-AUC decrease after permutation', title=f'Feature importance: {frozen["selected_model"]}')
    save(fig, out, 'feature_importance.png')
    learning = pd.read_csv(out/'tables/mlp_learning_history.csv')
    fig, ax = plt.subplots(figsize=(7, 4))
    ax.plot(learning.epoch, learning.loss, label='Weighted training loss')
    ax.plot(learning.epoch, learning.val_loss, label='Unweighted validation loss')
    ax.set(xlabel='Epoch', ylabel='Binary cross-entropy', title='MLP learning history')
    ax.legend()
    save(fig, out, 'mlp_learning_curve.png')
    best = frozen['selected_model']
    errors = predictions.merge(dataset[['order_id', 'order_month', 'prior_order_count', 'customer_is_known', 'recency_months']],
                               on='order_id', validate='one_to_one')
    errors['new_customer'] = errors.prior_order_count.eq(0)
    errors['history_depth'] = pd.cut(errors.prior_order_count, [-1, 0, 2, 9, np.inf], labels=['0', '1-2', '3-9', '10+'])
    errors['year'] = errors.order_month.str[:4]
    errors['recency_group'] = pd.cut(errors.recency_months, [-1, 1, 3, 6, np.inf],
        labels=['0-1m', '2-3m', '4-6m', '7+m']).astype('string').fillna('no_history')
    # Present-day market is diagnostic context only, never a model feature or historical attribute.
    from .config import SOURCE
    from .data import private_id
    master = pd.read_csv(SOURCE/'dim_customer.csv')
    master['customer_id'] = master.ma_khach_hang.map(lambda v: private_id(v, 'C_'))
    errors = errors.merge(master[['customer_id', 'thi_truong']].rename(columns={'thi_truong': 'market_snapshot'}),
                          on='customer_id', how='left', validate='many_to_one')
    errors['market_snapshot'] = errors.market_snapshot.fillna('unknown')
    errors['error'] = errors.actual_chot_don.ne(errors[f'pred_{best}'])
    errors['false_positive'] = errors.actual_chot_don.eq(0) & errors[f'pred_{best}'].eq(1)
    errors['false_negative'] = errors.actual_chot_don.eq(1) & errors[f'pred_{best}'].eq(0)
    errors[errors.false_positive].to_csv(out/'tables/false_positive_cases.csv', index=False)
    errors[errors.false_negative].to_csv(out/'tables/false_negative_cases.csv', index=False)
    rows = []
    for field in ['year', 'order_month', 'new_customer', 'history_depth', 'customer_is_known', 'customer_id',
                  'recency_group', 'market_snapshot']:
        for value, g in errors.groupby(field, dropna=False, observed=True):
            rows.append(dict(group=field, value=str(value), n=len(g), errors=int(g.error.sum()),
                false_positive=int(g.false_positive.sum()), false_negative=int(g.false_negative.sum()),
                error_rate=float(g.error.mean()),
                **metrics(g.actual_chot_don, g[f'prob_{best}'], frozen['selection'][best]['threshold'])))
    groups = pd.DataFrame(rows)
    groups.to_csv(out/'tables/subgroup_metrics.csv', index=False)
    from .drift import export_temporal_diagnostics
    export_temporal_diagnostics(out, dataset, frozen)
    # Customer-cluster bootstrap quantifies sampling variability without treating repeated customers as independent.
    rng = np.random.default_rng(42)
    errors['cluster'] = errors.customer_id.where(errors.customer_id.fillna('').ne(''), errors.order_id)
    blocks = [g.index.to_numpy() for _, g in errors.groupby('cluster')]
    boot = []
    for _ in range(300):
        idx = np.concatenate([blocks[j] for j in rng.integers(0, len(blocks), len(blocks))])
        g = errors.loc[idx]
        boot.append(metrics(g.actual_chot_don, g[f'prob_{best}'], frozen['selection'][best]['threshold']))
    pd.DataFrame(boot).quantile([.025, .5, .975]).rename_axis('quantile').to_csv(
        out/'tables/selected_model_cluster_bootstrap.csv')
    return groups
