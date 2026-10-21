# Dự báo sản lượng KM nền theo tháng

## 1. Bài toán và phạm vi

Dự báo trên chuỗi tháng của **sản lượng KM nền** của đơn bán, sau khi tách các dự án đã xác nhận và các dòng cực trị thống kê. Đây là thí nghiệm baseline phục vụ phân tích, **không phải dự báo toàn bộ nhu cầu, doanh thu hoặc kế hoạch giao hàng chính thức**.

| Mốc / kết quả | Giá trị |
|---|---|
| Lịch sử quan sát | 2023-01 – 2025-12 |
| Validation dạng rolling | 2024-01 – 2025-06 (3 folds) |
| Holdout test không dùng để chọn mô hình | 2025-07 – 2025-12 |
| Mô hình chọn trên validation | **EWMA hiệu chỉnh alpha = 0.5** |
| Validation WAPE | **139.04%** |
| Test WAPE | **69.14%** |
| Bản forecast đã đóng băng | 2026-01 – 2026-06 |

Kết quả dự báo được lưu như snapshot của lần huấn luyện. Khoảng 2026-01 – 2026-06 không còn là tương lai tại thời điểm xem nếu thời gian đã đi qua; chỉ có thể gọi là **forecast được tạo cho giai đoạn đó**, không gọi là dự báo live mới nhất.

## 2. Phương pháp

- Các ứng viên: **Naive**, **Historical Mean**, **Seasonal Naive** (khi đủ lịch sử) và **adjusted EWMA**. Ứng viên điều chỉnh EWMA dùng `level × (1 − alpha/2)` với `alpha = 0.5` trong snapshot được chọn; đây là **công thức heuristic**, không phải hiệu chỉnh sai lệch đã được chứng minh tối ưu.
- Đánh giá validation theo **rolling-origin** và cùng quy định horizon; chọn theo pooled validation **WAPE**, hòa thì xét **MAE**, tiếp theo tên mô hình.
- Cờ ngoại lệ của mart tính toàn kỳ chỉ phục vụ mô tả. Trong đánh giá mô hình, **ngưỡng outlier được fit trên tập train của từng fold** rồi cố định cho phần validation/test tương ứng; không fit threshold bằng toàn bộ dữ liệu trước khi đánh giá.
- Holdout chỉ dùng đo hiệu năng sau khi chọn mô hình. Sau đó mô hình được refit trên lịch sử được phép và sinh forecast 6 tháng của snapshot.
- Chuỗi thời gian dựng lịch trước khi lọc dự án/cực trị; tháng không có lượng nền được ghi 0 dưới giả định tracker hoàn chỉnh. Các dòng có lượng trống vẫn là unknown.

## 3. Đánh giá và giới hạn

**WAPE = 100 × tổng |actual − prediction| / tổng |actual|** trên cùng tập kỳ; khi mẫu số gần 0, WAPE không ổn định hoặc không xác định nên phải báo thêm MAE. **MAE** có đơn vị KM và được giữ trong kết quả nội bộ; không công bố giá trị KM tuyệt đối trong tài liệu GitHub.

WAPE validation 139.04% cho thấy sai số cao; WAPE test 69.14% vẫn chưa đủ cơ sở dùng baseline này để ra quyết định kế hoạch. Hai tập có mức sai số khác nhau, không được khẳng định mô hình có độ chính xác ổn định. Lịch sử ngắn, nhiễu do dự án/cực trị, tháng thưa và giả định nguồn đầy đủ là các rủi ro chính. **Không có prediction interval đã được hiệu chuẩn.**

Holdout hồi cứu có nguy cơ *prior analyst exposure*; khả năng dự báo thực tế cần được kiểm chứng **prospective** trên kỳ phát sinh sau thời điểm đóng băng dự báo. `prospective.py` lưu thời điểm phát hành thật và chỉ chấm kỳ hoàn tất khi người dùng xác nhận nguồn đã đầy đủ, không lùi ngày phát hành.
