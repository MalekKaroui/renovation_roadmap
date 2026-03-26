"""
06_temporal_analysis.py

Track how permit values change over time using multiple time windows.
This stage identifies growth patterns and flags grid cells that appear
to be emerging, accelerating, declining, or stable.
"""

import os
import sys

import geopandas as gpd
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns

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


def load_spatial_permits():
    """
    Load the spatial permit dataset created earlier in the pipeline.
    """
    return gpd.read_file(data_path("permits_spatial.gpkg"))


def compute_windowed_statistics(gdf):
    """
    Aggregate permit statistics for each grid cell within each time window.
    """
    records = []

    for start_year, end_year, label in TIME_WINDOWS:
        window_df = gdf[(gdf["YEAR"] >= start_year) & (gdf["YEAR"] <= end_year)]
        window_df = window_df[window_df["GRID_ID"] != "UNKNOWN"]

        stats = (
            window_df.groupby("GRID_ID")
            .agg(
                mean_value=("BPEVAL", "mean"),
                permit_count=("BPEVAL", "count"),
            )
            .reset_index()
        )

        stats["window"] = label
        records.append(stats)

    windowed_df = pd.concat(records, ignore_index=True)
    logger.info(f"Windowed stats: {len(windowed_df):,} grid-window pairs")

    return windowed_df


def compute_growth_rates(windowed_df):
    """
    Calculate CAGR and assign a simple trajectory label to each grid cell.
    """
    pivot_df = windowed_df.pivot(index="GRID_ID", columns="window", values="mean_value")

    window_labels = [window[2] for window in TIME_WINDOWS]
    first_window = window_labels[0]
    last_window = window_labels[-1]

    pivot_df["CAGR"] = (
        (pivot_df[last_window] / pivot_df[first_window].replace(0, np.nan)) ** (1 / 10) - 1
    )

    median_cagr = pivot_df["CAGR"].median()
    city_first_median = pivot_df[first_window].median()
    city_last_median = pivot_df[last_window].median()

    def classify_trajectory(row):
        cagr = row["CAGR"]
        first_value = row.get(first_window, 0)
        last_value = row.get(last_window, 0)

        if pd.isna(cagr):
            return "Insufficient Data"
        if first_value < city_first_median and last_value > city_last_median:
            return "Emerging"
        if cagr > median_cagr:
            return "Accelerating"
        if cagr < 0:
            return "Declining"
        return "Stable"

    pivot_df["trajectory"] = pivot_df.apply(classify_trajectory, axis=1)

    logger.info(
        "Trajectory classification:\n" +
        pivot_df["trajectory"].value_counts().to_string()
    )

    return pivot_df


def plot_city_trend(windowed_df):
    """
    Plot the city-wide average permit value across time windows.
    """
    city_trend = windowed_df.groupby("window")["mean_value"].mean()
    city_trend = city_trend.reindex([window[2] for window in TIME_WINDOWS])

    fig, ax = plt.subplots(figsize=(10, 4))
    ax.plot(
        city_trend.index,
        city_trend.values / 1000,
        "o-",
        color="#1565C0",
        linewidth=2.5,
        markersize=7
    )

    style_axis(
        ax,
        "City-wide Mean Permit Value Over Time",
        "Time Window",
        "Mean Value ($000 CAD)"
    )

    save_figure(fig, "06_city_trend.png")


def plot_grid_heatmap(windowed_df, top_n=15):
    """
    Plot a heatmap of the highest-value grid cells across time windows.
    """
    pivot_df = windowed_df.pivot(index="GRID_ID", columns="window", values="mean_value")
    top_cells = pivot_df.mean(axis=1).nlargest(top_n).index
    top_df = pivot_df.loc[top_cells]

    normalized_df = top_df.apply(
        lambda row: (row - row.mean()) / (row.std() + 1e-9),
        axis=1
    )

    fig, ax = plt.subplots(figsize=(10, max(6, top_n * 0.4)))
    sns.heatmap(
        normalized_df,
        ax=ax,
        cmap="RdYlGn",
        center=0,
        linewidths=0.5,
        annot=True,
        fmt=".1f",
        cbar_kws={"label": "Normalized Value (z-score)"}
    )

    ax.set_title(
        f"Permit Value Trends — Top {top_n} Grid Cells",
        fontsize=12,
        fontweight="bold"
    )

    save_figure(fig, "06_grid_heatmap.png", dpi=180)


def plot_cagr_distribution(growth_df):
    """
    Plot the distribution of compound annual growth rates.
    """
    cagr_values = growth_df["CAGR"].dropna() * 100

    fig, ax = plt.subplots(figsize=(9, 4))
    ax.hist(cagr_values, bins=30, color="#43A047", edgecolor="white", alpha=0.8)
    ax.axvline(0, color="black", linewidth=1)

    style_axis(
        ax,
        "Grid Cell Investment CAGR Distribution (2015-2025)",
        "CAGR (%)",
        "Number of Grid Cells"
    )

    save_figure(fig, "06_cagr_distribution.png")


def print_emerging_cells(growth_df, top_n=10):
    """
    Print the emerging grid cells with the highest CAGR values.
    """
    emerging_df = growth_df[growth_df["trajectory"] == "Emerging"]

    print(f"\n{len(emerging_df)} EMERGING grid cells (pre-gentrification signal):")
    print(
        emerging_df[["CAGR"]]
        .sort_values("CAGR", ascending=False)
        .head(top_n)
        .to_string()
    )


def main():
    logger.info("=" * 60)
    logger.info("STAGE 6 — Temporal Analysis")
    logger.info("=" * 60)

    permits_gdf = load_spatial_permits()

    windowed_df = compute_windowed_statistics(permits_gdf)
    growth_df = compute_growth_rates(windowed_df)

    plot_city_trend(windowed_df)
    plot_grid_heatmap(windowed_df, top_n=15)
    plot_cagr_distribution(growth_df)

    growth_df.to_csv(OUT_CSV)
    logger.info(f"Temporal analysis → {OUT_CSV}")

    print_emerging_cells(growth_df)


if __name__ == "__main__":
    main()