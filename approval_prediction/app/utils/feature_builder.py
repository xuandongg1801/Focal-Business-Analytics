"""Inference adapter: history_features is also called by training."""
import pandas as pd
import numpy as np
from approval_prediction.data import history_features
from approval_prediction.config import FEATURES

def build_transaction(customer_id, transaction_date, history):
    when = pd.Timestamp(transaction_date)
    if pd.isna(when): raise ValueError('Ngày giao dịch không hợp lệ.')
    customer_id = '' if pd.isna(customer_id) else str(customer_id)
    month = when.strftime('%Y-%m')
    values = history_features(customer_id, month, history)
    return pd.DataFrame([values], columns=FEATURES).astype('float64')

def customer_summary(customer_id, transaction_date, history):
    month = pd.Timestamp(transaction_date).strftime('%Y-%m')
    past = history[history.customer_id.eq(customer_id) & history.order_month.lt(month)] if customer_id else history.iloc[:0]
    if not past.chot_don.isin([0, 1]).all():
        raise ValueError('Customer history must contain binary WIN/LOST labels')
    return dict(last_date=past.order_date.max() if len(past) else None,
                total_orders=len(past), win_count=int(past.chot_don.eq(1).sum()),
                lost_count=int(past.chot_don.eq(0).sum()),
                win_rate=float(past.chot_don.eq(1).sum()/len(past)) if len(past) else np.nan)
