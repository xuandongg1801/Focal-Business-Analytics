# Từ điển dữ liệu và hợp đồng ngữ nghĩa

## Cách đọc tài liệu

Tài liệu này giải thích **schema/cột kỹ thuật**, không cung cấp tên khách, mã đơn, hợp đồng, số lượng theo giao dịch hoặc đơn giá thực tế. Dtype bên dưới phản ánh **semantic contract** từ `scripts/data_contract.py` trong snapshot, có thể khác kiểu pandas suy tự động khi đọc CSV. `Nullable` nói về hợp đồng hiện tại, không phải tần suất thiếu dữ liệu của mọi kỳ.

**Quan hệ khóa:** `fact_order_header` (1 dòng/đơn) → `fact_order_items` (1 dòng nguồn) → `fact_product_items` (0..n dòng phân bổ hợp lệ); dòng không quy thuộc nằm ở `unresolved_items`. `mart_order_items` và `mart_product_items` phục vụ phân tích theo grain tương ứng. Customer/product/price dimensions dùng khóa tham chiếu và join kiểm soát `many_to_one`.

**Nguyên tắc chung:** trường `*_raw` giữ nguyên nguồn, trường `*_km` chỉ quy đổi đúng đơn vị đo, `canonical_product_code` chỉ được gán khi khớp danh mục, tên/mã khách là định danh riêng tư **không phát hành giá trị thực tế**. Các cột giá chỉ là **tham chiếu**, không phải số liệu doanh thu hay thanh toán. Đơn giá, thông tin khách và mô tả gốc thuộc dữ liệu riêng của doanh nghiệp.

## Danh mục dữ liệu

| Bảng | Grain / chức năng |
|---|---|
| `dim_customer.csv` | Một mã khách chính thức trong danh mục |
| `dim_product.csv` | Một mã sản phẩm trong danh mục |
| `dim_price_list.csv` | Một dòng quy cách và giá tham chiếu; mã có thể lặp theo quy cách |
| `fact_order_header.csv` | Một đơn theo khóa xác nhận |
| `fact_order_items.csv` | Một dòng Excel vật lý, sổ nguồn |
| `mart_order_items.csv` | Sổ nguồn bổ sung dimension, cờ chất lượng và lượng |
| `fact_product_items.csv` | Một token sản phẩm đã có căn cứ phân bổ |
| `mart_product_items.csv` | Product fact kết hợp dimension và giá tham chiếu |
| `unresolved_items.csv` | Các dòng chưa đủ căn cứ quy thuộc mã/lượng |

Các định nghĩa cột dưới đây được giữ để hỗ trợ đọc mã nguồn; số dòng cụ thể phụ thuộc dữ liệu snapshot và được kiểm định cục bộ, không đưa vào schema công khai.


## `dim_customer.csv`

| Cột | Kiểu ngữ nghĩa | Cho phép null | Ý nghĩa |
|---|---|:---:|---|
| ma_khach_hang | string | Không | Mã danh mục khách |
| ten_khach_hang | nullable string | Có | Trường tên khách trong nguồn (giữ riêng tư; có thể được ẩn danh khi trích xuất) |
| thi_truong | nullable string | Có | Nhãn thị trường nguồn |
| ten_khach_hang_la_placeholder | boolean | Không | Tên nguồn là placeholder ẩn danh |

## `dim_product.csv`

| Cột | Kiểu ngữ nghĩa | Cho phép null | Ý nghĩa |
|---|---|:---:|---|
| stt | nullable integer | Có | Thứ tự nguồn |
| ma_san_pham | string | Không | Mã danh mục sản phẩm |
| ten_san_pham | nullable string | Có | Tên danh mục sản phẩm |
| nhom_san_pham | nullable string | Có | Nhóm danh mục |
| don_vi_tinh | nullable string | Có | Đơn vị danh mục |
| trang_thai_kinh_doanh | nullable string | Có | Trạng thái trong master, không phải đơn |
| loai_san_pham_quy_cach | nullable string | Có | Quy cách master |
| nguon_hang | nullable string | Có | Nguồn hàng ghi trong master |

