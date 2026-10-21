import streamlit as st
from ..utils.formatting import model_name


def prediction_card(row, period=None):
    probability, threshold = float(row['probability']), float(row['threshold'])
    with st.container(border=True):
        st.subheader('Kết quả ước lượng' + (f' · {period}' if period else ''))
        st.caption(model_name(row['model']))
        st.metric('Khả năng WIN', f'{probability:.1%}')
        st.progress(probability)
        st.write(f"**Dự đoán: {row['predicted_class']}** · Ngưỡng phân loại {threshold:.1%}")
        st.caption('Xác suất chưa được hiệu chuẩn, không phải mức chắc chắn.')


def prediction_placeholder():
    with st.container(border=True):
        st.subheader('Kết quả dự báo')
        st.info('Chọn mã khách, tháng, năm, mô hình và nhấn Phân tích giao dịch.')
