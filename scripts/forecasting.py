"""Temporal selection and one final test; item thresholds are fitted on train only."""
from functools import partial
import numpy as np
import pandas as pd
from config import (FORECAST_HORIZON, MIN_TRAIN_MONTHS, MAX_VALIDATION_FOLDS,
                    EWMA_ALPHAS, CONFIRMED_PROJECT_ORDERS, WAPE_EPSILON,
                    HOLDOUT_MONTHS, VALIDATION_MONTHS, HISTORICAL_EXTERNAL_EXPOSURE)
from data_rules import monthly_series, observation_months, fit_item_outlier_threshold, item_outlier_mask, sales_km


def wape(actual: np.ndarray, pred: np.ndarray) -> float:
    denom = np.abs(actual).sum()
    return float(np.abs(actual - pred).sum() / denom * 100) if denom > WAPE_EPSILON else np.nan


def ewma(train: np.ndarray, horizon: int, alpha: float) -> np.ndarray:
    """Existing adjusted EWMA candidate; alpha is selected on validation only."""
    level = float(train[0])
    for value in train[1:]:
        level = alpha * value + (1 - alpha) * level
    return np.full(horizon, max(0, (1 - alpha / 2) * level))


def candidates(min_train: int) -> dict:
    funcs = {'Naive': lambda train, h: np.full(h, train[-1]),
             'Historical Mean': lambda train, h: np.full(h, np.mean(train))}
    if min_train >= 12:
        funcs['Seasonal Naive'] = lambda train, h: np.resize(train[-12:], h)
    for alpha in EWMA_ALPHAS:
        funcs[f'EWMA hiệu chỉnh alpha={alpha:g}'] = partial(ewma, alpha=alpha)
    return funcs


