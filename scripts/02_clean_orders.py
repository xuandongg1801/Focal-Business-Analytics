"""
02_clean_orders.py
-------------------
Đọc dữ liệu tracker 2023-2025 từ sheet DATA_CHUAN_HOA (đã được chuẩn hóa:
một dòng nguồn có thể chứa nhiều sản phẩm) và tạo:
  - fact_order_header.csv : grain = 1 đơn/xác nhận đơn hàng
  - fact_order_items.csv  : grain = 1 dòng nguồn trong 1 đơn

Nguyên tắc nghiệp vụ đã xác nhận:
- Sheet DATA_CHUAN_HOA là nguồn duy nhất; header ở dòng 2.
- 5 cột tài chính vẫn trống 100%; không coi giá trị quy đổi từ bảng giá là doanh thu thật.
- Bảng giá "gia cap 2020" vẫn áp dụng cho 2023-2025.
- FTTH LỎNG -> -LT; FTTH CHẶT/ÉP CHẶT -> -SQ.
- Mã/quy cách không tồn tại trong bảng giá: giữ vết ở mart nhưng KHÔNG tính giá trị.
- 3 cụm ÉP CHẶT của DVVT-VNPTHN là số lượng phát sinh thật, không phải lặp khung hợp đồng.
- WO thiếu là khoảng trống ghi nhận quy trình; không suy diễn là giao từ tồn kho.
"""
from __future__ import annotations
import re
from config import (ORDER_TYPE_MAP, SALES_PREFIXES, PROC, TAB, order_sources)
from pathlib import Path
import numpy as np
import pandas as pd
from products import parse_product, validate_allocation, reference_codes, product_semantics


def extract_order_month(code: str) -> str | None:
    if pd.isna(code):
        return None
    m = re.search(r"/(\d{2})(\d{2})/", str(code))
    if not m:
        return None
    yy, mm = m.groups()
    if not (1 <= int(mm) <= 12):
        return None
    return f"20{yy}-{mm}"


def classify_prefix(code: str) -> str | None:
    if pd.isna(code):
        return None
    m = re.match(r"^([A-Z]+)-", str(code).strip().upper())
    return m.group(1) if m else None


def classify_prefix_with_fallback(so_xac_nhan: str, so_hop_dong: str) -> tuple[str | None, bool]:
    """Use contract prefix only when order prefix cannot be parsed; never infer from product."""
    prefix = classify_prefix(so_xac_nhan)
    if prefix is not None:
        return prefix, False
    fallback_prefix = classify_prefix(so_hop_dong)
    return fallback_prefix, fallback_prefix is not None


def classify_order_type_with_fallback(prefix: str | None) -> str:
    return ORDER_TYPE_MAP.get(prefix, f"Khác - {prefix}" if prefix else "Không xác định")


def parse_source_sheet(path: Path, year: int) -> pd.DataFrame:
    with pd.ExcelFile(path) as xls:
        if 'DATA_CHUAN_HOA' not in xls.sheet_names:
            raise ValueError(f'{path.name}: DATA_CHUAN_HOA is required')
        df = pd.read_excel(xls, sheet_name='DATA_CHUAN_HOA', header=1)
    rename = {
        "NĂM": "nam_excel",
        "STT SP": "stt_sp",
        "NGÀY": "ngay",
        "MÃ KHÁCH": "ma_khach",
        "SỐ XÁC NHẬN ĐƠN HÀNG": "so_xac_nhan_don_hang",
        "SỐ HỢP ĐỒNG": "so_hop_dong",
        "WO": "wo",
        "SẢN PHẨM": "san_pham_raw",
        "SỐ LƯỢNG": "so_luong",
        "ĐƠN VỊ": "don_vi",
        "DN GIAO HÀNG": "dn_giao_hang",
        "TỒN KHO CHƯA GIAO": "ton_kho_chua_giao",
        "SỐ TIỀN ĐƠN HÀNG": "so_tien",
        "TIỀN THUẾ VAT": "tien_thue_vat",
        "TỔNG SỐ TIỀN ĐƠN HÀNG": "tong_so_tien",
    }
    missing = set(rename) - set(df.columns)
    assert not missing, f"Thiếu cột ở DATA_CHUAN_HOA {year}: {missing}"
    df = df.rename(columns=rename)
    df['source_file'] = path.name
    df['source_sheet'] = 'DATA_CHUAN_HOA'
    df['source_excel_row'] = df.index + 3
    blank = df[list(rename.values())].isna().all(axis=1)
    df = df.loc[~blank].copy()
    if df['so_xac_nhan_don_hang'].isna().any():
        raise ValueError(f'{path.name}: nonempty rows without order code')
    df["raw_item_already_normalized"] = True
    df["nam_file"] = year
    return df