## `dim_price_list.csv`

| Cột | Kiểu ngữ nghĩa | Cho phép null | Ý nghĩa |
|---|---|:---:|---|
| stt | nullable integer | Có | Thứ tự nguồn |
| ten_hang_hoa | nullable string | Có | Tên trong bảng giá |
| ky_ma_hieu | string | Không | Mã bảng giá |
| tieu_chuan_ky_thuat | nullable string | Có | Quy cách kỹ thuật bảng giá |
| gia_cap_1 | nullable real number | Có | Đơn giá tham chiếu cấp 1 |
| gia_cap_2 | nullable real number | Có | Đơn giá tham chiếu cấp 2 |
| gia_cap_3 | nullable real number | Có | Đơn giá tham chiếu cấp 3 |
| gia_ban_khach_le | nullable real number | Có | Đơn giá tham chiếu khách lẻ |
| so_bien_the_theo_ma | nullable integer | Có | Số quy cách cùng mã trong bảng giá |

## `fact_order_header.csv`

| Cột | Kiểu ngữ nghĩa | Cho phép null | Ý nghĩa |
|---|---|:---:|---|
| order_row_id | integer | Không | Khóa header: ID dòng nguồn đầu tiên của mã xác nhận đơn |
| nam_file | integer | Không | Năm trong tên tracker |
| ngay | nullable string | Có | Ngày nguồn |
| ngay_dt | nullable date | Có | Ngày parse dayfirst |
| order_month | string | Không | Alias của tháng canonical cho aggregate/feature |
| order_year | integer | Không | Năm tháng canonical |
| ngay_bi_thieu | boolean | Không | Ngày nguồn trống |
| ngay_khong_hop_le | boolean | Không | Ngày có nhập nhưng không parse được |
| ngay_nam_khong_khop_file | boolean | Không | Năm ngày khác năm tệp |
| ma_khach | nullable string | Có | Mã khách ghi trong tracker |
| so_xac_nhan_don_hang | string | Không | Khóa đơn nghiệp vụ |
| so_hop_dong | nullable string | Có | Mã hợp đồng nguồn |
| wo | nullable string | Có | Mã lệnh sản xuất được ghi nhận |
| loai_don | nullable string | Có | Loại đơn theo prefix |
| la_don_ban_hang | boolean | Không | Thuộc population đơn bán |
| loai_don_tu_so_hop_dong | boolean | Không | Phân loại dùng prefix hợp đồng |
| order_month_from_date | nullable string | Có | Tháng suy từ ngày parse |
| order_month_from_code | nullable string | Có | Tháng /YYMM/ trong mã đơn |
| order_month_canonical | string | Không | Tháng phân tích |
| order_month_conflict | boolean | Không | Ngày và mã có tháng khác nhau |
| order_month_rule | nullable string | Có | Nhánh chọn tháng |

## `fact_order_items.csv`

