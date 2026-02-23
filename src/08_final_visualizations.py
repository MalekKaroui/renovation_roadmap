"""
08_final_visualizations.py — Summary dashboard & integrated map
"""
import numpy as np
import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import matplotlib.patches as mpatches
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from utils import logger, data_path, save_figure, style_axis

def load_all_results():
    results = {}
    paths = {
        "grid_stats": data_path("grid_stats.csv"),
        "kmeans_stats": data_path("kmeans_stats.csv"),
        "dbscan_stats": data_path("dbscan_stats.csv"),
        "getis_ord": data_path("getis_ord_results.csv"),
        "temporal": data_path("temporal_analysis.csv"),
        "assessment": data_path("assessment_integration.csv"),
    }
    for key, path in paths.items():
        if os.path.exists(path):
            results[key] = pd.read_csv(path)
            logger.info(f"Loaded {key}")
        else:
            results[key] = pd.DataFrame()
    return results

def plot_dashboard(results):
    """4-panel summary dashboard"""
    fig = plt.figure(figsize=(16, 12))
    gs = gridspec.GridSpec(2, 2, figure=fig, hspace=0.4, wspace=0.35)
    
    ax_A = fig.add_subplot(gs[0, 0])
    ax_B = fig.add_subplot(gs[0, 1])
    ax_C = fig.add_subplot(gs[1, 0])
    ax_D = fig.add_subplot(gs[1, 1])
    
    # Panel A: Permit count by year (reconstruct from grid stats)
    grid_stats = results["grid_stats"]
    if not grid_stats.empty:
        total = grid_stats["permit_count"].sum()
        ax_A.text(0.5, 0.5, f"Total Permits\n{total:,}", ha="center", va="center",
                  fontsize=28, fontweight="bold")
        ax_A.axis("off")
        ax_A.set_title("A: Total Building Permits (2015-2025)", fontsize=13, fontweight="bold")
    
    # Panel B: K-Means cluster sizes
    km = results["kmeans_stats"]
    if not km.empty:
        ax_B.bar(range(len(km)), km["n_permits"], color=plt.cm.tab10(np.linspace(0, 1, len(km))))
        style_axis(ax_B, "B: K-Means Cluster Sizes", "Cluster", "Permits")
    
    # Panel C: Hotspot counts
    gi = results["getis_ord"]
    if not gi.empty and "hotspot" in gi.columns:
        counts = gi["hotspot"].value_counts()
        ax_C.barh(counts.index, counts.values, color=["#BD0026", "#9E9E9E", "#2B8CBE"])
        style_axis(ax_C, "C: Hotspot Classification Counts", "Count", "")
    
    # Panel D: Top IAR grid cells
    assess = results["assessment"]
    if not assess.empty and "IAR" in assess.columns:
        top = assess.nlargest(10, "IAR")
        ax_D.barh(range(len(top)), top["IAR"], color="#E53935")
        ax_D.set_yticks(range(len(top)))
        ax_D.set_yticklabels(top["GRID_ID"], fontsize=8)
        style_axis(ax_D, "D: Top 10 Grid Cells by IAR", "IAR", "")
    
    fig.suptitle("The Renovation Roadmap — Summary Dashboard\nSaint John, NB (2015-2025)",
                 fontsize=15, fontweight="bold", y=1.01)
    save_figure(fig, "08_dashboard.png", dpi=200)

def plot_integrated_map(results):
    """Single map with IAR + hotspot overlay"""
    grid = gpd.read_file(data_path("spatial_grid.gpkg"))
    
    merged = grid.copy()
    for key, col in [("assessment", "IAR"), ("getis_ord", "Gi_star")]:
        df = results[key]
        if not df.empty and col in df.columns:
            merged = merged.merge(df[["GRID_ID", col]], on="GRID_ID", how="left")
    
    fig, ax = plt.subplots(figsize=(14, 12))
    
    if "IAR" in merged.columns:
        merged.plot(column="IAR", ax=ax, cmap="YlOrRd", edgecolor="#CCCCCC",
                    linewidth=0.3, legend=True, alpha=0.8,
                    legend_kwds={"label": "IAR", "shrink": 0.5})
    
    if "Gi_star" in merged.columns:
        hot = merged[merged["Gi_star"] > 1.96]
        if len(hot):
            hot.boundary.plot(ax=ax, color="#BD0026", linewidth=2, label="Hot Spot")
    
    ax.set_title("Integrated Investment Map\nIAR (background) + Hotspots (outline)",
                 fontsize=13, fontweight="bold")
    ax.set_axis_off()
    save_figure(fig, "08_integrated_map.png", dpi=220)

def print_summary(results):
    print("\n" + "="*65)
    print("  RENOVATION ROADMAP — FINAL FINDINGS")
    print("  Saint John, NB  |  2015-2025")
    print("="*65)
    
    assess = results["assessment"]
    if not assess.empty and "signal" in assess.columns:
        pregen = assess[assess["signal"] == "⚠️ Pre-Gentrification Signal"]
        print(f"\n⚠️  Pre-Gentrification Cells: {len(pregen)}")
    
    gi = results["getis_ord"]
    if not gi.empty and "hotspot" in gi.columns:
        hot = gi[gi["hotspot"].str.startswith("Hot", na=False)]
        print(f"🔴 Hot Spots: {len(hot)}")
    
    print("="*65 + "\n")

def main():
    logger.info("="*60)
    logger.info("STAGE 8 — Final Visualizations")
    logger.info("="*60)
    
    results = load_all_results()
    plot_dashboard(results)
    plot_integrated_map(results)
    print_summary(results)

if __name__ == "__main__":
    main()
