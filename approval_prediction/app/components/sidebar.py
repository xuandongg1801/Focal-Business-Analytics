import streamlit as st
PAGES = ['Overview', 'EDA', 'Prediction']


def sidebar():
    with st.sidebar:
        st.markdown('<div class="brand">FOCAL <span>ANALYTICS</span></div>', unsafe_allow_html=True)
        st.caption('ĐƠN HÀNG · SẢN LƯỢNG · KHÁCH HÀNG')
        selected = st.radio('Điều hướng', PAGES, key='navigation', label_visibility='collapsed')
        st.caption('Dữ liệu thực • mô hình nghiên cứu')
    return PAGES.index(selected)
