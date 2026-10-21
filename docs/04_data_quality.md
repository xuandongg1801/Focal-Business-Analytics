# Chất lượng dữ liệu

| Chỉ tiêu | Giá trị |
|---|---|
| orders | 1168.0000 |
| items | 1720.0000 |
| canonical_product_rows | 1284.0000 |
| exact_product_rows | 1123.0000 |
| generic_product_rows | 161.0000 |
| ambiguous_product_rows | 0.0000 |
| unresolved_rows | 436.0000 |
| unresolved_multi_product_rows | 7.0000 |
| unmapped_product_rows | 429.0000 |
| month_conflict_orders | 46.0000 |
| duplicate_order_ids | 0.0000 |
| duplicate_item_ids | 0.0000 |
| duplicate_item_candidate_rows | 2.0000 |
| missing_quantity | 373.0000 |
| missing_customer_code | 192.0000 |
| outlier_rows | 5.0000 |
| sales_km_raw | 1079381.8730 |
| sales_km_non_outlier | 819821.8730 |

Nguồn: [pipeline_validation.json](../outputs/tables/pipeline_validation.json).
Conservation: [quantity_conservation.csv](../outputs/tables/quantity_conservation.csv), tính riêng từng đơn vị.
Mã chưa ánh xạ có thể là hàng không phải cáp, ghi chú hoặc mã chưa có reference; không tự gọi là dữ liệu sai.
Hai dòng FE12 8 KM cùng đơn CA-094/2503/GIGA-NET ở các dòng nguồn khác nhau được giữ lại để xác minh.
Không tự xóa cực trị, hợp nhất mã khách hoặc sửa lượng. Không có log hiệu lực master hay trạng thái giao hàng để chứng minh thêm.
