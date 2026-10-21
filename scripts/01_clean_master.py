"""
01_clean_master.py
-------------------
Làm sạch 3 bảng "master data" (ít biến động):
  - danh_muc_khach_hang.xlsx      -> dim_customer.csv
  - danh_muc_san_pham.xlsx        -> dim_product.csv
  - bang_gia_ban_cap_cho_khach_hang.xlsx -> dim_price_list.csv

Nguyên tắc: chỉ gắn cờ bất thường, không tự suy đoán/sửa giá trị nghiệp vụ.
"""
from __future__ import annotations
from config import (PRICE_SHEET, RAW, PROC)
import pandas as pd


def clean_customer() -> pd.DataFrame:
    df = pd.read_excel(RAW / "danh_muc_khach_hang.xlsx",
                        sheet_name="Danh mục khách hàng", header=1)
    df = df.rename(columns={
        "Mã khách hàng": "ma_khach_hang",
        "Tên khách hàng": "ten_khach_hang",
        "Thị trường": "thi_truong",
    })
    df["ma_khach_hang"] = df["ma_khach_hang"].astype("string").str.strip().str.upper()
    df.loc[df["ma_khach_hang"].isin(["", "NAN", "NONE"]), "ma_khach_hang"] = pd.NA
    # Nguồn danh mục dùng tên placeholder ẩn danh theo vị trí dòng.
    df["ten_khach_hang_la_placeholder"] = True
    dup = df["ma_khach_hang"].duplicated().sum()
    assert df['ma_khach_hang'].notna().all(), 'Null customer key'
    assert dup == 0, f"Trùng mã khách hàng: {dup} dòng"
    return df


def clean_product() -> pd.DataFrame:
    df = pd.read_excel(RAW / "danh_muc_san_pham.xlsx",
                        sheet_name="Danh mục sản phẩm", header=1)
    df = df.rename(columns={
        "STT": "stt",
        "Mã sản phẩm": "ma_san_pham",
        "Tên sản phẩm": "ten_san_pham",
        "Nhóm sản phẩm": "nhom_san_pham",
        "Đơn vị tính": "don_vi_tinh",
        "Trạng thái kinh doanh": "trang_thai_kinh_doanh",
        "Loại sản phẩm / quy cách": "loai_san_pham_quy_cach",
        "Nguồn hàng": "nguon_hang",
    })
    df["ma_san_pham"] = df["ma_san_pham"].astype("string").str.strip().str.upper()
    df.loc[df["ma_san_pham"].isin(["", "NAN", "NONE"]), "ma_san_pham"] = pd.NA
    dup = df["ma_san_pham"].duplicated().sum()
    assert df['ma_san_pham'].notna().all(), 'Null product key'
    assert dup == 0, f"Trùng mã sản phẩm: {dup} dòng"
    return df


def clean_price_list() -> pd.DataFrame:
    """Bảng giá cáp quang có nhiều block con (mỗi block cách nhau 1 dòng trống),
    header lặp lại 'STT | TÊN HÀNG HÓA | KÝ MÃ HIỆU | ...' chỉ ở đầu file.
    Đọc header 1 lần, sau đó bỏ toàn bộ dòng trống/dòng lặp header phụ."""
    raw = pd.read_excel(RAW / "bang_gia_ban_cap_cho_khach_hang.xlsx",
                         sheet_name=PRICE_SHEET, header=3)
    raw = raw.rename(columns={
        "STT": "stt",
        "TÊN HÀNG HÓA": "ten_hang_hoa",
        "KÝ MÃ HIỆU": "ky_ma_hieu",
        "TIÊU CHUẨN \nKỸ THUẬT": "tieu_chuan_ky_thuat",
        "Giá cấp 1": "gia_cap_1",
        "Gia cấp 2": "gia_cap_2",
        "Giá cap 3": "gia_cap_3",
        "GIÁ BÁN KHÁCH LẺ": "gia_ban_khach_le",
    })
    expected = {"stt", "ten_hang_hoa", "ky_ma_hieu", "tieu_chuan_ky_thuat",
                "gia_cap_1", "gia_cap_2", "gia_cap_3", "gia_ban_khach_le"}
    leftover = expected - set(raw.columns)
    assert not leftover, (
        f"Rename thất bại cho cột: {leftover} - có thể do lệch dấu/hoa-thường "
        "trong tên cột gốc (VD Unicode tổ hợp khác nhau cho cùng 1 ký tự có dấu). "
        f"Cột thực tế đang có: {list(raw.columns)}"
    )
    df = raw.dropna(subset=["ky_ma_hieu"]).copy()
    df["ky_ma_hieu"] = df["ky_ma_hieu"].astype(str).str.strip().str.upper()
    # Một mã (VD FE04) có thể lặp lại ứng với nhiều tiêu chuẩn kỹ thuật (7x0.7mm / 7x1.0mm)
    # -> giữ nguyên toàn bộ dòng, không gộp; đánh dấu số biến thể theo mã
    variant_count = df.groupby("ky_ma_hieu")["ky_ma_hieu"].transform("count")
    df["so_bien_the_theo_ma"] = variant_count
    return df.reset_index(drop=True)


def main():
    PROC.mkdir(parents=True, exist_ok=True)
    cust = clean_customer()
    prod = clean_product()
    price = clean_price_list()

    cust.to_csv(PROC / "dim_customer.csv", index=False, encoding="utf-8-sig")
    prod.to_csv(PROC / "dim_product.csv", index=False, encoding="utf-8-sig")
    price.to_csv(PROC / "dim_price_list.csv", index=False, encoding="utf-8-sig")

    print(f"[OK] dim_customer: {cust.shape}")
    print(f"[OK] dim_product : {prod.shape}")
    print(f"[OK] dim_price_list: {price.shape} "
          f"({price['ky_ma_hieu'].nunique()} mã duy nhất)")


if __name__ == "__main__":
    main()
