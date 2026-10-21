# Kiểm soát chất lượng dữ liệu

## Phạm vi và số liệu tổng hợp

Số liệu dưới đây phản ánh **snapshot đầu vào được dùng để tạo artifacts trong project**, không phải phép thống kê trực tiếp trên một repository không chứa dữ liệu gốc. Không công bố mã đơn, khách hàng, bảng giá, tổng KM hay trường hợp bất thường ở cấp giao dịch.

| Chỉ tiêu | Kết quả |
|---|---:|
| Số đơn hàng nguồn | {{ORDERS}} |
| Số dòng sản phẩm nguồn | {{ITEMS}} |
| Dòng được quy thuộc sản phẩm | {{CANONICAL_ROWS}} |
| Trong đó: mã tham chiếu chính xác | {{EXACT_ROWS}} |
| Trong đó: nhận diện ở cấp generic | {{GENERIC_ROWS}} |
| Dòng còn chưa quy thuộc | {{UNRESOLVED_ROWS}} |
| Dòng nhiều mã chưa đủ căn cứ phân bổ | {{UNRESOLVED_MULTI_ROWS}} |
| Dòng chưa ánh xạ mã | {{UNMAPPED_ROWS}} |
| Đơn có xung đột tháng | {{MONTH_CONFLICTS}} |
| Dòng thiếu số lượng (sau chuẩn hóa) | {{MISSING_QTY}} |
| Dòng thiếu mã khách hàng (theo kết quả kiểm định) | {{MISSING_CUST}} |
| Dòng được gắn cờ cực trị thống kê | {{OUTLIER_ROWS}} |
| Mã đơn trùng trong header / item ID trùng | {{DUP_ORDERS}} / {{DUP_ITEMS}} |
| Dòng là ứng viên trùng cần soát xét | {{DUP_CANDIDATES}} |

**Kiểm tra đối chiếu:** `canonical_product_rows + unresolved_rows = items` đối với snapshot đã kiểm tra. Phép so sánh về **lượng** bắt buộc thực hiện riêng từng đơn vị, không cộng các đơn vị không tương thích.

## Cách hiểu và hướng xử lý

- **Unresolved/unmapped** không tự động đồng nghĩa dữ liệu sai: có thể do mô tả phi sản phẩm, mã chưa có trong danh mục hoặc chưa đủ căn cứ chia lượng.
- **Thiếu số lượng** không được tự động thay bằng 0. Một ô số lượng có ký tự không hợp lệ là vấn đề chất lượng dữ liệu, nhưng việc có hay không có giá trị ô nguồn được đánh giá riêng khi tạo WIN/LOST.
- **Xung đột tháng** được lưu cờ và nhánh lựa chọn, không âm thầm làm biến mất dữ liệu gốc.
- **Cực trị thống kê** không bị xóa khỏi ledger; chỉ được lọc trong các phân tích có khai báo rõ phạm vi và phải tách khỏi các dự án được xác nhận.
- **Ứng viên trùng** cần có kiểm tra nguồn, không xóa theo quy tắc trùng số lượng/văn bản đơn giản.
- **Mã khách trống** không được suy ra là một khách hàng định danh duy nhất từ chuỗi ký tự của đơn.

## Kiểm tra khả năng tái lập

Các kiểm thử bảo toàn số dòng, khóa, đối soát nguồn, thời gian và semantics ở `tests/` / `verify_project.py`. Báo cáo đối soát và log chi tiết được tạo trong `outputs/` **chỉ để kiểm tra nội bộ**; không dẫn link từ docs công khai vì có thể chứa thông tin định danh và được `.gitignore` loại khỏi repository.

> Các chỉ số có thể thay đổi nếu dữ liệu nguồn thay đổi. Chỉ công bố bản tổng hợp này khi doanh nghiệp cho phép chia sẻ thống kê đã ẩn danh.
