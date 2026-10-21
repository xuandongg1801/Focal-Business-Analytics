# Từ điển dữ liệu

Dtype ngữ nghĩa lấy từ scripts/data_contract.py, độc lập với dtype pandas suy từ snapshot. Quyền null theo contract; cột mã toàn null vẫn là nullable string.

## dim_customer.csv

Grain: một mã khách. Dòng: 504.

| Cột | Dtype | Nullable | Định nghĩa | Nguồn / biến đổi | Domain |
|---|---|---|---|---|---|
| ma_khach_hang | string | Không | Mã danh mục khách | Excel danh mục/bảng giá → chuẩn hóa khóa; giữ thuộc tính nguồn | theo nguồn; numeric giá >=0/null |
| ten_khach_hang | nullable string | Có | Tên nguồn đã ẩn danh | Excel danh mục/bảng giá → chuẩn hóa khóa; giữ thuộc tính nguồn | theo nguồn; numeric giá >=0/null |
| thi_truong | nullable string | Có | Nhãn thị trường nguồn | Excel danh mục/bảng giá → chuẩn hóa khóa; giữ thuộc tính nguồn | theo nguồn; numeric giá >=0/null |
| ten_khach_hang_la_placeholder | boolean | Không | Tên nguồn là placeholder ẩn danh | Excel danh mục/bảng giá → chuẩn hóa khóa; giữ thuộc tính nguồn | theo nguồn; numeric giá >=0/null |

## dim_product.csv

Grain: một mã danh mục sản phẩm. Dòng: 856.

| Cột | Dtype | Nullable | Định nghĩa | Nguồn / biến đổi | Domain |
|---|---|---|---|---|---|
| stt | nullable integer | Có | Thứ tự nguồn | Excel danh mục/bảng giá → chuẩn hóa khóa; giữ thuộc tính nguồn | theo nguồn; numeric giá >=0/null |
| ma_san_pham | string | Không | Mã danh mục sản phẩm | Excel danh mục/bảng giá → chuẩn hóa khóa; giữ thuộc tính nguồn | theo nguồn; numeric giá >=0/null |
| ten_san_pham | nullable string | Có | Tên danh mục sản phẩm | Excel danh mục/bảng giá → chuẩn hóa khóa; giữ thuộc tính nguồn | theo nguồn; numeric giá >=0/null |
| nhom_san_pham | nullable string | Có | Nhóm danh mục | Excel danh mục/bảng giá → chuẩn hóa khóa; giữ thuộc tính nguồn | theo nguồn; numeric giá >=0/null |
| don_vi_tinh | nullable string | Có | Đơn vị danh mục | Excel danh mục/bảng giá → chuẩn hóa khóa; giữ thuộc tính nguồn | theo nguồn; numeric giá >=0/null |
| trang_thai_kinh_doanh | nullable string | Có | Trạng thái trong master, không phải đơn | Excel danh mục/bảng giá → chuẩn hóa khóa; giữ thuộc tính nguồn | theo nguồn; numeric giá >=0/null |
| loai_san_pham_quy_cach | nullable string | Có | Quy cách master | Excel danh mục/bảng giá → chuẩn hóa khóa; giữ thuộc tính nguồn | theo nguồn; numeric giá >=0/null |
| nguon_hang | nullable string | Có | Nguồn hàng ghi trong master | Excel danh mục/bảng giá → chuẩn hóa khóa; giữ thuộc tính nguồn | theo nguồn; numeric giá >=0/null |

## dim_price_list.csv

Grain: một mã/quy cách giá; mã có thể lặp. Dòng: 177.

| Cột | Dtype | Nullable | Định nghĩa | Nguồn / biến đổi | Domain |
|---|---|---|---|---|---|
| stt | nullable integer | Có | Thứ tự nguồn | Excel danh mục/bảng giá → chuẩn hóa khóa; giữ thuộc tính nguồn | theo nguồn; numeric giá >=0/null |
| ten_hang_hoa | nullable string | Có | Tên trong bảng giá | Excel danh mục/bảng giá → chuẩn hóa khóa; giữ thuộc tính nguồn | theo nguồn; numeric giá >=0/null |
| ky_ma_hieu | string | Không | Mã bảng giá | Excel danh mục/bảng giá → chuẩn hóa khóa; giữ thuộc tính nguồn | theo nguồn; numeric giá >=0/null |
| tieu_chuan_ky_thuat | nullable string | Có | Quy cách kỹ thuật bảng giá | Excel danh mục/bảng giá → chuẩn hóa khóa; giữ thuộc tính nguồn | theo nguồn; numeric giá >=0/null |
| gia_cap_1 | nullable real number | Có | Đơn giá tham chiếu cấp 1 | Excel danh mục/bảng giá → chuẩn hóa khóa; giữ thuộc tính nguồn | theo nguồn; numeric giá >=0/null |
| gia_cap_2 | nullable real number | Có | Đơn giá tham chiếu cấp 2 | Excel danh mục/bảng giá → chuẩn hóa khóa; giữ thuộc tính nguồn | theo nguồn; numeric giá >=0/null |
| gia_cap_3 | nullable real number | Có | Đơn giá tham chiếu cấp 3 | Excel danh mục/bảng giá → chuẩn hóa khóa; giữ thuộc tính nguồn | theo nguồn; numeric giá >=0/null |
| gia_ban_khach_le | nullable real number | Có | Đơn giá tham chiếu khách lẻ | Excel danh mục/bảng giá → chuẩn hóa khóa; giữ thuộc tính nguồn | theo nguồn; numeric giá >=0/null |
| so_bien_the_theo_ma | nullable integer | Có | Số quy cách cùng mã trong bảng giá | Excel danh mục/bảng giá → chuẩn hóa khóa; giữ thuộc tính nguồn | theo nguồn; numeric giá >=0/null |

## fact_order_header.csv

Grain: một mã xác nhận đơn hàng. Dòng: 1168.

