"""Cached analytical inputs and pure, grain-aware aggregations for the app."""
from dataclasses import dataclass
import pandas as pd
import streamlit as st
from .data_loader import _csv, stamp, ArtifactError
from approval_prediction.config import ROOT


@dataclass
class AnalyticsData:
    orders: pd.DataFrame
    items: pd.DataFrame
    products: pd.DataFrame
    rfv: pd.DataFrame


def load_analytics() -> AnalyticsData:
    h, i, p = [_csv(stamp(ROOT/'data/processed'/name)) for name in
               ['fact_order_header.csv', 'mart_order_items.csv', 'mart_product_items.csv']]
    rfv = _csv(stamp(ROOT/'outputs/tables/customer_rfm_segments.csv'))
    if not h.order_row_id.is_unique or not i.item_id.is_unique or not p.product_item_id.is_unique:
        raise ArtifactError('Khóa bảng phân tích bị trùng. Chạy verify_project.py để kiểm tra dữ liệu.')
    return AnalyticsData(h, i, p, rfv)


def filtered(data: AnalyticsData, start: str, end: str, customers: list[str], types: list[str]) -> AnalyticsData:
    h = data.orders
    mask = h.la_don_ban_hang & h.order_month.between(start, end) & h.loai_don.isin(types)
    if customers:
        mask &= h.ma_khach.fillna('Thiếu mã khách').isin(customers)
    h = h[mask].copy()
    return AnalyticsData(h, data.items[data.items.order_row_id.isin(h.order_row_id)].copy(),
        data.products[data.products.order_row_id.isin(h.order_row_id)].copy(),
        data.rfv[data.rfv.ma_khach.isin(h.ma_khach.dropna())].copy())


def quantity_layers(items: pd.DataFrame) -> pd.Series:
    return pd.Series('Nền', index=items.index).mask(items.nghi_ngo_outlier, 'Cực trị thống kê').mask(
        items.outlier_duoc_xac_nhan_la_phat_sinh_that, 'Dự án xác nhận')


def monthly(data: AnalyticsData, start: str, end: str) -> pd.DataFrame:
    calendar = pd.period_range(start, end, freq='M').astype(str)
    orders = data.orders.groupby('order_month').size().reindex(calendar, fill_value=0)
    rows = data.items.assign(layer=quantity_layers(data.items))
    quantities = rows.groupby(['order_month', 'layer']).so_luong_km.sum(min_count=1).unstack('layer')
    result = quantities.reindex(calendar).reindex(columns=['Nền', 'Dự án xác nhận', 'Cực trị thống kê']).fillna(0)
    result['Số đơn'] = orders
    result['Thiếu lượng'] = data.items.groupby('order_month').so_luong.apply(lambda s: s.isna().sum()).reindex(calendar, fill_value=0)
    return result.rename_axis('Tháng').reset_index()


def kpis(data: AnalyticsData) -> dict:
    i = data.items
    return dict(orders=len(data.orders), km=i.so_luong_km.sum(min_count=1),
                customers=data.orders.ma_khach.nunique(), unresolved=int(i.allocation_status.eq('unresolved').sum()),
                missing=int(i.so_luong.isna().sum()), source_rows=len(i))


def product_totals(data: AnalyticsData, level: str = 'reference') -> pd.DataFrame:
    if level not in {'reference', 'generic', 'family'}:
        raise ValueError('Unknown product analytical level')
    rows = data.products
    field = 'canonical_product_code'
    if level == 'reference':
        rows = rows[rows.is_reference_product_code]
    elif level == 'generic':
        rows = rows[rows.parse_status.eq('recognized_generic')]
        field = 'product_family_code'
    else:
        field = 'nhom_san_pham_don_hang'
    return rows.groupby(field).so_luong_km.sum(min_count=1).dropna().sort_values(ascending=False).rename('KM').reset_index()


def observations(data: AnalyticsData) -> list[str]:
    values = kpis(data)
    if not values['orders']:
        return []
    total = values['km']
    project = data.items.loc[data.items.outlier_duoc_xac_nhan_la_phat_sinh_that, 'so_luong_km'].sum()
    notes = [f"{len(data.orders):,} đơn bán trong phạm vi đã chọn; {data.orders.ma_khach.isna().sum():,} đơn chưa ghi mã khách."]
    if pd.notna(total) and total > 0:
        notes.append(f"Dự án xác nhận đóng góp {project/total:.1%} KM ghi nhận. Tách phần này khi lập kế hoạch nhu cầu nền.")
        notes.append(f"{data.products.so_luong_km.sum()/total:.1%} KM đã quy thuộc mã tham chiếu hoặc quy cách chung; xếp hạng mã tham chiếu chỉ dùng phần khớp reference.")
    notes.append(f"{values['missing']:,}/{values['source_rows']:,} dòng thiếu lượng; tổng KM quan sát không đại diện phần lượng chưa ghi nhận.")
    notes.append(f"{data.orders.order_month_conflict.sum():,} đơn có ngày và mã đơn khác tháng; chart dùng tháng canonical theo quy tắc nguồn.")
    return notes


def filters(data: AnalyticsData) -> tuple[AnalyticsData, str, str]:
    h = data.orders[data.orders.la_don_ban_hang]
    months = pd.period_range(h.order_month.min(), h.order_month.max(), freq='M').astype(str).tolist()
    with st.sidebar:
        st.divider()
        st.caption('PHẠM VI PHÂN TÍCH · ĐƠN BÁN')
        start, end = st.select_slider('Khoảng tháng', options=months, value=(months[0], months[-1]), key='analysis_months')
        codes = sorted(h.ma_khach.dropna().unique().tolist()) + ['Thiếu mã khách']
        customers = st.multiselect('Mã khách hàng', codes, placeholder='Tất cả khách hàng', key='analysis_customers')
        types = st.multiselect('Loại đơn bán', sorted(h.loai_don.unique()), default=sorted(h.loai_don.unique()), key='analysis_types',
            format_func=lambda value: {'Đơn khách hàng - Năng lượng mặt trời':'NLMT',
                                       'Đơn khách hàng - Phụ kiện quang':'Phụ kiện'}.get(value, value.removeprefix('Đơn khách hàng - ')),
            help='NLMT: Năng lượng mặt trời. Phụ kiện: Phụ kiện quang. Bộ lọc giữ nguyên loại đơn nguồn.')
    st.caption(f'Đơn bán · {start} → {end} · Khách: {", ".join(customers) if customers else "tất cả"} · {len(types)} loại đơn')
    return filtered(data, start, end, customers, types), start, end
