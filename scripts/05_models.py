"""
05_models.py
------------
Các mô hình phục vụ định hướng sản xuất:

A. Dự báo sản lượng với horizon cấu hình.
   - Dùng toàn bộ đơn bán cáp có số lượng KM, không phụ thuộc bảng giá.
   - Loại các outlier thống kê và tách riêng 3 đơn dự án đã được xác nhận là
     sự kiện đặc biệt để không kéo lệch nền dự báo.
   - Chọn Naive / Seasonal Naive / EWMA trên rolling validation trước holdout.
   - Ngưỡng outlier fit riêng trong train; final holdout không dùng chọn model.
B. Phân nhóm RFV theo tứ phân vị thực nghiệm, không dùng doanh thu.
C. Phân tích ABC sản phẩm theo sản lượng.
D. Liệt kê khách ít giao dịch gần đây để đối chiếu nghiệp vụ.
"""
from __future__ import annotations

from config import FORECAST_HORIZON, PROC, TAB
import numpy as np
import pandas as pd
import hashlib
import importlib.metadata
from segmentation import relative_score, segment_labels, LABEL_RECENT, LABEL_INACTIVE, LABEL_FREQUENT, LABEL_OTHER
from data_rules import observation_months, abc_labels, sales_km
from reporting import configure_plots, save_figure, write_json, COLOR_MAIN, COLOR_GREY, COLOR_RED
from forecasting import run_forecast


def model_forecast(cable: pd.DataFrame, plt):
    outcome = run_forecast(cable, FORECAST_HORIZON)
    baseline_monthly = outcome['baseline']
    forecast = outcome['forecast']
    future_months = outcome['future'].astype(str)
    comparison = outcome['comparison']
    selected_model = outcome['metrics']['selected_model']
    outcome['detail'].to_csv(TAB / 'forecast_backtest.csv', index=False, encoding='utf-8-sig')
    comparison.to_csv(TAB / 'forecast_model_comparison.csv', index=False, encoding='utf-8-sig')
    outcome['holdout_comparison'].to_csv(TAB / 'forecast_holdout_comparison.csv', index=False, encoding='utf-8-sig')
    outcome['test'].to_csv(TAB / 'forecast_holdout.csv', index=False, encoding='utf-8-sig')
    outcome['metrics']['dataset_sha256'] = hashlib.sha256((PROC/'mart_order_items.csv').read_bytes()).hexdigest()
    outcome['metrics']['runtime_versions'] = {name: importlib.metadata.version(name) for name in ['numpy', 'pandas']}
    outcome['metrics']['run_id'] = hashlib.sha256(repr((outcome['metrics']['dataset_sha256'], selected_model,
        outcome['metrics']['runtime_versions'], FORECAST_HORIZON)).encode()).hexdigest()
    write_json(TAB / 'forecast_methodology.json', outcome['metrics'])
    baseline_monthly.index = baseline_monthly.index.astype(str)
    forecast_df = pd.DataFrame({
        "thang": future_months,
        "du_bao_km": np.round(forecast, 1),
        "mo_hinh": selected_model,
        "pham_vi": "Nền sản lượng, không gồm sự kiện dự án đã xác nhận",
    })
    forecast_df.to_csv(TAB / "forecast.csv", index=False, encoding="utf-8-sig")

    plot_forecast(baseline_monthly, forecast, future_months, selected_model, outcome['metrics'], plt)
    plot_model_comparison(comparison, plt)
    print(f"[OK] Forecast: {selected_model}; validation WAPE={outcome['metrics']['validation_wape_pct']}; holdout WAPE={outcome['metrics']['test_wape_pct']}")
    print('[LIMITATION] ' + outcome['metrics']['limitations'][0])


