import pandas as pd
import streamlit as st
from . import predict, model_comparison, explainability
from ..utils.analytics import load_analytics, quantity_layers
from ..utils.data_loader import _csv, _json, stamp
from approval_prediction.config import ROOT
from ..components.analytics_charts import forecast


def render():
    st.title('Prediction')
    st.write('Ước lượng từ mô hình đã huấn luyện, với ngưỡng và phương pháp đánh giá được lưu cùng artifacts.')
    classification, forecasting, evaluation, explanation = st.tabs(['Phân loại giao dịch', 'Dự báo sản lượng', 'Đánh giá mô hình', 'Giải thích'])
    with classification:
        predict.render()
    with forecasting:
        folder = ROOT/'outputs/tables'
        method = _json(stamp(folder/'forecast_methodology.json'))
        future = _csv(stamp(folder/'forecast.csv'))
        st.subheader('Snapshot dự báo cố định')
        st.caption('Được tính từ lịch sử đến ' + method['history_end'] + '. Holdout bên dưới là backtest riêng; snapshot không có actual mới để đánh giá và không phải dự báo live.')
        if pd.Period(future.thang.iloc[-1], freq='M') < pd.Timestamp.today().to_period('M'):
            st.warning('Kỳ snapshot đã qua. Cần dữ liệu nguồn mới trước khi phát hành dự báo cho kỳ hiện tại.')
        st.selectbox('Chuỗi dự báo', ['Tổng KM nền của đơn bán'], disabled=True)
        horizon = st.slider('Số tháng hiển thị', 1, len(future), len(future), key='forecast_horizon')
        history = load_analytics().items
        history = history[history.la_don_ban_hang & quantity_layers(history).eq('Nền')]
        historical = history.groupby('order_month').so_luong_km.sum(min_count=1).reindex(
            pd.period_range(method['history_start'], method['history_end'], freq='M').astype(str), fill_value=0).rename('km').rename_axis('month').reset_index()
        a, b, c = st.columns(3)
        a.metric('Cuối dữ liệu refit', method['history_end'])
        b.metric('Tháng bắt đầu dự báo', future.thang.iloc[0])
        c.metric('Holdout WAPE', f"{method['test_wape_pct']:.2f}%" if method['test_wape_pct'] is not None else 'Không xác định')
        st.caption(f"Mô hình: {method['selected_model']} · validation WAPE {method['validation_wape_pct']:.2f}% · holdout {method['test_start']} → {method['test_end']}")
        st.plotly_chart(forecast(historical, future.head(horizon)), width='stretch')
        st.dataframe(future.head(horizon), hide_index=True, width='stretch')
        st.info('Dự báo nền có sai số cao, không gồm dự án tương lai. Chưa có khoảng dự báo được hiệu chuẩn. Horizon chỉ hiển thị các tháng mô hình đã tạo.')
    with evaluation:
        model_comparison.render()
    with explanation:
        explainability.render()
