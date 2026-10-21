# Phân tích mô tả

Header đếm số đơn; sổ nguồn cộng lượng ghi nhận; product fact tách mã tham chiếu và quy cách chung. Xếp hạng/ABC mã chỉ dùng exact_reference; cơ cấu họ dùng cả hai.
KM nguồn gồm nền + dự án xác nhận + cực trị thống kê, ba phần không giao nhau.
KM không cực trị vẫn gồm dự án. Nền loại cả dự án và cực trị, không được gọi là nhu cầu chắc chắn lặp lại.
Các dòng thiếu lượng được đếm riêng, không thay bằng 0. Calendar trống là không có lượng ghi nhận,
không chứng minh nhu cầu bằng 0. Không cộng M/KG/BỘ/CÁI vào KM ngoài quy đổi M/1.000.

ABC xếp giảm dần KM của sản phẩm có attribution hợp lệ, ngưỡng tích lũy 80/95%; sản phẩm
làm vượt ngưỡng vẫn thuộc lớp đang cộng. Denominator ABC chỉ là phần lượng đã quy thuộc.
Không sử dụng mã chưa rõ như một sản phẩm giả. Cần đọc quantity_conservation để biết phần bị loại khỏi attribution.
Nhóm khách SUY_DIEN là nhóm thống kê từ hậu tố đơn, không dùng cho RFV hoặc lịch sử khách model.
