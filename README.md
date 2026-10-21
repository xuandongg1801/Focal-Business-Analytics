# Focal Analytics: Phân tích dữ liệu kinh doanh và Dự đoán WIN/LOST đơn hàng

Dự án xây dựng quy trình **phân tích dữ liệu đơn hàng**, đánh giá khách hàng và sản phẩm, đồng thời ứng dụng **Machine Learning / Deep Learning** để dự đoán khả năng một đơn hàng thuộc nhóm **WIN** hoặc **LOST** theo tiêu chí nghiệp vụ được doanh nghiệp xác nhận.

Công nghệ chính: **Python · Pandas · Scikit-learn · XGBoost · TensorFlow/Keras · Streamlit · Plotly**.


## 1. Giới thiệu

Nguồn dữ liệu của dự án là bảng theo dõi đơn hàng **2023–2025**, danh mục khách hàng, danh mục sản phẩm và bảng giá tham chiếu. Pipeline được thiết kế để chuẩn hóa dữ liệu, đối soát các dòng đơn hàng và xây dựng các bảng phục vụ phân tích.

Dự án tập trung vào ba nhóm nhiệm vụ:

- **Data Engineering & Data Quality:** làm sạch Excel, chuẩn hóa mã sản phẩm, kiểm tra thiếu dữ liệu và bảo toàn số lượng khi xử lý đơn nhiều dòng.
- **Business Analytics:** thực hiện EDA, phân tích biến động đơn hàng/sản lượng, phân khúc khách hàng theo **RFV** và phân tích danh mục sản phẩm theo **ABC/Pareto**.
- **Predictive Analytics:** xây dựng và so sánh các mô hình phân loại **WIN/LOST**, kết hợp dashboard **Streamlit** để khám phá dữ liệu và mô phỏng dự đoán.

## 2. Mục tiêu dự án

1. Xây dựng pipeline có thể tái chạy từ dữ liệu Excel gốc đến các bảng phân tích.
2. Chuẩn hóa và đối soát dữ liệu ở cấp **đơn hàng**, **dòng nguồn** và **dòng sản phẩm đã quy thuộc**.
3. Phân tích hoạt động kinh doanh theo thời gian, nhóm sản phẩm và khách hàng.
4. Phân nhóm khách hàng bằng **Recency – Frequency – Volume (RFV)**; trong đó *Volume* là sản lượng, **không phải doanh thu**.
5. Xây dựng nhãn WIN/LOST từ tiêu chí nghiệp vụ và huấn luyện nhiều thuật toán phân loại để so sánh.
6. Trực quan hóa kết quả bằng ứng dụng Streamlit và cung cấp tài liệu/kiểm thử cho khả năng tái lập.

## 3. Dataset

Dữ liệu đầu vào gồm **6 file Excel** đặt trong `data/raw/` trên máy có quyền truy cập dữ liệu.

| File | Vai trò |
|---|---|
| `bang_theo_doi_don_hang_nam_2023.xlsx` | Theo dõi đơn hàng năm 2023 |
| `bang_theo_doi_don_hang_nam_2024.xlsx` | Theo dõi đơn hàng năm 2024 |
| `bang_theo_doi_don_hang_nam_2025.xlsx` | Theo dõi đơn hàng năm 2025 |
| `danh_muc_khach_hang.xlsx` | Danh mục và mã khách hàng |
| `danh_muc_san_pham.xlsx` | Danh mục sản phẩm và quy cách |
| `bang_gia_ban_cap_cho_khach_hang.xlsx` | Bảng giá **tham chiếu**, không đồng nghĩa với doanh thu thực tế |

**Quy mô dữ liệu ở lần chạy được kiểm tra trong snapshot 2023–2025:**

| Chỉ tiêu | Số lượng |
|---|---:|
| Tổng số đơn hàng | 1.168 |
| Số dòng hàng trong dữ liệu nguồn | 1.720 |
| Số đơn bán đưa vào bài toán WIN/LOST | 1.089 |
| Đơn WIN theo tiêu chí dữ liệu | 790 |
| Đơn LOST theo tiêu chí dữ liệu | 299 |

Các con số trên là **snapshot**, có thể thay đổi khi dữ liệu nguồn hoặc quy tắc xử lý được cập nhật. Project **không tự tải dữ liệu nội bộ** từ Internet.

## 4. Cấu trúc dự án

