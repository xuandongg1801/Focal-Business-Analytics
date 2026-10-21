"""
03_build_mart.py
-----------------
Ghép fact_order_items + fact_order_header + dim_customer + dim_price_list.

Quy tắc giá đã xác nhận:
- Sheet `gia cap 2020` vẫn áp dụng cho 2023-2025.
- Không có thông tin đủ chắc chắn để chọn riêng cấp 1/2/3/khách lẻ cho từng đơn;
  vì vậy KHÔNG dùng một giá trung bình làm "doanh thu".
- Với mã có nhiều quy cách kỹ thuật trong bảng giá, lưu MIN/MAX cho từng cấp.
- Giá trị quy đổi theo từng cấp = số lượng KM x MIN/MAX đơn giá tương ứng.
- Mã/quy cách không có trong bảng giá: KHÔNG tính giá trị, nhưng vẫn giữ dòng để audit.
- FTTH -LT/-SQ phải được chuẩn hóa đúng biến thể.
- Ba cụm ÉP CHẶT DVVT-VNPTHN là phát sinh thật và không bị loại như outlier.
"""
from __future__ import annotations
import re
from config import (FAMILY_MAP, NONCABLE_KEYWORDS, PRICE_COLS, PROC, TAB, CONFIRMED_PROJECT_ORDERS, PRICE_VALID_YEARS)
import numpy as np
import pandas as pd


from data_rules import fit_item_outlier_threshold, item_outlier_mask, unpriced_metrics


def code_family(canon_code: str | None) -> str | None:
    if not isinstance(canon_code, str):
        return None
    m = re.match(r"^(ADSS|FTTH|FEAM|FEA|FEM|FE|DUAM|DUA|DUM|DU|AAC|DAC|DB|FC|CORE)", canon_code)
    return FAMILY_MAP.get(m.group(1)) if m else None


def unparsed_bucket(raw_text: str) -> str:
    t = str(raw_text).upper()
    for bucket, kws in NONCABLE_KEYWORDS.items():
        if any(k in t for k in kws):
            return bucket
    return "khac_chua_phan_loai"


def customer_group_fallback(so_xac_nhan: str) -> str | None:
    """Order suffix is a statistical group, never a confirmed customer identity."""
    if pd.isna(so_xac_nhan):
        return None
    text = str(so_xac_nhan).strip()
    if not text:
        return None
    tail = text.rsplit("/", 1)[-1].strip().upper()
    return tail or None


def price_ranges(price: pd.DataFrame) -> pd.DataFrame:
    p = price.copy()
    p["ky_ma_hieu"] = p["ky_ma_hieu"].astype("string").str.strip().str.upper()
    for c in PRICE_COLS.values():
        p[c] = pd.to_numeric(p[c], errors="raise")
        if (p[c].dropna() < 0).any() or not np.isfinite(p[c].dropna()).all():
            raise ValueError(f'Invalid price: {c}')
    g = p.dropna(subset=["ky_ma_hieu"]).groupby("ky_ma_hieu")
    out = g.agg(
        so_quy_cach=("ky_ma_hieu", "size"),
        **{f"{k}_min": (v, "min") for k, v in PRICE_COLS.items()},
        **{f"{k}_max": (v, "max") for k, v in PRICE_COLS.items()},
    ).reset_index()
    return out


