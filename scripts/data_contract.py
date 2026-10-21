"""Semantic CSV types independent of inferred dtype and all-null snapshots."""
STRING_COLUMNS = frozenset("""ma_khach_hang ten_khach_hang thi_truong ten_hang_hoa ky_ma_hieu
 tieu_chuan_ky_thuat ma_san_pham ten_san_pham nhom_san_pham don_vi_tinh trang_thai_kinh_doanh
 loai_san_pham_quy_cach nguon_hang ngay order_month ma_khach so_xac_nhan_don_hang so_hop_dong wo
 loai_don order_month_from_date order_month_from_code order_month_canonical order_month_rule
 item_text_raw parsed_product_token canonical_product_code product_family_code don_vi bien_the
 source_file source_sheet parse_status allocation_status product_candidates parse_reason product_item_id
 ma_khach_nhom ten_khach_hang_nhom nhom_san_pham_don_hang ly_do_khong_co_gia""".split())
BOOLEAN_COLUMNS = frozenset("""ten_khach_hang_la_placeholder ngay_bi_thieu ngay_khong_hop_le
 ngay_nam_khong_khop_file la_don_ban_hang loai_don_tu_so_hop_dong order_month_conflict parsed
 is_reference_product_code co_ma_khach_chinh_thuc gia_trong_giai_doan_xac_nhan co_don_gia_tham_khao
 nghi_ngo_outlier outlier_duoc_xac_nhan_la_phat_sinh_that""".split())
INTEGER_COLUMNS = frozenset("""stt so_bien_the_theo_ma order_row_id nam_file order_year item_id
 order_source_row_id source_excel_row so_quy_cach""".split())
REAL_COLUMNS = frozenset('so_luong so_luong_km don_gia_tham_khao gia_tri_uoc_tinh outlier_stat_threshold_km'.split())


def semantic_dtype(column: str) -> str:
    if column in STRING_COLUMNS:
        return 'string'
    if column in BOOLEAN_COLUMNS:
        return 'boolean'
    if column in INTEGER_COLUMNS:
        return 'integer'
    if column == 'ngay_dt':
        return 'date'
    if column in REAL_COLUMNS or column.startswith(('gia_', 'cap_1_', 'cap_2_', 'cap_3_', 'khach_le_')):
        return 'real number'
    raise ValueError(f'Column missing from semantic type contract: {column}')