| Cột | Dtype | Nullable | Định nghĩa | Nguồn / biến đổi | Domain |
|---|---|---|---|---|---|
| order_row_id | integer | Không | Khóa header: ID dòng nguồn đầu tiên của mã xác nhận đơn | tracker → nhóm mã xác nhận | unique ở header; FK trong item |
| nam_file | integer | Không | Năm trong tên tracker | tên tệp YYYY | year |
| ngay | nullable string | Có | Ngày nguồn | NGÀY → giữ nguyên | date/text/null |
| ngay_dt | nullable date | Có | Ngày parse dayfirst | to_datetime format=mixed | date/null; supplied invalid bị validator từ chối |
| order_month | string | Không | Alias của tháng canonical cho aggregate/feature | order_month_canonical | YYYY-MM không null |
| order_year | integer | Không | Năm tháng canonical | order_month[:4] | year |
| ngay_bi_thieu | boolean | Không | Ngày nguồn trống | ngay.isna | boolean |
| ngay_khong_hop_le | boolean | Không | Ngày có nhập nhưng không parse được | ngay.notna & ngay_dt.isna | boolean |
| ngay_nam_khong_khop_file | boolean | Không | Năm ngày khác năm tệp | ngay_dt.year != nam_file nếu có ngày | boolean |
| ma_khach | nullable string | Có | Mã khách ghi trong tracker | MÃ KHÁCH → trim/uppercase | text/null; không suy danh tính từ hậu tố đơn |
| so_xac_nhan_don_hang | string | Không | Khóa đơn nghiệp vụ | SỐ XÁC NHẬN ĐƠN HÀNG | unique, không null ở header |
| so_hop_dong | nullable string | Có | Mã hợp đồng nguồn | SỐ HỢP ĐỒNG | text/null |
| wo | nullable string | Có | Mã lệnh sản xuất được ghi nhận | WO | text/null; thiếu không suy giao từ tồn |
| loai_don | nullable string | Có | Loại đơn theo prefix | ORDER_TYPE_MAP | CA/AC/SL/EQ sales; RM/IT nội bộ |
| la_don_ban_hang | boolean | Không | Thuộc population đơn bán | prefix CA/AC/SL/EQ; contract fallback nếu thiếu prefix | boolean |
| loai_don_tu_so_hop_dong | boolean | Không | Phân loại dùng prefix hợp đồng | prefix fallback | boolean |
| order_month_from_date | nullable string | Có | Tháng suy từ ngày parse | ngay_dt → YYYY-MM | tháng hợp lệ/null |
| order_month_from_code | nullable string | Có | Tháng /YYMM/ trong mã đơn | regex kiểm tra month 1..12 | YYYY-MM/null |
| order_month_canonical | string | Không | Tháng phân tích | date nếu năm khớp file, rồi code, rồi date fallback | YYYY-MM không null |
| order_month_conflict | boolean | Không | Ngày và mã có tháng khác nhau | cả hai có tháng và khác nhau | boolean |
| order_month_rule | nullable string | Có | Nhánh chọn tháng | canonical month rule | date_in_file_year / code_fallback / date_fallback |

## fact_order_items.csv

Grain: một dòng vật lý Excel; sổ nguồn, chưa phải product fact. Dòng: 1720.

| Cột | Dtype | Nullable | Định nghĩa | Nguồn / biến đổi | Domain |
|---|---|---|---|---|---|
| item_id | integer | Không | Khóa sổ nguồn, một dòng Excel | tracker → thứ tự nạp deterministic | unique ở fact_order_items; FK trong product fact |
| order_row_id | integer | Không | Khóa header: ID dòng nguồn đầu tiên của mã xác nhận đơn | tracker → nhóm mã xác nhận | unique ở header; FK trong item |
| order_source_row_id | integer | Không | ID dòng nguồn, liên kết ngược ingestion | tracker → thứ tự nạp | unique, không null |
| item_text_raw | nullable string | Có | Mô tả sản phẩm nguyên gốc | SẢN PHẨM → giữ nguyên | text/null |
| parsed | boolean | Không | Có numeric quantity và đơn vị | so_luong.notna & don_vi.notna | boolean; không chứng minh product match |
| parsed_product_token | nullable string | Có | Token chuẩn hóa từ RAW; KHÔNG đồng nghĩa mã tham chiếu | Unicode/semantic parser + bảng tham chiếu | không null ở product fact; null khi unresolved hoặc split ở sổ nguồn |
| so_luong | nullable real number | Có | Lượng nguồn hoặc lượng được phân bổ ở product fact | SỐ LƯỢNG → numeric; split chỉ theo amount rõ ràng | finite >= 0/null; không cộng các đơn vị khác nhau |
| don_vi | nullable string | Có | Đơn vị nguồn chuẩn hóa | ĐƠN VỊ → trim/uppercase | KM/M/KG/CÁI/BỘ/LICENSE/TẤN/null trong snapshot |
| bien_the | nullable string | Có | Marker biến thể để audit | raw regex LT/SQ/LỎNG/CHẶT | text/null; canonical là kết quả parser |
| so_luong_km | nullable real number | Có | KM quan sát, không điền thiếu | KM giữ nguyên; M chia 1000; đơn vị khác null | finite >=0/null |
| source_file | string | Không | Tên tệp nguồn | ingestion | thuộc data/raw |
| source_sheet | string | Không | Sheet nguồn | ingestion | DATA_CHUAN_HOA |
| source_excel_row | integer | Không | Số dòng vật lý Excel, gồm header | ingestion → index + 3 | integer >= 3 |
| parse_status | string | Không | Cấp xác nhận sản phẩm | parser + authoritative reference | exact_reference / recognized_generic / ambiguous / unmapped / unresolved_multiple / allocated_multiple |
| allocation_status | string | Không | Căn cứ phân bổ lượng | parser + đối soát source total | single / split / unresolved |
| product_candidates | nullable string | Có | Danh sách mã nhận diện phục vụ audit, không phải dimension sản phẩm | parser → join bằng dấu phân cách | text/null; không dùng cộng lượng theo mã |
| parse_reason | string | Không | Lý do nhận diện/phân bổ hoặc từ chối | parser | text |
| canonical_product_code | nullable string | Có | Mã thuộc danh mục sản phẩm hoặc bảng giá; có thể bao phủ nhiều quy cách kỹ thuật | chỉ gán khi exact_reference | nullable string; generic/unresolved bắt buộc null |
| is_reference_product_code | boolean | Không | Khớp chính xác mã tham chiếu | parse_status == exact_reference | boolean; false cho generic/unresolved |
| product_family_code | nullable string | Có | Quy cách cơ sở của token (ví dụ FTTH02), không phải SKU | token bỏ hậu tố sau dấu gạch nối | string/null; giữ LT/SQ trong parsed_product_token và canonical_product_code |

