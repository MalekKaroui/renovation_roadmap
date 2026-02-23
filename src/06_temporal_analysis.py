"""
06_temporal_analysis.py — Track investment patterns over time windows
"""
import numpy as np
import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt
import seaborn as sns
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from utils import logger, data_path, save_figure, style_axis

TIME_WINDOWS = [
    (2015, 2016, "2015-16"),
    (2017, 2018, "2017-18"),
    (2019, 2020, "2019-20"),
    (2021, 2022, "2021-22"),
    (2023, 2025, "2023-25"),
]
OUT_CSV = data_path("temporal_analysis.csv")

def load_spatial():
    gdf = gpd.read_file(data_path("permits_spatial.gpkg"))
    return gdf

def compute_windowed_stats(gdf):
    records = []
    for start, end, label in TIME_WINDOWS:
        window = gdf[(gdf["YEAR"] >= start) & (gdf["YEAR"] <= end)]
        window = window[window["GRID_ID"] != "UNKNOWN"]
        
        agg = (
            window.groupby("GRID_ID")
            .agg(
                mean_value = ("BPEVAL", "mean"),
                permit_count = ("BPEVAL", "count"),
            )
            .reset_index()
        )
        agg["window"] = label
        records.append(agg)
    
    df = pd.concat(records, ignore_index=True)
    logger.info(f"Windowed stats: {len(df):,} grid-window pairs")
    return df

def compute_growth_rates(windowed):
    """Calculate CAGR and trajectory labels"""
    pivot = windowed.pivot(index="GRID_ID", columns="window", values="mean_value")
    
    window_labels = [w[2] for w in TIME_WINDOWS]
    first_col = window_labels[0]
    last_col = window_labels[-1]
    
    pivot["CAGR"] = (
        (pivot[last_col] / pivot[first_col].replace(0, np.nan)) ** (1/10) - 1
    )
    
    median_cagr = pivot["CAGR"].median()
    city_first = pivot[first_col].median()
    city_last = pivot[last_col].median()
    
    def label(row):
        cagr = row["CAGR"]
        first = row.get(first_col, 0)
        last = row.get(last_col, 0)
        
        if pd.isna(cagr):
            return "Insufficient Data"
        if first < city_first and last > city_last:
            return "Emerging 🚀"
        if cagr > median_cagr:
            return "Accelerating"
        if cagr < 0:
            return "Declining"
        return "Stable"
    
    pivot["trajectory"] = pivot.apply(label, axis=1)
    logger.info("Trajectory classification:\n" + pivot["trajectory"].value_counts().to_string())
    return pivot

def plot_city_trend(windowed):
    """City-wide aggregate trend"""
    city = windowed.groupby("window")["mean_value"].mean()
    city = city.reindex([w[2] for w in TIME_WINDOWS])
    
    fig, ax = plt.subplots(figsize=(10, 4))
    ax.plot(city.index, city.values / 1000, "o-", color="#1565C0", linewidth=2.5, markersize=7)
    style_axis(ax, "City-wide Mean Permit Value Over Time", "Time Window", "Mean Value ($000 CAD)")
    save_figure(fig, "06_city_trend.png")

def plot_grid_heatmap(windowed, top_n=15):
    """Heatmap of top grid cells over time"""
    pivot = windowed.pivot(index="GRID_ID", columns="window", values="mean_value")
    top = pivot.mean(axis=1).nlargest(top_n).index
    pivot_top = pivot.loc[top]
    
    # Row-normalize
    pivot_norm = pivot_top.apply(lambda row: (row - row.mean()) / (row.std() + 1e-9), axis=1)
    
    fig, ax = plt.subplots(figsize=(10, max(6, top_n * 0.4)))
    sns.heatmap(pivot_norm, ax=ax, cmap="RdYlGn", center=0, linewidths=0.5,
                annot=True, fmt=".1f", cbar_kws={"label": "Normalized Value (z-score)"})
    ax.set_title(f"Permit Value Trends — Top {top_n} Grid Cells", fontsize=12, fontweight="bold")
    save_figure(fig, "06_grid_heatmap.png", dpi=180)

def plot_cagr_histogram(growth):
    """Histogram of CAGR distribution"""
    cagr_clean = growth["CAGR"].dropna()
    
    fig, ax = plt.subplots(figsize=(9, 4))
    ax.hist(cagr_clean * 100, bins=30, color="#43A047", edgecolor="white", alpha=0.8)
    ax.axvline(0, color="black", linewidth=1)
    style_axis(ax, "Grid Cell Investment CAGR Distribution (2015-2025)",
               "CAGR (%)", "Number of Grid Cells")
    save_figure(fig, "06_cagr_distribution.png")

def main():
    logger.info("="*60)
    logger.info("STAGE 6 — Temporal Analysis")
    logger.info("="*60)
    
    gdf = load_spatial()
    windowed = compute_windowed_stats(gdf)
    growth = compute_growth_rates(windowed)
    
    plot_city_trend(windowed)
    plot_grid_heatmap(windowed, top_n=15)
    plot_cagr_histogram(growth)
    
    growth.to_csv(OUT_CSV)
    logger.info(f"Temporal analysis → {OUT_CSV}")
    
    emerging = growth[growth["trajectory"] == "Emerging 🚀"]
    print(f"\n{len(emerging)} EMERGING grid cells (pre-gentrification signal):")
    print(emerging[["CAGR"]].sort_values("CAGR", ascending=False).head(10))

if __name__ == "__main__":
    main()
