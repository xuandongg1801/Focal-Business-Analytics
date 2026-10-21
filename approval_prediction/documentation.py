"""Vietnamese reports generated exclusively from current-run artifacts."""
import pandas as pd
from .config import FEATURES, BLACKLIST, FEATURE_DOMAINS

from .target import TARGET_DEFINITION as TARGET

LIMITATIONS = """Trong project, WIN/LOST được xác định theo quy tắc nghiệp vụ Product + Quantity + Unit của toàn bộ dòng thuộc đơn. Nhãn này không chứng minh ký hợp đồng, doanh thu, thanh toán hoặc trạng thái CRM opportunity Won/Lost.

Tracker là ảnh chụp hồi cứu, thiếu log chứng minh mã khách/ngày tiếp nhận đã được lưu trước kết quả. Thí nghiệm giả định các thông tin này được biết khi tạo đơn; đơn có thể được nhập bổ sung muộn. Không dùng outcome/volume/sản phẩm lịch sử vì thiếu timestamp sẵn có. WIN/LOST lịch sử trong UI chỉ mô tả các đơn trước tháng được chọn theo snapshot, không làm predictor. Probability chưa calibrated; không tự động chấp nhận/từ chối đơn.

Mẫu khoảng một nghìn đơn, ba năm, lặp theo khách và chỉ một holdout 2025 nên hiệu năng/nhóm nhỏ có thể không ổn định. Holdout có prior analyst exposure; đánh giá hồi cứu không thay thế kiểm định prospective trên dữ liệu phát sinh sau phát hành mô hình. Không diễn giải importance là nhân quả. DL không nhất thiết vượt ML. Cần log thời gian và kiểm định prospective trước triển khai."""
DESCRIPTIONS = {
    'customer_is_known': 'Có mã khách nguồn; không khẳng định khớp master hoặc khách cũ',
    'prior_order_count': 'Số lần tiếp nhận đơn bán trước tháng hiện tại của cùng mã khách',
    'recency_months': 'Khoảng cách tháng tới lần tiếp nhận trước gần nhất; missing nếu không có lịch sử',
    'customer_active_months_before': 'Số tháng có đơn trước tháng hiện tại',
    'orders_last_3m': 'Số đơn trong ba tháng hoàn tất trước tháng hiện tại',
    'orders_last_6m': 'Số đơn trong sáu tháng hoàn tất trước tháng hiện tại',
    'prior_monthly_order_trend': '(Số đơn ba tháng gần nhất - số đơn ba tháng trước đó)/3',
    'year': 'Năm tiếp nhận theo order_month', 'month': 'Tháng tiếp nhận', 'quarter': 'Quý tiếp nhận',
    'month_sin': 'sin(2*pi*month/12)', 'month_cos': 'cos(2*pi*month/12)',
}
HISTORY = '''Mỗi đơn tháng t chỉ đọc đơn tháng <t; không có thứ tự giả giữa các đơn cùng ngày/tháng. Mỗi đơn sales có đúng một nhãn nhị phân WIN/LOST; tất cả đơn sales đều tham gia dataset. Thiếu mã không gộp thành khách ảo. History trong validation/test có thể dùng số lần tiếp nhận các tháng trước trong validation/test, không đọc outcome/nội dung hàng hóa của chúng. Đây là đánh giá tuần tự, không dự báo cả năm từ đầu năm. Median/scaling/class weights fit train-only. ID không vào X; không có categorical feature cần encode.

Market snapshot chỉ dùng error analysis hồi cứu, không làm predictor vì master thiếu effective date. data_completeness_by_period.csv chỉ mô tả drift của nhãn, không dùng làm feature hoặc giải thích lỗi từng dự đoán.'''


def markdown_table(frame):
    d = frame.copy()
    for c in d.select_dtypes('number'):
        d[c] = d[c].astype(str) if pd.api.types.is_integer_dtype(d[c]) else d[c].map(lambda v: f'{v:.4f}' if pd.notna(v) else 'NA')
    return '| '+' | '.join(d.columns)+' |\n|'+'|'.join(['---']*len(d.columns))+'|\n'+'\n'.join(
        '| '+' | '.join(str(v).replace('|','/') for v in r)+' |' for r in d.itertuples(index=False, name=None))


def write(out, name, content):
    (out/'docs'/name).write_text(content.strip()+'\n', encoding='utf-8')