## mart_order_items.csv

Grain: một dòng nguồn đã nối header/master. Dòng: 1720.

| Cột | Dtype | Nullable | Định nghĩa | Nguồn / biến đổi | Domain |
|---|---|---|---|---|---|
| item_id | integer | Không | Khóa sổ nguồn, một dòng Excel | tracker → thứ tự nạp deterministic | unique ở fact_order_items; FK trong product fact |
| order_row_id | integer | Không | Khóa header: ID dòng nguồn đầu tiên của mã xác nhận đơn | tracker → nhóm mã xác nhận | unique ở header; FK trong item |
| order_source_row_id | integer | Không | ID dòng nguồn, liên kết ngược ingestion | tracker → thứ tự nạp | unique, không null |
| item_text_raw | nullable string | Có | Mô tả sản phẩm nguyên gốc | SẢN PHẨM → giữ nguyên | text/null |
| parsed | boolean | Không | Có numeric quantity và đơn vị | so_luong.notna & don_vi.notna | boolean; không chứng minh product match |
| parsed_product_token | nullable string | Có | Token chuẩn hóa từ RAW; KHÔNG đồng nghĩa mã tham chiếu | Unicode/semantic parser + bảng tham chiếu | không null ở product fact; null khi unresolved hoặc split ở sổ nguồn |
| so_luong | nullable real number | Có | Lượng nguồn hoặc lượng được phân bổ ở product fact | SỐ LƯỢNG → numeric; split chỉ theo amount rõ ràng | finite >= 0/null; không cộng các đơn vị khác nhau |
| don_vi | nullable string | Có | Đơn vị nguồn chuẩn hóa | ĐƠN VỊ → trim/uppercase | KM/M/KG/CÁI/BỘ/LICENSE/TẤN/null trong snapshot |
| bien_the | nullable string | Có | Marker biến thể để audit | raw regex LT/SQ/LỎNG/CHẶT | text/null; canonical là kết quả parser |
| so_luong_km | nullable real number | Có | KM quan sát, không điền thiếu | KM giữ nguyên; M chia 1000; đơn vị khác null | finite >=0/null |
| source_file | string | Không | Tên tệp nguồn | ingestion | thuộc data/raw |
| source_sheet | string | Không | Sheet nguồn | ingestion | DATA_CHUAN_HOA |
| source_excel_row | integer | Không | Số dòng vật lý Excel, gồm header | ingestion → index + 3 | integer >= 3 |
| parse_status | string | Không | Cấp xác nhận sản phẩm | parser + authoritative reference | exact_reference / recognized_generic / ambiguous / unmapped / unresolved_multiple / allocated_multiple |
| allocation_status | string | Không | Căn cứ phân bổ lượng | parser + đối soát source total | single / split / unresolved |
| product_candidates | nullable string | Có | Danh sách mã nhận diện phục vụ audit, không phải dimension sản phẩm | parser → join bằng dấu phân cách | text/null; không dùng cộng lượng theo mã |
| parse_reason | string | Không | Lý do nhận diện/phân bổ hoặc từ chối | parser | text |
| canonical_product_code | nullable string | Có | Mã thuộc danh mục sản phẩm hoặc bảng giá; có thể bao phủ nhiều quy cách kỹ thuật | chỉ gán khi exact_reference | nullable string; generic/unresolved bắt buộc null |
| is_reference_product_code | boolean | Không | Khớp chính xác mã tham chiếu | parse_status == exact_reference | boolean; false cho generic/unresolved |
| product_family_code | nullable string | Có | Quy cách cơ sở của token (ví dụ FTTH02), không phải SKU | token bỏ hậu tố sau dấu gạch nối | string/null; giữ LT/SQ trong parsed_product_token và canonical_product_code |
| nam_file | integer | Không | Năm trong tên tracker | tên tệp YYYY | year |
| ngay | nullable string | Có | Ngày nguồn | NGÀY → giữ nguyên | date/text/null |
| ngay_dt | nullable date | Có | Ngày parse dayfirst | to_datetime format=mixed | date/null; supplied invalid bị validator từ chối |
| order_month | string | Không | Alias của tháng canonical cho aggregate/feature | order_month_canonical | YYYY-MM không null |
| order_year | integer | Không | Năm tháng canonical | order_month[:4] | year |
| ngay_bi_thieu | boolean | Không | Ngày nguồn trống | ngay.isna | boolean |
| ngay_khong_hop_le | boolean | Không | Ngày có nhập nhưng không parse được | ngay.notna & ngay_dt.isna | boolean |
| ngay_nam_khong_khop_file | boolean | Không | Năm ngày khác năm tệp | ngay_dt.year != nam_file nếu có ngày | boolean |
| ma_khach | nullable string | Có | Mã khách ghi trong tracker | MÃ KHÁCH → trim/uppercase | text/null; không suy danh tính từ hậu tố đơn |
| so_xac_nhan_don_hang | string | Không | Khóa đơn nghiệp vụ | SỐ XÁC NHẬN ĐƠN HÀNG | unique, không null ở header |
| so_hop_dong | nullable string | Có | Mã hợp đồng nguồn | SỐ HỢP ĐỒNG | text/null |
| wo | nullable string | Có | Mã lệnh sản xuất được ghi nhận | WO | text/null; thiếu không suy giao từ tồn |
| loai_don | nullable string | Có | Loại đơn theo prefix | ORDER_TYPE_MAP | CA/AC/SL/EQ sales; RM/IT nội bộ |
| la_don_ban_hang | boolean | Không | Thuộc population đơn bán | prefix CA/AC/SL/EQ; contract fallback nếu thiếu prefix | boolean |
| loai_don_tu_so_hop_dong | boolean | Không | Phân loại dùng prefix hợp đồng | prefix fallback | boolean |
| order_month_from_date | nullable string | Có | Tháng suy từ ngày parse | ngay_dt → YYYY-MM | tháng hợp lệ/null |
| order_month_from_code | nullable string | Có | Tháng /YYMM/ trong mã đơn | regex kiểm tra month 1..12 | YYYY-MM/null |
| order_month_canonical | string | Không | Tháng phân tích | date nếu năm khớp file, rồi code, rồi date fallback | YYYY-MM không null |
| order_month_conflict | boolean | Không | Ngày và mã có tháng khác nhau | cả hai có tháng và khác nhau | boolean |
| order_month_rule | nullable string | Có | Nhánh chọn tháng | canonical month rule | date_in_file_year / code_fallback / date_fallback |
| ma_khach_hang | nullable string | Có | Mã danh mục khách | Excel danh mục/bảng giá → chuẩn hóa khóa; giữ thuộc tính nguồn | theo nguồn; numeric giá >=0/null |
| ten_khach_hang | nullable string | Có | Tên nguồn đã ẩn danh | Excel danh mục/bảng giá → chuẩn hóa khóa; giữ thuộc tính nguồn | theo nguồn; numeric giá >=0/null |
| thi_truong | nullable string | Có | Nhãn thị trường nguồn | Excel danh mục/bảng giá → chuẩn hóa khóa; giữ thuộc tính nguồn | theo nguồn; numeric giá >=0/null |
| co_ma_khach_chinh_thuc | boolean | Không | Mã tracker khớp danh mục | merge many_to_one | boolean |
| ma_khach_nhom | string | Không | Mã chính thức hoặc nhóm SUY_DIEN từ hậu tố đơn | fallback bảo toàn thống kê lượng | không phải định danh pháp nhân với nhóm suy diễn |
| ten_khach_hang_nhom | string | Không | Tên hiển thị cho nhóm thống kê | master hoặc hậu tố đơn | text không null |
| nhom_san_pham_don_hang | nullable string | Có | Họ mã hoặc bucket mô tả chưa ánh xạ | FAMILY_MAP / NONCABLE_KEYWORDS | product analytics chỉ đọc mart_product_items |
| so_quy_cach | nullable integer | Có | Số quy cách giá được gom theo mã | Excel danh mục/bảng giá → chuẩn hóa khóa; giữ thuộc tính nguồn | theo nguồn; numeric giá >=0/null |
| cap_1_min | nullable real number | Có | Biên giá trị tham chiếu theo cấp, không phải doanh thu | min/max giá trong các quy cách cùng mã | numeric finite >=0/null |
| cap_2_min | nullable real number | Có | Biên giá trị tham chiếu theo cấp, không phải doanh thu | min/max giá trong các quy cách cùng mã | numeric finite >=0/null |
| cap_3_min | nullable real number | Có | Biên giá trị tham chiếu theo cấp, không phải doanh thu | min/max giá trong các quy cách cùng mã | numeric finite >=0/null |
| khach_le_min | nullable real number | Có | Biên giá trị tham chiếu theo cấp, không phải doanh thu | min/max giá trong các quy cách cùng mã | numeric finite >=0/null |
| cap_1_max | nullable real number | Có | Biên giá trị tham chiếu theo cấp, không phải doanh thu | min/max giá trong các quy cách cùng mã | numeric finite >=0/null |
| cap_2_max | nullable real number | Có | Biên giá trị tham chiếu theo cấp, không phải doanh thu | min/max giá trong các quy cách cùng mã | numeric finite >=0/null |
| cap_3_max | nullable real number | Có | Biên giá trị tham chiếu theo cấp, không phải doanh thu | min/max giá trong các quy cách cùng mã | numeric finite >=0/null |
| khach_le_max | nullable real number | Có | Biên giá trị tham chiếu theo cấp, không phải doanh thu | min/max giá trong các quy cách cùng mã | numeric finite >=0/null |
| gia_trong_giai_doan_xac_nhan | boolean | Không | Năm nằm trong hiệu lực giá xác nhận | PRICE_VALID_YEARS | boolean |
| co_don_gia_tham_khao | boolean | Không | Có ít nhất một cấp giá | merge exact canonical code | boolean |
| ly_do_khong_co_gia | nullable string | Có | Lý do thiếu giá hoặc ngoài hiệu lực | price join/validity | text/null |
| gia_tri_cap_1_min | nullable real number | Có | Biên giá trị tham chiếu theo cấp, không phải doanh thu | KM × biên giá | numeric finite >=0/null |
| gia_tri_cap_1_max | nullable real number | Có | Biên giá trị tham chiếu theo cấp, không phải doanh thu | KM × biên giá | numeric finite >=0/null |
| gia_tri_cap_2_min | nullable real number | Có | Biên giá trị tham chiếu theo cấp, không phải doanh thu | KM × biên giá | numeric finite >=0/null |
| gia_tri_cap_2_max | nullable real number | Có | Biên giá trị tham chiếu theo cấp, không phải doanh thu | KM × biên giá | numeric finite >=0/null |
| gia_tri_cap_3_min | nullable real number | Có | Biên giá trị tham chiếu theo cấp, không phải doanh thu | KM × biên giá | numeric finite >=0/null |
| gia_tri_cap_3_max | nullable real number | Có | Biên giá trị tham chiếu theo cấp, không phải doanh thu | KM × biên giá | numeric finite >=0/null |
| gia_tri_khach_le_min | nullable real number | Có | Biên giá trị tham chiếu theo cấp, không phải doanh thu | KM × biên giá | numeric finite >=0/null |
| gia_tri_khach_le_max | nullable real number | Có | Biên giá trị tham chiếu theo cấp, không phải doanh thu | KM × biên giá | numeric finite >=0/null |
| don_gia_tham_khao | nullable real number | Có | Midpoint khoảng đơn giá cấp 2 | (cap_2_min+cap_2_max)/2 | finite >=0/null |
| gia_tri_uoc_tinh | nullable real number | Có | Giá trị quy đổi tham khảo, không phải doanh thu | KM × midpoint cấp 2 | null khi thiếu giá/lượng; đơn vị tiền chưa xác minh |
| nghi_ngo_outlier | boolean | Không | Cờ cực trị trên sổ dòng nguồn | sales ngoài dự án; log1p(KM) > Q3+3IQR | boolean; không xóa khỏi tổng ghi nhận |
| outlier_stat_threshold_km | nullable real number | Có | Ngưỡng mô tả hồi cứu | fit toàn lịch sử ở mart; forecast fit riêng train | finite >=0 |
| outlier_duoc_xac_nhan_la_phat_sinh_that | boolean | Không | Đơn dự án đã được xác nhận lượng | CONFIRMED_PROJECT_ORDERS | boolean; không gắn cờ cực trị |

