# Ứng dụng Streamlit

## Kiến trúc giao diện

Ứng dụng tại `approval_prediction/app/app.py`, dùng ba khu vực chính:

| Trang | Nội dung | Giới hạn |
|---|---|---|
| **Overview** | KPI ở grain đơn, xu hướng lượng, cơ cấu và tình trạng dữ liệu | Tổng lượng không phải doanh thu/giao hàng |
| **EDA** | Phân tích thời gian, mã/họ sản phẩm, RFV và kiểm soát chất lượng | RFV là snapshot, không tái phân khúc tự động theo bộ lọc |
| **Prediction** | Xác suất WIN/LOST, lịch sử tổng hợp, so sánh bốn model và forecast nền | Không tự động duyệt đơn hoặc đưa dự báo realtime mới ngoài snapshot |

## Bộ lọc và kết quả

- Overview/EDA hỗ trợ lọc tháng, mã khách, loại đơn bán. Các KPI và biểu đồ thuộc cùng tập khóa đơn khi cùng phạm vi lọc; biểu đồ sản phẩm ghi rõ cấp phân tích (reference code, generic hoặc họ sản phẩm).
- Prediction nhận mã khách, tháng/năm và model đang xem. Một lần bấm phân tích tạo một vector 12 features lịch sử và chạy **cả bốn model** theo cùng đầu vào, hiển thị probability, nhãn và threshold của từng model.
- Mô hình mặc định dùng lựa chọn trên validation; đổi model chỉ đổi card tóm tắt sang kết quả đã tính, không tạo phép dự đoán mới không nhất quán.
- Lịch sử WIN/LOST của khách chỉ mang tính **mô tả hồi cứu**, không tham gia features của model. Không có lịch sử thì hiển thị “chưa có dữ liệu”, không tự gán tỷ lệ WIN bằng 0.
- Nếu một model inference lỗi, hiển thị lỗi tương ứng; không thay bằng kết quả giả. Dự báo tháng nằm ngoài dữ liệu quan sát phải có cảnh báo về phạm vi ngoại suy.
- Forecast cho xem các horizon **1–6 tháng** thuộc snapshot đã lưu; không tự suy thêm khoảng tin cậy hay dự báo cho một khách/SKU khi chưa có model tương ứng.

## Kỹ thuật và bảo mật khi chia sẻ

Ứng dụng chỉ load data/model bundle cục bộ, sử dụng cache cho bảng và resources; kiểm tra tương thích schema, version và hash. Không train trong giao diện. Thiếu model/dữ liệu cần phát thông báo rõ thay vì âm thầm sinh số.

Không đưa lên GitHub hoặc Streamlit Community Cloud công khai các artifact, Excel, khách hàng, dashboard có định danh, URL kết nối nội bộ hoặc `.streamlit/secrets.toml`. Repository công khai không chứa dữ liệu thật thì app có thể **không chạy đầy đủ**; muốn có demo public, cần xây **bộ dữ liệu tổng hợp nhân tạo riêng** và đánh giá lại kết quả trên bộ đó. Không lấy dữ liệu doanh nghiệp rồi đơn thuần thay tên cột/khách và xem là đã ẩn danh an toàn.
