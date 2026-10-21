import streamlit as st


def metric_card(title, value, subtitle=None):
    st.metric(title, value, help=subtitle)


def metric_grid(items):
    for col, item in zip(st.columns(len(items)), items):
        with col:
            metric_card(*item)
