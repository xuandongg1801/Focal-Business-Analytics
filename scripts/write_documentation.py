"""Write current technical documentation from validated outputs and schema."""
import json
import sys

import pandas as pd
from config import ROOT, PROC, TAB, PROCESSED_FILES

sys.path.insert(0, str(ROOT))
from approval_prediction.config import FEATURES, FEATURE_DOMAINS
from data_contract import semantic_dtype
from approval_prediction.documentation import DESCRIPTIONS, TARGET, HISTORY, LIMITATIONS, markdown_table


def read_json(path):
    return json.loads(path.read_text(encoding='utf-8'))


def main():
    docs = ROOT/'docs'
    docs.mkdir(exist_ok=True)
    quality = read_json(TAB/'pipeline_validation.json')
    forecast = read_json(TAB/'forecast_methodology.json')
    model_root = ROOT/'outputs/approval_prediction'
    selection = read_json(model_root/'models/selection.json')
    schema = read_json(model_root/'models/model_schema.json')
    comparison = pd.read_csv(model_root/'tables/model_comparison.csv')
    splits = pd.read_csv(model_root/'tables/split_audit.csv')
    rfv = pd.read_csv(TAB/'customer_rfm_segments.csv')
    def write(name, text):
        (docs/name).write_text(text.strip()+'\n', encoding='utf-8')
    write('01_project_overview.md', '''# Mục đích và kiến trúc

Phân tích đơn hàng, sản lượng ghi nhận, cơ cấu sản phẩm và khách hàng; thử nghiệm
dự báo nhu cầu nền và dự đoán WIN/LOST đơn hàng theo rule Product + Quantity + Unit. Dữ liệu lượng không chứng minh
đã giao hàng; giá tham chiếu không phải doanh thu. Không có giá vốn, lợi nhuận, thanh toán hoặc CRM opportunity outcome để xác minh kết quả thương mại.

```text
data/raw/*.xlsx → ingestion và kiểm tra schema
  → header + sổ dòng nguồn → đối chiếu đầy đủ khóa/trường
  → phân bổ có căn cứ → fact_product_items + unresolved_items
  → mart nguồn / mart sản phẩm → EDA, RFV, ABC, forecast
  → nhãn WIN/LOST từ dòng nguồn → feature lịch sử → train/validation/test
  → model + schema + fingerprint → Streamlit: Overview / EDA / Prediction
```

Các pipeline chạy offline, không tải dữ liệu bên ngoài. Source Excel được giữ nguyên.
Business rule tập trung ở scripts/config.py và approval_prediction/config.py; rule nhãn tại approval_prediction/target.py.
Transformation không chạy lúc import. Đường dẫn suy từ vị trí source, không dựa vào cwd.
''')
    meanings = {
        'order_row_id': ('Khóa header: ID dòng nguồn đầu tiên của mã xác nhận đơn', 'tracker → nhóm mã xác nhận', 'unique ở header; FK trong item'),
        'item_id': ('Khóa sổ nguồn, một dòng Excel', 'tracker → thứ tự nạp deterministic', 'unique ở fact_order_items; FK trong product fact'),
        'order_source_row_id': ('ID dòng nguồn, liên kết ngược ingestion', 'tracker → thứ tự nạp', 'unique, không null'),
        'source_file': ('Tên tệp nguồn', 'ingestion', 'thuộc data/raw'),
        'source_sheet': ('Sheet nguồn', 'ingestion', 'DATA_CHUAN_HOA'),
        'source_excel_row': ('Số dòng vật lý Excel, gồm header', 'ingestion → index + 3', 'integer >= 3'),
        'product_item_id': ('Khóa source item + thứ tự phân bổ', 'parser → item_id:allocation_index', 'unique, không null'),
        'item_text_raw': ('Mô tả sản phẩm nguyên gốc', 'SẢN PHẨM → giữ nguyên', 'text/null'),
        'parsed_product_token': ('Token chuẩn hóa từ RAW; KHÔNG đồng nghĩa mã tham chiếu', 'Unicode/semantic parser + bảng tham chiếu', 'không null ở product fact; null khi unresolved hoặc split ở sổ nguồn'),
        'product_candidates': ('Danh sách mã nhận diện phục vụ audit, không phải dimension sản phẩm', 'parser → join bằng dấu phân cách', 'text/null; không dùng cộng lượng theo mã'),
        'parse_status': ('Cấp xác nhận sản phẩm', 'parser + authoritative reference', 'exact_reference / recognized_generic / ambiguous / unmapped / unresolved_multiple / allocated_multiple'),
        'canonical_product_code': ('Mã thuộc danh mục sản phẩm hoặc bảng giá; có thể bao phủ nhiều quy cách kỹ thuật', 'chỉ gán khi exact_reference', 'nullable string; generic/unresolved bắt buộc null'),
        'is_reference_product_code': ('Khớp chính xác mã tham chiếu', 'parse_status == exact_reference', 'boolean; false cho generic/unresolved'),
        'product_family_code': ('Quy cách cơ sở của token (ví dụ FTTH02), không phải SKU', 'token bỏ hậu tố sau dấu gạch nối', 'string/null; giữ LT/SQ trong parsed_product_token và canonical_product_code'),
        'allocation_status': ('Căn cứ phân bổ lượng', 'parser + đối soát source total', 'single / split / unresolved'),
        'parse_reason': ('Lý do nhận diện/phân bổ hoặc từ chối', 'parser', 'text'),
        'parsed': ('Có numeric quantity và đơn vị', 'so_luong.notna & don_vi.notna', 'boolean; không chứng minh product match'),
        'so_luong': ('Lượng nguồn hoặc lượng được phân bổ ở product fact', 'SỐ LƯỢNG → numeric; split chỉ theo amount rõ ràng', 'finite >= 0/null; không cộng các đơn vị khác nhau'),
        'don_vi': ('Đơn vị nguồn chuẩn hóa', 'ĐƠN VỊ → trim/uppercase', 'KM/M/KG/CÁI/BỘ/LICENSE/TẤN/null trong snapshot'),
        'so_luong_km': ('KM quan sát, không điền thiếu', 'KM giữ nguyên; M chia 1000; đơn vị khác null', 'finite >=0/null'),
        'order_month_from_date': ('Tháng suy từ ngày parse', 'ngay_dt → YYYY-MM', 'tháng hợp lệ/null'),
        'order_month_from_code': ('Tháng /YYMM/ trong mã đơn', 'regex kiểm tra month 1..12', 'YYYY-MM/null'),
        'order_month_canonical': ('Tháng phân tích', 'date nếu năm khớp file, rồi code, rồi date fallback', 'YYYY-MM không null'),
        'order_month': ('Alias của tháng canonical cho aggregate/feature', 'order_month_canonical', 'YYYY-MM không null'),
        'order_month_rule': ('Nhánh chọn tháng', 'canonical month rule', 'date_in_file_year / code_fallback / date_fallback'),
        'order_month_conflict': ('Ngày và mã có tháng khác nhau', 'cả hai có tháng và khác nhau', 'boolean'),
        'ma_khach': ('Mã khách ghi trong tracker', 'MÃ KHÁCH → trim/uppercase', 'text/null; không suy danh tính từ hậu tố đơn'),
        'so_xac_nhan_don_hang': ('Khóa đơn nghiệp vụ', 'SỐ XÁC NHẬN ĐƠN HÀNG', 'unique, không null ở header'),
        'la_don_ban_hang': ('Thuộc population đơn bán', 'prefix CA/AC/SL/EQ; contract fallback nếu thiếu prefix', 'boolean'),
        'loai_don': ('Loại đơn theo prefix', 'ORDER_TYPE_MAP', 'CA/AC/SL/EQ sales; RM/IT nội bộ'),
        'loai_don_tu_so_hop_dong': ('Phân loại dùng prefix hợp đồng', 'prefix fallback', 'boolean'),
        'nghi_ngo_outlier': ('Cờ cực trị trên sổ dòng nguồn', 'sales ngoài dự án; log1p(KM) > Q3+3IQR', 'boolean; không xóa khỏi tổng ghi nhận'),
        'outlier_stat_threshold_km': ('Ngưỡng mô tả hồi cứu', 'fit toàn lịch sử ở mart; forecast fit riêng train', 'finite >=0'),
        'outlier_duoc_xac_nhan_la_phat_sinh_that': ('Đơn dự án đã được xác nhận lượng', 'CONFIRMED_PROJECT_ORDERS', 'boolean; không gắn cờ cực trị'),
        'co_ma_khach_chinh_thuc': ('Mã tracker khớp danh mục', 'merge many_to_one', 'boolean'),
        'ma_khach_nhom': ('Mã chính thức hoặc nhóm SUY_DIEN từ hậu tố đơn', 'fallback bảo toàn thống kê lượng', 'không phải định danh pháp nhân với nhóm suy diễn'),
        'ten_khach_hang_nhom': ('Tên hiển thị cho nhóm thống kê', 'master hoặc hậu tố đơn', 'text không null'),
        'nhom_san_pham_don_hang': ('Họ mã hoặc bucket mô tả chưa ánh xạ', 'FAMILY_MAP / NONCABLE_KEYWORDS', 'product analytics chỉ đọc mart_product_items'),
        'gia_tri_uoc_tinh': ('Giá trị quy đổi tham khảo, không phải doanh thu', 'KM × midpoint cấp 2', 'null khi thiếu giá/lượng; đơn vị tiền chưa xác minh'),
        'don_gia_tham_khao': ('Midpoint khoảng đơn giá cấp 2', '(cap_2_min+cap_2_max)/2', 'finite >=0/null'),
        'co_don_gia_tham_khao': ('Có ít nhất một cấp giá', 'merge exact canonical code', 'boolean'),
        'gia_trong_giai_doan_xac_nhan': ('Năm nằm trong hiệu lực giá xác nhận', 'PRICE_VALID_YEARS', 'boolean'),
        'ly_do_khong_co_gia': ('Lý do thiếu giá hoặc ngoài hiệu lực', 'price join/validity', 'text/null'),
        'ngay': ('Ngày nguồn', 'NGÀY → giữ nguyên', 'date/text/null'),
        'ngay_dt': ('Ngày parse dayfirst', 'to_datetime format=mixed', 'date/null; supplied invalid bị validator từ chối'),
        'ngay_bi_thieu': ('Ngày nguồn trống', 'ngay.isna', 'boolean'),
        'ngay_khong_hop_le': ('Ngày có nhập nhưng không parse được', 'ngay.notna & ngay_dt.isna', 'boolean'),
        'ngay_nam_khong_khop_file': ('Năm ngày khác năm tệp', 'ngay_dt.year != nam_file nếu có ngày', 'boolean'),
        'order_year': ('Năm tháng canonical', 'order_month[:4]', 'year'),
        'nam_file': ('Năm trong tên tracker', 'tên tệp YYYY', 'year'),
        'wo': ('Mã lệnh sản xuất được ghi nhận', 'WO', 'text/null; thiếu không suy giao từ tồn'),
        'so_hop_dong': ('Mã hợp đồng nguồn', 'SỐ HỢP ĐỒNG', 'text/null'),
        'bien_the': ('Marker biến thể để audit', 'raw regex LT/SQ/LỎNG/CHẶT', 'text/null; canonical là kết quả parser'),
    }
    master_fields = {
        'ma_khach_hang':'Mã danh mục khách', 'ten_khach_hang':'Tên nguồn đã ẩn danh', 'thi_truong':'Nhãn thị trường nguồn',
        'ten_khach_hang_la_placeholder':'Tên nguồn là placeholder ẩn danh', 'stt':'Thứ tự nguồn',
        'ma_san_pham':'Mã danh mục sản phẩm', 'ten_san_pham':'Tên danh mục sản phẩm', 'nhom_san_pham':'Nhóm danh mục',
        'don_vi_tinh':'Đơn vị danh mục', 'trang_thai_kinh_doanh':'Trạng thái trong master, không phải đơn',
        'loai_san_pham_quy_cach':'Quy cách master', 'nguon_hang':'Nguồn hàng ghi trong master',
        'ky_ma_hieu':'Mã bảng giá', 'ten_hang_hoa':'Tên trong bảng giá', 'tieu_chuan_ky_thuat':'Quy cách kỹ thuật bảng giá',
        'gia_cap_1':'Đơn giá tham chiếu cấp 1', 'gia_cap_2':'Đơn giá tham chiếu cấp 2', 'gia_cap_3':'Đơn giá tham chiếu cấp 3',
        'gia_ban_khach_le':'Đơn giá tham chiếu khách lẻ', 'so_bien_the_theo_ma':'Số quy cách cùng mã trong bảng giá',
        'so_quy_cach':'Số quy cách giá được gom theo mã',
    }
    dictionary = ['# Từ điển dữ liệu', '\nDtype ngữ nghĩa lấy từ scripts/data_contract.py, độc lập với dtype pandas suy từ snapshot. Quyền null theo contract; cột mã toàn null vẫn là nullable string.']
    grains = {'dim_customer.csv':'một mã khách', 'dim_product.csv':'một mã danh mục sản phẩm',
              'dim_price_list.csv':'một mã/quy cách giá; mã có thể lặp',
              'fact_order_header.csv':'một mã xác nhận đơn hàng',
              'fact_order_items.csv':'một dòng vật lý Excel; sổ nguồn, chưa phải product fact',
              'mart_order_items.csv':'một dòng nguồn đã nối header/master',
              'fact_product_items.csv':'một sản phẩm được quy thuộc trong một dòng nguồn',
              'mart_product_items.csv':'một canonical product item đã nối metadata',
              'unresolved_items.csv':'một dòng nguồn chưa thể quy thuộc mã/lượng'}
    mandatory = {'order_row_id','item_id','order_source_row_id','source_file','source_sheet','source_excel_row','product_item_id','so_xac_nhan_don_hang','order_month','order_month_canonical','order_year','nam_file','parse_status','allocation_status','parse_reason','parsed','ma_khach_nhom','ten_khach_hang_nhom','ma_khach_hang','ma_san_pham','ky_ma_hieu'}
    for name in PROCESSED_FILES:
        df = pd.read_csv(PROC/name)
        rows = []
        for col in df:
            if col in meanings:
                definition, source, domain = meanings[col]
            elif col in master_fields:
                definition, source, domain = master_fields[col], 'Excel danh mục/bảng giá → chuẩn hóa khóa; giữ thuộc tính nguồn', 'theo nguồn; numeric giá >=0/null'
            elif col.endswith(('_min','_max')):
                definition, source, domain = ('Biên giá trị tham chiếu theo cấp, không phải doanh thu', 'KM × biên giá' if col.startswith('gia_tri_') else 'min/max giá trong các quy cách cùng mã', 'numeric finite >=0/null')
            else:
                raise ValueError(f'Missing dictionary definition: {name}.{col}')
            nullable = col not in mandatory and semantic_dtype(col) != 'boolean'
            if col == 'parsed_product_token' and 'product_items' in name:
                nullable = False
            if col == 'ma_khach_hang' and name.startswith('mart'):
                nullable = True
            rows.append([col,('nullable ' if nullable else '') + semantic_dtype(col),'Có' if nullable else 'Không',definition,source,domain])
        dictionary += [f'\n## {name}\n\nGrain: {grains[name]}. Dòng: {len(df)}.\n', markdown_table(pd.DataFrame(rows,columns=['Cột','Dtype','Nullable','Định nghĩa','Nguồn / biến đổi','Domain']))]
    dictionary += ['\n## Target và feature\n', TARGET, '\nGrain modeling_dataset: một đơn sales, target nhị phân bắt buộc. order_id duy nhất; customer_id có thể rỗng. history_latest_month phải nhỏ hơn order_month. chot_don là binary target: 1 = WIN, 0 = LOST, không nullable. Ba trường tạo nhãn và mọi cờ dẫn xuất đều bị loại khỏi predictors.']
    dictionary += [markdown_table(pd.DataFrame([[f,'float64', 'Có' if f=='recency_months' else 'Không', DESCRIPTIONS[f], 'Header sales trước tháng dự báo / lịch tháng', FEATURE_DOMAINS[f][0] + '; đơn vị: ' + FEATURE_DOMAINS[f][1]] for f in FEATURES],columns=['Cột','Dtype','Nullable','Ý nghĩa','Nguồn','Domain']))]
    write('02_data_dictionary.md','\n'.join(dictionary))
    write('03_data_pipeline.md', '''# Pipeline và grain

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
''')
    keys = ['orders','items','canonical_product_rows','exact_product_rows','generic_product_rows','ambiguous_product_rows','unresolved_rows','unresolved_multi_product_rows','unmapped_product_rows','month_conflict_orders','duplicate_order_ids','duplicate_item_ids','duplicate_item_candidate_rows','missing_quantity','missing_customer_code','outlier_rows','sales_km_raw','sales_km_non_outlier']
    write('04_data_quality.md', '# Chất lượng dữ liệu\n\n'+markdown_table(pd.DataFrame([(k,quality[k]) for k in keys],columns=['Chỉ tiêu','Giá trị']))+'''

Nguồn: [pipeline_validation.json](../outputs/tables/pipeline_validation.json).
Conservation: [quantity_conservation.csv](../outputs/tables/quantity_conservation.csv), tính riêng từng đơn vị.
Mã chưa ánh xạ có thể là hàng không phải cáp, ghi chú hoặc mã chưa có reference; không tự gọi là dữ liệu sai.
Hai dòng FE12 8 KM cùng đơn CA-094/2503/GIGA-NET ở các dòng nguồn khác nhau được giữ lại để xác minh.
Không tự xóa cực trị, hợp nhất mã khách hoặc sửa lượng. Không có log hiệu lực master hay trạng thái giao hàng để chứng minh thêm.
''')
    write('05_eda.md', '''# Phân tích mô tả

Header đếm số đơn; sổ nguồn cộng lượng ghi nhận; product fact tách mã tham chiếu và quy cách chung. Xếp hạng/ABC mã chỉ dùng exact_reference; cơ cấu họ dùng cả hai.
KM nguồn gồm nền + dự án xác nhận + cực trị thống kê, ba phần không giao nhau.
KM không cực trị vẫn gồm dự án. Nền loại cả dự án và cực trị, không được gọi là nhu cầu chắc chắn lặp lại.
Các dòng thiếu lượng được đếm riêng, không thay bằng 0. Calendar trống là không có lượng ghi nhận,
không chứng minh nhu cầu bằng 0. Không cộng M/KG/BỘ/CÁI vào KM ngoài quy đổi M/1.000.

ABC xếp giảm dần KM của sản phẩm có attribution hợp lệ, ngưỡng tích lũy 80/95%; sản phẩm
làm vượt ngưỡng vẫn thuộc lớp đang cộng. Denominator ABC chỉ là phần lượng đã quy thuộc.
Không sử dụng mã chưa rõ như một sản phẩm giả. Cần đọc quantity_conservation để biết phần bị loại khỏi attribution.
Nhóm khách SUY_DIEN là nhóm thống kê từ hậu tố đơn, không dùng cho RFV hoặc lịch sử khách model.
''')
    distribution = rfv.groupby('phan_khuc').agg(customers=('ma_khach','size'),km=('total_km','sum')).reset_index()
    write('06_rfv_analysis.md', f'''# Phân nhóm RFV

Snapshot: {rfv.snapshot_month.iloc[0] if len(rfv) else 'Không đủ dữ liệu'}; một dòng mỗi mã khách khớp danh mục.
Population: sales có KM không cực trị. Dòng HỦY hiện không có lượng, không vào population.
Không có trạng thái hủy/hoàn tất chính thức cho mọi đơn để lọc sâu hơn.

R = số tháng từ lần ghi nhận KM gần nhất đến snapshot; thấp hơn tốt hơn.
F = distinct order_row_id có KM; cao hơn nhiều lần ghi nhận hơn.
V = tổng KM; cao hơn nhiều lượng hơn, không suy doanh thu/lợi nhuận. total_value chỉ là tham khảo.

Điểm 1..4 = ceil(rank phần trăm × 4), average rank cho ties. R rank đảo chiều;
F/V rank cùng chiều. Ties có cùng điểm, không bẻ ties bằng mã khách; ít quan sát có thể thiếu một số lớp điểm.
Không dùng clustering hoặc dự đoán churn.

Nhãn heuristic, áp theo thứ tự: R=1 → Ít giao dịch gần đây; R/F/V đều >=3 → Gần đây,
thường xuyên, lượng cao; F>=3 → Tần suất cao; còn lại → Nhóm còn lại.
“Cao” là tương đối trong tập snapshot. Không dùng nhãn làm ground truth hay bằng chứng khách rời bỏ.

{markdown_table(distribution)}
''')
    write('07_forecasting.md', '# Dự báo KM nền\n\n'+markdown_table(pd.DataFrame([(k,forecast[k]) for k in ['history_start','history_end','validation_start','validation_end','validation_folds','test_start','test_end','selected_model','validation_wape_pct','validation_mae_km','test_wape_pct','test_mae_km','forecast_start','forecast_end']],columns=['Thuộc tính','Giá trị']))+'''

Naive, Historical Mean, Seasonal Naive (đủ lịch sử) và adjusted EWMA dùng cùng rolling folds.
Adjusted EWMA = level × (1−alpha/2), là ứng viên heuristic, không khẳng định bias correction tối ưu.
Outlier threshold fit riêng train mỗi fold; khóa để lọc validation/holdout. Cờ mart toàn lịch sử không vào evaluation.
Chọn pooled validation WAPE, tie-break MAE rồi tên; nếu denominator gần 0, dùng MAE và WAPE null.
Test không dùng selection hoặc tune; refit lựa chọn trên toàn history để tạo 6 tháng sau history_end.
Calendar tính trước khi lọc; tháng chỉ có dự án vẫn tồn tại. Calendar trống giả định tracker đầy đủ,
còn quantity thiếu trên dòng có thật vẫn chưa biết. Dự báo chỉ áp dụng nền đã lọc, không phải tổng nhu cầu.
Holdout có external exposure và dự án không có timestamp xác nhận, nên cần prospective evidence.
Không có prediction interval được hiệu chuẩn. Đây là frozen forecast snapshot, khác backtest holdout.
Khi horizon đã qua ngày xem, snapshot không phải dự báo tương lai live và chưa có actual mới để chấm.
prospective.py giữ thời điểm phát hành UTC thật, threshold và danh sách dự án; chỉ chấm tháng hoàn tất
sau issuance khi người dùng xác nhận độ đầy đủ tracker, không lùi ngày phát hành.
''')
    write('08_approval_prediction.md', '# Dự đoán WIN / LOST của đơn hàng\n\n'+TARGET+'\n\n'+HISTORY+'\n\n'+markdown_table(splits)+f'''

Mô hình được chọn: {selection['selected_model']}; threshold {schema['threshold']:.6f}.
12 numeric features: {', '.join(FEATURES)}. Không có ID/categorical encoding.
Median imputation (keep_empty_features), StandardScaler, class weights chỉ fit train.
Logistic C=.1/1/10; RF 200 cây depth/leaf (4,5)/(6,5)/(6,10); XGBoost depth2/3,
learning rate .03, max400, early stop25 trên validation; MLP 64/32, dropout .2,
Adam .001, max250, early stop20. MLP dùng Dataset shuffle seed42, batch32; validation không shuffle.
Đúng bốn ứng viên: Logistic Regression, Random Forest, XGBoost và MLP Neural Network.
Chọn validation macro-F1, ROC-AUC tie-break; threshold .05→.95 bước .01, macro-F1/F1/proximity0.5.
Persist lựa chọn trước khi chấm test. Cùng khách qua nhiều thời điểm là use case sequential arrivals,
không khẳng định đánh giá độc lập trên khách hoàn toàn mới. Không refit sau selection cho classification.

{markdown_table(comparison[['model','validation_macro_f1','validation_roc_auc','test_macro_f1','test_roc_auc','threshold']])}

{LIMITATIONS}

Target chỉ xét presence của ô nguồn; quality/mapping/conversion không tham gia label.
Metadata tại models/model_schema.json: run ID deterministic, dataset SHA, library versions,
features/order/dtype/nullability, threshold, validation/test metrics, source/artifact SHA.
Registry tập trung tại approval_prediction/registry.py. Mỗi model lưu type, feature schema, preprocessing version/hash, training cutoff, validation metrics, threshold, artifact hash và model version.
Inference kiểm tra schema, runtime versions và bundle hashes. File serialized chỉ tải từ bundle nội bộ tin cậy.
''')
    write('09_streamlit_app.md', '''# Ứng dụng

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
''')
    write('10_reproducibility.md', '''# Tái lập và kiểm định

Python 3.12; packages pin trong requirements.txt. Seed 42, single-thread estimator,
TensorFlow deterministic ops. Models được huấn luyện cùng runtime ghi trong manifest.
Không suppress incompatible-version warning. TensorFlow chạy CPU trên Windows;
thông báo GPU/platform hoặc deprecation nội bộ dependency không phải cảnh báo tương thích artifact.

verify_project.py compile recursive mọi source Python ngoài .venv/.cache/third-party;
check environment pins, paths, narrative and document links; pip check; full ETL; train;
full pytest data/ML/app với FutureWarning-as-error; pipeline lần hai so SHA; train độc lập lần hai so tables/figures/docs,
joblib artifacts và từng tensor trọng số MLP (không so timestamp trong archive Keras).
Cuối cùng kiểm tra schema/bundle và khởi động Streamlit qua health endpoint.
Failure ghi status FAIL, không giữ trạng thái thành công từ lần thực thi khác.

Kết quả máy đọc: [verification.json](../outputs/logs/verification.json),
[model verification](../outputs/approval_prediction/verification.json).
Fixture nguồn bảo vệ keys/raw text/quantity/unit/flags khi source SHA khớp;
semantic sản phẩm được bảo vệ bằng regression độc lập. Cột mã toàn null có kiểu nullable string theo data_contract.py.
Verifier sinh docs trước lần test cuối, lưu fingerprint source, versions và thời điểm hoàn tất; dọn runtime junk rồi kiểm tra hygiene.
Kiểm định trực tiếp repository local; không có bước đóng gói. Runtime cache và log không giữ sau khi PASS. Logs chẩn đoán được giữ nếu verifier thất bại, xóa sau khi đạt.
Pandas 2.2.3 có thể được kiểm tra bằng --pandas22-path trỏ tới package directory riêng; không đổi runtime chính.

Raw cần 3 tracker 2023–2025 trong snapshot và 3 danh mục/bảng giá tại data/raw/.
Thêm năm tracker được khám phá từ tên; thiếu sheet/cột/key phải fail rõ. Giá ngoài hiệu lực giữ null.
File nguồn riêng tư cần được cung cấp hợp lệ tại đúng vị trí; pipeline không tự fetch.
''')
    print(f'Wrote {len(list(docs.glob("*.md")))} current documentation files')


if __name__ == '__main__':
    main()