```text
Focal-Analytics/
├── approval_prediction/            # Xây nhãn, features, huấn luyện, đánh giá ML/DL
│   ├── app/                        # Ứng dụng Streamlit và các trang dashboard
│   ├── config.py                   # Cấu hình mô hình
│   ├── modeling.py                 # Training / model comparison
│   ├── target.py                   # Quy tắc xác định WIN/LOST
│   └── run.py                      # Entry point huấn luyện classification
├── data/
│   ├── raw/                        # Excel nội bộ (KHÔNG commit)
│   └── processed/                  # Bảng dữ liệu đã làm sạch (KHÔNG commit)
├── docs/                           # Tài liệu phương pháp và kiến trúc
├── outputs/                        # Models, tables, figures và logs sinh khi chạy
├── scripts/                        # Data cleaning, xây data mart, EDA, kiểm tra
├── tests/                          # Unit / regression / pipeline tests
├── .python-version                 # Phiên bản Python đã kiểm chứng
├── .gitignore                      # Loại dữ liệu nội bộ và file sinh ra khỏi Git
├── requirements.txt                # Các thư viện Python
├── run_pipeline.py                 # Chạy pipeline dữ liệu
├── verify_project.py               # Kiểm định tổng thể (cần dữ liệu/fixtures cục bộ)
└── README.md
```

Luồng tổng quát:

```text
Excel gốc
   ↓
Data validation & cleaning
   ↓
Fact / Dimension tables → Analytical marts
   ↓
EDA · RFV · ABC
   ↓
WIN/LOST target → Feature engineering → ML/DL evaluation
   ↓
Streamlit Dashboard
```

## 5. Cài đặt môi trường

