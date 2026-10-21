import streamlit as st
from ..utils.analytics import load_analytics, filters, kpis, monthly, product_totals, observations
from ..utils.formatting import number
from ..components.analytics_charts import trend, ranking


def render():
    st.title('Overview')
    st.write('Theo dõi đơn bán, sản lượng ghi nhận và mức độ đầy đủ của dữ liệu kinh doanh.')
    data, start, end = filters(load_analytics())
    values = kpis(data)
    cards = [('Đơn bán', values['orders'], 'Đếm một lần mỗi mã xác nhận đơn hàng'),
             ('KM ghi nhận', values['km'], 'KM và M/1.000; gồm dự án, cực trị; chưa có lượng thiếu'),
             ('Mã khách ghi nhận', values['customers'], 'Mã không rỗng trong đơn; không suy từ hậu tố'),
             ('Chưa quy thuộc mã', values['unresolved'], 'Số dòng mô tả chưa ánh xạ hoặc nhiều mã chưa phân bổ'),
             ('Dòng thiếu lượng', values['missing'], 'Giữ null, không điền bằng 0')]
    for column, (label, value, help_text) in zip(st.columns(5), cards):
        column.metric(label, number(value), help=help_text)
    if data.orders.empty:
        st.info('Không có đơn phù hợp. Hãy mở rộng khoảng tháng hoặc bộ lọc khách hàng/loại đơn.')
        return
    mode = st.segmented_control('Chỉ tiêu xu hướng', ['Sản lượng KM', 'Số đơn'], default='Sản lượng KM')
    st.plotly_chart(trend(monthly(data, start, end), orders=mode == 'Số đơn'), width='stretch')
    st.caption('Tổng lượng quan sát. Tháng không có lượng ghi nhận hiển thị 0; dòng thiếu lượng được đếm riêng.')
    left, right = st.columns(2)
    with left:
        st.plotly_chart(ranking(product_totals(data), 'canonical_product_code', 'KM', 'Mã tham chiếu dẫn đầu · khớp danh mục/bảng giá'), width='stretch')
    with right:
        customers = data.items[data.items.co_ma_khach_chinh_thuc].groupby('ma_khach').so_luong_km.sum(min_count=1).rename('KM').reset_index()
        st.plotly_chart(ranking(customers, 'ma_khach', 'KM', 'Khách có mã chính thức · KM ghi nhận'), width='stretch')
    st.subheader('Điểm cần chú ý')
    for note in observations(data):
        st.markdown('- '+note)
