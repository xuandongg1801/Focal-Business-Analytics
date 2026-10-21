"""
04_eda.py
---------
Phân tích khám phá dữ liệu (EDA) trên mart_order_items.csv.
Xuất biểu đồ PNG vào outputs/figures/ và số liệu tổng hợp vào
outputs/tables/eda_summary.json (để dùng lại khi viết báo cáo, tránh
số liệu trong báo cáo lệch khỏi số liệu đã tính).
"""
from __future__ import annotations
from config import PROC, TAB, ABC_LIMITS
import numpy as np
import pandas as pd
from data_rules import monthly_series, observation_months, unpriced_metrics, abc_labels
from reporting import configure_plots, save_figure, write_json, COLOR_MAIN, COLOR_ACC, COLOR_GREY


def trend_reports(cable, cable_raw, header, summary, plt):
    history_index = observation_months(cable_raw)
    monthly = monthly_series(cable, history_index)
    monthly.index = monthly.index.astype(str)
    monthly.to_csv(TAB / "monthly_km.csv", header=["so_luong_km"])

    fig, ax = plt.subplots(figsize=(11, 4.2))
    ax.plot(monthly.index, monthly.values, color=COLOR_MAIN, marker="o", markersize=3, linewidth=1.6)
    ax.set_title("Diễn biến sản lượng cáp quang theo tháng", fontsize=12, fontweight="bold")
    ax.set_ylabel("KM")
    ax.set_xticks(range(0, len(monthly), 3))
    ax.set_xticklabels(monthly.index[::3], rotation=45, ha="right")
    ax.grid(alpha=0.25)
    save_figure(fig, "01_xu_huong_san_luong_thang.png")

    yearly = cable.groupby("order_year")["so_luong_km"].sum()
    yearly_orders = header[header["la_don_ban_hang"] == True].groupby("order_year").size()
    summary["san_luong_km_theo_nam"] = yearly.round(1).to_dict()
    summary["so_don_ban_hang_theo_nam"] = yearly_orders.to_dict()
    for previous, current in zip(yearly.index[:-1], yearly.index[1:]):
        summary[f'tang_truong_km_{current}_vs_{previous}_pct'] = (
            round((yearly[current] / yearly[previous] - 1) * 100, 1) if yearly[previous] else None)

    fig, ax = plt.subplots(figsize=(6, 4.2))
    bars = ax.bar(yearly.index, yearly.values, color=[COLOR_MAIN, COLOR_ACC, COLOR_GREY])
    for b in bars:
        ax.text(b.get_x() + b.get_width() / 2, b.get_height(), f"{b.get_height():,.0f}",
                ha="center", va="bottom", fontsize=10)
    ax.set_title("Tổng sản lượng cáp quang theo năm", fontsize=12, fontweight="bold")
    ax.set_ylabel("KM")
    save_figure(fig, "02_san_luong_theo_nam.png")

    seasonal_data = monthly.rename('km').reset_index()
    seasonal_data.columns = ['month', 'km']
    seasonal_data['nam'] = seasonal_data['month'].str[:4]
    seasonal_data['thang'] = seasonal_data['month'].str[5:7].astype(int)
    seasonal = seasonal_data.pivot(index='thang', columns='nam', values='km').reindex(range(1, 13))
    seasonal_avg = seasonal.mean(axis=1)
    summary["chi_so_thoi_vu_theo_thang"] = seasonal_avg.dropna().round(1).to_dict()

    fig, ax = plt.subplots(figsize=(9, 4.2))
    width = 0.8 / max(1, len(seasonal.columns))
    x = np.arange(1, 13)
    for i, y in enumerate(seasonal.columns):
        ax.bar(x + (i - (len(seasonal.columns)-1)/2) * width, seasonal[y].values, width=width, label=y)
    ax.set_xticks(x)
    ax.set_title("Mức sản lượng theo tháng trong năm", fontsize=12, fontweight="bold")
    ax.set_xlabel("Tháng")
    ax.set_ylabel("KM")
    ax.legend()
    ax.grid(alpha=0.2, axis="y")
    save_figure(fig, "03_thoi_vu_theo_thang.png")


def product_reports(cable, summary, plt):
    by_family = cable.groupby("nhom_san_pham_don_hang")["so_luong_km"].sum().sort_values(ascending=False)
    cum_pct = (by_family.cumsum() / by_family.sum() * 100)
    abc_family = pd.DataFrame({"km": by_family, "cum_pct": cum_pct})
    abc_family["nhom_abc"] = abc_labels(by_family)
    abc_family.to_csv(TAB / "abc_product_family.csv")
    summary["abc_nhom_san_pham"] = abc_family.reset_index().to_dict("records")

    fig, ax1 = plt.subplots(figsize=(10, 4.5))
    ax1.bar(by_family.index, by_family.values, color=COLOR_MAIN)
    ax1.set_ylabel("KM", color=COLOR_MAIN)
    ax1.set_xticks(range(len(by_family.index)))
    ax1.set_xticklabels(by_family.index, rotation=40, ha="right", fontsize=8)
    ax2 = ax1.twinx()
    ax2.plot(by_family.index, cum_pct.values, color=COLOR_ACC, marker="o", markersize=4)
    ax2.axhline(ABC_LIMITS[0], color="grey", linestyle="--", linewidth=1)
    ax2.set_ylabel("% tích luỹ", color=COLOR_ACC)
    ax2.set_ylim(0, 105)
    ax1.set_title("Phân tích Pareto sản lượng theo nhóm sản phẩm cáp quang", fontsize=12, fontweight="bold")
    save_figure(fig, "04_pareto_nhom_san_pham.png")

    by_code = cable[cable.is_reference_product_code].groupby("canonical_product_code")["so_luong_km"].sum().sort_values(ascending=False).head(15)
    summary["top15_reference_product_codes"] = by_code.round(1).to_dict()