Khuyến nghị **Python 3.12** (snapshot kiểm chứng sử dụng Python `3.12.14`). Chạy lệnh bằng **PowerShell** trong thư mục gốc project:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m pip check
```

Trên macOS/Linux, thay `py -3.12` bằng trình Python 3.12 tương ứng và sử dụng `.venv/bin/python` thay cho `.venv\Scripts\python.exe`.

Các bước chạy dữ liệu cần 6 tệp Excel có cấu trúc phù hợp trong `data/raw/`. Bạn phải có quyền hợp lệ để sử dụng chúng.

## 6. Chạy Data Pipeline

Tại thư mục gốc repository:

```powershell
.\.venv\Scripts\python.exe run_pipeline.py
```

Pipeline đọc dữ liệu nội bộ, làm sạch master data và đơn hàng, xây dựng các bảng fact/dimension, phân tích EDA và thực hiện kiểm tra dữ liệu. Kết quả sinh tại `data/processed/` và `outputs/`.

Một số bảng đầu ra quan trọng:

| Bảng | Ý nghĩa |
|---|---|
| `fact_order_header.csv` | Một dòng trên mỗi đơn hàng |
| `fact_order_items.csv` | Các dòng vật lý của đơn theo nguồn |
| `fact_product_items.csv` | Các sản phẩm đã nhận diện và phân bổ được |
| `mart_order_items.csv` | Dữ liệu dòng nguồn cho phân tích |
| `mart_product_items.csv` | Dữ liệu phân tích ở cấp sản phẩm |
| `unresolved_items.csv` | Những dòng cần tiếp tục kiểm tra hoặc đối soát |

> Lưu ý: ở **bản ZIP được kiểm tra**, pipeline vẫn còn thành phần Forecast. Nếu mục tiêu là công bố phiên bản *không Forecast*, cần loại bỏ thành phần này khỏi mã nguồn, tài liệu và kiểm thử trước khi phát hành repository.

## 7. Bài toán dự đoán WIN/LOST

### 7.1. Cách xác định nhãn

Theo xác nhận nghiệp vụ mà dự án sử dụng, **đơn đầy đủ thông tin được xác định là WIN; các đơn còn lại là LOST**. Dữ liệu nguồn **không ghi sẵn nhãn WIN/LOST riêng cho từng đơn**, vì vậy hệ thống áp dụng tiêu chí doanh nghiệp xác nhận để gán nhãn tự động:

- **WIN (`1`):** mọi dòng nguồn thuộc đơn đều có đủ **Sản phẩm**, **Số lượng** và **Đơn vị**.
- **LOST (`0`):** có ít nhất một dòng thiếu một trong ba trường trên.

Điều kiện “có thông tin” được xét trên ô Excel gốc (không null và không rỗng sau khi bỏ khoảng trắng). Quy tắc được thực thi tập trung ở `approval_prediction/target.py`.

Nhãn này phản ánh **kết quả theo tiêu chí nghiệp vụ doanh nghiệp đã xác nhận đối với bộ dữ liệu**.

### 7.2. Mô hình sử dụng

Dự án huấn luyện và so sánh bốn mô hình:

| Mô hình | Nhóm |
|---|---|
| Logistic Regression | Machine Learning |
| Random Forest | Machine Learning |
| XGBoost | Machine Learning |
| MLP Neural Network | Deep Learning |

Các biến dự đoán tập trung vào **lịch sử tiếp nhận đơn trước tháng cần dự đoán**, trạng thái đã biết của khách hàng và đặc trưng lịch. Các cột dùng để tạo nhãn (sản phẩm, số lượng, đơn vị, mức độ đầy đủ) **không được đưa trực tiếp vào features**, nhằm tránh target leakage.

Phân chia dữ liệu theo thời gian: **train (01/2023–06/2024), validation (07/2024–12/2024), test (01/2025–12/2025)**. Việc chọn mô hình và ngưỡng phân loại dựa trên tập validation; tập test dành cho đánh giá sau lựa chọn.

### 7.3. Huấn luyện mô hình

Sau khi chạy pipeline dữ liệu:

```powershell
.\.venv\Scripts\python.exe -m approval_prediction.run --clean
```

Mô hình, metadata, các bảng đánh giá và biểu đồ được tạo trong `outputs/approval_prediction/` trên máy cục bộ. **Các artifact đã huấn luyện không được lưu trong repository công khai** theo cấu hình `.gitignore` đi kèm.

## 8. Chạy ứng dụng Streamlit

```powershell
.\.venv\Scripts\python.exe -m streamlit run approval_prediction/app/app.py
```

Các khu vực chính:

| Trang | Chức năng |
|---|---|
| **Overview** | KPI đơn hàng, sản lượng, cơ cấu khách hàng/sản phẩm |
| **EDA** | Khám phá dữ liệu theo thời gian, khách hàng, sản phẩm, tình trạng thiếu dữ liệu |
| **Prediction** | Mô phỏng xác suất WIN, so sánh các mô hình, xem đánh giá và giải thích |

Để sử dụng dashboard đầy đủ, cần **chạy pipeline và huấn luyện mô hình tại máy được cấp quyền dữ liệu trước**. Chỉ clone repository sẽ chưa có dữ liệu/model để hiển thị kết quả thật.

## 9. Business Analytics

### Exploratory Data Analysis (EDA)

- Thống kê số đơn, số dòng hàng và biến động theo tháng/năm.
- Phân tích sản lượng theo thời gian, loại đơn và danh mục sản phẩm.
- Theo dõi dữ liệu thiếu, mã sản phẩm không xác định và các trường hợp cần đối soát.

### RFV – Phân khúc khách hàng

- **Recency:** mức độ gần đây của lần phát sinh đơn.
- **Frequency:** tần suất đơn hàng.
- **Volume:** sản lượng ghi nhận (không phải Monetary Value/doanh thu).

### ABC / Pareto

- Phân tích mức độ tập trung sản lượng theo nhóm sản phẩm hoặc mã sản phẩm đủ điều kiện tham chiếu.
- Không tự suy đoán SKU chính xác đối với các mã mới chỉ nhận diện được ở cấp quy cách chung.

## 10. Kiểm thử và tài liệu

Kiểm thử (trên môi trường có dữ liệu và fixtures phù hợp):

```powershell
.\.venv\Scripts\python.exe -m pytest tests approval_prediction/test_approval.py approval_prediction/app/test_app.py -p no:cacheprovider
```

Kiểm định end-to-end (chạy lại dữ liệu, mô hình và kiểm thử; tốn tài nguyên hơn):

```powershell
.\.venv\Scripts\python.exe verify_project.py
```

Tài liệu trong repository:

- [Tổng quan dự án](docs/01_project_overview.md)
- [Từ điển dữ liệu](docs/02_data_dictionary.md)
- [Data Pipeline](docs/03_data_pipeline.md)
- [Data Quality](docs/04_data_quality.md)
- [EDA](docs/05_eda.md)
- [RFV](docs/06_rfv_analysis.md)
- [Classification – WIN/LOST](docs/08_approval_prediction.md)
- [Streamlit App](docs/09_streamlit_app.md)
- [Reproducibility](docs/10_reproducibility.md)