## fact_product_items.csv

Grain: một sản phẩm được quy thuộc trong một dòng nguồn. Dòng: 1284.

| Cột | Dtype | Nullable | Định nghĩa | Nguồn / biến đổi | Domain |
|---|---|---|---|---|---|
| item_id | integer | Không | Khóa sổ nguồn, một dòng Excel | tracker → thứ tự nạp deterministic | unique ở fact_order_items; FK trong product fact |
| order_row_id | integer | Không | Khóa header: ID dòng nguồn đầu tiên của mã xác nhận đơn | tracker → nhóm mã xác nhận | unique ở header; FK trong item |
| order_source_row_id | integer | Không | ID dòng nguồn, liên kết ngược ingestion | tracker → thứ tự nạp | unique, không null |
| item_text_raw | nullable string | Có | Mô tả sản phẩm nguyên gốc | SẢN PHẨM → giữ nguyên | text/null |
| parsed | boolean | Không | Có numeric quantity và đơn vị | so_luong.notna & don_vi.notna | boolean; không chứng minh product match |
| parsed_product_token | string | Không | Token chuẩn hóa từ RAW; KHÔNG đồng nghĩa mã tham chiếu | Unicode/semantic parser + bảng tham chiếu | không null ở product fact; null khi unresolved hoặc split ở sổ nguồn |
| so_luong | nullable real number | Có | Lượng nguồn hoặc lượng được phân bổ ở product fact | SỐ LƯỢNG → numeric; split chỉ theo amount rõ ràng | finite >= 0/null; không cộng các đơn vị khác nhau |
| don_vi | nullable string | Có | Đơn vị nguồn chuẩn hóa | ĐƠN VỊ → trim/uppercase | KM/M/KG/CÁI/BỘ/LICENSE/TẤN/null trong snapshot |
| bien_the | nullable string | Có | Marker biến thể để audit | raw regex LT/SQ/LỎNG/CHẶT | text/null; canonical là kết quả parser |
| so_luong_km | nullable real number | Có | KM quan sát, không điền thiếu | KM giữ nguyên; M chia 1000; đơn vị khác null | finite >=0/null |
| source_file | string | Không | Tên tệp nguồn | ingestion | thuộc data/raw |
| source_sheet | string | Không | Sheet nguồn | ingestion | DATA_CHUAN_HOA |
| source_excel_row | integer | Không | Số dòng vật lý Excel, gồm header | ingestion → index + 3 | integer >= 3 |
| parse_status | string | Không | Cấp xác nhận sản phẩm | parser + authoritative reference | exact_reference / recognized_generic / ambiguous / unmapped / unresolved_multiple / allocated_multiple |
| allocation_status | string | Không | Căn cứ phân bổ lượng | parser + đối soát source total | single / split / unresolved |
| product_candidates | nullable string | Có | Danh sách mã nhận diện phục vụ audit, không phải dimension sản phẩm | parser → join bằng dấu phân cách | text/null; không dùng cộng lượng theo mã |
| parse_reason | string | Không | Lý do nhận diện/phân bổ hoặc từ chối | parser | text |
| canonical_product_code | nullable string | Có | Mã thuộc danh mục sản phẩm hoặc bảng giá; có thể bao phủ nhiều quy cách kỹ thuật | chỉ gán khi exact_reference | nullable string; generic/unresolved bắt buộc null |
| is_reference_product_code | boolean | Không | Khớp chính xác mã tham chiếu | parse_status == exact_reference | boolean; false cho generic/unresolved |
| product_family_code | nullable string | Có | Quy cách cơ sở của token (ví dụ FTTH02), không phải SKU | token bỏ hậu tố sau dấu gạch nối | string/null; giữ LT/SQ trong parsed_product_token và canonical_product_code |
| product_item_id | string | Không | Khóa source item + thứ tự phân bổ | parser → item_id:allocation_index | unique, không null |