| Cột | Kiểu ngữ nghĩa | Cho phép null | Ý nghĩa |
|---|---|:---:|---|
| item_id | integer | Không | Khóa sổ nguồn, một dòng Excel |
| order_row_id | integer | Không | Khóa header: ID dòng nguồn đầu tiên của mã xác nhận đơn |
| order_source_row_id | integer | Không | ID dòng nguồn, liên kết ngược ingestion |
| item_text_raw | nullable string | Có | Mô tả sản phẩm nguyên gốc |
| parsed | boolean | Không | Có numeric quantity và đơn vị |
| parsed_product_token | nullable string | Có | Token chuẩn hóa từ RAW; KHÔNG đồng nghĩa mã tham chiếu |
| so_luong | nullable real number | Có | Lượng nguồn hoặc lượng được phân bổ ở product fact |
| don_vi | nullable string | Có | Đơn vị nguồn chuẩn hóa |
| bien_the | nullable string | Có | Marker biến thể để audit |
| so_luong_km | nullable real number | Có | KM quan sát, không điền thiếu |
| source_file | string | Không | Tên tệp nguồn |
| source_sheet | string | Không | Sheet nguồn |
| source_excel_row | integer | Không | Số dòng vật lý Excel, gồm header |
| parse_status | string | Không | Cấp xác nhận sản phẩm |
| allocation_status | string | Không | Căn cứ phân bổ lượng |
| product_candidates | nullable string | Có | Danh sách mã nhận diện phục vụ audit, không phải dimension sản phẩm |
| parse_reason | string | Không | Lý do nhận diện/phân bổ hoặc từ chối |
| canonical_product_code | nullable string | Có | Mã thuộc danh mục sản phẩm hoặc bảng giá; có thể bao phủ nhiều quy cách kỹ thuật |
| is_reference_product_code | boolean | Không | Khớp chính xác mã tham chiếu |
| product_family_code | nullable string | Có | Quy cách cơ sở của token (ví dụ FTTH02), không phải SKU |

## `mart_order_items.csv`

