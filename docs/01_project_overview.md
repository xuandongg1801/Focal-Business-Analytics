# Tổng quan dự án và phạm vi phân tích

## Mục tiêu

Dự án xây dựng quy trình phân tích dữ liệu đơn hàng từ bảng theo dõi Excel, gồm: (1) làm sạch và kiểm định dữ liệu, (2) phân tích mô tả đơn hàng, khách hàng và sản phẩm, (3) phân khúc khách hàng RFV (Recency–Frequency–Volume), (4) dự báo **sản lượng cáp nền** theo tháng và (5) dự đoán trạng thái **WIN/LOST** của đơn hàng bằng Machine Learning/Deep Learning. Kết quả được trình bày qua ứng dụng Streamlit.

**Quy tắc xác định WIN/LOST đã được doanh nghiệp xác nhận:** đơn hàng được xem là **đã chốt (WIN)** khi **tất cả dòng** của đơn có đủ ba ô nguồn *Sản phẩm, Số lượng, Đơn vị*. Nếu **bất kỳ dòng nào** thiếu ít nhất một ô, đơn thuộc **LOST** theo cách phân loại thống nhất với doanh nghiệp. Doanh nghiệp **không lập cột trạng thái chốt/không chốt riêng** cho từng đơn; nhãn được tái tạo từ dữ liệu gốc theo quy tắc đã xác nhận. Nội dung chi tiết: [08_approval_prediction.md](08_approval_prediction.md).

## Sơ đồ hệ thống

```text
Dữ liệu Excel nội bộ (chỉ lưu cục bộ, không đưa lên GitHub công khai)
  └─ Kiểm tra schema / đối soát với nguồn
     ├─ Header đơn + sổ dòng nguồn (giữ lineage)
     ├─ Phân tích mã sản phẩm và phân bổ sản lượng có căn cứ
     │  └─ Product fact + bảng dòng chưa quy thuộc
     └─ Data marts / kiểm soát chất lượng
        ├─ EDA / ABC / RFV
        ├─ Forecast: phân tách nhu cầu nền + backtest theo thời gian
        └─ WIN/LOST: nhãn theo quy tắc doanh nghiệp
           └─ Đặc trưng lịch sử trước tháng dự đoán
              └─ Logistic / Random Forest / XGBoost / MLP
                 └─ Artifacts có metadata → Streamlit
```

## Khái niệm và ranh giới

| Thành phần | Ý nghĩa | Không được suy diễn |
|---|---|---|
| Số đơn | Số đơn ở grain *order header* | Không phải số dòng sản phẩm |
| Sản lượng KM | Lượng ghi nhận, chỉ quy đổi M sang KM khi hợp lệ | Không chứng minh đã giao/đã nghiệm thu |
| ABC | Tỷ trọng KM đã quy thuộc sản phẩm | Không bao phủ phần chưa ánh xạ |
| RFV | Mức độ gần đây, tần suất và **khối lượng KM** | V không phải Monetary Value; không kết luận churn |
| WIN/LOST | Trạng thái chốt theo **quy tắc đã xác nhận của doanh nghiệp** | Không xác thực thanh toán, ký hợp đồng hay giao hàng |
| Forecast | Baseline KM đã lọc dự án và cực trị theo quy tắc | Không đại diện tổng nhu cầu hoặc doanh thu |
| Giá tham chiếu | Thông tin hỗ trợ đối soát nội bộ | Không phải doanh thu, biên lợi nhuận hay dòng tiền |

## Tài liệu

Đọc theo thứ tự [Data dictionary](02_data_dictionary.md) → [Pipeline](03_data_pipeline.md) → [Quality](04_data_quality.md) → [EDA](05_eda.md) → [RFV](06_rfv_analysis.md) → [Forecast](07_forecasting.md) → [WIN/LOST](08_approval_prediction.md) → [Ứng dụng](09_streamlit_app.md) → [Tái lập](10_reproducibility.md).
