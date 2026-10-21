# Tái lập, kiểm thử và hướng dẫn phát hành GitHub

## 1. Yêu cầu môi trường

- Runtime tham chiếu: phiên bản Python trong `.python-version` (nhánh Python 3.12) và dependencies được pin trong `requirements.txt`.
- Chạy offline với dữ liệu Excel được doanh nghiệp cho phép sử dụng, đặt trong `data/raw/`. Hệ thống **không tự tải dữ liệu**; không có dữ liệu hợp lệ thì không thể tái lập số liệu và mô hình, dù có mã nguồn.
- Đặt thư mục làm việc tại gốc repository hoặc sử dụng các đường dẫn trong lệnh mẫu; cấu trúc code xác định root từ vị trí file.

Ví dụ PowerShell (Windows), sau khi tạo môi trường `.venv` phù hợp:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -B run_pipeline.py
.\.venv\Scripts\python.exe -B -m approval_prediction.run --clean
.\.venv\Scripts\python.exe -B scripts/write_documentation.py
.\.venv\Scripts\python.exe -B -m pytest tests approval_prediction/test_approval.py approval_prediction/app/test_app.py -q
```

Để kiểm định end-to-end trong môi trường phù hợp:

```powershell
.\.venv\Scripts\python.exe -B verify_project.py
```

Verifier kiểm tra schema/invariants, đối soát nguồn, bảo toàn lượng, huấn luyện/phân loại, các test, tương thích thư viện, hash/schema bundle và hành vi Streamlit. Khi chạy full có bước tạo tài liệu; **không xem file log hoặc PASS cũ là bằng chứng cho code/dữ liệu đã thay đổi**. Log kiểm thử sinh tại máy người chạy, không đưa lên GitHub công khai.

## 2. Cách tái tạo tài liệu

`docs/` là bản tài liệu công khai có kiểm soát; `docs_templates/` là bản nguồn của chính các trang đó. Lệnh `scripts/write_documentation.py` dựng lại các bảng **chỉ gồm số liệu tổng hợp an toàn**, cập nhật chính xác từ artifacts hiện tại và từ chối nếu thiếu placeholder hoặc file đầu vào. Nhờ vậy lần chạy pipeline **không ghi đè** nội dung diễn giải WIN/LOST đã xác nhận, phần giới hạn RFV, forecast và quy tắc bảo mật.

Nếu thay đổi rule hoặc feature trong code, phải soát lại cả `docs_templates/`, generator và kiểm thử; một mô tả kỹ thuật tự động sinh không thay thế xác nhận nghiệp vụ.

## 3. Chính sách phân tách công khai / riêng tư

| Được cân nhắc công khai sau khi rà soát | **Không phát hành công khai** khi chưa có phép |
|---|---|
| Code tổng quát, `README.md`, `docs/`, test không dùng dữ liệu thật | `data/raw/`, `data/processed/`, `outputs/` chứa dữ liệu/model/report |
| File hướng dẫn, schema cột, mô tả phương pháp | Excel danh mục khách/sản phẩm, bảng giá, tên khách, hợp đồng, mã đơn |
| Metric tổng hợp không định danh **đã được phép công bố** | Bảng cases, loss logs, thông tin nội bộ, đường dẫn mạng/tài khoản/secrets |
| Dữ liệu **tổng hợp nhân tạo** do nhóm tạo và kiểm tra riêng | Screenshot bảng điều khiển lộ khách, mã sản phẩm, sản lượng hoặc đơn giá |

Ví dụ `.gitignore` cho repository công khai:

```gitignore
.venv/
.cache/
__pycache__/
.pytest_cache/
.streamlit/secrets.toml
data/raw/
data/processed/
outputs/
*.xlsx
*.xls
*.csv
```

**Cảnh báo:** `.gitignore` chỉ ngăn file *chưa được track*. Nếu thông tin nội bộ từng được commit, phải **kiểm tra toàn bộ git history và xử lý theo quy trình bảo mật**, không chỉ xóa file ở commit mới. Các file mã nguồn/config/test cũng có thể chứa mã đơn thực tế, danh sách dự án, đơn giá hoặc chuỗi khách hàng; **không tự động xem code là đã vô hại**. Cần rà soát toàn repository và được doanh nghiệp phê duyệt trước khi chuyển `Public`.
