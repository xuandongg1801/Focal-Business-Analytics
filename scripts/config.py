"""Shared configuration; confirmed business values must not be tuned to outputs."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / 'data/raw'
PROC = ROOT / 'data/processed'
TAB = ROOT / 'outputs/tables'
FIG = ROOT / 'outputs/figures'
LOG = ROOT / 'outputs/logs'
FIXTURES = ROOT / 'tests/fixtures/current_dataset'
FORECAST_HORIZON = 6
HOLDOUT_MONTHS = 6
VALIDATION_MONTHS = 6
MIN_TRAIN_MONTHS = 12
MAX_VALIDATION_FOLDS = 4
EWMA_ALPHAS = (0.10, 0.15, 0.20, 0.25, 0.30, 0.40, 0.50)
OUTLIER_IQR_MULTIPLIER = 3.0
WAPE_EPSILON = 1e-12
RANDOM_STATE = 42
HISTORICAL_EXTERNAL_EXPOSURE = 'holdout_has_prior_analyst_exposure'
ABC_LIMITS = (80, 95)
PRICE_SHEET = 'gia cap 2020'
PRICE_VALID_YEARS = (2023, 2024, 2025)
CONFIRMED = {
    'CA-033/2401/DVVT-VNPTHN': {'FTTH01-SQ': 208426, 'FTTH02-SQ': 12280, 'FTTH04-SQ': 7668},
    'CA-153/2404/DVVT-VNPTHN': {'FTTH01-SQ': 208426, 'FTTH02-SQ': 12280, 'FTTH04-SQ': 7668},
    'CA-168/2505/DVVT-VNPTHN': {'FTTH01-SQ': 208426, 'FTTH02-SQ': 12280, 'FTTH04-SQ': 7668},
}
CONFIRMED_PROJECT_ORDERS = frozenset(CONFIRMED)


def order_sources() -> list[tuple[Path, int]]:
    paths = sorted(RAW.glob('bang_theo_doi_don_hang_nam_[0-9][0-9][0-9][0-9].xlsx'))
    if not paths:
        raise FileNotFoundError(f'No normalized order trackers in {RAW}')
    return [(path, int(path.stem.rsplit('_', 1)[1])) for path in paths]

ORDER_TYPE_MAP = {
    "CA": "Đơn khách hàng - Cáp quang",
    "RM": "Mua nguyên vật liệu",
    "AC": "Đơn khách hàng - Phụ kiện quang",
    "SL": "Đơn khách hàng - Năng lượng mặt trời",
    "EQ": "Đơn khách hàng - Thiết bị",
    "IT": "Mua phần mềm/license nội bộ",
}
SALES_PREFIXES = {"CA", "AC", "SL", "EQ"}

FAMILY_MAP = {
    "FE": "Cáp treo phi kim loại (FE)", "FEA": "Cáp treo gia cường kim loại (FEA)",
    "FEM": "Cáp treo phi kim loại - Midspan (FEM)", "FEAM": "Cáp treo kim loại - Midspan (FEAM)",
    "DU": "Cáp cống phi kim loại (DU)", "DUA": "Cáp cống kim loại (DUA)",
    "DUM": "Cáp cống phi kim loại - Midspan (DUM)", "DUAM": "Cáp cống kim loại - Midspan (DUAM)",
    "AAC": "Cáp truy nhập treo (AAC)", "DAC": "Cáp truy nhập cống (DAC)",
    "DB": "Cáp chôn trực tiếp (DB)", "FTTH": "Dây thuê bao quang - FTTH",
    "ADSS": "Cáp tự treo ADSS", "FC": "Cáp dã chiến (FC)",
    "CORE": "Chưa xác định rõ quy cách (CORE) - cần xác nhận",
}
NONCABLE_KEYWORDS = {
    "raw_material": ["NHỰA", "THÉP", "FRP", "HDPE", "MDPE", "DẦU NHỒI", "SỢI QUANG", "DÂY TREO", "BĂNG THÉP", "BĂNG CHỐNG THẤM", "CHỈ BÓ CÁP", "BĂNG IN"],
    "accessory_generic": ["PHỤ KIỆN", "MĂNG XÔNG", "ODF", "ADAPTER", "TỦ QUANG", "MX", "SC/APC"],
    "commercial_note": ["THƯƠNG MẠI", "BÁO GIÁ", "HỦY", "HỢP ĐỒNG NGUYÊN TẮC", "TIỂU NGẠCH"],
    "software_it": ["PHẦN MỀM", "LICENCE", "LICENSE", "ERP"],
    "solar": ["SOLAR"], "equipment": ["ONT", "SWITCH", "LOA", "CÁP ĐIỆN", "CÁP MẠNG", "CAT5E"],
    "generic_cable_no_spec": ["CÁP QUANG CÁC LOẠI", "CÁP CÁC LOẠI", "CÁP VÀ PHỤ KIỆN", "CÁP LẺ", "CÁP MẪU", "CÁP CŨ", "CÁP QUANG VÀ PHỤ KIỆN", "DU CÁC LOẠI", "PK CÁC LOẠI"],
}
PRICE_COLS = {"cap_1": "gia_cap_1", "cap_2": "gia_cap_2", "cap_3": "gia_cap_3", "khach_le": "gia_ban_khach_le"}

STAGES = ('01_clean_master', '02_clean_orders', '03_build_mart', '04_eda', '05_models', '06_validate_pipeline')
PROCESSED_FILES = ('dim_customer.csv', 'dim_product.csv', 'dim_price_list.csv',
                   'fact_order_header.csv', 'fact_order_items.csv', 'mart_order_items.csv',
                   'fact_product_items.csv', 'mart_product_items.csv', 'unresolved_items.csv')
TABLE_FILES = (
    'quantity_conservation.csv', 'product_parse_quality.csv', 'order_month_conflicts.csv',
    'abc_product_code.csv', 'abc_product_family.csv', 'customer_rfm_segments.csv',
    'duplicate_item_candidates.csv', 'dvvt_vnpthn_ep_chat_confirmed.csv', 'eda_summary.json',
    'forecast.csv', 'forecast_backtest.csv', 'forecast_holdout.csv', 'forecast_holdout_comparison.csv',
    'forecast_methodology.json', 'forecast_model_comparison.csv',
    'khach_hang_chua_co_ma_loai_khoi_phan_khuc.csv', 'customer_low_recency.csv',
    'model_summary.json', 'monthly_km.csv', 'outlier_report.csv', 'pipeline_validation.json',
    'unpriced_items_excluded.csv', 'unpriced_km_reconciliation.csv',
)
FIGURE_FILES = (
    '01_xu_huong_san_luong_thang.png', '02_san_luong_theo_nam.png', '03_thoi_vu_theo_thang.png',
    '04_pareto_nhom_san_pham.png', '06_top20_khach_hang.png', '08_co_cau_loai_don.png',
    '09_du_bao_san_luong.png', '10_phan_khuc_khach_hang.png', '11_quy_mo_don_theo_nam.png',
    '12_ty_le_wo_theo_nam.png', '13_model_validation.png',
)