def temporal_plan(n: int, validation_months: int = VALIDATION_MONTHS,
                  holdout_months: int = HOLDOUT_MONTHS) -> tuple[list[int], int, int]:
    """Evaluation windows are configured independently of future forecast horizon."""
    if min(validation_months, holdout_months) < 1:
        raise ValueError('Evaluation windows must be positive')
    if n < 5:
        raise ValueError('At least 5 months required for train/validation/test')
    evaluation_horizon = min(validation_months, max(1, n // 5))
    test_start = n - min(holdout_months, max(1, n // 5))
    min_train = min(MIN_TRAIN_MONTHS, test_start - evaluation_horizon)
    origins = list(range(test_start - evaluation_horizon, min_train - 1, -evaluation_horizon))
    origins = sorted(origins[:MAX_VALIDATION_FOLDS])
    if not origins:
        raise ValueError('Insufficient temporal validation data')
    return origins, test_start, evaluation_horizon


def prepare_split(items: pd.DataFrame, index: pd.PeriodIndex, origin: int,
                  horizon: int) -> tuple[np.ndarray, np.ndarray, float]:
    """No full-mart outlier flag is read. Freeze train threshold for validation/test."""
    train_rows = items[items['order_month'] < str(index[origin])]
    threshold = fit_item_outlier_threshold(train_rows)
    allowed = ~items['so_xac_nhan_don_hang'].isin(CONFIRMED_PROJECT_ORDERS)
    clean = items[allowed & ~item_outlier_mask(items, threshold)]
    train = monthly_series(clean[clean['order_month'] < str(index[origin])], index[:origin])
    actual_rows = clean[clean['order_month'].isin(index[origin:origin+horizon].astype(str))]
    actual = monthly_series(actual_rows, index[origin:origin+horizon])
    return train.to_numpy(), actual.to_numpy(), threshold


def validate_candidates(items, idx, origins, eval_horizon, funcs):
    """This function receives only pre-holdout rows from the caller."""
    records = []
    for origin in origins:
        train, actual, threshold = prepare_split(items, idx, origin, eval_horizon)
        for name, func in funcs.items():
            pred = func(train, eval_horizon)
            records.append(dict(mo_hinh=name, train_start=str(idx[0]), diem_cat=str(idx[origin-1]),
                                validation_start=str(idx[origin]), validation_end=str(idx[origin+eval_horizon-1]),
                                outlier_threshold_km=threshold, wape_pct=wape(actual, pred),
                                mae_km=float(np.abs(actual-pred).mean()),
                                absolute_error=float(np.abs(actual-pred).sum()), actual_km=float(np.abs(actual).sum())))
    detail = pd.DataFrame(records)
    comparison = detail.groupby('mo_hinh', sort=True).agg(
        wape_trung_binh_pct=('wape_pct', 'mean'), mae_trung_binh_km=('mae_km', 'mean'),
        absolute_error=('absolute_error', 'sum'), actual_km=('actual_km', 'sum'), folds=('diem_cat', 'size')).reset_index()
    denominator = comparison['actual_km'].where(comparison['actual_km'] > WAPE_EPSILON)
    comparison['selection_wape_pct'] = comparison['absolute_error'].div(denominator) * 100
    comparison = comparison.sort_values(['selection_wape_pct', 'mae_trung_binh_km', 'mo_hinh'], na_position='last')
    selected = comparison.iloc[0]['mo_hinh']
    return detail, comparison, selected


def evaluate_candidates(items, idx, test_start, funcs, selected):
    """Post-selection diagnostics for all frozen candidates; never rank on test."""
    horizon = len(idx) - test_start
    train, actual, threshold = prepare_split(items, idx, test_start, horizon)
    rows, selected_test = [], None
    for name, func in funcs.items():
        pred = func(train, horizon)
        rows.append({'mo_hinh': name, 'holdout_wape_pct': wape(actual, pred),
                     'holdout_mae_km': float(np.abs(actual-pred).mean()), 'selected_on_validation': name == selected})
        if name == selected:
            selected_test = pd.DataFrame({'thang': idx[test_start:].astype(str), 'actual_km': actual, 'prediction_km': pred})
    return selected_test, pd.DataFrame(rows), threshold


def run_forecast(items: pd.DataFrame, horizon: int = FORECAST_HORIZON) -> dict:
    """Validation -> locked choice -> holdout diagnostics -> full-history refit."""
    if not isinstance(horizon, int) or isinstance(horizon, bool) or horizon < 1:
        raise ValueError('horizon must be a positive integer')
    items = items.loc[sales_km(items)].copy()
    idx = observation_months(items)
    origins, test_start, eval_horizon = temporal_plan(len(idx))
    funcs = candidates(min(origins))
    development = items[items['order_month'] < str(idx[test_start])]
    detail, comparison, selected = validate_candidates(development, idx[:test_start], origins, eval_horizon, funcs)
    test, holdout_comparison, threshold = evaluate_candidates(items, idx, test_start, funcs, selected)
    selected_test = holdout_comparison.loc[holdout_comparison['selected_on_validation']].iloc[0]
    final_threshold = fit_item_outlier_threshold(items)
    baseline_rows = items[~item_outlier_mask(items, final_threshold) & ~items['so_xac_nhan_don_hang'].isin(CONFIRMED_PROJECT_ORDERS)]
    baseline = monthly_series(baseline_rows, idx)
    future = pd.period_range(idx[-1]+1, periods=horizon, freq='M')
    forecast = funcs[selected](baseline.to_numpy(), horizon)
    if not np.isfinite(forecast).all() or (forecast < 0).any():
        raise ValueError('Forecast must be finite and nonnegative')
    limitations = ['Forecast is a weak reference baseline due to limited history / noisy demand / sparse observations.',
                   'The historical holdout has prior analyst exposure; prospective evaluation requires observations unavailable at model issuance.',
                   'Months without eligible rows inside the observed span are treated as zero; source completeness is assumed.',
                   'Metrics describe baseline KM filtered using the training threshold, not unfiltered total demand.']
    if comparison['selection_wape_pct'].isna().all():
        limitations.append('Validation WAPE is undefined because actual KM is near zero; selection uses MAE.')
    if len(origins) < 3:
        limitations.append(f'Only {len(origins)} validation folds; selection uncertainty is high.')
    if eval_horizon < VALIDATION_MONTHS or len(idx)-test_start < HOLDOUT_MONTHS:
        limitations.append(f'Short history: validation window {eval_horizon}, holdout window {len(idx)-test_start}; forecast horizon {horizon}.')
    metrics = dict(history_start=str(idx[0]), history_end=str(idx[-1]), final_train_start=str(idx[0]),
                   final_train_end=str(idx[-1]), selection_train_end=str(idx[test_start-1]),
                   test_start=str(idx[test_start]), test_end=str(idx[-1]), validation_folds=len(origins),
                   validation_start=str(idx[min(origins)]), validation_end=str(idx[test_start-1]),
                   evaluation_horizon=len(idx)-test_start, validation_horizon=eval_horizon,
                   forecast_start=str(future[0]), forecast_end=str(future[-1]),
                   forecast_horizon=horizon, selected_model=selected,
                   validation_wape_pct=(None if pd.isna(comparison.iloc[0]['selection_wape_pct']) else float(comparison.iloc[0]['selection_wape_pct'])),
                   validation_mae_km=float(comparison.iloc[0]['mae_trung_binh_km']),
                   test_wape_pct=None if pd.isna(selected_test['holdout_wape_pct']) else float(selected_test['holdout_wape_pct']),
                   test_mae_km=float(selected_test['holdout_mae_km']), test_threshold_km=threshold,
                   final_threshold_km=final_threshold, holdout_used_for_tuning=False,
                   pipeline_holdout_leakage=False, historical_external_exposure=HISTORICAL_EXTERNAL_EXPOSURE,
                   history_end_semantics='last_observed_sales_km_month_before_project_and_item_outlier_filtering',
                   last_eligible_demand_month=(str(baseline_rows['order_month'].max()) if not baseline_rows.empty else None),
                   confirmed_project_orders=sorted(CONFIRMED_PROJECT_ORDERS),
                   limitations=limitations)
    return dict(baseline=baseline, future=future, forecast=forecast, comparison=comparison,
                detail=detail, test=test, holdout_comparison=holdout_comparison, metrics=metrics)