## mart_product_items.csv

Grain: một canonical product item đã nối metadata. Dòng: 1284.

| Cột | Dtype | Nullable | Định nghĩa | Nguồn / biến đổi | Domain |
|---|---|---|---|---|---|
| item_id | integer | Không | Khóa sổ nguồn, một dòng Excel | tracker → thứ tự nạp deterministic | unique ở fact_order_items; FK trong product fact |
| order_row_id | integer | Không | Khóa header: ID dòng nguồn đầu tiên của mã xác nhận đơn | tracker → nhóm mã xác nhận | unique ở header; FK trong item |
| order_source_row_id | integer | Không | ID dòng nguồn, liên kết ngược ingestion | tracker → thứ tự nạp | unique, không null |
| item_text_raw | nullable string | Có | Mô tả sản phẩm nguyên gốc | SẢN PHẨM → giữ nguyên | text/null |
| parsed | boolean | Không | Có numeric quantity và đơn vị | so_luong.notna & don_vi.notna | boolean; không chứng minh product match |
| parsed_product_token | string | Không | Token chuẩn hóa từ RAW; KHÔNG đồng nghĩa mã tham chiếu | Unicode/semantic parser + bảng tham chiếu | không null ở product fact; null khi unresolved hoặc split ở sổ nguồn |
| so_luong | nullable real number | Có | Lượng nguồn hoặc lượng được phân bổ ở product fact | SỐ LƯỢNG → numeric; split chỉ theo amount rõ ràng | finite >= 0/null; không cộng các đơn vị khác nhau |
| don_vi | nullable string | Có | Đơn vị nguồn chuẩn hóa | ĐƠN VỊ → trim/uppercase | KM/M/KG/CÁI/BỘ/LICENSE/TẤN/null trong snapshot |
| bien_the | nullable string | Có | Marker biến thể để audit | raw regex LT/SQ/LỎNG/CHẶT | text/null; canonical là kết quả parser |
| so_luong_km | nullable real number | Có | KM quan sát, không điền thiếu | KM giữ nguyên; M chia 1000; đơn vị khác null | finite >=0/null |
| source_file | string | Không | Tên tệp nguồn | ingestion | thuộc data/raw |
| source_sheet | string | Không | Sheet nguồn | ingestion | DATA_CHUAN_HOA |
| source_excel_row | integer | Không | Số dòng vật lý Excel, gồm header | ingestion → index + 3 | integer >= 3 |
| parse_status | string | Không | Cấp xác nhận sản phẩm | parser + authoritative reference | exact_reference / recognized_generic / ambiguous / unmapped / unresolved_multiple / allocated_multiple |
| allocation_status | string | Không | Căn cứ phân bổ lượng | parser + đối soát source total | single / split / unresolved |
| product_candidates | nullable string | Có | Danh sách mã nhận diện phục vụ audit, không phải dimension sản phẩm | parser → join bằng dấu phân cách | text/null; không dùng cộng lượng theo mã |
| parse_reason | string | Không | Lý do nhận diện/phân bổ hoặc từ chối | parser | text |
| canonical_product_code | nullable string | Có | Mã thuộc danh mục sản phẩm hoặc bảng giá; có thể bao phủ nhiều quy cách kỹ thuật | chỉ gán khi exact_reference | nullable string; generic/unresolved bắt buộc null |
| is_reference_product_code | boolean | Không | Khớp chính xác mã tham chiếu | parse_status == exact_reference | boolean; false cho generic/unresolved |
| product_family_code | nullable string | Có | Quy cách cơ sở của token (ví dụ FTTH02), không phải SKU | token bỏ hậu tố sau dấu gạch nối | string/null; giữ LT/SQ trong parsed_product_token và canonical_product_code |
| product_item_id | string | Không | Khóa source item + thứ tự phân bổ | parser → item_id:allocation_index | unique, không null |
| nam_file | integer | Không | Năm trong tên tracker | tên tệp YYYY | year |
| ngay | nullable string | Có | Ngày nguồn | NGÀY → giữ nguyên | date/text/null |
| ngay_dt | nullable date | Có | Ngày parse dayfirst | to_datetime format=mixed | date/null; supplied invalid bị validator từ chối |
| order_month | string | Không | Alias của tháng canonical cho aggregate/feature | order_month_canonical | YYYY-MM không null |
| order_year | integer | Không | Năm tháng canonical | order_month[:4] | year |
| ngay_bi_thieu | boolean | Không | Ngày nguồn trống | ngay.isna | boolean |
| ngay_khong_hop_le | boolean | Không | Ngày có nhập nhưng không parse được | ngay.notna & ngay_dt.isna | boolean |
| ngay_nam_khong_khop_file | boolean | Không | Năm ngày khác năm tệp | ngay_dt.year != nam_file nếu có ngày | boolean |
| ma_khach | nullable string | Có | Mã khách ghi trong tracker | MÃ KHÁCH → trim/uppercase | text/null; không suy danh tính từ hậu tố đơn |
| so_xac_nhan_don_hang | string | Không | Khóa đơn nghiệp vụ | SỐ XÁC NHẬN ĐƠN HÀNG | unique, không null ở header |
| so_hop_dong | nullable string | Có | Mã hợp đồng nguồn | SỐ HỢP ĐỒNG | text/null |
| wo | nullable string | Có | Mã lệnh sản xuất được ghi nhận | WO | text/null; thiếu không suy giao từ tồn |
| loai_don | nullable string | Có | Loại đơn theo prefix | ORDER_TYPE_MAP | CA/AC/SL/EQ sales; RM/IT nội bộ |
| la_don_ban_hang | boolean | Không | Thuộc population đơn bán | prefix CA/AC/SL/EQ; contract fallback nếu thiếu prefix | boolean |
| loai_don_tu_so_hop_dong | boolean | Không | Phân loại dùng prefix hợp đồng | prefix fallback | boolean |
| order_month_from_date | nullable string | Có | Tháng suy từ ngày parse | ngay_dt → YYYY-MM | tháng hợp lệ/null |
| order_month_from_code | nullable string | Có | Tháng /YYMM/ trong mã đơn | regex kiểm tra month 1..12 | YYYY-MM/null |
| order_month_canonical | string | Không | Tháng phân tích | date nếu năm khớp file, rồi code, rồi date fallback | YYYY-MM không null |
| order_month_conflict | boolean | Không | Ngày và mã có tháng khác nhau | cả hai có tháng và khác nhau | boolean |
| order_month_rule | nullable string | Có | Nhánh chọn tháng | canonical month rule | date_in_file_year / code_fallback / date_fallback |
| ma_khach_hang | nullable string | Có | Mã danh mục khách | Excel danh mục/bảng giá → chuẩn hóa khóa; giữ thuộc tính nguồn | theo nguồn; numeric giá >=0/null |
| ten_khach_hang | nullable string | Có | Tên nguồn đã ẩn danh | Excel danh mục/bảng giá → chuẩn hóa khóa; giữ thuộc tính nguồn | theo nguồn; numeric giá >=0/null |
| thi_truong | nullable string | Có | Nhãn thị trường nguồn | Excel danh mục/bảng giá → chuẩn hóa khóa; giữ thuộc tính nguồn | theo nguồn; numeric giá >=0/null |
| co_ma_khach_chinh_thuc | boolean | Không | Mã tracker khớp danh mục | merge many_to_one | boolean |
| ma_khach_nhom | string | Không | Mã chính thức hoặc nhóm SUY_DIEN từ hậu tố đơn | fallback bảo toàn thống kê lượng | không phải định danh pháp nhân với nhóm suy diễn |
| ten_khach_hang_nhom | string | Không | Tên hiển thị cho nhóm thống kê | master hoặc hậu tố đơn | text không null |
| nhom_san_pham_don_hang | nullable string | Có | Họ mã hoặc bucket mô tả chưa ánh xạ | FAMILY_MAP / NONCABLE_KEYWORDS | product analytics chỉ đọc mart_product_items |
| so_quy_cach | nullable integer | Có | Số quy cách giá được gom theo mã | Excel danh mục/bảng giá → chuẩn hóa khóa; giữ thuộc tính nguồn | theo nguồn; numeric giá >=0/null |
| cap_1_min | nullable real number | Có | Biên giá trị tham chiếu theo cấp, không phải doanh thu | min/max giá trong các quy cách cùng mã | numeric finite >=0/null |
| cap_2_min | nullable real number | Có | Biên giá trị tham chiếu theo cấp, không phải doanh thu | min/max giá trong các quy cách cùng mã | numeric finite >=0/null |
| cap_3_min | nullable real number | Có | Biên giá trị tham chiếu theo cấp, không phải doanh thu | min/max giá trong các quy cách cùng mã | numeric finite >=0/null |
| khach_le_min | nullable real number | Có | Biên giá trị tham chiếu theo cấp, không phải doanh thu | min/max giá trong các quy cách cùng mã | numeric finite >=0/null |
| cap_1_max | nullable real number | Có | Biên giá trị tham chiếu theo cấp, không phải doanh thu | min/max giá trong các quy cách cùng mã | numeric finite >=0/null |
| cap_2_max | nullable real number | Có | Biên giá trị tham chiếu theo cấp, không phải doanh thu | min/max giá trong các quy cách cùng mã | numeric finite >=0/null |
| cap_3_max | nullable real number | Có | Biên giá trị tham chiếu theo cấp, không phải doanh thu | min/max giá trong các quy cách cùng mã | numeric finite >=0/null |
| khach_le_max | nullable real number | Có | Biên giá trị tham chiếu theo cấp, không phải doanh thu | min/max giá trong các quy cách cùng mã | numeric finite >=0/null |
| gia_trong_giai_doan_xac_nhan | boolean | Không | Năm nằm trong hiệu lực giá xác nhận | PRICE_VALID_YEARS | boolean |
| co_don_gia_tham_khao | boolean | Không | Có ít nhất một cấp giá | merge exact canonical code | boolean |
| ly_do_khong_co_gia | nullable string | Có | Lý do thiếu giá hoặc ngoài hiệu lực | price join/validity | text/null |
| gia_tri_cap_1_min | nullable real number | Có | Biên giá trị tham chiếu theo cấp, không phải doanh thu | KM × biên giá | numeric finite >=0/null |
| gia_tri_cap_1_max | nullable real number | Có | Biên giá trị tham chiếu theo cấp, không phải doanh thu | KM × biên giá | numeric finite >=0/null |
| gia_tri_cap_2_min | nullable real number | Có | Biên giá trị tham chiếu theo cấp, không phải doanh thu | KM × biên giá | numeric finite >=0/null |
| gia_tri_cap_2_max | nullable real number | Có | Biên giá trị tham chiếu theo cấp, không phải doanh thu | KM × biên giá | numeric finite >=0/null |
| gia_tri_cap_3_min | nullable real number | Có | Biên giá trị tham chiếu theo cấp, không phải doanh thu | KM × biên giá | numeric finite >=0/null |
| gia_tri_cap_3_max | nullable real number | Có | Biên giá trị tham chiếu theo cấp, không phải doanh thu | KM × biên giá | numeric finite >=0/null |
| gia_tri_khach_le_min | nullable real number | Có | Biên giá trị tham chiếu theo cấp, không phải doanh thu | KM × biên giá | numeric finite >=0/null |
| gia_tri_khach_le_max | nullable real number | Có | Biên giá trị tham chiếu theo cấp, không phải doanh thu | KM × biên giá | numeric finite >=0/null |
| don_gia_tham_khao | nullable real number | Có | Midpoint khoảng đơn giá cấp 2 | (cap_2_min+cap_2_max)/2 | finite >=0/null |
| gia_tri_uoc_tinh | nullable real number | Có | Giá trị quy đổi tham khảo, không phải doanh thu | KM × midpoint cấp 2 | null khi thiếu giá/lượng; đơn vị tiền chưa xác minh |
| nghi_ngo_outlier | boolean | Không | Cờ cực trị trên sổ dòng nguồn | sales ngoài dự án; log1p(KM) > Q3+3IQR | boolean; không xóa khỏi tổng ghi nhận |
| outlier_stat_threshold_km | nullable real number | Có | Ngưỡng mô tả hồi cứu | fit toàn lịch sử ở mart; forecast fit riêng train | finite >=0 |
| outlier_duoc_xac_nhan_la_phat_sinh_that | boolean | Không | Đơn dự án đã được xác nhận lượng | CONFIRMED_PROJECT_ORDERS | boolean; không gắn cờ cực trị |

