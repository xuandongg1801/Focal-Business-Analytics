from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'data/processed'
OUTPUT = ROOT / 'outputs/approval_prediction'
SEED = 42
VALIDATION_START = '2024-07'
TEST_START = '2025-01'
# Frozen after inspecting actual source values, not inferred from quantities.
VALID_UNITS = frozenset({'KM', 'M', 'KG', 'CÁI', 'BỘ', 'LICENSE', 'TẤN'})
INVALID_PRODUCT_EXACT = frozenset({'KM', 'M', 'M .)', 'THƯƠNG MẠI', 'HỦY',
                                  'HỢP ĐỒNG NGUYÊN TẮC',
                                  'CÁP', 'PHỤ KIỆN', 'NVL', 'CÁP VÀ PHỤ KIỆN', 'CÁP QUANG VÀ PHỤ KIỆN', 'BÁN NVL'})
INVALID_PRODUCT_PATTERNS = ('BÁO GIÁ', 'CÁC LOẠI', 'CÁC LOAI')
AMBIGUOUS_PRODUCT_EXACT = frozenset({'QUẤN LẠI CÁP', 'VNTT GIAO BÌNH DƯƠNG'})
TARGET_VERSION = 'order_win_lost_cell_presence'
# No historical outcomes/volumes: snapshot has no outcome-availability timestamps.
FEATURES = ['customer_is_known', 'prior_order_count', 'recency_months',
            'customer_active_months_before', 'orders_last_3m', 'orders_last_6m',
            'prior_monthly_order_trend', 'year', 'month', 'quarter', 'month_sin', 'month_cos']
BLACKLIST = {'chot_don', 'product_valid', 'quantity_valid', 'unit_valid',
             'has_product', 'has_quantity', 'has_unit', 'item_count', 'item_text_raw',
             'parsed_product_token', 'canonical_product_code', 'product_family_code',
             'parse_status', 'is_reference_product_code', 'so_luong', 'don_vi', 'so_luong_km', 'wo',
             'so_hop_dong', 'prior_approved_count', 'prior_failed_count',
             'prior_approval_rate', 'prior_total_volume', 'prior_avg_volume',
             'prior_median_volume', 'approved_orders_last_6m', 'approved_orders_last_3m',
             'completeness_score', 'missing_product', 'missing_quantity', 'missing_unit',
             'contract_id', 'delivery_status', 'actual_delivery', 'final_status', 'completed_date',
             'price', 'gia_tri_uoc_tinh', 'raw_product', 'raw_quantity', 'raw_unit'}
BLACKLIST |= {'product', 'quantity', 'unit', 'product_missing', 'quantity_missing', 'unit_missing',
              'product_complete', 'quantity_complete', 'unit_complete', 'required_fields_complete',
              'missing_required_fields', 'completeness_flag', 'item_target', 'incomplete_fields',
              'historical_win_count', 'historical_lost_count', 'historical_win_rate',
              'product_present', 'quantity_present', 'unit_present', 'line_complete', 'order_complete'}


def validate_feature_names(names):
    """Require audited lineage, not merely the absence of a short denylist."""
    import re
    names = list(names)
    risky = re.compile(r'product|quantity|unit|complet|missing|target|chot_don|win|lost|approved|failed|volume', re.I)
    if len(names) != len(set(names)) or any(n in BLACKLIST or risky.search(n) for n in names):
        raise ValueError('Target-defining or outcome-derived feature is forbidden')
    if names != FEATURES:
        raise ValueError('Feature list must match the audited arrival/calendar allowlist')

# Numeric model storage is float64; domains describe meaning, not current extrema.
FEATURE_DOMAINS = {
    'customer_is_known': ('0 or 1', 'indicator'),
    'prior_order_count': ('integer >= 0', 'orders'),
    'recency_months': ('integer >= 1; null without customer history', 'months'),
    'customer_active_months_before': ('integer >= 0', 'active months'),
    'orders_last_3m': ('integer >= 0', 'orders'),
    'orders_last_6m': ('integer >= 0', 'orders'),
    'prior_monthly_order_trend': ('signed real, unbounded; >0 increasing, <0 decreasing, 0 unchanged; zero without history', 'orders/month difference between adjacent three-month averages'),
    'year': ('calendar year', 'year'),
    'month': ('integer 1..12', 'month'),
    'quarter': ('integer 1..4', 'quarter'),
    'month_sin': ('-1..1', 'unitless'),
    'month_cos': ('-1..1', 'unitless'),
}
