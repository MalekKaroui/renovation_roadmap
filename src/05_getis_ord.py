"""
05_getis_ord.py

Run Getis-Ord Gi* hotspot analysis on grid-level permit data.
The analysis is done at the grid-cell level rather than using
neighborhood boundaries.
"""

import os
import sys

import geopandas as gpd
import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(__file__))

from utils import logger, data_path, save_figure, style_axis


try:
    from libpysal.weights import Queen
    from esda.getisord import G_Local
    PYSAL_OK = True
except ImportError:
    PYSAL_OK = False
    logger.warning("PySAL not available — using manual implementation instead.")


OUT_CSV = data_path("getis_ord_results.csv")
DISTANCE_BAND_METERS = 3000


def load_grid_data():
    """
    Load the spatial grid and merge it with aggregated permit statistics.
    """
    grid_gdf = gpd.read_file(data_path("spatial_grid.gpkg"))
    stats_df = pd.read_csv(data_path("grid_stats.csv"))

    merged_gdf = grid_gdf.merge(stats_df, on="GRID_ID", how="inner")
    logger.info(f"Grid layer: {len(merged_gdf)} cells with data")

    return merged_gdf


def classify_hotspots(z_scores, p_values):
    """
    Classify each grid cell based on z-score and p-value.
    """
    labels = []

    for z_score, p_value in zip(z_scores, p_values):
        if z_score > 2.576 and p_value < 0.01:
            labels.append("Hot Spot (99%)")
        elif z_score > 1.960 and p_value < 0.05:
            labels.append("Hot Spot (95%)")
        elif z_score < -2.576 and p_value < 0.01:
            labels.append("Cold Spot (99%)")
        elif z_score < -1.960 and p_value < 0.05:
            labels.append("Cold Spot (95%)")
        else:
            labels.append("Not Significant")

    return labels


def run_getis_ord_with_pysal(gdf):
    """
    Run Getis-Ord Gi* using PySAL.
    """
    weights = Queen.from_dataframe(gdf, silence_warnings=True)
    weights.transform = "R"

    values = gdf["mean_value"].values
    local_g = G_Local(values, weights, transform="R", star=True, permutations=999)

    result_gdf = gdf.copy()
    result_gdf["Gi_star"] = local_g.Zs
    result_gdf["p_value"] = local_g.p_sim
    result_gdf["hotspot"] = classify_hotspots(local_g.Zs, local_g.p_sim)

    return result_gdf


def run_getis_ord_manually(gdf):
    """
    Run a simplified manual Getis-Ord style analysis using a fixed
    distance band and normal-approximation p-values.
    """
    from scipy.spatial.distance import cdist
    from scipy.stats import norm

    centroids = np.array([(geom.centroid.x, geom.centroid.y) for geom in gdf.geometry])
    distance_matrix = cdist(centroids, centroids)

    weights = (distance_matrix <= DISTANCE_BAND_METERS).astype(float)
    np.fill_diagonal(weights, 0)

    values = gdf["mean_value"].values
    n = len(values)
    mean_value = values.mean()
    std_value = np.sqrt(((values - mean_value) ** 2).sum() / n)

    gi_scores = np.zeros(n)

    for i in range(n):
        local_weights = weights[i]
        sum_w = local_weights.sum()
        sum_w2 = (local_weights ** 2).sum()

        numerator = (local_weights * values).sum() - mean_value * sum_w
        denominator = std_value * np.sqrt((n * sum_w2 - sum_w ** 2) / (n - 1))

        gi_scores[i] = numerator / denominator if denominator != 0 else 0.0

    p_values = 2 * (1 - norm.cdf(np.abs(gi_scores)))

    result_gdf = gdf.copy()
    result_gdf["Gi_star"] = gi_scores
    result_gdf["p_value"] = p_values
    result_gdf["hotspot"] = classify_hotspots(gi_scores, p_values)

    return result_gdf


def plot_hotspot_map(gdf):
    """
    Plot hotspot classifications as a choropleth map.
    """
    color_map = {
        "Hot Spot (99%)": "#BD0026",
        "Hot Spot (95%)": "#F03B20",
        "Not Significant": "#FFFFCC",
        "Cold Spot (95%)": "#2B8CBE",
        "Cold Spot (99%)": "#045A8D",
    }

    plot_gdf = gdf.copy()
    plot_gdf["color"] = plot_gdf["hotspot"].map(color_map).fillna("#CCCCCC")

    fig, ax = plt.subplots(figsize=(13, 11))
    plot_gdf.plot(color=plot_gdf["color"], edgecolor="white", linewidth=0.3, ax=ax)

    legend_patches = [mpatches.Patch(color=color, label=label)
                      for label, color in color_map.items()]
    ax.legend(handles=legend_patches, loc="lower right", title="Getis-Ord Gi*")

    ax.set_title(
        "Getis-Ord Hotspot Analysis\nMean Permit Value — Saint John, NB",
        fontsize=13,
        fontweight="bold"
    )
    ax.set_axis_off()

    save_figure(fig, "05_hotspot_map.png", dpi=200)


def plot_gi_distribution(gdf):
    """
    Plot the distribution of Gi* z-scores.
    """
    fig, ax = plt.subplots(figsize=(9, 4))

    ax.hist(gdf["Gi_star"], bins=30, color="#78909C", edgecolor="white", alpha=0.8)
    ax.axvline(1.96, color="#F03B20", linestyle="--", label="p < 0.05")
    ax.axvline(-1.96, color="#2B8CBE", linestyle="--")

    style_axis(ax, "Distribution of Gi* Z-Scores", "Gi* Z-Score", "Count")
    ax.legend()

    save_figure(fig, "05_gi_distribution.png")


def print_hotspot_summary(gdf):
    """
    Print hotspot classification counts and significant hot spots.
    """
    counts = gdf["hotspot"].value_counts()

    print("\nHotspot Classification:")
    print(counts.to_string())

    hot_spots = gdf[gdf["hotspot"].str.startswith("Hot", na=False)]

    print(f"\n{len(hot_spots)} statistically significant HOT SPOTS:")
    print(
        hot_spots[["GRID_ID", "Gi_star", "p_value", "mean_value"]]
        .sort_values("Gi_star", ascending=False)
        .to_string(index=False)
    )


def save_results(gdf):
    """
    Save the main hotspot results to CSV.
    """
    result_columns = [
        "GRID_ID",
        "mean_value",
        "permit_count",
        "Gi_star",
        "p_value",
        "hotspot"
    ]

    gdf[result_columns].to_csv(OUT_CSV, index=False)
    logger.info(f"Hotspot results → {OUT_CSV}")


def main():
    logger.info("=" * 60)
    logger.info("STAGE 5 — Getis-Ord Hotspot Analysis")
    logger.info("=" * 60)

    grid_gdf = load_grid_data()

    if PYSAL_OK:
        result_gdf = run_getis_ord_with_pysal(grid_gdf)
    else:
        result_gdf = run_getis_ord_manually(grid_gdf)

    print_hotspot_summary(result_gdf)

    plot_hotspot_map(result_gdf)
    plot_gi_distribution(result_gdf)
    save_results(result_gdf)


if __name__ == "__main__":
    main()