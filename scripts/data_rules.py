"""Pure helpers shared by retrospective reporting and train-only preprocessing."""
import numpy as np
import pandas as pd
from config import CONFIRMED_PROJECT_ORDERS, OUTLIER_IQR_MULTIPLIER, ABC_LIMITS


def sales_km(df: pd.DataFrame) -> pd.Series:
    return df['la_don_ban_hang'].eq(True) & df['so_luong_km'].notna()


def fit_item_outlier_threshold(df: pd.DataFrame) -> float:
    """Fit log-IQR to sales item KM, excluding confirmed projects."""
    mask = sales_km(df) & ~df['so_xac_nhan_don_hang'].isin(CONFIRMED_PROJECT_ORDERS)
    values = df.loc[mask, 'so_luong_km'].astype(float)
    if not np.isfinite(values).all() or (values < 0).any():
        raise ValueError('KM must be finite and nonnegative')
    if values.empty:
        raise ValueError('No eligible item KM to fit outlier threshold')
    q1, q3 = np.log1p(values).quantile([0.25, 0.75])
    return float(np.expm1(q3 + OUTLIER_IQR_MULTIPLIER * (q3 - q1)))


def item_outlier_mask(df: pd.DataFrame, threshold: float) -> pd.Series:
    return (sales_km(df) & ~df['so_xac_nhan_don_hang'].isin(CONFIRMED_PROJECT_ORDERS)
            & df['so_luong_km'].gt(threshold))


def observation_months(df: pd.DataFrame) -> pd.PeriodIndex:
    """Observed sales calendar before filtering, not last eligible-demand month."""
    observed = df.loc[sales_km(df)]
    values = observed['so_luong_km'].to_numpy(dtype=float)
    if not np.isfinite(values).all() or (values < 0).any():
        raise ValueError('Observed sales KM must be finite and nonnegative')
    months = pd.PeriodIndex(observed['order_month'], freq='M')
    if months.empty or months.hasnans:
        raise ValueError('Valid historical months are required')
    return pd.period_range(months.min(), months.max(), freq='M')


def monthly_series(df: pd.DataFrame, index=None) -> pd.Series:
    """Sum eligible sales KM; interior empty months assume complete tracker coverage."""
    if index is None:
        index = observation_months(df)
    index = pd.PeriodIndex(index, freq='M')
    grouped = df.loc[sales_km(df)].groupby('order_month')['so_luong_km'].sum(min_count=1)
    grouped.index = pd.PeriodIndex(grouped.index, freq='M')
    return grouped.reindex(index, fill_value=0).astype(float)


def unpriced_metrics(df: pd.DataFrame) -> dict[str, float]:
    unpriced = df['so_luong_km'].notna() & ~df['co_don_gia_tham_khao']
    masks = {
        'unpriced_km_all_items_total': unpriced,
        'unpriced_km_sales_total': unpriced & sales_km(df),
        'unpriced_km_sales_non_outlier': unpriced & sales_km(df) & ~df['nghi_ngo_outlier'],
        'unpriced_km_sales_outlier': unpriced & sales_km(df) & df['nghi_ngo_outlier'],
        'unpriced_km_non_sales': unpriced & ~df['la_don_ban_hang'],
    }
    return {key: round(float(df.loc[mask, 'so_luong_km'].sum()), 3) for key, mask in masks.items()}


def abc_labels(values: pd.Series) -> pd.Series:
    # Include the item crossing the boundary; a dominant product must still be A.
    total = values.sum()
    before = (values.cumsum() - values) / total * 100 if total else values * 0
    return pd.Series(np.where(before < ABC_LIMITS[0], 'A',
                    np.where(before < ABC_LIMITS[1], 'B', 'C')), index=values.index)