| Cột | Kiểu ngữ nghĩa | Cho phép null | Ý nghĩa |
|---|---|:---:|---|
| item_id | integer | Không | Khóa sổ nguồn, một dòng Excel |
| order_row_id | integer | Không | Khóa header: ID dòng nguồn đầu tiên của mã xác nhận đơn |
| order_source_row_id | integer | Không | ID dòng nguồn, liên kết ngược ingestion |
| item_text_raw | nullable string | Có | Mô tả sản phẩm nguyên gốc |
| parsed | boolean | Không | Có numeric quantity và đơn vị |
| parsed_product_token | nullable string | Có | Token chuẩn hóa từ RAW; KHÔNG đồng nghĩa mã tham chiếu |
| so_luong | nullable real number | Có | Lượng nguồn hoặc lượng được phân bổ ở product fact |
| don_vi | nullable string | Có | Đơn vị nguồn chuẩn hóa |
| bien_the | nullable string | Có | Marker biến thể để audit |
| so_luong_km | nullable real number | Có | KM quan sát, không điền thiếu |
| source_file | string | Không | Tên tệp nguồn |
| source_sheet | string | Không | Sheet nguồn |
| source_excel_row | integer | Không | Số dòng vật lý Excel, gồm header |
| parse_status | string | Không | Cấp xác nhận sản phẩm |
| allocation_status | string | Không | Căn cứ phân bổ lượng |
| product_candidates | nullable string | Có | Danh sách mã nhận diện phục vụ audit, không phải dimension sản phẩm |
| parse_reason | string | Không | Lý do nhận diện/phân bổ hoặc từ chối |
| canonical_product_code | nullable string | Có | Mã thuộc danh mục sản phẩm hoặc bảng giá; có thể bao phủ nhiều quy cách kỹ thuật |
| is_reference_product_code | boolean | Không | Khớp chính xác mã tham chiếu |
| product_family_code | nullable string | Có | Quy cách cơ sở của token (ví dụ FTTH02), không phải SKU |
| nam_file | integer | Không | Năm trong tên tracker |
| ngay | nullable string | Có | Ngày nguồn |
| ngay_dt | nullable date | Có | Ngày parse dayfirst |
| order_month | string | Không | Alias của tháng canonical cho aggregate/feature |
| order_year | integer | Không | Năm tháng canonical |
| ngay_bi_thieu | boolean | Không | Ngày nguồn trống |
| ngay_khong_hop_le | boolean | Không | Ngày có nhập nhưng không parse được |
| ngay_nam_khong_khop_file | boolean | Không | Năm ngày khác năm tệp |
| ma_khach | nullable string | Có | Mã khách ghi trong tracker |
| so_xac_nhan_don_hang | string | Không | Khóa đơn nghiệp vụ |
| so_hop_dong | nullable string | Có | Mã hợp đồng nguồn |
| wo | nullable string | Có | Mã lệnh sản xuất được ghi nhận |
| loai_don | nullable string | Có | Loại đơn theo prefix |
| la_don_ban_hang | boolean | Không | Thuộc population đơn bán |
| loai_don_tu_so_hop_dong | boolean | Không | Phân loại dùng prefix hợp đồng |
| order_month_from_date | nullable string | Có | Tháng suy từ ngày parse |
| order_month_from_code | nullable string | Có | Tháng /YYMM/ trong mã đơn |
| order_month_canonical | string | Không | Tháng phân tích |
| order_month_conflict | boolean | Không | Ngày và mã có tháng khác nhau |
| order_month_rule | nullable string | Có | Nhánh chọn tháng |
| ma_khach_hang | nullable string | Có | Mã danh mục khách |
| ten_khach_hang | nullable string | Có | Trường tên khách trong nguồn (giữ riêng tư; có thể được ẩn danh khi trích xuất) |
| thi_truong | nullable string | Có | Nhãn thị trường nguồn |
| co_ma_khach_chinh_thuc | boolean | Không | Mã tracker khớp danh mục |
| ma_khach_nhom | string | Không | Mã chính thức hoặc nhóm SUY_DIEN từ hậu tố đơn |
| ten_khach_hang_nhom | string | Không | Nhãn nội bộ cho nhóm thống kê; không bảo đảm định danh pháp nhân |
| nhom_san_pham_don_hang | nullable string | Có | Họ mã hoặc bucket mô tả chưa ánh xạ |
| so_quy_cach | nullable integer | Có | Số quy cách giá được gom theo mã |
| cap_1_min | nullable real number | Có | Biên giá trị tham chiếu theo cấp, không phải doanh thu |
| cap_2_min | nullable real number | Có | Biên giá trị tham chiếu theo cấp, không phải doanh thu |
| cap_3_min | nullable real number | Có | Biên giá trị tham chiếu theo cấp, không phải doanh thu |
| khach_le_min | nullable real number | Có | Biên giá trị tham chiếu theo cấp, không phải doanh thu |
| cap_1_max | nullable real number | Có | Biên giá trị tham chiếu theo cấp, không phải doanh thu |
| cap_2_max | nullable real number | Có | Biên giá trị tham chiếu theo cấp, không phải doanh thu |
| cap_3_max | nullable real number | Có | Biên giá trị tham chiếu theo cấp, không phải doanh thu |
| khach_le_max | nullable real number | Có | Biên giá trị tham chiếu theo cấp, không phải doanh thu |
| gia_trong_giai_doan_xac_nhan | boolean | Không | Năm nằm trong hiệu lực giá xác nhận |
| co_don_gia_tham_khao | boolean | Không | Có ít nhất một cấp giá |
| ly_do_khong_co_gia | nullable string | Có | Lý do thiếu giá hoặc ngoài hiệu lực |
| gia_tri_cap_1_min | nullable real number | Có | Biên giá trị tham chiếu theo cấp, không phải doanh thu |
| gia_tri_cap_1_max | nullable real number | Có | Biên giá trị tham chiếu theo cấp, không phải doanh thu |
| gia_tri_cap_2_min | nullable real number | Có | Biên giá trị tham chiếu theo cấp, không phải doanh thu |
| gia_tri_cap_2_max | nullable real number | Có | Biên giá trị tham chiếu theo cấp, không phải doanh thu |
| gia_tri_cap_3_min | nullable real number | Có | Biên giá trị tham chiếu theo cấp, không phải doanh thu |
| gia_tri_cap_3_max | nullable real number | Có | Biên giá trị tham chiếu theo cấp, không phải doanh thu |
| gia_tri_khach_le_min | nullable real number | Có | Biên giá trị tham chiếu theo cấp, không phải doanh thu |
| gia_tri_khach_le_max | nullable real number | Có | Biên giá trị tham chiếu theo cấp, không phải doanh thu |
| don_gia_tham_khao | nullable real number | Có | Midpoint khoảng đơn giá cấp 2 |
| gia_tri_uoc_tinh | nullable real number | Có | Giá trị quy đổi tham khảo, không phải doanh thu |
| nghi_ngo_outlier | boolean | Không | Cờ cực trị trên sổ dòng nguồn |
| outlier_stat_threshold_km | nullable real number | Có | Ngưỡng mô tả hồi cứu |
| outlier_duoc_xac_nhan_la_phat_sinh_that | boolean | Không | Đơn dự án đã được xác nhận lượng |

