import streamlit as st


def info_box(title, text):
    st.info(f'**{title}** · {text}')


def page_header(title, subtitle):
    st.subheader(title)
    st.caption(subtitle)


def section_header(title, subtitle=None):
    st.subheader(title)
    if subtitle:
        st.caption(subtitle)
