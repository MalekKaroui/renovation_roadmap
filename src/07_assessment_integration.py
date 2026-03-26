"""
07_assessment_integration.py

Integrate property assessment data with the permit grid and calculate
the Investment-Assessment Ratio (IAR) for each grid cell.
"""

import os
import sys

import geopandas as gpd
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(__file__))

from utils import logger, data_path, save_figure, style_axis


ASSESSMENT_GEOJSON = data_path("Property_Assessments.geojson")
GRID_PATH = data_path("spatial_grid.gpkg")
GRID_STATS_CSV = data_path("grid_stats.csv")
OUT_CSV = data_path("assessment_integration.csv")

TARGET_CRS = "EPSG:32620"

PRE_GENTRIFICATION_LABEL = "Pre-Gentrification Signal"
HIGH_INVESTMENT_LABEL = "High Investment"
LOW_BASE_VALUE_LABEL = "Low Base Value"
STABLE_LABEL = "Stable"


def load_assessment_data():
    """
    Load and clean the property assessment GeoJSON.
    """
    gdf = gpd.read_file(ASSESSMENT_GEOJSON)
    logger.info(f"Loaded {len(gdf):,} property assessments")

    gdf = gdf.to_crs(TARGET_CRS)
    gdf["CURR_ASSMT"] = pd.to_numeric(gdf["CURR_ASSMT"], errors="coerce")

    gdf = gdf.dropna(subset=["CURR_ASSMT"]).copy()
    gdf = gdf[gdf["CURR_ASSMT"] > 0].copy()

    logger.info(f"Valid assessments: {len(gdf):,}")
    return gdf


def aggregate_assessments_to_grid(assessment_gdf):
    """
    Spatially join property assessments to the project grid and
    aggregate mean assessment values by grid cell.
    """
    grid_gdf = gpd.read_file(GRID_PATH)

    joined = gpd.sjoin(assessment_gdf, grid_gdf, how="left", predicate="within")
    joined["GRID_ID"] = joined["GRID_ID"].fillna("UNKNOWN")

    aggregated = (
        joined[joined["GRID_ID"] != "UNKNOWN"]
        .groupby("GRID_ID")["CURR_ASSMT"]
        .agg(
            mean_assessment="mean",
            n_properties="count",
        )
        .reset_index()
    )

    logger.info(f"Assessment aggregation: {len(aggregated)} grid cells")
    return aggregated


def compute_iar(grid_stats_df, assessment_stats_df):
    """
    Merge permit statistics with assessment statistics and calculate IAR.
    """
    merged_df = grid_stats_df.merge(assessment_stats_df, on="GRID_ID", how="inner")

    merged_df["IAR"] = merged_df["mean_value"] / merged_df["mean_assessment"]

    iar_threshold = merged_df["IAR"].quantile(0.75)
    assessment_threshold = merged_df["mean_assessment"].quantile(0.25)

    def classify_signal(row):
        if row["IAR"] >= iar_threshold and row["mean_assessment"] <= assessment_threshold:
            return PRE_GENTRIFICATION_LABEL
        if row["IAR"] >= iar_threshold:
            return HIGH_INVESTMENT_LABEL
        if row["mean_assessment"] <= assessment_threshold:
            return LOW_BASE_VALUE_LABEL
        return STABLE_LABEL

    merged_df["signal"] = merged_df.apply(classify_signal, axis=1)

    signal_count = (merged_df["signal"] == PRE_GENTRIFICATION_LABEL).sum()
    logger.info(f"Pre-gentrification signal: {signal_count} grid cells")

    return merged_df


def plot_investment_vs_assessment(merged_df):
    """
    Plot permit investment against average assessed property value.
    """
    color_map = {
        PRE_GENTRIFICATION_LABEL: "#E53935",
        HIGH_INVESTMENT_LABEL: "#43A047",
        LOW_BASE_VALUE_LABEL: "#1E88E5",
        STABLE_LABEL: "#9E9E9E",
    }

    fig, ax = plt.subplots(figsize=(11, 8))

    for signal_label, color in color_map.items():
        subset = merged_df[merged_df["signal"] == signal_label]

        ax.scatter(
            subset["mean_value"] / 1000,
            subset["mean_assessment"] / 1000,
            c=color,
            s=60,
            alpha=0.7,
            label=f"{signal_label} (n={len(subset)})"
        )

    ax.axvline(
        merged_df["mean_value"].median() / 1000,
        color="grey",
        linestyle="--",
        alpha=0.5
    )
    ax.axhline(
        merged_df["mean_assessment"].median() / 1000,
        color="grey",
        linestyle="--",
        alpha=0.5
    )

    style_axis(
        ax,
        "Investment vs Assessed Property Value\nby Grid Cell (Saint John 2015–2025)",
        "Mean Permit Value ($000 CAD)",
        "Mean Assessed Value ($000 CAD)"
    )
    ax.legend(loc="lower right", fontsize=9)

    save_figure(fig, "07_investment_vs_assessment.png")


def plot_iar_map(merged_df):
    """
    Plot a choropleth map of IAR values by grid cell.
    """
    grid_gdf = gpd.read_file(GRID_PATH)
    plot_gdf = grid_gdf.merge(merged_df[["GRID_ID", "IAR"]], on="GRID_ID", how="left")

    fig, ax = plt.subplots(figsize=(13, 11))
    plot_gdf.plot(
        column="IAR",
        ax=ax,
        cmap="hot_r",
        edgecolor="white",
        linewidth=0.3,
        legend=True,
        legend_kwds={"label": "IAR", "shrink": 0.6},
        missing_kwds={"color": "lightgrey"}
    )

    ax.set_title(
        "Investment–Assessment Ratio (IAR)\nSaint John Grid Cells",
        fontsize=13,
        fontweight="bold"
    )
    ax.set_axis_off()

    save_figure(fig, "07_iar_map.png", dpi=200)


def print_top_signals(merged_df, top_n=10):
    """
    Print the strongest pre-gentrification signal cells.
    """
    signal_df = merged_df[merged_df["signal"] == PRE_GENTRIFICATION_LABEL]

    print(f"\n{len(signal_df)} PRE-GENTRIFICATION SIGNAL grid cells:")
    print(
        signal_df[["GRID_ID", "IAR", "mean_value", "mean_assessment"]]
        .sort_values("IAR", ascending=False)
        .head(top_n)
        .to_string(index=False)
    )


def main():
    logger.info("=" * 60)
    logger.info("STAGE 7 — Assessment Integration")
    logger.info("=" * 60)

    assessment_gdf = load_assessment_data()
    assessment_stats_df = aggregate_assessments_to_grid(assessment_gdf)

    grid_stats_df = pd.read_csv(GRID_STATS_CSV)
    merged_df = compute_iar(grid_stats_df, assessment_stats_df)

    plot_investment_vs_assessment(merged_df)
    plot_iar_map(merged_df)

    merged_df.to_csv(OUT_CSV, index=False)
    logger.info(f"Assessment integration → {OUT_CSV}")

    print_top_signals(merged_df)


if __name__ == "__main__":
    main()