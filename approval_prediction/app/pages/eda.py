import pandas as pd
import streamlit as st
from ..utils.analytics import load_analytics, filters, monthly, product_totals
from ..components.analytics_charts import trend, ranking


def render():
    st.title('EDA')
    st.write('Đi từ xu hướng đến cơ cấu sản phẩm, khách hàng và chất lượng ghi nhận.')
    data, start, end = filters(load_analytics())
    if data.orders.empty:
        st.info('Không có dữ liệu trong phạm vi đã chọn. Hãy điều chỉnh bộ lọc.')
        return
    time, products, customers, quality = st.tabs(['Thời gian & đơn hàng', 'Sản phẩm', 'Khách hàng & RFV', 'Chất lượng dữ liệu'])
    with time:
        table = monthly(data, start, end)
        st.plotly_chart(trend(table, orders=True), width='stretch')
        st.dataframe(table, hide_index=True, width='stretch')
        quantities = data.items.groupby('order_row_id').so_luong_km.sum(min_count=1).dropna()
        st.metric('Trung vị KM/đơn có lượng', f'{quantities.median():,.2f}' if len(quantities) else 'Chưa có')
        st.caption('Mỗi đơn đếm một lần. Lượng theo đơn có thể chưa đầy đủ nếu còn item thiếu lượng.')
    with products:
        level = st.selectbox('Cấp phân tích sản phẩm', ['reference', 'generic', 'family'],
            format_func=lambda x: {'reference':'Mã tham chiếu chính xác', 'generic':'Quy cách chung chưa đủ biến thể', 'family':'Họ sản phẩm (gồm quy cách chung)'}[x])
        field = {'reference':'canonical_product_code', 'generic':'product_family_code', 'family':'nhom_san_pham_don_hang'}[level]
        table = product_totals(data, level)
        st.plotly_chart(ranking(table, field, 'KM', 'Sản lượng theo cấp sản phẩm đã chọn', 15), width='stretch')
        st.dataframe(table, hide_index=True, width='stretch')
        st.caption('Mã tham chiếu khớp danh mục hoặc bảng giá, có thể bao phủ nhiều quy cách kỹ thuật. Quy cách chung không phải SKU; không tự chọn LT/SQ. Họ sản phẩm gồm cả hai nhóm. Dòng chưa phân bổ giữ ngoài các xếp hạng.')
        st.metric('KM chưa quy thuộc mã', f'{data.items.loc[data.items.allocation_status.eq("unresolved"), "so_luong_km"].sum():,.3f}')
    with customers:
        st.caption('RFV dùng Recency, Frequency và Volume (KM), không phải doanh thu. Snapshot toàn lịch sử; bộ lọc chọn khách để xem, không tính lại điểm trong khoảng tháng.')
        if data.rfv.empty:
            st.info('Không có khách đủ điều kiện phân nhóm trong phạm vi này.')
        else:
            st.caption('Snapshot: '+str(data.rfv.snapshot_month.iloc[0])+' · khách khớp danh mục, đơn bán có KM và không bị cờ cực trị.')
            counts = data.rfv.groupby('phan_khuc').size().rename('Số khách').reset_index()
            st.plotly_chart(ranking(counts, 'phan_khuc', 'Số khách', 'Phân nhóm hành vi · quy tắc mô tả'), width='stretch')
            st.dataframe(data.rfv[['ma_khach','last_order_month','n_orders','total_km','recency_months','r_score','f_score','v_score','phan_khuc']], hide_index=True, width='stretch')
        st.info('“Ít giao dịch gần đây” là nhóm tứ phân vị theo recency, chưa chứng minh khách đã rời bỏ. Tên khách trong nguồn đã ẩn danh.')
    with quality:
        i, h = data.items, data.orders
        counts = pd.DataFrame({'Vấn đề':['Nhiều mã chưa phân bổ','Chưa ánh xạ mã','Xung đột tháng (đơn)','Thiếu mã khách (đơn)','Thiếu lượng (dòng)'],
            'Số lượng':[int((i.allocation_status.eq('unresolved') & i.product_candidates.fillna('').str.contains(' | ', regex=False)).sum()),
                       int(i.parse_status.eq('unmapped').sum()), int(h.order_month_conflict.sum()), int(h.ma_khach.isna().sum()), int(i.so_luong.isna().sum())]})
        st.dataframe(counts, hide_index=True, width='stretch')
        st.write('Dòng cần đối chiếu sản phẩm')
        unresolved = i[i.allocation_status.eq('unresolved')]
        st.dataframe(unresolved[['source_file','source_excel_row','item_text_raw','product_candidates','so_luong','don_vi','parse_reason']], hide_index=True, width='stretch')
        st.write('Đơn lệch tháng giữa ngày và mã')
        st.dataframe(h.loc[h.order_month_conflict, ['so_xac_nhan_don_hang','order_month_from_date','order_month_from_code','order_month_canonical','order_month_rule']], hide_index=True, width='stretch')
        duplicate = i[i.duplicated(['order_row_id','item_text_raw','so_luong','don_vi'], keep=False)]
        st.caption(f'{len(duplicate)} dòng cùng đơn/mô tả/lượng/đơn vị. Khác dòng nguồn nên giữ lại để đối chiếu; khóa kỹ thuật không được trùng.')
