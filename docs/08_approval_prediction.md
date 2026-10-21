# Dự đoán WIN/LOST theo quy tắc chốt đơn đã xác nhận

## 1. Cơ sở nghiệp vụ và nguồn nhãn

**Doanh nghiệp đã xác nhận quy tắc:** một đơn hàng có đầy đủ thông tin ở **ba trường Sản phẩm, Số lượng và Đơn vị cho toàn bộ các dòng** là đơn **đã được chốt (WIN)**. Nếu **ít nhất một dòng của đơn** thiếu một trong ba trường, đơn được phân loại **LOST** theo quy ước quản lý đơn của doanh nghiệp.

Dữ liệu nguồn **không có cột riêng** ghi “chốt” hoặc “không chốt” cho từng đơn. Pipeline tạo `chot_don` bằng cách áp dụng **chính quy tắc được doanh nghiệp xác nhận** lên các ô nguồn; nhãn không phải kết quả gán thủ công từng đơn và cũng không phải nhãn suy diễn tùy ý của nhóm phân tích.

| Điều kiện trên **mỗi dòng Excel gốc** | Nhãn dòng |
|---|---|
| Sản phẩm có dữ liệu **và** Số lượng có dữ liệu **và** Đơn vị có dữ liệu | Đủ thông tin |
| Thiếu ít nhất một trong ba ô | Không đủ thông tin |

**Gộp lên đơn:** `WIN (chot_don=1)` khi có ít nhất một dòng nguồn **và tất cả dòng đều đủ thông tin**; trường hợp còn lại là `LOST (chot_don=0)`. Phạm vi mô hình là **đơn bán**; không gom các loại chứng từ nội bộ làm cùng một bài toán.

**Định nghĩa “có dữ liệu” ở code:** giá trị ô gốc khác null và `str(value).strip()` không rỗng. Nhãn được tính trực tiếp từ Excel bằng `approval_prediction/target.py` **trước xử lý số lượng, parse sản phẩm, đổi đơn vị hoặc nối master**. Do đó, **0 hoặc một chuỗi nhập sai định dạng nhưng không rỗng vẫn được xem là có dữ liệu cho mục đích đặt nhãn**. Kiểm soát hợp lệ/giá trị không âm/đơn vị được thực hiện **độc lập** trong data quality; không nên viết rằng ba trường đã được kiểm định toàn diện chỉ từ điều kiện “có dữ liệu”.

**Ranh giới nghiệp vụ:** WIN ở đây là **đã chốt theo quy tắc quản lý tracker mà doanh nghiệp xác nhận**. Nó **không tự động chứng minh** hàng đã giao, hợp đồng đã ký, chứng từ đã thanh toán hay CRM có trạng thái Won; LOST cũng không tự động tương đương khách từ chối về mặt thương mại. Không công khai danh tính người xác nhận hoặc bằng chứng làm việc nội bộ.

## 2. Mục tiêu dự đoán và chống rò rỉ nhãn

Mục tiêu mô hình là ước tính xác suất một **đơn bán ở tháng mục tiêu** sẽ có trạng thái WIN **dựa trên thông tin được giả định có trước khi hoàn tất ba ô tạo nhãn**. Tránh rò rỉ nhãn bằng cách không đưa các ô Sản phẩm/Số lượng/Đơn vị, cờ presence/completeness, `chot_don` hoặc outcome lịch sử chưa chứng minh thời điểm sẵn có vào predictors.

12 đặc trưng numeric đang dùng:

| Nhóm | Features | Cách dùng |
|---|---|---|
| Nhận diện mã khách | `customer_is_known` | Chỉ cho biết mã khách có trong tracker, không dùng chính giá trị mã khách |
| Lịch sử đơn **trước tháng t** | `prior_order_count`, `recency_months`, `customer_active_months_before`, `orders_last_3m`, `orders_last_6m`, `prior_monthly_order_trend` | Đếm/đo lịch sử tiếp nhận, **không đọc kết quả chốt của đơn lịch sử** |
| Lịch | `year`, `month`, `quarter`, `month_sin`, `month_cos` | Mùa vụ và xu hướng thời gian |

Với đơn tháng `t`, feature lịch sử chỉ được sử dụng đơn có tháng **nhỏ hơn t**. Không đặt thứ tự tùy ý cho các đơn cùng tháng. Khách không có mã không được gộp vào một “khách ảo”. `recency_months` có thể thiếu khi chưa có lịch sử; dữ liệu thiếu và scale được xử lý bằng tham số fit trên train. Master snapshot thiếu ngày hiệu lực nên thông tin master chỉ dùng cho phân tích hồi cứu, không dùng để tạo feature có nguy cơ biết tương lai.

**Giới hạn quan trọng:** tracker là ảnh chụp hồi cứu; chưa có log độc lập xác nhận thời điểm mã khách, ngày tiếp nhận và các dữ liệu lịch sử đã sẵn có tại thời điểm inference. Vì vậy kiểm định hiện tại đo hiệu năng **hồi cứu theo giả định thời điểm**, chưa chứng minh triển khai thời gian thực là không leakage.

## 3. Dữ liệu, phân chia thời gian và dịch chuyển phân bố

Tổng số đơn bán tham gia phân loại: **1089**, gồm **790 WIN** và **299 LOST**. Chia thời gian cố định, không trộn ngẫu nhiên các đơn giữa các kỳ:

| Tập | Khoảng tháng | Số đơn | WIN | LOST | Tỷ lệ WIN |
| --- | --- | --- | --- | --- | --- |
| train | 2023-01 – 2024-06 | 569 | 482 | 87 | 84.71% |
| validation | 2024-07 – 2024-12 | 182 | 101 | 81 | 55.49% |
| test | 2025-01 – 2025-12 | 338 | 207 | 131 | 61.24% |

