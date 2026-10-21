# Kiểm soát chất lượng dữ liệu

## Phạm vi và số liệu tổng hợp

Số liệu dưới đây phản ánh **snapshot đầu vào được dùng để tạo artifacts trong project**, không phải phép thống kê trực tiếp trên một repository không chứa dữ liệu gốc. Không công bố mã đơn, khách hàng, bảng giá, tổng KM hay trường hợp bất thường ở cấp giao dịch.

| Chỉ tiêu | Kết quả |
|---|---:|
| Số đơn hàng nguồn | 1168 |
| Số dòng sản phẩm nguồn | 1720 |
| Dòng được quy thuộc sản phẩm | 1284 |
| Trong đó: mã tham chiếu chính xác | 1123 |
| Trong đó: nhận diện ở cấp generic | 161 |
| Dòng còn chưa quy thuộc | 436 |
| Dòng nhiều mã chưa đủ căn cứ phân bổ | 7 |
| Dòng chưa ánh xạ mã | 429 |
| Đơn có xung đột tháng | 46 |
| Dòng thiếu số lượng (sau chuẩn hóa) | 373 |
| Dòng thiếu mã khách hàng (theo kết quả kiểm định) | 192 |
| Dòng được gắn cờ cực trị thống kê | 5 |
| Mã đơn trùng trong header / item ID trùng | 0 / 0 |
| Dòng là ứng viên trùng cần soát xét | 2 |

**Kiểm tra đối chiếu:** `canonical_product_rows + unresolved_rows = items` đối với snapshot đã kiểm tra. Phép so sánh về **lượng** bắt buộc thực hiện riêng từng đơn vị, không cộng các đơn vị không tương thích.

## Cách hiểu và hướng xử lý

- **Unresolved/unmapped** không tự động đồng nghĩa dữ liệu sai: có thể do mô tả phi sản phẩm, mã chưa có trong danh mục hoặc chưa đủ căn cứ chia lượng.
- **Thiếu số lượng** không được tự động thay bằng 0. Một ô số lượng có ký tự không hợp lệ là vấn đề chất lượng dữ liệu, nhưng việc có hay không có giá trị ô nguồn được đánh giá riêng khi tạo WIN/LOST.
- **Xung đột tháng** được lưu cờ và nhánh lựa chọn, không âm thầm làm biến mất dữ liệu gốc.
- **Cực trị thống kê** không bị xóa khỏi ledger; chỉ được lọc trong các phân tích có khai báo rõ phạm vi và phải tách khỏi các dự án được xác nhận.
- **Ứng viên trùng** cần có kiểm tra nguồn, không xóa theo quy tắc trùng số lượng/văn bản đơn giản.
- **Mã khách trống** không được suy ra là một khách hàng định danh duy nhất từ chuỗi ký tự của đơn.