def customer_reports(cable, summary, plt):
    assert cable["ma_khach_nhom"].notna().all(), "ma_khach_nhom không được để trống"

    by_cust = cable.groupby(["ma_khach_nhom", "ten_khach_hang_nhom"])["so_luong_km"].sum().sort_values(ascending=False)
    assert abs(by_cust.sum() - cable["so_luong_km"].sum()) < 1e-6, (
        "Pareto khách hàng bị mất KM sau groupby - kiểm tra lại ma_khach_nhom"
    )
    is_fallback_group = by_cust.index.get_level_values("ma_khach_nhom").str.startswith("SUY_DIEN::")
    n_active_total = by_cust.shape[0]
    n_active_chinh_thuc = int((~is_fallback_group).sum())
    n_active_suy_dien = int(is_fallback_group.sum())
    km_suy_dien_total = float(by_cust[is_fallback_group].sum())

    n_total_registered = pd.read_csv(PROC / "dim_customer.csv").shape[0]
    summary["so_khach_hang_dang_ky"] = int(n_total_registered)
    summary["so_khach_hang_co_ma_chinh_thuc_phat_sinh_don_cap"] = n_active_chinh_thuc
    summary["so_nhom_suy_dien_tu_ma_don_khong_co_ma_khach"] = n_active_suy_dien
    summary["ty_le_khach_hang_active"] = round(n_active_chinh_thuc / n_total_registered, 4)
    summary["km_thuoc_nhom_suy_dien_khong_co_ma_khach"] = round(km_suy_dien_total, 1)
    summary["ty_trong_km_nhom_suy_dien_pct"] = round(km_suy_dien_total / by_cust.sum() * 100, 2)

    cum_pct_cust = (by_cust.cumsum() / by_cust.sum() * 100)
    n_80pct = int((cum_pct_cust < ABC_LIMITS[0]).sum()) + 1
    summary["so_dau_moi_chiem_80pct_san_luong"] = n_80pct
    summary["ty_le_dau_moi_chiem_80pct"] = round(n_80pct / n_active_total, 4)

    top20 = by_cust.head(20)
    top20_is_fallback = is_fallback_group[:20]
    fig, ax = plt.subplots(figsize=(8.5, 6))
    labels = [f"{name}{'  (chưa có mã khách)' if fb else ''}" for (_, name), fb in zip(top20.index, top20_is_fallback)]
    colors = [COLOR_ACC if fb else COLOR_MAIN for fb in top20_is_fallback]
    ax.barh(labels[::-1], top20.values[::-1], color=colors[::-1])
    ax.set_title("20 đầu mối dẫn đầu về sản lượng", fontsize=12, fontweight="bold")
    ax.set_xlabel("KM")
    from matplotlib.patches import Patch
    ax.legend(handles=[Patch(color=COLOR_MAIN, label="Có mã khách chính thức"),
                        Patch(color=COLOR_ACC, label="Suy ra từ mã đơn - chưa có mã khách")],
              loc="lower right", fontsize=8, frameon=False)
    save_figure(fig, "06_top20_khach_hang.png")


