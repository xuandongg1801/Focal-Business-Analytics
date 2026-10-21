# Quy trình xử lý dữ liệu (ETL, lineage và grain)

## 1. Đầu vào và khóa

- Pipeline đọc các tracker Excel theo năm và các danh mục liên quan tại `data/raw/` (nguồn nội bộ; không tải qua API). Tracker sử dụng sheet `DATA_CHUAN_HOA`, hàng tiêu đề theo schema mà chương trình kiểm tra.
- `fact_order_header`: **một dòng/một đơn** theo khóa xác nhận đơn; `fact_order_items`: **một dòng vật lý của file nguồn**. Các item nối với header qua `order_row_id`.
- Duy trì `source_file`, `source_sheet`, `source_excel_row`, `item_id`, `order_source_row_id` để tái đối soát. Đây là **tên cột kỹ thuật**, tài liệu không công bố giá trị định danh thực tế.

## 2. Chuẩn hóa và phân bổ sản phẩm

1. Chuẩn hóa Unicode (`NFKC`), khoảng trắng, chữ hoa phục vụ nhận diện; vẫn giữ nguyên `item_text_raw` phục vụ kiểm toán cục bộ.
2. Nhận diện mã theo danh mục và quy cách: `exact_reference` là mã tham chiếu đối chiếu được; `recognized_generic` chỉ ở cấp mô tả/quy cách chung, **không mặc định là SKU**.
3. Với dòng có nhiều mã, chỉ chia lượng khi từng thành phần có lượng/đơn vị rõ ràng và tổng khớp dòng nguồn. Nếu không đủ căn cứ, giữ dòng ở `unresolved_items` và **không tự chia đều**.
4. `fact_product_items` chỉ chứa phần đã quy thuộc; `unresolved_items` giữ phần còn lại. Không xóa mất lượng chỉ vì mã sản phẩm chưa nhận diện được.
5. Việc có mã trong danh mục/bảng giá không bảo đảm mã có duy nhất một cấu hình kỹ thuật. Giá tham chiếu không được chuyển thành doanh thu.

## 3. Quy tắc cộng lượng và tháng

- Chỉ tổng hợp các đơn vị đo cùng bản chất: **M / 1.000 → KM**; các đơn vị KG, CÁI, BỘ và những đơn vị khác không được cộng chung thành KM.
- Missing quantity giữ là **unknown**, không mặc định 0.
- Tháng phân tích (`order_month_canonical`) ưu tiên ngày hợp lệ có năm khớp nguồn; nếu không, dùng tháng xác định được trong mã; cuối cùng sử dụng ngày như nhánh dự phòng. Cờ `order_month_conflict` giữ các bất đồng để đánh giá.
- Các phép nối header–customer–price có ràng buộc `many_to_one` nhằm tránh nhân bản dòng và lượng.

## 4. Phân nhánh phân tích

| Đầu ra | Nguồn chính | Lưu ý grain |
|---|---|---|
| Thống kê đơn hàng | `fact_order_header` | Không đếm dòng hàng thành đơn |
| EDA tháng và RFV | `mart_order_items` từ sổ nguồn | Không làm mất lượng chưa quy thuộc |
| ABC sản phẩm | `mart_product_items` | Mã chính xác khác mã generic |
| Forecast | Dòng bán có KM, phân tách dự án/cực trị | Ngưỡng cực trị trong từng fold được fit bằng train |
| WIN/LOST | **Ba ô Excel gốc của mọi dòng trong đơn** | Không phụ thuộc thành công parse hay hợp lệ số lượng |
| Đặc trưng mô hình | Header và lịch sử **trước tháng dự đoán** | Không dùng nhãn hoặc trường tạo nhãn làm đầu vào |

## 5. Data gates

- Trước khi tạo nhãn, pipeline đối soát tập header/item đã xử lý với nguồn theo khóa, số dòng và nội dung liên quan (outer reconciliation). Thiếu dòng, dư dòng, trùng khóa hoặc lệch dữ liệu phải báo lỗi thay vì im lặng bỏ qua.
- Kiểm tra bảo toàn lượng theo **dòng nguồn + đơn vị**: lượng quy thuộc cộng lượng chưa quy thuộc phải bằng lượng nguồn khi có thể đối soát.
- Các quy tắc dữ liệu kiểm thử nằm ở `tests/`, mô tả kết quả tổng hợp tại [04_data_quality.md](04_data_quality.md).

**Bảo mật:** ví dụ và báo cáo công khai không ghi tên khách hàng, chuỗi mã đơn thực tế, đơn giá, hợp đồng, mô tả sản phẩm nguyên gốc hoặc hàng dữ liệu cụ thể.
