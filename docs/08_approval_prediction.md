# Dự đoán WIN / LOST của đơn hàng

Trong phạm vi đề tài, một đơn được gán WIN khi cả ba trường Sản phẩm, Số lượng và Đơn vị đều có dữ liệu; nếu thiếu ít nhất một trong ba trường, đơn được gán LOST.

CHOT_DON là binary target: 1 = WIN, 0 = LOST. Có dữ liệu nghĩa là giá trị không null và chuyển sang text rồi strip whitespace không rỗng. Với đơn nhiều dòng, tất cả dòng nguồn phải có đủ ba trường để đơn WIN; chỉ một dòng thiếu thì LOST. Đơn không có dòng cũng không được gán WIN.

Nhãn đọc ô Excel gốc theo source_file/source_sheet/source_excel_row, trước chuyển kiểu, mapping hoặc quy đổi. Giá trị như KM, M .), quantity 0, chuỗi không phải số hoặc unit ngoài danh sách vẫn được tính là có dữ liệu. Data quality được audit riêng và không quyết định target. product_present, quantity_present, unit_present, line_complete và mọi cờ tạo nhãn đều bị loại khỏi predictors. Rule thực thi tập trung tại approval_prediction/target.py.

Mỗi đơn tháng t chỉ đọc đơn tháng <t; không có thứ tự giả giữa các đơn cùng ngày/tháng. Mỗi đơn sales có đúng một nhãn nhị phân WIN/LOST; tất cả đơn sales đều tham gia dataset. Thiếu mã không gộp thành khách ảo. History trong validation/test có thể dùng số lần tiếp nhận các tháng trước trong validation/test, không đọc outcome/nội dung hàng hóa của chúng. Đây là đánh giá tuần tự, không dự báo cả năm từ đầu năm. Median/scaling/class weights fit train-only. ID không vào X; không có categorical feature cần encode.

Market snapshot chỉ dùng error analysis hồi cứu, không làm predictor vì master thiếu effective date. data_completeness_by_period.csv chỉ mô tả drift của nhãn, không dùng làm feature hoặc giải thích lỗi từng dự đoán.

| split | n | first_month | last_month | first_date | last_date | class_1 | class_0 | class_1_rate | minority_rate | imbalance_warning |
|---|---|---|---|---|---|---|---|---|---|---|
| test | 338 | 2025-01 | 2025-12 | 2025-01-02 | 2025-12-31 | 207 | 131 | 0.6124 | 0.3876 | False |
| train | 569 | 2023-01 | 2024-06 | 2023-01-03 | 2024-06-25 | 482 | 87 | 0.8471 | 0.1529 | False |
| validation | 182 | 2024-07 | 2024-12 | 2024-07-01 | 2024-12-31 | 101 | 81 | 0.5549 | 0.4451 | False |

Mô hình được chọn: xgboost; threshold 0.490000.
12 numeric features: customer_is_known, prior_order_count, recency_months, customer_active_months_before, orders_last_3m, orders_last_6m, prior_monthly_order_trend, year, month, quarter, month_sin, month_cos. Không có ID/categorical encoding.
Median imputation (keep_empty_features), StandardScaler, class weights chỉ fit train.
Logistic C=.1/1/10; RF 200 cây depth/leaf (4,5)/(6,5)/(6,10); XGBoost depth2/3,
learning rate .03, max400, early stop25 trên validation; MLP 64/32, dropout .2,
Adam .001, max250, early stop20. MLP dùng Dataset shuffle seed42, batch32; validation không shuffle.
Đúng bốn ứng viên: Logistic Regression, Random Forest, XGBoost và MLP Neural Network.
Chọn validation macro-F1, ROC-AUC tie-break; threshold .05→.95 bước .01, macro-F1/F1/proximity0.5.
Persist lựa chọn trước khi chấm test. Cùng khách qua nhiều thời điểm là use case sequential arrivals,
không khẳng định đánh giá độc lập trên khách hoàn toàn mới. Không refit sau selection cho classification.

| model | validation_macro_f1 | validation_roc_auc | test_macro_f1 | test_roc_auc | threshold |
|---|---|---|---|---|---|
| logistic | 0.5659 | 0.5266 | 0.6909 | 0.7436 | 0.3300 |
| random_forest | 0.5675 | 0.5289 | 0.6564 | 0.7483 | 0.4400 |
| xgboost | 0.5843 | 0.5527 | 0.6521 | 0.7263 | 0.4900 |
| mlp | 0.5658 | 0.5661 | 0.6936 | 0.7388 | 0.5400 |

Trong project, WIN/LOST được xác định theo quy tắc nghiệp vụ Product + Quantity + Unit của toàn bộ dòng thuộc đơn. Nhãn này không chứng minh ký hợp đồng, doanh thu, thanh toán hoặc trạng thái CRM opportunity Won/Lost.

Tracker là ảnh chụp hồi cứu, thiếu log chứng minh mã khách/ngày tiếp nhận đã được lưu trước kết quả. Thí nghiệm giả định các thông tin này được biết khi tạo đơn; đơn có thể được nhập bổ sung muộn. Không dùng outcome/volume/sản phẩm lịch sử vì thiếu timestamp sẵn có. WIN/LOST lịch sử trong UI chỉ mô tả các đơn trước tháng được chọn theo snapshot, không làm predictor. Probability chưa calibrated; không tự động chấp nhận/từ chối đơn.

Mẫu khoảng một nghìn đơn, ba năm, lặp theo khách và chỉ một holdout 2025 nên hiệu năng/nhóm nhỏ có thể không ổn định. Holdout có prior analyst exposure; đánh giá hồi cứu không thay thế kiểm định prospective trên dữ liệu phát sinh sau phát hành mô hình. Không diễn giải importance là nhân quả. DL không nhất thiết vượt ML. Cần log thời gian và kiểm định prospective trước triển khai.

Target chỉ xét presence của ô nguồn; quality/mapping/conversion không tham gia label.
Metadata tại models/model_schema.json: run ID deterministic, dataset SHA, library versions,
features/order/dtype/nullability, threshold, validation/test metrics, source/artifact SHA.
Registry tập trung tại approval_prediction/registry.py. Mỗi model lưu type, feature schema, preprocessing version/hash, training cutoff, validation metrics, threshold, artifact hash và model version.
Inference kiểm tra schema, runtime versions và bundle hashes. File serialized chỉ tải từ bundle nội bộ tin cậy.
