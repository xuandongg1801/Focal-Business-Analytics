# Tái lập và kiểm định

Python 3.12; packages pin trong requirements.txt. Seed 42, single-thread estimator,
TensorFlow deterministic ops. Models được huấn luyện cùng runtime ghi trong manifest.
Không suppress incompatible-version warning. TensorFlow chạy CPU trên Windows;
thông báo GPU/platform hoặc deprecation nội bộ dependency không phải cảnh báo tương thích artifact.

verify_project.py compile recursive mọi source Python ngoài .venv/.cache/third-party;
check environment pins, paths, narrative and document links; pip check; full ETL; train;
full pytest data/ML/app với FutureWarning-as-error; pipeline lần hai so SHA; train độc lập lần hai so tables/figures/docs,
joblib artifacts và từng tensor trọng số MLP (không so timestamp trong archive Keras).
Cuối cùng kiểm tra schema/bundle và khởi động Streamlit qua health endpoint.
Failure ghi status FAIL, không giữ trạng thái thành công từ lần thực thi khác.

Kết quả máy đọc: [verification.json](../outputs/logs/verification.json),
[model verification](../outputs/approval_prediction/verification.json).
Fixture nguồn bảo vệ keys/raw text/quantity/unit/flags khi source SHA khớp;
semantic sản phẩm được bảo vệ bằng regression độc lập. Cột mã toàn null có kiểu nullable string theo data_contract.py.
Verifier sinh docs trước lần test cuối, lưu fingerprint source, versions và thời điểm hoàn tất; dọn runtime junk rồi kiểm tra hygiene.
Kiểm định trực tiếp repository local; không có bước đóng gói. Runtime cache và log không giữ sau khi PASS. Logs chẩn đoán được giữ nếu verifier thất bại, xóa sau khi đạt.
Pandas 2.2.3 có thể được kiểm tra bằng --pandas22-path trỏ tới package directory riêng; không đổi runtime chính.

Raw cần 3 tracker 2023–2025 trong snapshot và 3 danh mục/bảng giá tại data/raw/.
Thêm năm tracker được khám phá từ tên; thiếu sheet/cột/key phải fail rõ. Giá ngoài hiệu lực giữ null.
File nguồn riêng tư cần được cung cấp hợp lệ tại đúng vị trí; pipeline không tự fetch.