Tỷ lệ WIN **84.71% ở train → 55.49% ở validation → 61.24% ở test** thay đổi đáng kể theo kỳ. Đây là **temporal distribution shift** của nhãn; có thể do quy trình ghi nhận, cơ cấu đơn và mức độ đầy đủ của tracker thay đổi. Chưa đủ bằng chứng để chỉ ra nguyên nhân riêng lẻ. Vì vậy độ chính xác trên một kỳ không được suy rộng thành hiệu năng ổn định ở kỳ khác. Các khách xuất hiện lặp theo thời gian phản ánh kịch bản tiếp nhận tuần tự, **không phải kiểm định trên khách hoàn toàn mới**.

## 4. Mô hình và nguyên tắc chọn

So sánh đúng bốn họ mô hình: **Logistic Regression, Random Forest, XGBoost và MLP Neural Network**. Logistic/Random Forest dùng các cấu hình thử nghiệm có giới hạn; XGBoost sử dụng early stopping; MLP có dropout và early stopping. Feature engineering, imputing/scaling và class weighting được thực hiện với quy tắc fit trên **train**; validation dùng để chọn siêu tham số, threshold và model; **test được giữ để đánh giá sau khi khóa lựa chọn**.

- Threshold tìm trong dải `0.05`–`0.95` bước `0.01`, ưu tiên **validation Macro-F1**, tie-break theo **F1 lớp WIN** và độ gần `0.5`.
- Model được chọn bằng **validation Macro-F1**, khi bằng nhau xét **validation ROC-AUC** theo logic hiện tại.
- Không chọn lại model hoặc threshold chỉ vì model khác có **test score** cao hơn. Không refit bộ phân loại sau khi đã chốt lựa chọn trong snapshot này.

| Mô hình | Val Macro-F1 | Val ROC-AUC | Test Macro-F1 | Test ROC-AUC | Threshold |
| --- | --- | --- | --- | --- | --- |
| Logistic Regression | 0.5659 | 0.5266 | 0.6909 | 0.7436 | 0.33 |
| Random Forest | 0.5675 | 0.5289 | 0.6564 | 0.7483 | 0.44 |
| **XGBoost** | 0.5843 | 0.5527 | 0.6521 | 0.7263 | 0.49 |
| MLP Neural Network | 0.5658 | 0.5661 | 0.6936 | 0.7388 | 0.54 |

**Kết luận nhất quán:** `XGBoost` có **validation Macro-F1 cao nhất** (**0.5843**) với threshold **0.49**, nên được chọn mặc định theo quy tắc đã công bố. Nhưng trên holdout test, mô hình có Macro-F1 lớn nhất là **MLP Neural Network** (**0.6936**), không phải mặc nhiên mô hình được chọn. Không dùng test để đổi lựa chọn hồi cứu.

Các ROC-AUC validation chỉ khoảng **0,53–0,57** trong snapshot, cho thấy khả năng phân biệt WIN/LOST **còn hạn chế**. Test thay đổi theo thời gian và ngưỡng; vì thế không được quảng bá mô hình là dự đoán chính xác cao hoặc đã sẵn sàng tự động chốt đơn.

## 5. Cách đọc metric và sai sót

- **Macro-F1** = trung bình F1 của WIN và LOST, tránh chỉ nhìn lớp chiếm đa số.
- **ROC-AUC** đánh giá khả năng xếp hạng WIN cao hơn LOST qua các ngưỡng; không tự nói lên xác suất đã được hiệu chuẩn.
- **Precision/Recall lớp WIN** đánh giá khi cần dự đoán WIN. **Specificity lớp LOST** rất quan trọng nếu muốn hạn chế phân loại nhầm LOST thành WIN.
- False positive: dự đoán WIN khi nhãn theo quy tắc là LOST; false negative: dự đoán LOST khi nhãn theo quy tắc là WIN. Không diễn giải thành mất doanh thu hoặc mất đơn thực tế.

Trong kết quả test của mô hình được chọn, ma trận nhầm lẫn ở mức tổng hợp: **TN=58, FP=73, FN=30, TP=177** (quy ước lớp dương `WIN=1`). Các số đếm không tiết lộ khách hàng, mã đơn hoặc dữ liệu giao dịch cá nhân.

## 6. Những giới hạn còn lại và sử dụng có trách nhiệm

1. Quy tắc WIN/LOST được **doanh nghiệp xác nhận** nhưng chỉ dựa trên **độ có mặt của ba ô nguồn**, không chứng minh tính đúng của thông tin và các nghiệp vụ hậu chốt.
2. Dữ liệu ba năm, một holdout theo thời gian, phân bố nhãn biến đổi và khách lặp có thể làm kết quả thiếu ổn định.
3. Xác suất đầu ra **chưa được hiệu chuẩn (uncalibrated)**. Feature importance không chứng minh quan hệ nhân quả hoặc quyết định số phận từng đơn.
4. Phải kiểm định **prospective**, lưu timestamp feature tại lúc dự báo và so sánh hiệu năng theo thời gian/nhóm trước khi vận hành thật.
5. Ứng dụng chỉ **hỗ trợ phân tích**, không tự động duyệt, từ chối hay thay thế quyết định chốt đơn của doanh nghiệp.

## 7. Truy vết thực thi

Nhãn: `approval_prediction/target.py`; thiết lập feature và chia tập: `approval_prediction/config.py` / `approval_prediction/data.py`; huấn luyện & chọn model: `approval_prediction/modeling.py` / `approval_prediction/run.py`; đánh giá: `approval_prediction/evaluation.py`; kiểm tra schema/hash: `approval_prediction/registry.py` / `approval_prediction/schema.py`.
