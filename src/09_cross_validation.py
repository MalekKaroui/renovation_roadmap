"""
09_cross_validation.py

Run additional validation across the main project outputs.
This script compares which grid cells are flagged by different methods
and summarizes how much agreement exists between them.
"""

import os
import sys

import geopandas as gpd
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from matplotlib_venn import venn3

sys.path.insert(0, os.path.dirname(__file__))

from utils import logger, data_path, save_figure


RESULT_FILES = {
    "getis_ord": data_path("getis_ord_results.csv"),
    "assessment": data_path("assessment_integration.csv"),
    "temporal": data_path("temporal_analysis.csv"),
    "grid_stats": data_path("grid_stats.csv"),
}

GRID_PATH = data_path("spatial_grid.gpkg")
OUT_CSV = data_path("cross_validation.csv")

PRE_GENTRIFICATION_LABEL = "Pre-Gentrification Signal"
EMERGING_LABEL = "Emerging"


def load_all_results():
    """
    Load the result files needed for cross-validation.
    """
    results = {
        "getis_ord": pd.read_csv(RESULT_FILES["getis_ord"]),
        "assessment": pd.read_csv(RESULT_FILES["assessment"]),
        "temporal": pd.read_csv(RESULT_FILES["temporal"]),
        "grid_stats": pd.read_csv(RESULT_FILES["grid_stats"]),
    }

    logger.info("Loaded all result files")
    return results


def identify_key_zones(results):
    """
    Identify sets of grid cells flagged by each method.
    """
    hotspot_cells = set(
        results["getis_ord"][
            results["getis_ord"]["hotspot"].str.startswith("Hot", na=False)
        ]["GRID_ID"]
    )

    high_iar_cells = set(
        results["assessment"][
            results["assessment"]["signal"] == PRE_GENTRIFICATION_LABEL
        ]["GRID_ID"]
    )

    emerging_cells = set(
        results["temporal"][
            results["temporal"]["trajectory"] == EMERGING_LABEL
        ].index
    )

    density_threshold = results["grid_stats"]["permit_count"].quantile(0.75)
    high_density_cells = set(
        results["grid_stats"][
            results["grid_stats"]["permit_count"] >= density_threshold
        ]["GRID_ID"]
    )

    logger.info(f"Hotspots (Getis-Ord): {len(hotspot_cells)}")
    logger.info(f"High IAR cells: {len(high_iar_cells)}")
    logger.info(f"Emerging trajectories: {len(emerging_cells)}")
    logger.info(f"High density cells: {len(high_density_cells)}")

    return hotspot_cells, high_iar_cells, emerging_cells, high_density_cells


def compute_overlap_matrix(zone_sets):
    """
    Compute pairwise overlap counts between all methods.
    """
    method_names = list(zone_sets.keys())
    n_methods = len(method_names)

    overlap = np.zeros((n_methods, n_methods), dtype=int)

    for i, method_a in enumerate(method_names):
        for j, method_b in enumerate(method_names):
            overlap[i, j] = len(zone_sets[method_a] & zone_sets[method_b])

    return pd.DataFrame(overlap, index=method_names, columns=method_names)


def plot_overlap_heatmap(overlap_df):
    """
    Plot a heatmap showing overlap between methods.
    """
    fig, ax = plt.subplots(figsize=(8, 7))

    sns.heatmap(
        overlap_df,
        annot=True,
        fmt="d",
        cmap="YlOrRd",
        cbar_kws={"label": "Number of Overlapping Grid Cells"},
        linewidths=0.5,
        ax=ax
    )

    ax.set_title(
        "Cross-Method Validation Matrix\nAgreement Between Detection Methods",
        fontsize=13,
        fontweight="bold",
        pad=15
    )

    save_figure(fig, "09_overlap_heatmap.png")


def plot_venn_diagram(hotspot_cells, high_iar_cells, high_density_cells):
    """
    Plot a Venn diagram for three of the main detection methods.
    """
    fig, ax = plt.subplots(figsize=(10, 8))

    venn = venn3(
        [hotspot_cells, high_iar_cells, high_density_cells],
        set_labels=(
            "Getis-Ord\nHotspots",
            "High IAR\n(Pre-Gentrification)",
            "High Permit\nDensity",
        ),
        ax=ax
    )

    if venn.get_patch_by_id("100"):
        venn.get_patch_by_id("100").set_color("#BD0026")
        venn.get_patch_by_id("100").set_alpha(0.5)

    if venn.get_patch_by_id("010"):
        venn.get_patch_by_id("010").set_color("#E53935")
        venn.get_patch_by_id("010").set_alpha(0.5)

    if venn.get_patch_by_id("001"):
        venn.get_patch_by_id("001").set_color("#FD8D3C")
        venn.get_patch_by_id("001").set_alpha(0.5)

    ax.set_title(
        "Zone Detection Method Overlap\nCross-Validation of Spatial Signals",
        fontsize=13,
        fontweight="bold",
        pad=15
    )

    save_figure(fig, "09_venn_diagram.png")


