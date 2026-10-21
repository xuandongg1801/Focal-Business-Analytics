# Dự báo KM nền

| Thuộc tính | Giá trị |
|---|---|
| history_start | 2023-01 |
| history_end | 2025-12 |
| validation_start | 2024-01 |
| validation_end | 2025-06 |
| validation_folds | 3 |
| test_start | 2025-07 |
| test_end | 2025-12 |
| selected_model | EWMA hiệu chỉnh alpha=0.5 |
| validation_wape_pct | 139.03893762408472 |
| validation_mae_km | 3130.7531216682987 |
| test_wape_pct | 69.14320407950989 |
| test_mae_km | 1196.1595685811335 |
| forecast_start | 2026-01 |
| forecast_end | 2026-06 |

Naive, Historical Mean, Seasonal Naive (đủ lịch sử) và adjusted EWMA dùng cùng rolling folds.
Adjusted EWMA = level × (1−alpha/2), là ứng viên heuristic, không khẳng định bias correction tối ưu.
Outlier threshold fit riêng train mỗi fold; khóa để lọc validation/holdout. Cờ mart toàn lịch sử không vào evaluation.
Chọn pooled validation WAPE, tie-break MAE rồi tên; nếu denominator gần 0, dùng MAE và WAPE null.
Test không dùng selection hoặc tune; refit lựa chọn trên toàn history để tạo 6 tháng sau history_end.
Calendar tính trước khi lọc; tháng chỉ có dự án vẫn tồn tại. Calendar trống giả định tracker đầy đủ,
còn quantity thiếu trên dòng có thật vẫn chưa biết. Dự báo chỉ áp dụng nền đã lọc, không phải tổng nhu cầu.
Holdout có external exposure và dự án không có timestamp xác nhận, nên cần prospective evidence.
Không có prediction interval được hiệu chuẩn. Đây là frozen forecast snapshot, khác backtest holdout.
Khi horizon đã qua ngày xem, snapshot không phải dự báo tương lai live và chưa có actual mới để chấm.
prospective.py giữ thời điểm phát hành UTC thật, threshold và danh sách dự án; chỉ chấm tháng hoàn tất
sau issuance khi người dùng xác nhận độ đầy đủ tracker, không lùi ngày phát hành.