def build_mart(items: pd.DataFrame, header: pd.DataFrame, customer: pd.DataFrame, price: pd.DataFrame,
               item_key: str = 'item_id') -> pd.DataFrame:
    df = items.merge(header, on="order_row_id", how="left", validate="many_to_one")
    if df[["order_month", "order_year"]].isna().any().any():
        raise ValueError("order_month/order_year rỗng trong mart: kiểm tra header và liên kết order_row_id trước khi tính giá")
    df = df.merge(customer[["ma_khach_hang", "ten_khach_hang", "thi_truong"]],
                  left_on="ma_khach", right_on="ma_khach_hang", how="left", validate="many_to_one")

    # Khóa nhóm khách hàng dùng cho Pareto/RFM: không để mất khối lượng khi ma_khach
    # trống. co_ma_khach_chinh_thuc=False đánh dấu rõ phần suy ra để không bị hiểu
    # nhầm là đã đối chiếu với danh mục khách hàng.
    df["co_ma_khach_chinh_thuc"] = df["ma_khach"].notna() & df["ma_khach_hang"].notna()
    fallback_tag = df["so_xac_nhan_don_hang"].apply(customer_group_fallback).astype("string").fillna("KHONG_XAC_DINH")
    df["ma_khach_nhom"] = np.where(df["co_ma_khach_chinh_thuc"], df["ma_khach"], "SUY_DIEN::" + fallback_tag)
    df["ten_khach_hang_nhom"] = np.where(
        df["co_ma_khach_chinh_thuc"], df["ten_khach_hang"].fillna(df["ma_khach"]),
        "(suy ra từ mã đơn) " + fallback_tag)

    df["nhom_san_pham_don_hang"] = df["parsed_product_token"].apply(code_family)
    missing_family = df["nhom_san_pham_don_hang"].isna()
    df.loc[missing_family, "nhom_san_pham_don_hang"] = df.loc[missing_family, "item_text_raw"].apply(unparsed_bucket)

    df["canonical_product_code"] = df["canonical_product_code"].astype("string")
    pr = price_ranges(price)
    df = df.merge(pr, left_on="canonical_product_code", right_on="ky_ma_hieu", how="left", validate="many_to_one")
    df = df.drop(columns=["ky_ma_hieu"])
    df['gia_trong_giai_doan_xac_nhan'] = df['order_year'].astype(int).isin(PRICE_VALID_YEARS)
    price_fields = [f'{tier}_{bound}' for tier in PRICE_COLS for bound in ('min', 'max')]
    df.loc[~df['gia_trong_giai_doan_xac_nhan'], price_fields] = np.nan
    if (~df['gia_trong_giai_doan_xac_nhan']).any():
        print('[WARNING] Price validity is unconfirmed outside configured years; KM retained, value unavailable.')
    df["co_don_gia_tham_khao"] = df["cap_1_min"].notna() | df["cap_2_min"].notna() | df["cap_3_min"].notna() | df["khach_le_min"].notna()
    df["ly_do_khong_co_gia"] = np.where(df["co_don_gia_tham_khao"], pd.NA,
                                         np.where(df["parsed_product_token"].isna(), "khong_xac_dinh_ma_quy_cach", "khong_co_trong_bang_gia"))
    df.loc[~df['gia_trong_giai_doan_xac_nhan'], 'ly_do_khong_co_gia'] = 'ngoai_giai_doan_gia_xac_nhan'

    for tier in PRICE_COLS:
        df[f"gia_tri_{tier}_min"] = df["so_luong_km"] * df[f"{tier}_min"]
        df[f"gia_tri_{tier}_max"] = df["so_luong_km"] * df[f"{tier}_max"]

    # Chỉ dùng để phục vụ các mô hình tương đối cần một scalar: midpoint của khoảng
    # cho CẤP 2, không coi là doanh thu thực tế và không dùng thay cho cấp giá thật.
    df["don_gia_tham_khao"] = (df["cap_2_min"] + df["cap_2_max"]) / 2
    df["gia_tri_uoc_tinh"] = df["so_luong_km"] * df["don_gia_tham_khao"]

    upper_bound_km = fit_item_outlier_threshold(df)
    df['nghi_ngo_outlier'] = item_outlier_mask(df, upper_bound_km)
    confirmed_mask = df['so_xac_nhan_don_hang'].isin(CONFIRMED_PROJECT_ORDERS)
    df["outlier_stat_threshold_km"] = upper_bound_km
    df["outlier_duoc_xac_nhan_la_phat_sinh_that"] = confirmed_mask

    assert len(df) == len(items) and df[item_key].is_unique
    assert df['so_xac_nhan_don_hang'].notna().all(), 'Orphan item header'
    return df


def write_mart_outputs(df: pd.DataFrame) -> None:
    outlier_report = df[df["nghi_ngo_outlier"]].copy()
    outlier_report[["item_id", "order_row_id", "so_xac_nhan_don_hang", "item_text_raw", "parsed_product_token", "so_luong_km"]].to_csv(TAB / "outlier_report.csv", index=False, encoding="utf-8-sig")

    # Audit 3 cụm DVVT: bắt buộc xuất riêng để đối chiếu.
    dvvt = df[df["so_xac_nhan_don_hang"].isin(CONFIRMED_PROJECT_ORDERS) & df["so_luong_km"].notna()]
    dvvt[["so_xac_nhan_don_hang", "nam_file", "item_text_raw", "parsed_product_token", "so_luong_km", "co_don_gia_tham_khao"]].to_csv(TAB / "dvvt_vnpthn_ep_chat_confirmed.csv", index=False, encoding="utf-8-sig")

    pd.Series(unpriced_metrics(df)).to_csv(TAB / 'unpriced_km_reconciliation.csv', header=['km'])
    df.to_csv(PROC / "mart_order_items.csv", index=False, encoding="utf-8-sig")

    # Mã có khối lượng nhưng không có giá: không tính các KPI giá trị; giữ riêng danh sách audit.
    unpriced = df[(df["so_luong_km"].notna()) & (~df["co_don_gia_tham_khao"])]
    unpriced[["so_xac_nhan_don_hang", "nam_file", "item_text_raw", "parsed_product_token", "so_luong_km", "ly_do_khong_co_gia"]].to_csv(TAB / "unpriced_items_excluded.csv", index=False, encoding="utf-8-sig")

    print(f'[OK] mart_order_items: {len(df)} rows; item outliers: {int(df.nghi_ngo_outlier.sum())}')


def main():
    PROC.mkdir(parents=True, exist_ok=True)
    TAB.mkdir(parents=True, exist_ok=True)
    items = pd.read_csv(PROC / 'fact_order_items.csv')
    header = pd.read_csv(PROC / 'fact_order_header.csv')
    customer = pd.read_csv(PROC / 'dim_customer.csv')
    price = pd.read_csv(PROC / 'dim_price_list.csv')
    ledger = build_mart(items, header, customer, price)
    write_mart_outputs(ledger)
    products = pd.read_csv(PROC/'fact_product_items.csv')
    product_mart = build_mart(products, header, customer, price, item_key='product_item_id')
    # Filtering is defined at source-row grain, independent of whether a row splits.
    for field in ['nghi_ngo_outlier', 'outlier_stat_threshold_km']:
        product_mart[field] = product_mart.item_id.map(ledger.set_index('item_id')[field])
    product_mart.to_csv(PROC/'mart_product_items.csv', index=False, encoding='utf-8-sig')


if __name__ == "__main__":
    main()