def load_raw_orders() -> pd.DataFrame:
    frames = []
    for path, y in order_sources():
        df = parse_source_sheet(path, y)
        frames.append(df)
    raw = pd.concat(frames, ignore_index=True)
    raw.insert(0, "source_row_id", range(1, len(raw) + 1))
    return raw


def clean_header(raw: pd.DataFrame) -> pd.DataFrame:
    d = raw.copy()
    d["ma_khach"] = d["ma_khach"].astype("string").str.strip().str.upper()
    d.loc[d["ma_khach"].isin(["NAN", "NONE", ""]), "ma_khach"] = pd.NA
    d["ngay_dt"] = pd.to_datetime(d["ngay"], errors="coerce", dayfirst=True, format='mixed')
    d["order_month_from_code"] = d["so_xac_nhan_don_hang"].apply(extract_order_month).astype("string")
    d["order_month_from_date"] = d["ngay_dt"].dt.strftime("%Y-%m").astype("string")
    date_year_match = d["ngay_dt"].dt.year.eq(d["nam_file"])
    d["order_month"] = d["order_month_from_date"].where(date_year_match, d["order_month_from_code"])
    d["order_month"] = d["order_month"].fillna(d["order_month_from_code"]).fillna(d["order_month_from_date"])
    d['order_month_canonical'] = d['order_month']
    d['order_month_conflict'] = (d.order_month_from_date.notna() & d.order_month_from_code.notna()
                                & d.order_month_from_date.ne(d.order_month_from_code))
    d['order_month_rule'] = np.where(date_year_match, 'date_in_file_year',
                                   np.where(d.order_month_from_code.notna(), 'code_fallback', 'date_fallback'))
    missing_month = d["order_month"].isna()
    if missing_month.any():
        codes = d.loc[missing_month, "so_xac_nhan_don_hang"].head(5).tolist()
        raise ValueError(
            f"order_month rỗng: không suy ra được từ mã đơn lẫn ngày; "
            f"{int(missing_month.sum())} dòng, mã đơn ví dụ: {codes}"
        )
    d['ngay_bi_thieu'] = d['ngay'].isna()
    d['ngay_khong_hop_le'] = d['ngay'].notna() & d['ngay_dt'].isna()
    d['ngay_nam_khong_khop_file'] = d['ngay_dt'].notna() & d['ngay_dt'].dt.year.ne(d['nam_file'])
    d["order_year"] = d["order_month"].astype("string").str.slice(0, 4)

    prefix_fallback = [
        classify_prefix_with_fallback(sxn, shd)
        for sxn, shd in zip(d["so_xac_nhan_don_hang"], d["so_hop_dong"])
    ]
    d["_prefix_hieu_luc"] = [p for p, _ in prefix_fallback]
    d["loai_don_tu_so_hop_dong"] = [f for _, f in prefix_fallback]
    d["loai_don"] = d["_prefix_hieu_luc"].apply(classify_order_type_with_fallback)
    d["la_don_ban_hang"] = d["_prefix_hieu_luc"].isin(SALES_PREFIXES)
    d = d.drop(columns=["_prefix_hieu_luc"])
    return d


def clean_money_assertions(raw: pd.DataFrame):
    checks = ["dn_giao_hang", "ton_kho_chua_giao", "so_tien", "tien_thue_vat", "tong_so_tien"]
    # Ghi chú là cột tùy chọn; nếu tồn tại thì kiểm tra độ trống.
    if "ghi_chu" in raw.columns:
        checks.append("ghi_chu")
    for c in checks:
        pct = raw[c].isna().mean()
        assert pct == 1.0, f"Cột {c} không còn trống 100% ({pct:.2%})"


