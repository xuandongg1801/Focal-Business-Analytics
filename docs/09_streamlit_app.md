# Ứng dụng

Navigation: **Overview / EDA / Prediction**.
Overview: 5 KPI đúng grain, trend tách nền/dự án/cực trị, sản phẩm và khách dẫn đầu,
các nhận xét tính từ subset. EDA: thời gian/đơn, sản phẩm, khách/RFV, data quality.
Prediction: classification, forecast, đánh giá và giải thích trong sub-tabs.

Bộ lọc Overview/EDA: khoảng tháng, mã khách nguồn, loại đơn bán. KPI/chart trong trang dùng
cùng tập order IDs; product chart ghi rõ cấp tham chiếu, quy cách chung hoặc họ. RFV là snapshot toàn lịch sử, filter chỉ chọn khách để xem.
Prediction có input mã khách, tháng, năm và model selector đúng bốn lựa chọn. Cùng tháng dùng cùng features.
Mặc định theo validation; card chính hiện Khả năng WIN, WIN/LOST và threshold của model đã chọn.
Sau card là lịch sử khách hàng, rồi bảng so sánh bốn model cùng probability/threshold/class.
WIN rate = số WIN / tổng đơn trước tháng dự báo; không có lịch sử hiển thị chưa có, không giả tỷ lệ 0.
Thống kê kết quả lịch sử mang tính hồi cứu, không làm features vì nguồn thiếu timestamp kết quả.
Một lần bấm Phân tích giao dịch tạo features một lần, chạy bốn model và hiển thị card, lịch sử, bảng so sánh ngay.
Card lấy trực tiếp dòng model được chọn trong kết quả chung. Đổi model chỉ đổi card, không inference lại.
Đổi khách/tháng/năm hoặc artifact làm mất hiệu lực kết quả. Nếu một model lỗi inference, UI nêu tên model, giữ kết quả thành công và không thay thế hoặc tạo số giả. Ngoài kỳ dữ liệu vẫn mô phỏng và cảnh báo “Thời điểm dự đoán nằm ngoài kỳ dữ liệu lịch sử hiện có.”
Forecast chỉ cho chọn horizon 1..6 đã lưu, không suy interval hoặc dự báo từng khách/sản phẩm chưa có model.

cache_data khóa theo path/mtime/size cho dữ liệu; cache_resource cho model. Không train trong UI.
Thiếu/stale artifact có lỗi hướng dẫn build; lỗi bất ngờ được giữ để test/log phát hiện.
Chart builders thuần kiểm thử cả empty/nonempty. CSS tối thiểu, native widgets cho điều hướng/form/KPI.
