"""Retrospective diagnostics, not inputs to selection or prediction."""
import numpy as np
import pandas as pd
from .modeling import metrics


def with_periods(df):
    d = df.copy()
    d['year'] = d.order_month.str[:4]
    d['half_year'] = d.year + np.where(d.order_month.str[5:7].astype(int).le(6), '-H1', '-H2')
    return d


def export_temporal_diagnostics(out, dataset, frozen):
    pred = with_periods(pd.read_csv(out/'tables/temporal_predictions.csv'))
    rows = []
    for split, part in pred.groupby('split'):
        groups = [('split', split, part)]
        groups += [('year', str(k), g) for k, g in part.groupby('year')]
        groups += [('half_year', str(k), g) for k, g in part.groupby('half_year')]
        for scope, period, g in groups:
            sufficient = len(g) >= 20 and g.chot_don.nunique() == 2 and g.chot_don.value_counts().min() >= 5
            for name, info in frozen['selection'].items():
                scores = metrics(g.chot_don, g[f'prob_{name}'], info['threshold'])
                rows.append(dict(model=name, split=split, scope=scope, period=period, n=len(g),
                    class_0=int(g.chot_don.eq(0).sum()), class_1=int(g.chot_don.eq(1).sum()),
                    win_rate=float(g.chot_don.mean()), adequate_sample=sufficient,
                    evaluation_role={'train': 'in_sample_optimistic', 'validation': 'used_for_selection',
                                     'test': 'held_out'}[split], threshold=info['threshold'], **scores))
    pd.DataFrame(rows).to_csv(out/'tables/temporal_performance.csv', index=False)
    d = with_periods(dataset)
    composition = []
    group_sets = [('split', k, g) for k, g in d.groupby('split')]
    group_sets += [('year', k, g) for k, g in d.groupby('year')]
    group_sets += [('half_year', k, g) for k, g in d.groupby('half_year')]
    for scope, period, g in group_sets:
        composition.append(dict(scope=scope, period=period, n=len(g), win_rate=float(g.chot_don.mean()),
            known_customer_rate=float(g.customer_is_known.mean()),
            distinct_known_customers=g.loc[g.customer_is_known.eq(1), 'customer_id'].nunique(),
            no_prior_history_rate=float(g.prior_order_count.eq(0).mean()),
            mean_prior_order_count=float(g.prior_order_count.mean()), median_prior_order_count=float(g.prior_order_count.median()),
            median_recency_months=float(g.recency_months.median())))
    pd.DataFrame(composition).to_csv(out/'tables/temporal_population_profile.csv', index=False)
    # Separate descriptive label-component audit: NEVER merged into modeling X or error explanations.
    audit = pd.read_csv(out/'tables/item_target_audit.csv')
    order_components = audit[audit.include].groupby('order_id').agg(
        product_incomplete=('product_present', lambda s: s.eq(0).any()),
        quantity_incomplete=('quantity_present', lambda s: s.eq(0).any()),
        unit_incomplete=('unit_present', lambda s: s.eq(0).any()))
    target = pd.read_csv(out/'tables/target_audit.csv')
    target = with_periods(target[target.include].merge(order_components, on='order_id', validate='one_to_one'))
    completeness = []
    for scope in ['year', 'half_year']:
        for period, g in target.groupby(scope):
            completeness.append(dict(scope=scope, period=period, orders=len(g),
                **{f'{c}_rate': float(g[c].mean()) for c in order_components.columns}))
    pd.DataFrame(completeness).to_csv(out/'tables/data_completeness_by_period.csv', index=False)
