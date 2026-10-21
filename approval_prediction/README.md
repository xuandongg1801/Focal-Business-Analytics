# Dự đoán WIN / LOST của đơn hàng

Một đơn WIN khi cả ba ô Product + Quantity + Unit của mọi dòng nguồn đều không null và không blank sau strip whitespace; còn lại LOST. Dùng ô Excel gốc, không dùng validity/mapping/conversion để tạo nhãn. Rule tập trung tại target.py, không dùng master match để tạo nhãn. Một dòng modeling là một đơn. Ba trường tạo nhãn, missingness và derived completeness không được dùng làm predictors.

Lịch sử tiếp nhận trước tháng dự báo và lịch tháng tạo 12 features chung cho Logistic Regression, Random Forest, XGBoost, MLP Neural Network. Model/threshold chọn bằng validation; test đánh giá sau khi khóa. Registry tại registry.py, metadata/hash trong bundle.

Prediction chọn khách, tháng, năm và model; một lần bấm Phân tích giao dịch tự hiển thị cả ba phần. Card model đã chọn lấy trực tiếp dòng tương ứng của bảng so sánh bốn model bên dưới lịch sử khách hàng.

Lệnh chạy và dependency tại [README](../README.md). Rule, leakage và metrics tại [tài liệu mô hình](../docs/08_approval_prediction.md). Artifacts tại `outputs/approval_prediction/`.