def build_items(raw: pd.DataFrame) -> pd.DataFrame:
    # Giữ nguyên một dòng nguồn để đối chiếu; phân bổ sản phẩm ở bảng riêng.
    if ('raw_item_already_normalized' not in raw or raw.empty
            or not raw['raw_item_already_normalized'].eq(True).astype('boolean').fillna(False).all()):
        raise ValueError('Input items must be normalized before build_items().')
    if not raw['source_row_id'].is_unique or raw['source_row_id'].isna().any():
        raise ValueError('source_row_id must be unique and non-null')
    items = raw[["source_row_id", "san_pham_raw", "so_luong", "don_vi", "so_xac_nhan_don_hang"]].copy()
    items = items.rename(columns={"source_row_id": "order_source_row_id"})
    items["item_text_raw"] = items["san_pham_raw"].astype("string")
    items['so_luong'] = pd.to_numeric(items['so_luong'], errors='raise')
    if (items['so_luong'].dropna() < 0).any() or not np.isfinite(items['so_luong'].dropna()).all():
        raise ValueError('Quantity must be finite and nonnegative')
    items["don_vi"] = items["don_vi"].astype("string").str.strip().str.upper()
    items['don_vi'] = items['don_vi'].replace('', pd.NA)
    items['parsed'] = items['so_luong'].notna() & items['don_vi'].notna()
    items["bien_the"] = items["san_pham_raw"].astype("string").str.upper().str.extract(r"(LỎNG|CHẶT|ÉP CHẶT|SQ|LT)", expand=False)
    items["so_luong_km"] = np.where(
        items["parsed"] & items["don_vi"].eq("KM"), items["so_luong"],
        np.where(items["parsed"] & items["don_vi"].eq("M"), items["so_luong"] / 1000.0, np.nan)
    )
    # item_id ổn định theo thứ tự nguồn
    items.insert(0, "item_id", range(1, len(items) + 1))
    for column in ['source_file', 'source_sheet', 'source_excel_row']:
        items[column] = raw[column].to_numpy()
    references = reference_codes(PROC)
    parsed = [parse_product(r.item_text_raw, r.so_luong, r.don_vi, references) for r in items.itertuples()]
    items['parsed_product_token'] = [p.codes[0] if p.allocation_status == 'single' else None for p in parsed]
    items['parsed_product_token'] = items['parsed_product_token'].astype('string')
    items['parse_status'] = [p.parse_status for p in parsed]
    semantics = pd.DataFrame([product_semantics(token, p.parse_status, references)
                              for token, p in zip(items.parsed_product_token.where(items.parsed_product_token.notna(), None), parsed)], index=items.index)
    for field in semantics:
        items[field] = semantics[field].astype('boolean' if field == 'is_reference_product_code' else 'string')
    items['allocation_status'] = [p.allocation_status for p in parsed]
    items['product_candidates'] = [' | '.join(p.codes) for p in parsed]
    items['parse_reason'] = [p.reason for p in parsed]
    # Map order_row_id theo order code sẽ tạo ở header.
    return items


