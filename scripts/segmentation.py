"""Descriptive RFV segmentation: recency, frequency, volume (not revenue)."""
import numpy as np
import pandas as pd

LABEL_RECENT = 'Gần đây, thường xuyên, lượng cao'
LABEL_INACTIVE = 'Ít giao dịch gần đây'
LABEL_FREQUENT = 'Tần suất cao'
LABEL_OTHER = 'Nhóm còn lại'


def relative_score(values: pd.Series, higher_is_better: bool) -> pd.Series:
    """Empirical quartiles 1..4; ties share average rank, no arbitrary tie splitting."""
    if values.isna().any() or not np.isfinite(values).all() or values.lt(0).any():
        raise ValueError('RFV scores require finite, nonnegative observations')
    return np.ceil(values.rank(method='average', pct=True, ascending=higher_is_better) * 4).astype(int)


def segment_labels(scores: pd.DataFrame) -> pd.Series:
    for name in ['r_score', 'f_score', 'v_score']:
        if not scores[name].isin([1, 2, 3, 4]).all():
            raise ValueError(f'Invalid quartile score: {name}')
    return pd.Series(np.select([
        scores.r_score.eq(1),
        scores.r_score.ge(3) & scores.f_score.ge(3) & scores.v_score.ge(3),
        scores.f_score.ge(3),
    ], [LABEL_INACTIVE, LABEL_RECENT, LABEL_FREQUENT], default=LABEL_OTHER), index=scores.index)