## `fact_product_items.csv`

| Cột | Kiểu ngữ nghĩa | Cho phép null | Ý nghĩa |
|---|---|:---:|---|
| item_id | integer | Không | Khóa sổ nguồn, một dòng Excel |
| order_row_id | integer | Không | Khóa header: ID dòng nguồn đầu tiên của mã xác nhận đơn |
| order_source_row_id | integer | Không | ID dòng nguồn, liên kết ngược ingestion |
| item_text_raw | nullable string | Có | Mô tả sản phẩm nguyên gốc |
| parsed | boolean | Không | Có numeric quantity và đơn vị |
| parsed_product_token | string | Không | Token chuẩn hóa từ RAW; KHÔNG đồng nghĩa mã tham chiếu |
| so_luong | nullable real number | Có | Lượng nguồn hoặc lượng được phân bổ ở product fact |
| don_vi | nullable string | Có | Đơn vị nguồn chuẩn hóa |
| bien_the | nullable string | Có | Marker biến thể để audit |
| so_luong_km | nullable real number | Có | KM quan sát, không điền thiếu |
| source_file | string | Không | Tên tệp nguồn |
| source_sheet | string | Không | Sheet nguồn |
| source_excel_row | integer | Không | Số dòng vật lý Excel, gồm header |
| parse_status | string | Không | Cấp xác nhận sản phẩm |
| allocation_status | string | Không | Căn cứ phân bổ lượng |
| product_candidates | nullable string | Có | Danh sách mã nhận diện phục vụ audit, không phải dimension sản phẩm |
| parse_reason | string | Không | Lý do nhận diện/phân bổ hoặc từ chối |
| canonical_product_code | nullable string | Có | Mã thuộc danh mục sản phẩm hoặc bảng giá; có thể bao phủ nhiều quy cách kỹ thuật |
| is_reference_product_code | boolean | Không | Khớp chính xác mã tham chiếu |
| product_family_code | nullable string | Có | Quy cách cơ sở của token (ví dụ FTTH02), không phải SKU |
| product_item_id | string | Không | Khóa source item + thứ tự phân bổ |

## `mart_product_items.csv`

