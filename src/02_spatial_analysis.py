"""
02_spatial_analysis.py — Convert permits to GeoDataFrame & create spatial grid
Since we have no neighborhood polygons, we create a grid-based spatial aggregation
"""
import pandas as pd
import geopandas as gpd
import numpy as np
from shapely.geometry import Point, box
import matplotlib.pyplot as plt
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from utils import logger, data_path, save_figure, style_axis

OUT_GPKG = data_path("permits_spatial.gpkg")
OUT_GRID = data_path("spatial_grid.gpkg")
OUT_STATS = data_path("grid_stats.csv")

def load_cleaned():
    df = pd.read_csv(data_path("permits_cleaned.csv"), parse_dates=["BPISDT"])
    logger.info(f"Loaded {len(df):,} cleaned permits")
    return df

def to_geodataframe(df):
    geometry = [Point(xy) for xy in zip(df["POINT_X"], df["POINT_Y"])]
    gdf = gpd.GeoDataFrame(df, geometry=geometry, crs="EPSG:4326")
    gdf = gdf.to_crs("EPSG:32620")  # UTM Zone 20N for accurate distances
    logger.info(f"Created GeoDataFrame: {len(gdf):,} points")
    return gdf

def create_spatial_grid(gdf, grid_size=1000):
    """
    Create a regular grid of squares (1km × 1km default)
    Each cell becomes our spatial analysis unit (replaces neighborhoods)
    """
    bounds = gdf.total_bounds
    xmin, ymin, xmax, ymax = bounds
    
    rows = int(np.ceil((ymax - ymin) / grid_size))
    cols = int(np.ceil((xmax - xmin) / grid_size))
    
    cells = []
    cell_ids = []
    
    for i in range(rows):
        for j in range(cols):
            x0 = xmin + j * grid_size
            y0 = ymin + i * grid_size
            cell = box(x0, y0, x0 + grid_size, y0 + grid_size)
            cells.append(cell)
            cell_ids.append(f"GRID_{i:02d}_{j:02d}")
    
    grid = gpd.GeoDataFrame({"GRID_ID": cell_ids}, geometry=cells, crs=gdf.crs)
    logger.info(f"Created {len(grid):,} grid cells ({grid_size}m × {grid_size}m)")
    return grid

def spatial_join(permits_gdf, grid_gdf):
    """Assign each permit to its grid cell"""
    joined = gpd.sjoin(permits_gdf, grid_gdf, how="left", predicate="within")
    joined["GRID_ID"] = joined["GRID_ID"].fillna("UNKNOWN")
    
    n_unmatched = (joined["GRID_ID"] == "UNKNOWN").sum()
    logger.info(f"Spatial join: {n_unmatched:,} permits outside grid")
    return joined

def compute_grid_stats(gdf):
    """Aggregate statistics per grid cell"""
    stats = (
        gdf[gdf["GRID_ID"] != "UNKNOWN"]
        .groupby("GRID_ID")
        .agg(
            permit_count = ("BPEVAL", "count"),
            total_value = ("BPEVAL", "sum"),
            mean_value = ("BPEVAL", "mean"),
            median_value = ("BPEVAL", "median"),
        )
        .reset_index()
    )
    logger.info(f"Grid stats computed for {len(stats)} cells")
    return stats

def plot_permit_density(gdf, grid_gdf, stats):
    """Choropleth: permit count per grid cell"""
    poly_stats = grid_gdf.merge(stats, on="GRID_ID", how="left")
    poly_stats["permit_count"] = poly_stats["permit_count"].fillna(0)
    
    fig, ax = plt.subplots(figsize=(12, 10))
    poly_stats.plot(
        column="permit_count",
        ax=ax,
        cmap="YlOrRd",
        edgecolor="white",
        linewidth=0.3,
        legend=True,
        legend_kwds={"label": "Permit Count", "shrink": 0.6}
    )
    ax.set_title("Building Permit Density (1km Grid)\nSaint John, NB 2015-2025",
                 fontsize=13, fontweight="bold")
    ax.set_axis_off()
    save_figure(fig, "02_permit_density_grid.png", dpi=200)

def plot_mean_value(grid_gdf, stats):
    """Choropleth: mean permit value per grid cell"""
    poly_stats = grid_gdf.merge(stats, on="GRID_ID", how="left")
    
    fig, ax = plt.subplots(figsize=(12, 10))
    poly_stats.plot(
        column="mean_value",
        ax=ax,
        cmap="Blues",
        edgecolor="white",
        linewidth=0.3,
        legend=True,
        legend_kwds={"label": "Mean Permit Value (CAD)", "shrink": 0.6}
    )
    ax.set_title("Mean Permit Value by Grid Cell\nSaint John, NB",
                 fontsize=13, fontweight="bold")
    ax.set_axis_off()
    save_figure(fig, "02_mean_value_grid.png", dpi=200)

def main():
    logger.info("="*60)
    logger.info("STAGE 2 — Spatial Analysis")
    logger.info("="*60)
    
    df = load_cleaned()
    gdf = to_geodataframe(df)
    grid = create_spatial_grid(gdf, grid_size=1000)  # 1km cells
    
    joined = spatial_join(gdf, grid)
    stats = compute_grid_stats(joined)
    
    plot_permit_density(joined, grid, stats)
    plot_mean_value(grid, stats)
    
    # Save
    joined.to_file(OUT_GPKG, driver="GPKG")
    logger.info(f"Spatial permits → {OUT_GPKG}")
    
    grid.to_file(OUT_GRID, driver="GPKG")
    logger.info(f"Grid saved → {OUT_GRID}")
    
    stats.to_csv(OUT_STATS, index=False)
    logger.info(f"Grid stats → {OUT_STATS}")
    
    print(f"\nTop 10 grid cells by permit count:")
    print(stats.nlargest(10, "permit_count")[["GRID_ID", "permit_count", "mean_value"]])

if __name__ == "__main__":
    main()
