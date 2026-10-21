# Pipeline và grain

1. Ingestion chỉ đọc DATA_CHUAN_HOA, header dòng 2; giữ tên tệp/sheet/dòng Excel.
2. Header unique theo mã xác nhận. Các item cùng đơn phải thống nhất ngày, khách, tháng, WO, hợp đồng.
3. fact_order_items giữ một dòng Excel, không explode tổng lượng. Source keys unique/non-null.
4. Parser NFKC, uppercase, whitespace; giữ raw; parse LT/SQ và LỎNG/CHẶT cả trong ngoặc.
   Exact reference được ưu tiên, biên regex tránh trùng tiền tố. Bare FTTH có variant trong
   reference được giữ như specification chưa xác định LT/SQ; không tự gán biến thể để lấy giá.
5. Nhiều mã chỉ split khi từng mã có amount/unit rõ và tổng khớp source quantity. Nếu thiếu,
   mâu thuẫn đơn vị hoặc tổng lệch: unresolved. Không chia đều. Dòng chỉ có một mã được quy thuộc,
   nhưng quantity thiếu vẫn null. Unknown code không đồng nghĩa mô tả không phải hàng hóa.
6. fact_product_items một dòng một token có lượng phân bổ: exact_reference hoặc recognized_generic.
   canonical_product_code chỉ có cho exact_reference. recognized_generic (ví dụ FTTH02) không phải SKU.
   Bảng giá có thể có nhiều quy cách trên một mã; exact_reference không bảo đảm một SKU kỹ thuật duy nhất.
   Xếp hạng mã và ABC mã chỉ dùng exact_reference. Họ sản phẩm bao gồm cả generic; RFV/forecast
   vẫn dùng sổ nguồn để bảo toàn lượng. unresolved_items giữ phần chưa phân bổ, không gán mã.
   Kiểm tra tổng allocated + unresolved bằng source theo từng dòng và đơn vị; tổng các đơn vị không cộng chung.
7. Mart nối header/customer/price với many_to_one. Product mart kế thừa cờ cực trị từ source item.
   Price min/max theo quy cách, ngoài hiệu lực không sinh giá trị. Giá trị tham chiếu chỉ ở mã được quy thuộc.
8. EDA/ABC sản phẩm đọc mart_product_items; tổng đơn/tháng, RFV và forecast đọc sổ mart nguồn.
9. Trước tạo target: dựng lại header/items từ RAW, outer reconcile theo key, so mọi trường
   serialized; bắt missing/extra/duplicate/customer/quantity/unit/product/order composition.
   Failure ghi loại/count/sample và dừng trước khi tạo nhãn hoặc train.

Tháng canonical ưu tiên ngày có năm khớp năm tracker, sau đó tháng trong mã, cuối cùng ngày
nếu mã không parse được. Đây là quy ước theo độ nhất quán với tệp, không chứng minh ngày đúng tuyệt đối.
Luôn giữ tháng ngày, tháng mã, conflict flag và nhánh quyết định; thiếu cả hai phải báo lỗi.
