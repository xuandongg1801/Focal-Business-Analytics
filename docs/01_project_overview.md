# Mục đích và kiến trúc

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
