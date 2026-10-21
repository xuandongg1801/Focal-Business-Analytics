"""Local analytics application; paths resolve from the repository, independent of cwd."""
from pathlib import Path
import sys
ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
import streamlit as st
from approval_prediction.app.utils.paths import APP
from approval_prediction.app.utils.data_loader import validate_bundle, ArtifactError
from approval_prediction.app.components.sidebar import sidebar
from approval_prediction.app.pages import overview, eda, prediction

st.set_page_config(page_title='Focal Analytics', layout='wide', initial_sidebar_state='expanded')
st.markdown('<style>'+(APP/'styles/app.css').read_text(encoding='utf-8')+'</style>', unsafe_allow_html=True)


def main():
    page = sidebar()
    try:
        validate_bundle()
        [overview, eda, prediction][page].render()
        from datetime import datetime
        refreshed = datetime.fromtimestamp((ROOT/'data/processed/mart_order_items.csv').stat().st_mtime)
        st.divider()
        st.caption(f'FOCAL ANALYTICS · Nguồn: tracker và danh mục nội bộ · Dữ liệu được tạo: {refreshed:%d/%m/%Y %H:%M} · Snapshot dữ liệu hiển thị trong bộ lọc. Giá tham chiếu không phải doanh thu.')
    except ArtifactError as exc:
        st.error(str(exc))

st.navigation([st.Page(main, title='Focal Analytics')], position='hidden').run()