## unresolved_items.csv

Grain: một dòng nguồn chưa thể quy thuộc mã/lượng. Dòng: 436.

| Cột | Dtype | Nullable | Định nghĩa | Nguồn / biến đổi | Domain |
|---|---|---|---|---|---|
| item_id | integer | Không | Khóa sổ nguồn, một dòng Excel | tracker → thứ tự nạp deterministic | unique ở fact_order_items; FK trong product fact |
| order_row_id | integer | Không | Khóa header: ID dòng nguồn đầu tiên của mã xác nhận đơn | tracker → nhóm mã xác nhận | unique ở header; FK trong item |
| order_source_row_id | integer | Không | ID dòng nguồn, liên kết ngược ingestion | tracker → thứ tự nạp | unique, không null |
| item_text_raw | nullable string | Có | Mô tả sản phẩm nguyên gốc | SẢN PHẨM → giữ nguyên | text/null |
| parsed | boolean | Không | Có numeric quantity và đơn vị | so_luong.notna & don_vi.notna | boolean; không chứng minh product match |
| parsed_product_token | nullable string | Có | Token chuẩn hóa từ RAW; KHÔNG đồng nghĩa mã tham chiếu | Unicode/semantic parser + bảng tham chiếu | không null ở product fact; null khi unresolved hoặc split ở sổ nguồn |
| so_luong | nullable real number | Có | Lượng nguồn hoặc lượng được phân bổ ở product fact | SỐ LƯỢNG → numeric; split chỉ theo amount rõ ràng | finite >= 0/null; không cộng các đơn vị khác nhau |
| don_vi | nullable string | Có | Đơn vị nguồn chuẩn hóa | ĐƠN VỊ → trim/uppercase | KM/M/KG/CÁI/BỘ/LICENSE/TẤN/null trong snapshot |
| bien_the | nullable string | Có | Marker biến thể để audit | raw regex LT/SQ/LỎNG/CHẶT | text/null; canonical là kết quả parser |
| so_luong_km | nullable real number | Có | KM quan sát, không điền thiếu | KM giữ nguyên; M chia 1000; đơn vị khác null | finite >=0/null |
| source_file | string | Không | Tên tệp nguồn | ingestion | thuộc data/raw |
| source_sheet | string | Không | Sheet nguồn | ingestion | DATA_CHUAN_HOA |
| source_excel_row | integer | Không | Số dòng vật lý Excel, gồm header | ingestion → index + 3 | integer >= 3 |
| parse_status | string | Không | Cấp xác nhận sản phẩm | parser + authoritative reference | exact_reference / recognized_generic / ambiguous / unmapped / unresolved_multiple / allocated_multiple |
| allocation_status | string | Không | Căn cứ phân bổ lượng | parser + đối soát source total | single / split / unresolved |
| product_candidates | nullable string | Có | Danh sách mã nhận diện phục vụ audit, không phải dimension sản phẩm | parser → join bằng dấu phân cách | text/null; không dùng cộng lượng theo mã |
| parse_reason | string | Không | Lý do nhận diện/phân bổ hoặc từ chối | parser | text |
| canonical_product_code | nullable string | Có | Mã thuộc danh mục sản phẩm hoặc bảng giá; có thể bao phủ nhiều quy cách kỹ thuật | chỉ gán khi exact_reference | nullable string; generic/unresolved bắt buộc null |
| is_reference_product_code | boolean | Không | Khớp chính xác mã tham chiếu | parse_status == exact_reference | boolean; false cho generic/unresolved |
| product_family_code | nullable string | Có | Quy cách cơ sở của token (ví dụ FTTH02), không phải SKU | token bỏ hậu tố sau dấu gạch nối | string/null; giữ LT/SQ trong parsed_product_token và canonical_product_code |

