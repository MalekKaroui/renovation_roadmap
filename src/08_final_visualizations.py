"""
08_final_visualizations.py

Create the final summary figures for the project, including:
- a four-panel dashboard
- an integrated map combining IAR and hotspot results
"""

import os
import sys

import geopandas as gpd
import matplotlib.gridspec as gridspec
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(__file__))

from utils import logger, data_path, save_figure, style_axis


RESULT_PATHS = {
    "grid_stats": data_path("grid_stats.csv"),
    "kmeans_stats": data_path("kmeans_stats.csv"),
    "dbscan_stats": data_path("dbscan_stats.csv"),
    "getis_ord": data_path("getis_ord_results.csv"),
    "temporal": data_path("temporal_analysis.csv"),
    "assessment": data_path("assessment_integration.csv"),
}

GRID_PATH = data_path("spatial_grid.gpkg")
PRE_GENTRIFICATION_LABEL = "Pre-Gentrification Signal"


def load_all_results():
    """
    Load all result files needed for the final summary figures.
    Missing files are replaced with empty DataFrames.
    """
    results = {}

    for key, path in RESULT_PATHS.items():
        if os.path.exists(path):
            results[key] = pd.read_csv(path)
            logger.info(f"Loaded {key}")
        else:
            results[key] = pd.DataFrame()

    return results


def plot_summary_dashboard(results):
    """
    Create a four-panel summary dashboard for the final report.
    """
    fig = plt.figure(figsize=(16, 12))
    grid_spec = gridspec.GridSpec(2, 2, figure=fig, hspace=0.4, wspace=0.35)

    ax_a = fig.add_subplot(grid_spec[0, 0])
    ax_b = fig.add_subplot(grid_spec[0, 1])
    ax_c = fig.add_subplot(grid_spec[1, 0])
    ax_d = fig.add_subplot(grid_spec[1, 1])

    grid_stats_df = results["grid_stats"]
    if not grid_stats_df.empty:
        total_permits = grid_stats_df["permit_count"].sum()
        ax_a.text(
            0.5,
            0.5,
            f"Total Permits\n{total_permits:,}",
            ha="center",
            va="center",
            fontsize=28,
            fontweight="bold"
        )
        ax_a.axis("off")
        ax_a.set_title(
            "A: Total Building Permits (2015–2025)",
            fontsize=13,
            fontweight="bold"
        )

    kmeans_df = results["kmeans_stats"]
    if not kmeans_df.empty:
        ax_b.bar(
            range(len(kmeans_df)),
            kmeans_df["n_permits"],
            color=plt.cm.tab10(np.linspace(0, 1, len(kmeans_df)))
        )
        style_axis(ax_b, "B: K-Means Cluster Sizes", "Cluster", "Permits")

    hotspot_df = results["getis_ord"]
    if not hotspot_df.empty and "hotspot" in hotspot_df.columns:
        counts = hotspot_df["hotspot"].value_counts()

        color_lookup = {
            "Hot Spot (99%)": "#BD0026",
            "Hot Spot (95%)": "#F03B20",
            "Not Significant": "#9E9E9E",
            "Cold Spot (95%)": "#2B8CBE",
            "Cold Spot (99%)": "#045A8D",
        }

        bar_colors = [color_lookup.get(label, "#BDBDBD") for label in counts.index]
        ax_c.barh(counts.index, counts.values, color=bar_colors)
        style_axis(ax_c, "C: Hotspot Classification Counts", "Count", "")

    assessment_df = results["assessment"]
    if not assessment_df.empty and "IAR" in assessment_df.columns:
        top_iar = assessment_df.nlargest(10, "IAR")

        ax_d.barh(range(len(top_iar)), top_iar["IAR"], color="#E53935")
        ax_d.set_yticks(range(len(top_iar)))
        ax_d.set_yticklabels(top_iar["GRID_ID"], fontsize=8)

        style_axis(ax_d, "D: Top 10 Grid Cells by IAR", "IAR", "")

    fig.suptitle(
        "The Renovation Roadmap — Summary Dashboard\nSaint John, NB (2015–2025)",
        fontsize=15,
        fontweight="bold",
        y=1.01
    )

    save_figure(fig, "08_dashboard.png", dpi=200)


def plot_integrated_map(results):
    """
    Create a final map showing IAR as the background and
    significant hotspots as an overlay.
    """
    grid_gdf = gpd.read_file(GRID_PATH)
    merged_gdf = grid_gdf.copy()

    for result_key, column_name in [("assessment", "IAR"), ("getis_ord", "Gi_star")]:
        df = results[result_key]
        if not df.empty and column_name in df.columns:
            merged_gdf = merged_gdf.merge(
                df[["GRID_ID", column_name]],
                on="GRID_ID",
                how="left"
            )

    fig, ax = plt.subplots(figsize=(14, 12))

    if "IAR" in merged_gdf.columns:
        merged_gdf.plot(
            column="IAR",
            ax=ax,
            cmap="YlOrRd",
            edgecolor="#CCCCCC",
            linewidth=0.3,
            legend=True,
            alpha=0.8,
            legend_kwds={"label": "IAR", "shrink": 0.5}
        )

    if "Gi_star" in merged_gdf.columns:
        hot_spots = merged_gdf[merged_gdf["Gi_star"] > 1.96]
        if len(hot_spots) > 0:
            hot_spots.boundary.plot(
                ax=ax,
                color="#BD0026",
                linewidth=2,
                label="Hot Spot"
            )

    ax.set_title(
        "Integrated Investment Map\nIAR (background) + Hotspots (outline)",
        fontsize=13,
        fontweight="bold"
    )
    ax.set_axis_off()

    save_figure(fig, "08_integrated_map.png", dpi=220)


def print_final_summary(results):
    """
    Print a short summary of the final project findings.
    """
    print("\n" + "=" * 65)
    print("  RENOVATION ROADMAP — FINAL FINDINGS")
    print("  Saint John, NB  |  2015-2025")
    print("=" * 65)

    assessment_df = results["assessment"]
    if not assessment_df.empty and "signal" in assessment_df.columns:
        pregen_df = assessment_df[
            assessment_df["signal"] == PRE_GENTRIFICATION_LABEL
        ]
        print(f"\nPre-Gentrification Cells: {len(pregen_df)}")

    hotspot_df = results["getis_ord"]
    if not hotspot_df.empty and "hotspot" in hotspot_df.columns:
        hot_spots = hotspot_df[hotspot_df["hotspot"].str.startswith("Hot", na=False)]
        print(f"Hot Spots: {len(hot_spots)}")

    print("=" * 65 + "\n")


def main():
    logger.info("=" * 60)
    logger.info("STAGE 8 — Final Visualizations")
    logger.info("=" * 60)

    results = load_all_results()

    plot_summary_dashboard(results)
    plot_integrated_map(results)
    print_final_summary(results)


if __name__ == "__main__":
    main()