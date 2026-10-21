# Phân nhóm RFV

Snapshot: 2025-12; một dòng mỗi mã khách khớp danh mục.
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

| phan_khuc | customers | km |
|---|---|---|
| Gần đây, thường xuyên, lượng cao | 20 | 82718.5540 |
| Nhóm còn lại | 27 | 1253.6000 |
| Tần suất cao | 8 | 1669.1700 |
| Ít giao dịch gần đây | 16 | 14776.5190 |