| Cột | Kiểu ngữ nghĩa | Cho phép null | Ý nghĩa |
|---|---|:---:|---|
| item_id | integer | Không | Khóa sổ nguồn, một dòng Excel |
| order_row_id | integer | Không | Khóa header: ID dòng nguồn đầu tiên của mã xác nhận đơn |
| order_source_row_id | integer | Không | ID dòng nguồn, liên kết ngược ingestion |
| item_text_raw | nullable string | Có | Mô tả sản phẩm nguyên gốc |
| parsed | boolean | Không | Có numeric quantity và đơn vị |
| parsed_product_token | string | Không | Token chuẩn hóa từ RAW; KHÔNG đồng nghĩa mã tham chiếu |
| so_luong | nullable real number | Có | Lượng nguồn hoặc lượng được phân bổ ở product fact |
| don_vi | nullable string | Có | Đơn vị nguồn chuẩn hóa |
| bien_the | nullable string | Có | Marker biến thể để audit |
| so_luong_km | nullable real number | Có | KM quan sát, không điền thiếu |
| source_file | string | Không | Tên tệp nguồn |
| source_sheet | string | Không | Sheet nguồn |
| source_excel_row | integer | Không | Số dòng vật lý Excel, gồm header |
| parse_status | string | Không | Cấp xác nhận sản phẩm |
| allocation_status | string | Không | Căn cứ phân bổ lượng |
| product_candidates | nullable string | Có | Danh sách mã nhận diện phục vụ audit, không phải dimension sản phẩm |
| parse_reason | string | Không | Lý do nhận diện/phân bổ hoặc từ chối |
| canonical_product_code | nullable string | Có | Mã thuộc danh mục sản phẩm hoặc bảng giá; có thể bao phủ nhiều quy cách kỹ thuật |
| is_reference_product_code | boolean | Không | Khớp chính xác mã tham chiếu |
| product_family_code | nullable string | Có | Quy cách cơ sở của token (ví dụ FTTH02), không phải SKU |
| product_item_id | string | Không | Khóa source item + thứ tự phân bổ |
| nam_file | integer | Không | Năm trong tên tracker |
| ngay | nullable string | Có | Ngày nguồn |
| ngay_dt | nullable date | Có | Ngày parse dayfirst |
| order_month | string | Không | Alias của tháng canonical cho aggregate/feature |
| order_year | integer | Không | Năm tháng canonical |
| ngay_bi_thieu | boolean | Không | Ngày nguồn trống |
| ngay_khong_hop_le | boolean | Không | Ngày có nhập nhưng không parse được |
| ngay_nam_khong_khop_file | boolean | Không | Năm ngày khác năm tệp |
| ma_khach | nullable string | Có | Mã khách ghi trong tracker |
| so_xac_nhan_don_hang | string | Không | Khóa đơn nghiệp vụ |
| so_hop_dong | nullable string | Có | Mã hợp đồng nguồn |
| wo | nullable string | Có | Mã lệnh sản xuất được ghi nhận |
| loai_don | nullable string | Có | Loại đơn theo prefix |
| la_don_ban_hang | boolean | Không | Thuộc population đơn bán |
| loai_don_tu_so_hop_dong | boolean | Không | Phân loại dùng prefix hợp đồng |
| order_month_from_date | nullable string | Có | Tháng suy từ ngày parse |
| order_month_from_code | nullable string | Có | Tháng /YYMM/ trong mã đơn |
| order_month_canonical | string | Không | Tháng phân tích |
| order_month_conflict | boolean | Không | Ngày và mã có tháng khác nhau |
| order_month_rule | nullable string | Có | Nhánh chọn tháng |
| ma_khach_hang | nullable string | Có | Mã danh mục khách |
| ten_khach_hang | nullable string | Có | Trường tên khách trong nguồn (giữ riêng tư; có thể được ẩn danh khi trích xuất) |
| thi_truong | nullable string | Có | Nhãn thị trường nguồn |
| co_ma_khach_chinh_thuc | boolean | Không | Mã tracker khớp danh mục |
| ma_khach_nhom | string | Không | Mã chính thức hoặc nhóm SUY_DIEN từ hậu tố đơn |
| ten_khach_hang_nhom | string | Không | Nhãn nội bộ cho nhóm thống kê; không bảo đảm định danh pháp nhân |
| nhom_san_pham_don_hang | nullable string | Có | Họ mã hoặc bucket mô tả chưa ánh xạ |
| so_quy_cach | nullable integer | Có | Số quy cách giá được gom theo mã |
| cap_1_min | nullable real number | Có | Biên giá trị tham chiếu theo cấp, không phải doanh thu |
| cap_2_min | nullable real number | Có | Biên giá trị tham chiếu theo cấp, không phải doanh thu |
| cap_3_min | nullable real number | Có | Biên giá trị tham chiếu theo cấp, không phải doanh thu |
| khach_le_min | nullable real number | Có | Biên giá trị tham chiếu theo cấp, không phải doanh thu |
| cap_1_max | nullable real number | Có | Biên giá trị tham chiếu theo cấp, không phải doanh thu |
| cap_2_max | nullable real number | Có | Biên giá trị tham chiếu theo cấp, không phải doanh thu |
| cap_3_max | nullable real number | Có | Biên giá trị tham chiếu theo cấp, không phải doanh thu |
| khach_le_max | nullable real number | Có | Biên giá trị tham chiếu theo cấp, không phải doanh thu |
| gia_trong_giai_doan_xac_nhan | boolean | Không | Năm nằm trong hiệu lực giá xác nhận |
| co_don_gia_tham_khao | boolean | Không | Có ít nhất một cấp giá |
| ly_do_khong_co_gia | nullable string | Có | Lý do thiếu giá hoặc ngoài hiệu lực |
| gia_tri_cap_1_min | nullable real number | Có | Biên giá trị tham chiếu theo cấp, không phải doanh thu |
| gia_tri_cap_1_max | nullable real number | Có | Biên giá trị tham chiếu theo cấp, không phải doanh thu |
| gia_tri_cap_2_min | nullable real number | Có | Biên giá trị tham chiếu theo cấp, không phải doanh thu |
| gia_tri_cap_2_max | nullable real number | Có | Biên giá trị tham chiếu theo cấp, không phải doanh thu |
| gia_tri_cap_3_min | nullable real number | Có | Biên giá trị tham chiếu theo cấp, không phải doanh thu |
| gia_tri_cap_3_max | nullable real number | Có | Biên giá trị tham chiếu theo cấp, không phải doanh thu |
| gia_tri_khach_le_min | nullable real number | Có | Biên giá trị tham chiếu theo cấp, không phải doanh thu |
| gia_tri_khach_le_max | nullable real number | Có | Biên giá trị tham chiếu theo cấp, không phải doanh thu |
| don_gia_tham_khao | nullable real number | Có | Midpoint khoảng đơn giá cấp 2 |
| gia_tri_uoc_tinh | nullable real number | Có | Giá trị quy đổi tham khảo, không phải doanh thu |
| nghi_ngo_outlier | boolean | Không | Cờ cực trị trên sổ dòng nguồn |
| outlier_stat_threshold_km | nullable real number | Có | Ngưỡng mô tả hồi cứu |
| outlier_duoc_xac_nhan_la_phat_sinh_that | boolean | Không | Đơn dự án đã được xác nhận lượng |