def compute_validation_strength(zone_sets):
    """
    Count how many methods flagged each grid cell.
    """
    all_cells = set.union(*zone_sets.values())

    validation_counts = {}
    for cell in all_cells:
        count = sum(1 for zone_set in zone_sets.values() if cell in zone_set)
        validation_counts[cell] = count

    return validation_counts


def print_validation_summary(validation_counts):
    """
    Print a summary of how many cells were flagged by multiple methods.
    """
    strong_cells = {cell: count for cell, count in validation_counts.items() if count >= 2}

    print("\n" + "=" * 60)
    print("CROSS-VALIDATION RESULTS")
    print("=" * 60)
    print(f"Total unique zones detected: {len(validation_counts)}")
    print(f"Zones validated by 2+ methods: {len(strong_cells)}")
    print(f"Zones validated by 3+ methods: {sum(1 for count in strong_cells.values() if count >= 3)}")

    print("\nStrongest validated zones (3+ methods):")
    for cell, count in sorted(strong_cells.items(), key=lambda item: item[1], reverse=True):
        if count >= 3:
            print(f"  {cell}: validated by {count} methods")


def plot_validation_strength_map(validation_counts):
    """
    Plot how many methods flagged each grid cell.
    """
    grid_gdf = gpd.read_file(GRID_PATH)
    grid_gdf["validation_count"] = grid_gdf["GRID_ID"].map(validation_counts).fillna(0)

    fig, ax = plt.subplots(figsize=(13, 11))

    grid_gdf.plot(
        column="validation_count",
        ax=ax,
        cmap="RdYlGn_r",
        edgecolor="white",
        linewidth=0.3,
        legend=True,
        legend_kwds={
            "label": "Number of Methods Flagging This Cell",
            "shrink": 0.6,
            "ticks": [0, 1, 2, 3, 4],
        },
        vmin=0,
        vmax=4
    )

    ax.set_title(
        "Cross-Validation Strength Map\nGrid Cells Flagged by Multiple Methods",
        fontsize=13,
        fontweight="bold"
    )
    ax.set_axis_off()

    save_figure(fig, "09_validation_strength_map.png", dpi=200)


def print_interpretation(zone_sets):
    """
    Print a short interpretation of the method overlap.
    """
    hotspot_cells = zone_sets["Getis-Ord Hotspots"]
    high_iar_cells = zone_sets["High IAR"]
    emerging_cells = zone_sets["Emerging"]
    high_density_cells = zone_sets["High Density"]

    hotspot_iar_overlap = len(hotspot_cells & high_iar_cells)
    hotspot_density_overlap = len(hotspot_cells & high_density_cells)
    iar_emerging_overlap = len(high_iar_cells & emerging_cells)

    print("\n" + "=" * 60)
    print("KEY FINDINGS — METHOD AGREEMENT")
    print("=" * 60)

    print("\n1. Getis-Ord Hotspots vs High-IAR Cells:")
    print(f"   Overlap: {hotspot_iar_overlap} cells")
    if hotspot_iar_overlap == 0:
        print("   Interpretation: these methods are picking up different signals.")
        print("   - Hotspots capture clustering of already-high values")
        print("   - High IAR captures investment moving into undervalued areas")

    print("\n2. High-IAR Cells vs Emerging Cells:")
    print(f"   Overlap: {iar_emerging_overlap} cells")
    if iar_emerging_overlap > 0:
        print("   This suggests some high-IAR cells are also changing quickly over time.")

    print("\n3. Hotspots vs High-Density Cells:")
    print(f"   Overlap: {hotspot_density_overlap} cells")
    print("   This is expected, since areas with many permits are more likely to cluster.")


def save_validation_results(validation_counts):
    """
    Save validation counts to CSV.
    """
    validation_df = pd.DataFrame(
        list(validation_counts.items()),
        columns=["GRID_ID", "validation_count"]
    )

    validation_df.to_csv(OUT_CSV, index=False)
    logger.info("Cross-validation results saved")


def main():
    logger.info("=" * 60)
    logger.info("ADDITIONAL VALIDATION — Cross-Method Comparison")
    logger.info("=" * 60)

    results = load_all_results()

    hotspot_cells, high_iar_cells, emerging_cells, high_density_cells = identify_key_zones(results)

    zone_sets = {
        "Getis-Ord Hotspots": hotspot_cells,
        "High IAR": high_iar_cells,
        "Emerging": emerging_cells,
        "High Density": high_density_cells,
    }

    overlap_df = compute_overlap_matrix(zone_sets)

    print("\nOverlap Matrix:")
    print(overlap_df.to_string())

    plot_overlap_heatmap(overlap_df)
    plot_venn_diagram(hotspot_cells, high_iar_cells, high_density_cells)

    validation_counts = compute_validation_strength(zone_sets)
    print_validation_summary(validation_counts)
    plot_validation_strength_map(validation_counts)

    print_interpretation(zone_sets)
    save_validation_results(validation_counts)


if __name__ == "__main__":
    main()