def plot_forecast(baseline_monthly, forecast, future_months, selected_model, method, plt):
    fig, ax = plt.subplots(figsize=(12, 5.2))
    x_hist = np.arange(len(baseline_monthly))
    x_future = np.arange(len(baseline_monthly), len(baseline_monthly) + FORECAST_HORIZON)
    smooth = baseline_monthly.rolling(6, min_periods=1).median()

    ax.plot(x_hist, baseline_monthly.values, color=COLOR_MAIN, marker="o", markersize=3.5,
            linewidth=1.8, label="Sản lượng nền sau hiệu chỉnh")
    ax.plot(x_hist, smooth.values, color=COLOR_GREY, linestyle="--", linewidth=2,
            label="Xu hướng trung vị sáu tháng")
    ax.plot(np.r_[x_hist[-1], x_future], np.r_[baseline_monthly.iloc[-1], forecast],
            color=COLOR_RED, linewidth=2.2, marker="s", markersize=5,
            label=f"Dự báo {FORECAST_HORIZON} tháng tới")
    ax.axvspan(len(baseline_monthly) - 0.5, len(baseline_monthly) + FORECAST_HORIZON - 0.5,
               color=COLOR_RED, alpha=0.06)

    all_labels = list(baseline_monthly.index) + list(future_months)
    ticks = np.arange(0, len(all_labels), 3)
    ax.set_xticks(ticks)
    ax.set_xticklabels([all_labels[i] for i in ticks], rotation=45, ha="right")
    ax.set_ylabel("Sản lượng KM")
    ax.set_xlabel("Thời gian")
    ax.set_title(f"Dự báo sản lượng cáp quang {FORECAST_HORIZON} tháng tới")
    holdout_wape = method['test_wape_pct']
    holdout_label = f'{holdout_wape:.2f}%' if holdout_wape is not None else 'không xác định'
    ax.text(
        0.01, 0.98,
        f"Mô hình được chọn: {selected_model}  |  WAPE holdout: {holdout_label}",
        transform=ax.transAxes, va="top", ha="left", fontsize=9, color="#4d4d4d"
    )
    ax.legend(loc="upper right", fontsize=9, frameon=False)
    ax.grid(alpha=0.22, axis="y")
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    save_figure(fig, "09_du_bao_san_luong.png")


def plot_model_comparison(comparison, plt):
    fig, ax = plt.subplots(figsize=(9, 5))
    ordered = comparison.iloc[::-1]
    if ordered['selection_wape_pct'].notna().any():
        ax.barh(ordered['mo_hinh'], ordered['selection_wape_pct'], color=COLOR_MAIN)
        ax.set_xlabel('Pooled validation WAPE % — thấp hơn tốt hơn')
    else:
        ax.barh(ordered['mo_hinh'], ordered['mae_trung_binh_km'], color=COLOR_MAIN)
        ax.set_xlabel('Validation MAE KM — WAPE không xác định do actual gần 0')
    ax.set_title('So sánh baseline trên rolling validation')
    save_figure(fig, '13_model_validation.png')


def customer_rfm(cable: pd.DataFrame, ref_date: pd.Period) -> pd.DataFrame:
    """Retrospective segmentation of matched customers; independent of forecasting."""
    grp = cable[cable['co_ma_khach_chinh_thuc']].groupby(['ma_khach', 'ten_khach_hang'], dropna=False)
    rfm = grp.agg(
        last_order_month=("order_month", "max"),
        n_orders=("order_row_id", "nunique"),
        total_km=("so_luong_km", "sum"),
        total_value=("gia_tri_uoc_tinh", lambda x: x.sum(min_count=1)),
    ).reset_index()
    rfm["recency_months"] = rfm["last_order_month"].apply(
        lambda m: (ref_date - pd.Period(m, freq="M")).n
    )

    if rfm.ma_khach.duplicated().any():
        raise ValueError('Customer segmentation requires one row per customer code')
    for feature, score, higher in [('recency_months', 'r_score', False),
                                   ('n_orders', 'f_score', True), ('total_km', 'v_score', True)]:
        rfm[score] = relative_score(rfm[feature], higher)
    rfm['snapshot_month'] = str(ref_date)
    rfm['phan_khuc'] = segment_labels(rfm)

    return rfm


def plot_customer_segments(rfm: pd.DataFrame, plt) -> None:
    fig, ax = plt.subplots(figsize=(8.5, 6))
    colors_map = {
        LABEL_RECENT: "#1f6f8b",
        LABEL_FREQUENT: "#4fa3bf",
        LABEL_OTHER: "#e0803c",
        LABEL_INACTIVE: "#c0392b",
    }
    for seg, sub in rfm.groupby("phan_khuc"):
        ax.scatter(
            sub["recency_months"], sub["total_km"],
            s=np.clip(sub["n_orders"] * 25, 25, 450),
            alpha=0.72, label=seg, color=colors_map.get(seg), edgecolors="white", linewidths=0.5,
        )
    ax.set_xlabel("Số tháng từ lần đặt hàng gần nhất")
    ax.set_ylabel("Tổng sản lượng đặt hàng KM")
    ax.set_yscale("symlog")
    ax.set_title("Phân khúc khách hàng theo hành vi mua hàng")
    ax.legend(fontsize=8.5, frameon=False)
    ax.grid(alpha=0.2, axis="both")
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    save_figure(fig, "10_phan_khuc_khach_hang.png")