## `unresolved_items.csv`

| Cột | Kiểu ngữ nghĩa | Cho phép null | Ý nghĩa |
|---|---|:---:|---|
| item_id | integer | Không | Khóa sổ nguồn, một dòng Excel |
| order_row_id | integer | Không | Khóa header: ID dòng nguồn đầu tiên của mã xác nhận đơn |
| order_source_row_id | integer | Không | ID dòng nguồn, liên kết ngược ingestion |
| item_text_raw | nullable string | Có | Mô tả sản phẩm nguyên gốc |
| parsed | boolean | Không | Có numeric quantity và đơn vị |
| parsed_product_token | nullable string | Có | Token chuẩn hóa từ RAW; KHÔNG đồng nghĩa mã tham chiếu |
| so_luong | nullable real number | Có | Lượng nguồn hoặc lượng được phân bổ ở product fact |
| don_vi | nullable string | Có | Đơn vị nguồn chuẩn hóa |
| bien_the | nullable string | Có | Marker biến thể để audit |
| so_luong_km | nullable real number | Có | KM quan sát, không điền thiếu |
| source_file | string | Không | Tên tệp nguồn |
| source_sheet | string | Không | Sheet nguồn |
| source_excel_row | integer | Không | Số dòng vật lý Excel, gồm header |
| parse_status | string | Không | Cấp xác nhận sản phẩm |
| allocation_status | string | Không | Căn cứ phân bổ lượng |
| product_candidates | nullable string | Có | Danh sách mã nhận diện phục vụ audit, không phải dimension sản phẩm |
| parse_reason | string | Không | Lý do nhận diện/phân bổ hoặc từ chối |
| canonical_product_code | nullable string | Có | Mã thuộc danh mục sản phẩm hoặc bảng giá; có thể bao phủ nhiều quy cách kỹ thuật |
| is_reference_product_code | boolean | Không | Khớp chính xác mã tham chiếu |
| product_family_code | nullable string | Có | Quy cách cơ sở của token (ví dụ FTTH02), không phải SKU |

