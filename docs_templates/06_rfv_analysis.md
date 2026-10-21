# Phân nhóm khách hàng RFV (Recency – Frequency – Volume)

## 1. Định nghĩa và tập nghiên cứu

RFV ở đây dùng **V = Volume (KM)**, không phải Monetary Value (doanh thu). Phân nhóm phục vụ mô tả hành vi **ghi nhận đơn có lượng KM**, không dự đoán churn hay xác nhận tình trạng hợp tác thực tế.

- **Mốc quan sát:** {{RFV_SNAPSHOT}} (snapshot cuối kỳ dữ liệu trong project).
- **Đơn đủ điều kiện:** đơn bán, có lượng quy đổi KM quan sát được, loại dòng bị gắn cờ cực trị theo quy tắc đã công bố.
- **Định danh khách hợp lệ:** chỉ sử dụng mã khách hàng có thể đối chiếu với danh mục chính thức. Không đưa nhóm khách suy diễn từ hậu tố mã đơn vào RFV.
- **Grain:** một khách hàng hợp lệ, một vector R/F/V tại thời điểm snapshot. Các dòng không đủ điều kiện không tham gia phép tính R/F/V.

## 2. Công thức tính

| Chỉ số | Công thức | Diễn giải |
|---|---|---|
| R (Recency) | Số tháng từ **lần ghi nhận KM đủ điều kiện gần nhất** tới snapshot | Càng nhỏ càng gần đây |
| F (Frequency) | Số **đơn khác nhau** có KM đủ điều kiện của khách trong kỳ | Càng cao càng có nhiều lần ghi nhận |
| V (Volume) | Tổng KM đủ điều kiện của khách | Càng lớn càng nhiều lượng ghi nhận, **không phải tiền** |

Mỗi chỉ tiêu được xếp hạng thực nghiệm và chuyển thành điểm 1–4 theo `ceil(percentile_rank × 4)`. `R` được xếp theo chiều ngược với giá trị gốc để khách gần đây nhận điểm cao; `F` và `V` xếp thuận. Trường hợp đồng hạng dùng *average rank* nên không cố chia bằng mã khách, có thể thiếu điểm ở một số lớp.

Nhãn phân khúc được áp dụng theo thứ tự ưu tiên trong `scripts/segmentation.py`:

1. `R_score = 1` → **Ít giao dịch gần đây**.
2. `R_score, F_score, V_score >= 3` → **Gần đây, thường xuyên, lượng cao**.
3. `F_score >= 3` → **Tần suất cao**.
4. Các trường hợp khác → **Nhóm còn lại**.

## 3. Độ phủ mẫu và thiên lệch chọn mẫu

| Độ phủ | Kết quả trong snapshot |
|---|---:|
| Mã khách trong danh mục chính thức | {{REGISTERED_CUSTOMERS}} |
| Khách có mã chính thức và đủ điều kiện có trong RFV | {{RFV_CUSTOMERS}} |
| Tỷ lệ so với danh mục | {{RFV_COVERAGE}} |
| Nhóm khách suy diễn (thống kê EDA, **không phải khách RFV**) | {{INFERRED_GROUPS}} |
| Tỷ trọng KM của các nhóm suy diễn trong tập EDA không cực trị | {{INFERRED_KM_SHARE}} |

**Cần phân biệt hai mẫu số:**

- **{{RFV_COVERAGE}}** = {{RFV_CUSTOMERS}} / {{REGISTERED_CUSTOMERS}} là **tỷ lệ phủ khách có mã chính thức trong phân tích**, không phải tỷ lệ đơn thất bại và không chứng minh tất cả khách còn lại đã ngừng mua.
- **{{INFERRED_KM_SHARE}}** là **tỷ trọng sản lượng KM** được quy về các nhóm suy diễn khi thiếu mã khách trong tập phân tích EDA (không cực trị). Đây **không phải tỷ lệ khách hàng bị loại**. Các nhóm suy diễn không có định danh đủ tin cậy để được xem là những khách hàng độc lập.

Sự thiếu hụt mã khách làm tập RFV thu hẹp và có nguy cơ **selection bias**: hành vi của khách có mã đầy đủ có thể khác nhóm chưa có mã. Vì vậy không thể ngoại suy tỷ trọng từng phân khúc RFV ra toàn bộ danh mục hoặc toàn bộ sản lượng doanh nghiệp.

## 4. Kết quả phân khúc (chỉ số lượng, không công bố KM/giá trị)

{{RFV_SEGMENT_TABLE}}

Các ngưỡng “cao”, “gần đây” mang tính tương đối trong snapshot và quy tắc phân lớp. Phân khúc là **heuristic**, không phải ground truth về rời bỏ khách, khả năng đặt hàng trong tương lai hay lợi nhuận. Khi mở rộng dữ liệu cần cải thiện mã khách, chuẩn hóa thời gian và kiểm định độ ổn định theo kỳ.