def model_customer_segments(cable: pd.DataFrame, results: dict, ref_date: pd.Period, plt):

    has_code = cable["co_ma_khach_chinh_thuc"] == True
    excluded = cable[~has_code]
    km_excluded = float(excluded["so_luong_km"].sum())
    km_total = float(cable["so_luong_km"].sum())
    results["phan_khuc__km_loai_vi_thieu_ma_khach_chinh_thuc"] = round(km_excluded, 1)
    results["phan_khuc__ty_trong_km_loai_pct"] = round(km_excluded / km_total * 100, 2) if km_total else 0.0
    results["phan_khuc__so_nhom_suy_dien_bi_loai"] = int(excluded["ma_khach_nhom"].nunique())
    excluded_breakdown = (
        excluded.groupby(["ma_khach_nhom", "ten_khach_hang_nhom"])["so_luong_km"]
        .sum().sort_values(ascending=False).reset_index()
    )
    excluded_breakdown.to_csv(TAB / "khach_hang_chua_co_ma_loai_khoi_phan_khuc.csv", index=False, encoding="utf-8-sig")
    print(f"[B] Loại khỏi phân khúc RFM vì thiếu mã khách chính thức: {km_excluded:,.1f} KM "
          f"({results['phan_khuc__ty_trong_km_loai_pct']:.1f}% tổng KM) - chi tiết trong "
          f"khach_hang_chua_co_ma_loai_khoi_phan_khuc.csv")

    if not has_code.any():
        results['phan_khuc_khach_hang'] = []
        print('[WARNING] No matched customers available for RFM')
        empty = pd.DataFrame(columns=['ma_khach','ten_khach_hang','last_order_month','n_orders',
                                      'total_km','total_value','recency_months','r_score','f_score','v_score','snapshot_month','phan_khuc'])
        empty.to_csv(TAB / 'customer_rfm_segments.csv', index=False)
        empty.to_csv(TAB / 'customer_low_recency.csv', index=False)
        fig, ax = plt.subplots(figsize=(8.5, 6))
        ax.text(.5,.5,'Không đủ khách có mã chính thức để phân khúc',ha='center')
        ax.set_axis_off()
        save_figure(fig, '10_phan_khuc_khach_hang.png')
        return
    rfm = customer_rfm(cable, ref_date)
    rfm.to_csv(TAB / "customer_rfm_segments.csv", index=False, encoding="utf-8-sig")

    seg_summary = rfm.groupby("phan_khuc").agg(
        so_khach=("ma_khach", "count"),
        tong_km=("total_km", "sum"),
        tb_recency_thang=("recency_months", "mean"),
        tb_so_don=("n_orders", "mean"),
    ).round(1)
    results["phan_khuc_khach_hang"] = seg_summary.reset_index().to_dict("records")

    plot_customer_segments(rfm, plt)

    at_risk = rfm[rfm["phan_khuc"] == LABEL_INACTIVE].sort_values("total_km", ascending=False)
    at_risk.head(15).to_csv(TAB / "customer_low_recency.csv", index=False, encoding="utf-8-sig")
    results["so_khach_it_giao_dich_gan_day"] = int(len(at_risk))
    results["km_lich_su_nhom_it_giao_dich_gan_day"] = round(float(at_risk["total_km"].sum()), 1)


def model_abc_products(cable: pd.DataFrame, results: dict):
    assert cable.parsed_product_token.notna().all(), 'ABC requires resolved product attribution'
    reference = cable[cable.is_reference_product_code]
    by_code = reference.groupby(["canonical_product_code", "nhom_san_pham_don_hang"])["so_luong_km"].sum()
    by_code = by_code.sort_values(ascending=False).reset_index()
    by_code["cum_pct"] = by_code["so_luong_km"].cumsum() / by_code["so_luong_km"].sum() * 100
    by_code["nhom_abc"] = abc_labels(by_code["so_luong_km"])
    by_code.to_csv(TAB / "abc_product_code.csv", index=False, encoding="utf-8-sig")

    abc_counts = by_code['nhom_abc'].value_counts().sort_index()
    results['abc_reference_excluded_generic_km'] = float(cable.loc[~cable.is_reference_product_code, 'so_luong_km'].sum())
    results['abc_semantic_level'] = 'authoritative reference code; not unique technical SKU'
    results["abc_san_pham__so_ma_theo_nhom"] = abc_counts.to_dict()
    results["abc_san_pham__nhom_A_ma"] = by_code[by_code["nhom_abc"] == "A"]["canonical_product_code"].tolist()
    print("[C] Số mã sản phẩm theo nhóm ABC:", abc_counts.to_dict())
    print("    Nhóm A:", results["abc_san_pham__nhom_A_ma"])


def main():
    TAB.mkdir(parents=True, exist_ok=True)
    plt = configure_plots()
    df = pd.read_csv(PROC / 'mart_order_items.csv')
    cable = df.loc[sales_km(df) & ~df['nghi_ngo_outlier']].copy()
    results = {}
    model_forecast(df, plt)
    model_customer_segments(cable, results, observation_months(df)[-1], plt)
    products = pd.read_csv(PROC/'mart_product_items.csv')
    model_abc_products(products[sales_km(products) & ~products.nghi_ngo_outlier], results)
    write_json(TAB / 'model_summary.json', results)


if __name__ == "__main__":
    main()