## Target và feature

Trong phạm vi đề tài, một đơn được gán WIN khi cả ba trường Sản phẩm, Số lượng và Đơn vị đều có dữ liệu; nếu thiếu ít nhất một trong ba trường, đơn được gán LOST.

CHOT_DON là binary target: 1 = WIN, 0 = LOST. Có dữ liệu nghĩa là giá trị không null và chuyển sang text rồi strip whitespace không rỗng. Với đơn nhiều dòng, tất cả dòng nguồn phải có đủ ba trường để đơn WIN; chỉ một dòng thiếu thì LOST. Đơn không có dòng cũng không được gán WIN.

Nhãn đọc ô Excel gốc theo source_file/source_sheet/source_excel_row, trước chuyển kiểu, mapping hoặc quy đổi. Giá trị như KM, M .), quantity 0, chuỗi không phải số hoặc unit ngoài danh sách vẫn được tính là có dữ liệu. Data quality được audit riêng và không quyết định target. product_present, quantity_present, unit_present, line_complete và mọi cờ tạo nhãn đều bị loại khỏi predictors. Rule thực thi tập trung tại approval_prediction/target.py.

Grain modeling_dataset: một đơn sales, target nhị phân bắt buộc. order_id duy nhất; customer_id có thể rỗng. history_latest_month phải nhỏ hơn order_month. chot_don là binary target: 1 = WIN, 0 = LOST, không nullable. Ba trường tạo nhãn và mọi cờ dẫn xuất đều bị loại khỏi predictors.
| Cột | Dtype | Nullable | Ý nghĩa | Nguồn | Domain |
|---|---|---|---|---|---|
| customer_is_known | float64 | Không | Có mã khách nguồn; không khẳng định khớp master hoặc khách cũ | Header sales trước tháng dự báo / lịch tháng | 0 or 1; đơn vị: indicator |
| prior_order_count | float64 | Không | Số lần tiếp nhận đơn bán trước tháng hiện tại của cùng mã khách | Header sales trước tháng dự báo / lịch tháng | integer >= 0; đơn vị: orders |
| recency_months | float64 | Có | Khoảng cách tháng tới lần tiếp nhận trước gần nhất; missing nếu không có lịch sử | Header sales trước tháng dự báo / lịch tháng | integer >= 1; null without customer history; đơn vị: months |
| customer_active_months_before | float64 | Không | Số tháng có đơn trước tháng hiện tại | Header sales trước tháng dự báo / lịch tháng | integer >= 0; đơn vị: active months |
| orders_last_3m | float64 | Không | Số đơn trong ba tháng hoàn tất trước tháng hiện tại | Header sales trước tháng dự báo / lịch tháng | integer >= 0; đơn vị: orders |
| orders_last_6m | float64 | Không | Số đơn trong sáu tháng hoàn tất trước tháng hiện tại | Header sales trước tháng dự báo / lịch tháng | integer >= 0; đơn vị: orders |
| prior_monthly_order_trend | float64 | Không | (Số đơn ba tháng gần nhất - số đơn ba tháng trước đó)/3 | Header sales trước tháng dự báo / lịch tháng | signed real, unbounded; >0 increasing, <0 decreasing, 0 unchanged; zero without history; đơn vị: orders/month difference between adjacent three-month averages |
| year | float64 | Không | Năm tiếp nhận theo order_month | Header sales trước tháng dự báo / lịch tháng | calendar year; đơn vị: year |
| month | float64 | Không | Tháng tiếp nhận | Header sales trước tháng dự báo / lịch tháng | integer 1..12; đơn vị: month |
| quarter | float64 | Không | Quý tiếp nhận | Header sales trước tháng dự báo / lịch tháng | integer 1..4; đơn vị: quarter |
| month_sin | float64 | Không | sin(2*pi*month/12) | Header sales trước tháng dự báo / lịch tháng | -1..1; đơn vị: unitless |
| month_cos | float64 | Không | cos(2*pi*month/12) | Header sales trước tháng dự báo / lịch tháng | -1..1; đơn vị: unitless |
