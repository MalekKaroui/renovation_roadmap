"""
02_spatial_analysis.py

Convert cleaned permit records into a GeoDataFrame, build a regular
spatial grid over Saint John, and aggregate permit activity by grid cell.
"""

import os
import sys

import geopandas as gpd
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from shapely.geometry import Point, box

sys.path.insert(0, os.path.dirname(__file__))

from utils import logger, data_path, save_figure


OUT_GPKG = data_path("permits_spatial.gpkg")
OUT_GRID = data_path("spatial_grid.gpkg")
OUT_STATS = data_path("grid_stats.csv")

GRID_SIZE_METERS = 1000
INPUT_CRS = "EPSG:4326"
TARGET_CRS = "EPSG:32620"


def load_cleaned_permits():
    """
    Load the cleaned permit CSV from Stage 1.
    """
    df = pd.read_csv(data_path("permits_cleaned.csv"), parse_dates=["BPISDT"])
    logger.info(f"Loaded {len(df):,} cleaned permits")
    return df


def permits_to_geodataframe(df):
    """
    Convert permit coordinates into a projected GeoDataFrame.
    """
    geometry = [Point(xy) for xy in zip(df["POINT_X"], df["POINT_Y"])]
    gdf = gpd.GeoDataFrame(df, geometry=geometry, crs=INPUT_CRS)
    gdf = gdf.to_crs(TARGET_CRS)

    logger.info(f"Created GeoDataFrame: {len(gdf):,} points")
    return gdf


def create_spatial_grid(gdf, grid_size=GRID_SIZE_METERS):
    """
    Create a regular square grid covering the permit extent.
    """
    xmin, ymin, xmax, ymax = gdf.total_bounds

    rows = int(np.ceil((ymax - ymin) / grid_size))
    cols = int(np.ceil((xmax - xmin) / grid_size))

    cells = []
    cell_ids = []

    for row in range(rows):
        for col in range(cols):
            x0 = xmin + col * grid_size
            y0 = ymin + row * grid_size

            cell = box(x0, y0, x0 + grid_size, y0 + grid_size)
            cell_id = f"GRID_{row:02d}_{col:02d}"

            cells.append(cell)
            cell_ids.append(cell_id)

    grid = gpd.GeoDataFrame({"GRID_ID": cell_ids}, geometry=cells, crs=gdf.crs)

    logger.info(f"Created {len(grid):,} grid cells ({grid_size}m × {grid_size}m)")
    return grid


def assign_permits_to_grid(permits_gdf, grid_gdf):
    """
    Spatially join each permit point to a grid cell.
    """
    joined = gpd.sjoin(permits_gdf, grid_gdf, how="left", predicate="within")
    joined["GRID_ID"] = joined["GRID_ID"].fillna("UNKNOWN")

    unmatched_count = (joined["GRID_ID"] == "UNKNOWN").sum()
    logger.info(f"Spatial join: {unmatched_count:,} permits outside grid")

    return joined


def compute_grid_statistics(joined_gdf):
    """
    Aggregate permit statistics for each active grid cell.
    """
    stats = (
        joined_gdf[joined_gdf["GRID_ID"] != "UNKNOWN"]
        .groupby("GRID_ID")
        .agg(
            permit_count=("BPEVAL", "count"),
            total_value=("BPEVAL", "sum"),
            mean_value=("BPEVAL", "mean"),
            median_value=("BPEVAL", "median"),
        )
        .reset_index()
    )

    logger.info(f"Grid stats computed for {len(stats)} cells")
    return stats


def plot_permit_density(grid_gdf, stats_df):
    """
    Plot permit count per grid cell.
    """
    plot_df = grid_gdf.merge(stats_df, on="GRID_ID", how="left")
    plot_df["permit_count"] = plot_df["permit_count"].fillna(0)

    fig, ax = plt.subplots(figsize=(12, 10))
    plot_df.plot(
        column="permit_count",
        ax=ax,
        cmap="YlOrRd",
        edgecolor="white",
        linewidth=0.3,
        legend=True,
        legend_kwds={"label": "Permit Count", "shrink": 0.6},
    )

    ax.set_title(
        "Building Permit Density (1 km Grid)\nSaint John, NB (2015–2025)",
        fontsize=13,
        fontweight="bold"
    )
    ax.set_axis_off()

    save_figure(fig, "02_permit_density_grid.png", dpi=200)


def plot_mean_permit_value(grid_gdf, stats_df):
    """
    Plot mean permit value per grid cell.
    """
    plot_df = grid_gdf.merge(stats_df, on="GRID_ID", how="left")

    fig, ax = plt.subplots(figsize=(12, 10))
    plot_df.plot(
        column="mean_value",
        ax=ax,
        cmap="Blues",
        edgecolor="white",
        linewidth=0.3,
        legend=True,
        legend_kwds={"label": "Mean Permit Value (CAD)", "shrink": 0.6},
    )

    ax.set_title(
        "Mean Permit Value by Grid Cell\nSaint John, NB",
        fontsize=13,
        fontweight="bold"
    )
    ax.set_axis_off()

    save_figure(fig, "02_mean_value_grid.png", dpi=200)


def print_top_cells(stats_df, n=10):
    """
    Print the top n grid cells by permit count.
    """
    top_cells = stats_df.nlargest(n, "permit_count")[
        ["GRID_ID", "permit_count", "mean_value"]
    ]

    print("\nTop 10 grid cells by permit count:")
    print(top_cells.to_string(index=False))


def main():
    logger.info("=" * 60)
    logger.info("STAGE 2 — Spatial Analysis")
    logger.info("=" * 60)

    permits_df = load_cleaned_permits()
    permits_gdf = permits_to_geodataframe(permits_df)

    grid_gdf = create_spatial_grid(permits_gdf)
    joined_gdf = assign_permits_to_grid(permits_gdf, grid_gdf)

    stats_df = compute_grid_statistics(joined_gdf)

    plot_permit_density(grid_gdf, stats_df)
    plot_mean_permit_value(grid_gdf, stats_df)

    joined_gdf.to_file(OUT_GPKG, driver="GPKG")
    logger.info(f"Spatial permits → {OUT_GPKG}")

    grid_gdf.to_file(OUT_GRID, driver="GPKG")
    logger.info(f"Grid saved → {OUT_GRID}")

    stats_df.to_csv(OUT_STATS, index=False)
    logger.info(f"Grid stats → {OUT_STATS}")

    print_top_cells(stats_df)


if __name__ == "__main__":
    main()