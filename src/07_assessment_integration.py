"""
07_assessment_integration.py — Integrate property assessments (GeoJSON)
Calculate Investment-Assessment Ratio (IAR) per grid cell
"""
import numpy as np
import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from utils import logger, data_path, save_figure, style_axis

ASSESSMENT_GEOJSON = data_path("Property_Assessments.geojson")
OUT_CSV = data_path("assessment_integration.csv")

def load_assessments():
    """Load property assessment GeoJSON (CURR_ASSMT = current assessment value)"""
    gdf = gpd.read_file(ASSESSMENT_GEOJSON)
    logger.info(f"Loaded {len(gdf):,} property assessments")
    
    gdf = gdf.to_crs("EPSG:32620")
    gdf["CURR_ASSMT"] = pd.to_numeric(gdf["CURR_ASSMT"], errors="coerce")
    gdf = gdf.dropna(subset=["CURR_ASSMT"])
    gdf = gdf[gdf["CURR_ASSMT"] > 0]
    
    logger.info(f"Valid assessments: {len(gdf):,}")
    return gdf

def spatial_join_assessments(assess_gdf):
    """Join assessments to grid cells"""
    grid = gpd.read_file(data_path("spatial_grid.gpkg"))
    
    joined = gpd.sjoin(assess_gdf, grid, how="left", predicate="within")
    joined["GRID_ID"] = joined["GRID_ID"].fillna("UNKNOWN")
    
    agg = (
        joined[joined["GRID_ID"] != "UNKNOWN"]
        .groupby("GRID_ID")["CURR_ASSMT"]
        .agg(
            mean_assessment = "mean",
            n_properties = "count",
        )
        .reset_index()
    )
    logger.info(f"Assessment aggregation: {len(agg)} grid cells")
    return agg

def compute_iar(permit_stats, assess_stats):
    """Investment-Assessment Ratio = mean_permit_value / mean_assessment"""
    merged = permit_stats.merge(assess_stats, on="GRID_ID", how="inner")
    
    merged["IAR"] = merged["mean_value"] / merged["mean_assessment"]
    
    # Classify
    iar_75 = merged["IAR"].quantile(0.75)
    ass_25 = merged["mean_assessment"].quantile(0.25)
    
    def classify(row):
        if row["IAR"] >= iar_75 and row["mean_assessment"] <= ass_25:
            return "⚠️ Pre-Gentrification Signal"
        elif row["IAR"] >= iar_75:
            return "High Investment"
        elif row["mean_assessment"] <= ass_25:
            return "Low Base Value"
        return "Stable"
    
    merged["signal"] = merged.apply(classify, axis=1)
    n_signal = (merged["signal"] == "⚠️ Pre-Gentrification Signal").sum()
    logger.info(f"Pre-gentrification signal: {n_signal} grid cells")
    return merged

def plot_investment_vs_assessment(merged):
    """Scatter plot: investment vs assessment"""
    signal_colours = {
        "⚠️ Pre-Gentrification Signal": "#E53935",
        "High Investment": "#43A047",
        "Low Base Value": "#1E88E5",
        "Stable": "#9E9E9E",
    }
    
    fig, ax = plt.subplots(figsize=(11, 8))
    for signal, colour in signal_colours.items():
        sub = merged[merged["signal"] == signal]
        ax.scatter(sub["mean_value"] / 1000, sub["mean_assessment"] / 1000,
                   c=colour, s=60, alpha=0.7, label=f"{signal} (n={len(sub)})")
    
    ax.axvline(merged["mean_value"].median() / 1000, color="grey", linestyle="--", alpha=0.5)
    ax.axhline(merged["mean_assessment"].median() / 1000, color="grey", linestyle="--", alpha=0.5)
    
    style_axis(ax, "Investment vs Assessed Property Value\nby Grid Cell (Saint John 2015-2025)",
               "Mean Permit Value ($000 CAD)", "Mean Assessed Value ($000 CAD)")
    ax.legend(loc="lower right", fontsize=9)
    save_figure(fig, "07_investment_vs_assessment.png")

def plot_iar_choropleth(merged):
    """Map of IAR values"""
    grid = gpd.read_file(data_path("spatial_grid.gpkg"))
    poly = grid.merge(merged[["GRID_ID", "IAR"]], on="GRID_ID", how="left")
    
    fig, ax = plt.subplots(figsize=(13, 11))
    poly.plot(column="IAR", ax=ax, cmap="hot_r", edgecolor="white", linewidth=0.3,
              legend=True, legend_kwds={"label": "IAR", "shrink": 0.6},
              missing_kwds={"color": "lightgrey"})
    ax.set_title("Investment–Assessment Ratio (IAR)\nSaint John Grid Cells",
                 fontsize=13, fontweight="bold")
    ax.set_axis_off()
    save_figure(fig, "07_iar_map.png", dpi=200)

def main():
    logger.info("="*60)
    logger.info("STAGE 7 — Assessment Integration")
    logger.info("="*60)
    
    assess_gdf = load_assessments()
    assess_agg = spatial_join_assessments(assess_gdf)
    
    permit_stats = pd.read_csv(data_path("grid_stats.csv"))
    merged = compute_iar(permit_stats, assess_agg)
    
    plot_investment_vs_assessment(merged)
    plot_iar_choropleth(merged)
    
    merged.to_csv(OUT_CSV, index=False)
    logger.info(f"Assessment integration → {OUT_CSV}")
    
    signals = merged[merged["signal"] == "⚠️ Pre-Gentrification Signal"]
    print(f"\n{len(signals)} PRE-GENTRIFICATION SIGNAL grid cells:")
    print(signals[["GRID_ID", "IAR", "mean_value", "mean_assessment"]]
          .sort_values("IAR", ascending=False).head(10))

if __name__ == "__main__":
    main()