def order_reports(cable, header, summary, plt):
    type_counts = header["loai_don"].value_counts()
    fig, ax = plt.subplots(figsize=(8, 5))
    wedges, _, _ = ax.pie(
        type_counts.values, autopct=lambda pct: f"{pct:.1f}%" if pct >= 3 else "",
        colors=plt.cm.Set2.colors, textprops={"fontsize": 9, "color": "white", "fontweight": "bold"},
        pctdistance=0.75,
    )
    ax.legend(wedges, [f"{k} ({v})" for k, v in type_counts.items()],
              loc="center left", bbox_to_anchor=(1.0, 0.5), fontsize=9, frameon=False)
    ax.set_title("Cơ cấu loại đơn hàng", fontsize=12, fontweight="bold")
    save_figure(fig, "08_co_cau_loai_don.png")
    summary["co_cau_loai_don"] = type_counts.to_dict()

    ca_orders = header[header["loai_don"] == "Đơn khách hàng - Cáp quang"]
    wo_rate = ca_orders["wo"].notna().mean()
    summary["ty_le_don_cap_co_wo"] = round(wo_rate, 4)
    wo_by_year = ca_orders.groupby("order_year")["wo"].apply(lambda s: s.notna().mean())
    summary["ty_le_wo_theo_nam"] = wo_by_year.round(4).to_dict()

    ftth = cable[cable["parsed_product_token"].str.startswith("FTTH", na=False)]
    variant = ftth["parsed_product_token"].str.extract(r"-(LT|SQ|UNK)$")[0].fillna("UNK")
    ftth_variant = variant.value_counts()
    summary["ftth_bien_the_so_dong"] = ftth_variant.to_dict()
    ftth_km_variant = ftth.groupby(variant)["so_luong_km"].sum()
    summary["ftth_bien_the_km"] = ftth_km_variant.round(1).to_dict()

    by_order = cable.groupby("order_row_id").agg(
        order_year=("order_year", "first"), km=("so_luong_km", "sum"))
    order_stats = by_order.groupby("order_year")["km"].agg(
        so_don="count", tb_km_don="mean", trung_vi_km="median")
    summary["quy_mo_don_theo_nam"] = order_stats.round(1).reset_index().to_dict("records")

    fig, ax1 = plt.subplots(figsize=(7, 4.5))
    ax1.bar(order_stats.index, order_stats["so_don"], color=COLOR_GREY, alpha=0.6, label="Số đơn có KM")
    ax1.set_ylabel("Số đơn hàng", color=COLOR_GREY)
    ax2 = ax1.twinx()
    ax2.plot(order_stats.index, order_stats["tb_km_don"], color=COLOR_ACC, marker="o", label="KM bình quân/đơn")
    ax2.set_ylabel("KM bình quân / đơn", color=COLOR_ACC)
    ax1.set_title("Số đơn hàng và quy mô bình quân theo năm", fontsize=12, fontweight="bold")
    fig.legend(loc="upper right", bbox_to_anchor=(0.9, 0.88), fontsize=8)
    save_figure(fig, "11_quy_mo_don_theo_nam.png")

    fig, ax = plt.subplots(figsize=(6, 4.2))
    years = list(wo_by_year.index)
    ax.bar(years, wo_by_year.values * 100, color=COLOR_MAIN)
    for i, v in enumerate(wo_by_year.values * 100):
        ax.text(i, v, f"{v:.1f}%", ha="center", va="bottom")
    ax.set_ylabel("% đơn cáp có mã WO")
    ax.set_title("Tỷ lệ đơn hàng cáp quang có mã lệnh sản xuất theo năm",
                 fontsize=11, fontweight="bold")
    ax.set_ylim(0, 100)
    save_figure(fig, "12_ty_le_wo_theo_nam.png")


def main():
    TAB.mkdir(parents=True, exist_ok=True)
    plt = configure_plots()
    df = pd.read_csv(PROC / "mart_order_items.csv")
    header = pd.read_csv(PROC / "fact_order_header.csv")
    df["order_year"] = df["order_month"].astype(str).str.slice(0, 4)
    header["order_year"] = header["order_month"].astype(str).str.slice(0, 4)
    summary = unpriced_metrics(df)

    summary["tong_so_dong_don_hang"] = int(len(header))
    summary["tong_so_dong_san_pham"] = int(len(df))
    summary["ty_le_tach_duoc_so_luong"] = round(df["parsed"].mean(), 4)
    summary["ty_le_co_don_gia_tham_khao"] = round(df["co_don_gia_tham_khao"].mean(), 4)

    sales = df[df["la_don_ban_hang"] == True].copy()
    cable_raw = sales[sales["so_luong_km"].notna()].copy()
    summary["so_dong_ban_hang"] = int(len(sales))
    summary["so_dong_co_km_trong_ban_hang"] = int(len(cable_raw))

    n_outlier_rows = int(cable_raw["nghi_ngo_outlier"].sum())
    outlier_km = float(cable_raw.loc[cable_raw["nghi_ngo_outlier"], "so_luong_km"].sum())
    cable = cable_raw[~cable_raw["nghi_ngo_outlier"]].copy()
    summary["outlier__so_dong"] = n_outlier_rows
    summary["outlier__tong_km"] = round(outlier_km, 1)
    summary["outlier__ty_trong_pct_tren_tong_tho"] = round(
        outlier_km / cable_raw["so_luong_km"].sum() * 100, 2)
    summary["san_luong_km_tong__THO_goc_outlier"] = round(cable_raw["so_luong_km"].sum(), 1)
    summary["san_luong_km_tong__DA_HIEU_CHINH"] = round(cable["so_luong_km"].sum(), 1)

    trend_reports(cable, cable_raw, header, summary, plt)
    products = pd.read_csv(PROC/'mart_product_items.csv')
    product_reports(products[products.la_don_ban_hang & products.so_luong_km.notna() & ~products.nghi_ngo_outlier], summary, plt)
    customer_reports(cable, summary, plt)
    order_reports(cable, header, summary, plt)
    write_json(TAB / 'eda_summary.json', summary)
    print(f'[OK] EDA: {len(header)} orders, {len(cable)} non-outlier sales items')


if __name__ == "__main__":
    main()