## Nhãn phân loại `chot_don`

**Quy tắc doanh nghiệp đã xác nhận:** WIN (1) nếu tất cả các dòng của một đơn bán đều có đủ ô **Sản phẩm, Số lượng, Đơn vị** ở Excel gốc; LOST (0) khi có ít nhất một ô còn thiếu trên một dòng hoặc đơn không có dòng nguồn. **Không tồn tại cột WIN/LOST gán thủ công riêng cho từng đơn** trong nguồn. Đây là nhãn được lập lại bằng phép kiểm tra ô theo quy tắc doanh nghiệp xác nhận.

Điều kiện ô **có dữ liệu** là khác null và `strip()` không rỗng; không hàm ý numeric validity, quy đổi được đơn vị hay tên sản phẩm đã đúng. Vì vậy phần chất lượng dữ liệu được kiểm định độc lập. Grain của modeling dataset: **một đơn bán/một nhãn bắt buộc**, `customer_id` có thể trống. Các trường nguồn tạo nhãn, cờ `product_present`, `quantity_present`, `unit_present`, `line_complete` và target không được đưa vào predictors.

## Từ điển 12 đặc trưng phân loại

| Feature | Diễn giải | Miền giá trị / đơn vị |
|---|---|---|
| `customer_is_known` | Có mã khách ở tracker, không phải xác nhận tồn tại lịch sử | 0/1 |
| `prior_order_count` | Tổng số đơn trước tháng dự báo của cùng mã khách | số đơn ≥ 0 |
| `recency_months` | Số tháng tới lần nhận đơn trước đó; null nếu không có | tháng ≥ 1 hoặc null |
| `customer_active_months_before` | Số tháng có đơn trong lịch sử trước tháng dự báo | số tháng ≥ 0 |
| `orders_last_3m` | Số đơn của 3 tháng đã hoàn tất gần nhất | số đơn ≥ 0 |
| `orders_last_6m` | Số đơn của 6 tháng đã hoàn tất gần nhất | số đơn ≥ 0 |
| `prior_monthly_order_trend` | Chênh lệch đơn bình quân giữa hai khối 3 tháng liền trước | số đơn/tháng, có thể âm |
| `year` | Năm dự báo | năm lịch |
| `month` | Tháng dự báo | 1..12 |
| `quarter` | Quý dự báo | 1..4 |
| `month_sin` | Biến đổi chu kỳ `sin(2π·month/12)` | [-1,1] |
| `month_cos` | Biến đổi chu kỳ `cos(2π·month/12)` | [-1,1] |

Các đặc trưng lịch sử sử dụng đơn ở **tháng nhỏ hơn tháng đang dự đoán** và không dùng outcome lịch sử; mã khách gốc không được dùng như một feature định danh. Kiểm tra giới hạn leakage và cách chọn model tại [08_approval_prediction.md](08_approval_prediction.md).

## Quy ước giá trị đặc biệt và bảo mật

- `null` không đồng nghĩa `0`, đặc biệt ở `so_luong`, `so_luong_km`, `recency_months`.
- Cột `gia_tri_uoc_tinh` là phép quy đổi tham khảo theo dữ liệu giá, **không dùng kết luận doanh thu**; giá có thể thiếu hoặc không đúng thời điểm hiệu lực.
