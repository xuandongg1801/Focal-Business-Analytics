# Phân tích khám phá dữ liệu (EDA)

## Câu hỏi phân tích

EDA nhằm quan sát biến động quy mô đơn và lượng hàng ghi nhận theo thời gian, cơ cấu dòng sản phẩm, phân phối khách hàng, chất lượng dữ liệu và các quan sát nổi bật. Kết quả chỉ mô tả **đơn và sản lượng ghi trong tracker**, không đo lượng giao thực tế, doanh thu, lợi nhuận hay tỷ lệ chuyển đổi của thị trường.

## Khung tính toán

| Nhóm phân tích | Cách tính / điều kiện | Giới hạn diễn giải |
|---|---|---|
| Số đơn | Đếm khóa đơn ở `fact_order_header` | Không đếm `fact_order_items` |
| KM theo thời gian | Cộng dòng đơn bán có KM đã chuyển đổi hợp lệ | Dòng thiếu lượng giữ unknown; các đơn vị khác không trộn |
| Quy mô đơn | Gom KM theo khóa đơn, sau đó phân tích trung bình/trung vị | Chỉ các đơn có KM quan sát được |
| Cơ cấu sản phẩm | Trên lượng sản phẩm quy thuộc ở `mart_product_items` | Không dùng hàng unresolved như mã giả |
| Phân tích ABC | Sắp giảm dần lượng KM, gán A/B/C theo tỷ lệ tích lũy 80%/95% | Tử và mẫu chỉ thuộc sản lượng đã quy thuộc |
| Khách hàng | Đối chiếu mã khách chính thức; trường hợp suy diễn chỉ dùng cho thống kê mô tả | Không dùng nhóm suy diễn làm định danh khách trong RFV/model |
| WO / mã sản xuất | Tỷ lệ đơn có giá trị trường tương ứng | Không xác nhận tình trạng giao hàng |

## Cách tách sản lượng

Sản lượng có thể được chia thành các nhóm **không chồng lấn** cho mục đích diễn giải: (1) dự án được đánh dấu xác nhận, (2) ngoại lệ cực trị theo phương pháp thống kê và (3) phần **nền** còn lại. “Không cực trị” vẫn có thể gồm dự án; **nền = loại cả dự án lẫn cực trị**, không phải cam kết nhu cầu lặp lại.

Tháng nằm trong lịch theo dõi nhưng không có dòng KM phù hợp được biểu diễn bằng 0 trong chuỗi aggregate, **chỉ khi giả định tracker đã ghi nhận đầy đủ**. Các ô lượng bỏ trống trên dòng thật không phải giá trị 0.

## Nhận xét và tính thận trọng

- Chênh lệch giá trị trung bình với trung vị có thể phản ánh vài đơn lớn; cần xem biểu đồ phân phối trước khi diễn giải “đơn điển hình”.
- Nhóm generic có thể tham gia cơ cấu **họ** sản phẩm nhưng không tự tạo thêm mã tham chiếu chuẩn để xếp hạng mã.
- Với ABC, mẫu số không đại diện tổng nguồn nếu vẫn tồn tại dòng unresolved. Cần báo cả phần độ phủ quy thuộc, không chỉ phần trăm A/B/C.
- Nhóm khách tạo ra từ hậu tố mã đơn không xác định được khách pháp lý và có thể gom nhiều giao dịch không cùng khách.

Biểu đồ đầu ra cục bộ do `scripts/04_eda.py` tạo. Không đưa biểu đồ có tên khách, mã sản phẩm nội bộ, đơn giá hoặc lượng giao dịch nhận diện được lên GitHub công khai nếu chưa ẩn thông tin và được phép phát hành.