def write_audit_docs(out, dataset):
    rows = [dict(feature_name=f, description=DESCRIPTIONS[f], semantic_type='numeric feature', dtype='float64',
        nullable=(f == 'recency_months'), domain=FEATURE_DOMAINS[f][0], unit=FEATURE_DOMAINS[f][1], source='fact_order_header',
        available_at_prediction_time='Có điều kiện: giả định đã biết khi tiếp nhận; history tháng < hiện tại',
        used_in_model=True, leakage_risk='Không dùng outcome; rủi ro nhập muộn chưa có log',
        reason='Lịch sử tiếp nhận/thời gian; không phụ thuộc ba trường tạo nhãn') for f in FEATURES]
    removed = sorted((BLACKLIST - {'chot_don'}) | {'market','customer_group','RFM','ABC','customer_id','order_id','raw_customer_name','order_type','prior_distinct_products'})
    for f in removed:
        reason = 'Trực tiếp tiết lộ nhãn, định danh hoặc không chứng minh được thời điểm sẵn có'
        if f.startswith(('prior_', 'approved_orders_')):
            reason = 'Không có timestamp xác nhận nội dung/kết quả đơn cũ đã biết khi dự báo'
        rows.append(dict(feature_name=f, description='Excluded', source='Items/header/master/derived',
            available_at_prediction_time='Không dùng: hậu nghiệm hoặc chưa xác minh', used_in_model=False,
            leakage_risk='High / unverified', reason=reason))
    rows.append(dict(feature_name='chot_don', description='Binary target: 1 = WIN, 0 = LOST; Product, Quantity and Unit cells present on every required source line',
        semantic_type='binary target', dtype='int64', nullable=False, domain='0 or 1', unit='class',
        source='Product + Quantity + Unit via target.py', available_at_prediction_time='Label only',
        used_in_model=False, leakage_risk='Target', reason='Three target-defining fields and derived flags are excluded from predictors'))
    dictionary = pd.DataFrame(rows)
    dictionary.to_csv(out/'tables/feature_dictionary.csv', index=False, encoding='utf-8-sig')
    mapping = [('SỐ XÁC NHẬN ĐƠN HÀNG','so_xac_nhan_don_hang','order_id','Pseudonymized order key'),
        ('NGÀY','ngay_dt/order_month','order_date/order_month','Existing normalization'),
        ('MÃ KHÁCH','ma_khach','customer_id','Pseudonymized ID; no suffix inference'),
        ('SẢN PHẨM','raw_product (original Excel cell)','product_present','Non-null and non-blank only; label audit, excluded from X'),
        ('SỐ LƯỢNG','raw_quantity (original Excel cell)','quantity_present','Non-null and non-blank only; no numeric parsing for label'),
        ('ĐƠN VỊ','raw_unit (original Excel cell)','unit_present','Non-null and non-blank only; no unit-list check for label')]
    pd.DataFrame(mapping, columns=['raw_column','processed_column','modeling_column','rule']).to_csv(out/'tables/column_mapping.csv', index=False, encoding='utf-8-sig')
    write(out, 'leakage_audit.md', '# Leakage audit\n\n'+markdown_table(dictionary)+'\n\n'+HISTORY+'\n\n'+LIMITATIONS)
    splits = dataset.groupby('split').agg(n=('order_id','size'), first_month=('order_month','min'),
        last_month=('order_month','max'), first_date=('order_date','min'), last_date=('order_date','max'), class_1=('chot_don','sum')).reset_index()
    splits['class_0'] = splits.n-splits.class_1
    splits['class_1_rate'] = splits.class_1/splits.n
    splits['minority_rate'] = splits[['class_0','class_1']].min(axis=1)/splits.n
    splits['imbalance_warning'] = splits.minority_rate.lt(.1)
    splits.to_csv(out/'tables/split_audit.csv', index=False)
    write(out, 'data_contract.md', '# Dữ liệu phân loại\n\n'+TARGET+'\n\n'+HISTORY+'\n\n'+markdown_table(splits))


def write_results(out, comparison, frozen):
    selected = comparison[comparison.model.eq(frozen['selected_model'])].iloc[0]
    content = f"""# Model card

Mô hình: {frozen['selected_model']}. Ngưỡng: {selected.threshold:.6f}.
Quy tắc chọn: {frozen['selection_metric']}. Median/scaler chỉ fit train.
Từng ứng viên được chấm trên cùng validation; threshold tối đa macro-F1,
sau đó F1 lớp 1, rồi khoảng cách tới 0,5. Test dùng đánh giá sau khi khóa lựa chọn.

{TARGET}

{markdown_table(comparison[['model','validation_macro_f1','validation_roc_auc','test_macro_f1','test_roc_auc','threshold','selected_on_validation']])}

{LIMITATIONS}

Feature: {', '.join(FEATURES)}.
Permutation importance trên validation; không suy diễn nhân quả hoặc đóng góp cho riêng một giao dịch.
Chi tiết: feature_importance.csv, subgroup_metrics.csv, false_positive_cases.csv,
false_negative_cases.csv và selected_model_cluster_bootstrap.csv trong tables/.
Bốn họ mô hình được giữ làm ứng viên so sánh có validation và holdout thực;
ứng dụng mặc định dùng mô hình được chọn trên validation, cho phép chọn từng model.
Một lần bấm Phân tích giao dịch tạo một vector features và chạy cả bốn model.
Card chính lấy trực tiếp kết quả của model được chọn từ bảng chung, với threshold riêng.
Đổi model chỉ đổi card; đổi khách/tháng/năm hoặc artifact làm mất hiệu lực toàn bộ kết quả.
Input gồm khách hàng, tháng, năm và mô hình; lịch sử khách hàng nằm giữa card chính và bảng so sánh.
"""
    write(out, 'model_card.md', content)