def build_order_tables(raw: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Pure table assembly from source rows; reusable by the integrity gate."""
    cleaned = clean_header(raw)

    # Header: 1 dòng duy nhất trên mỗi số xác nhận đơn hàng.
    consistency = cleaned.groupby("so_xac_nhan_don_hang").agg(
        n_source_rows=("source_row_id", "count"),
        n_date=("ngay_dt", lambda x: x.nunique(dropna=False)),
        n_customer=("ma_khach", lambda x: x.nunique(dropna=False)),
        n_order_month=("order_month", lambda x: x.nunique(dropna=False)),
        n_wo=('wo', lambda x: x.nunique(dropna=False)),
        n_contract=('so_hop_dong', lambda x: x.nunique(dropna=False)),
    )
    bad = consistency[(consistency["n_date"] > 1) | (consistency["n_customer"] > 1) | (consistency["n_order_month"] > 1) | (consistency["n_wo"] > 1) | (consistency["n_contract"] > 1)]
    assert bad.empty, f"Đơn có thông tin header không nhất quán: {bad.index.tolist()[:10]}"

    header = cleaned.sort_values(["so_xac_nhan_don_hang", "source_row_id"]).drop_duplicates("so_xac_nhan_don_hang").copy()
    order_map = dict(zip(header["so_xac_nhan_don_hang"], header["source_row_id"]))
    header = header.rename(columns={"source_row_id": "order_row_id"})
    keep_header = ["order_row_id", "nam_file", "ngay", "ngay_dt", "order_month", "order_year",
                   "ngay_bi_thieu", "ngay_khong_hop_le", "ngay_nam_khong_khop_file", "ma_khach", "so_xac_nhan_don_hang", "so_hop_dong", "wo",
                   "loai_don", "la_don_ban_hang", "loai_don_tu_so_hop_dong",
                   'order_month_from_date', 'order_month_from_code', 'order_month_canonical',
                   'order_month_conflict', 'order_month_rule']
    header = header[keep_header]

    items = build_items(cleaned)
    items["order_row_id"] = items["so_xac_nhan_don_hang"].map(order_map)
    items = items[["item_id", "order_row_id", "order_source_row_id", "item_text_raw", "parsed",
                   "parsed_product_token", "so_luong", "don_vi", "bien_the", "so_luong_km",
                   'source_file', 'source_sheet', 'source_excel_row', 'parse_status',
                   'allocation_status', 'product_candidates', 'parse_reason',
                   'canonical_product_code', 'is_reference_product_code', 'product_family_code']]
    return header, items


def build_product_items(items: pd.DataFrame) -> pd.DataFrame:
    """Canonical product fact excludes records whose attribution is unresolved."""
    records = []
    references = reference_codes(PROC)
    for row in items.to_dict('records'):
        parsed = parse_product(row['item_text_raw'], row['so_luong'], row['don_vi'], references)
        for index, (code, amount) in enumerate(parsed.allocations, 1):
            unit = row['don_vi'] if pd.notna(row['don_vi']) else ''
            km = amount if unit == 'KM' else amount / 1000 if unit == 'M' and pd.notna(amount) else np.nan
            records.append({**row, 'product_item_id': f"{row['item_id']}:{index}",
                            'parsed_product_token': code, 'so_luong': amount, 'so_luong_km': km,
                            'parse_status': 'exact_reference' if code in references else 'recognized_generic',
                            **product_semantics(code, 'exact_reference' if code in references else 'recognized_generic', references)})
    return pd.DataFrame(records, columns=[*items.columns, 'product_item_id'])


def main():
    PROC.mkdir(parents=True, exist_ok=True)
    TAB.mkdir(parents=True, exist_ok=True)
    raw = load_raw_orders()
    clean_money_assertions(raw)
    header, items = build_order_tables(raw)
    products = build_product_items(items)
    validate_allocation(items, products).to_csv(TAB/'quantity_conservation.csv', index=False)
    products.to_csv(PROC/'fact_product_items.csv', index=False, encoding='utf-8-sig')
    items[items.allocation_status.eq('unresolved')].to_csv(PROC/'unresolved_items.csv', index=False, encoding='utf-8-sig')
    items[~items.parse_status.eq('exact_reference')].to_csv(TAB/'product_parse_quality.csv', index=False, encoding='utf-8-sig')
    header[header.order_month_conflict].to_csv(TAB/'order_month_conflicts.csv', index=False, encoding='utf-8-sig')

    # Các dòng không có mã sản phẩm nhưng có text định lượng được vẫn giữ để audit.
    header.to_csv(PROC / "fact_order_header.csv", index=False, encoding="utf-8-sig")
    items.to_csv(PROC / "fact_order_items.csv", index=False, encoding="utf-8-sig")

    print(f"[OK] fact_order_header: {header.shape}")
    print(f"[OK] fact_order_items : {items.shape}")
    print(f"     Tách được số lượng cụ thể: {items['parsed'].sum()}/{len(items)} ")
    print(f"     Tỷ lệ dòng có số lượng và đơn vị: {items['parsed'].mean():.1%}")
    print(f"[INFO] Số đơn xác nhận duy nhất: {header['so_xac_nhan_don_hang'].nunique()}")
    print(f"[INFO] Dòng có mã sản phẩm chuẩn hóa: {items['parsed_product_token'].notna().sum()}")
    n_fallback = int(header["loai_don_tu_so_hop_dong"].sum())
    print(f"[INFO] Đơn phải dùng SỐ HỢP ĐỒNG để suy ra loại đơn (SỐ XÁC NHẬN không theo mẫu chuẩn): {n_fallback}")
    still_unknown = int((header["loai_don"] == "Không xác định").sum())
    print(f"[INFO] Đơn vẫn 'Không xác định' sau fallback: {still_unknown}")


if __name__ == "__main__":
    main()
