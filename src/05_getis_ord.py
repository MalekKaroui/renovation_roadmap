"""
05_getis_ord.py — Hotspot analysis using Getis-Ord Gi* statistic
Operates on grid cells (from stage 2) rather than neighborhoods
"""
import numpy as np
import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from utils import logger, data_path, save_figure, style_axis

try:
    from libpysal.weights import Queen
    from esda.getisord import G_Local
    PYSAL_OK = True
except ImportError:
    PYSAL_OK = False
    logger.warning("PySAL not available — using manual implementation")

OUT_CSV = data_path("getis_ord_results.csv")

def load_grid_layer():
    """Load grid cells with aggregated permit statistics"""
    grid = gpd.read_file(data_path("spatial_grid.gpkg"))
    stats = pd.read_csv(data_path("grid_stats.csv"))
    merged = grid.merge(stats, on="GRID_ID", how="inner")
    logger.info(f"Grid layer: {len(merged)} cells with data")
    return merged

def run_getis_ord_pysal(gdf):
    """PySAL implementation"""
    w = Queen.from_dataframe(gdf, silence_warnings=True)
    w.transform = "R"
    
    y = gdf["mean_value"].values
    g_local = G_Local(y, w, transform="R", star=True, permutations=999)
    
    gdf = gdf.copy()
    gdf["Gi_star"] = g_local.Zs
    gdf["p_value"] = g_local.p_sim
    gdf["hotspot"] = classify_hotspot(g_local.Zs, g_local.p_sim)
    return gdf

def run_getis_ord_manual(gdf):
    """Manual distance-band implementation"""
    from scipy.spatial.distance import cdist
    from scipy.stats import norm
    
    centroids = np.array([(g.centroid.x, g.centroid.y) for g in gdf.geometry])
    D = cdist(centroids, centroids)
    W = (D <= 3000).astype(float)  # 3km band
    np.fill_diagonal(W, 0)
    
    y = gdf["mean_value"].values
    n = len(y)
    x_bar = y.mean()
    S = np.sqrt(((y - x_bar)**2).sum() / n)
    
    Gi_star = np.zeros(n)
    for i in range(n):
        w_i = W[i]
        sum_w = w_i.sum()
        sum_w2 = (w_i**2).sum()
        
        num = (w_i * y).sum() - x_bar * sum_w
        denom = S * np.sqrt((n * sum_w2 - sum_w**2) / (n - 1))
        Gi_star[i] = num / denom if denom != 0 else 0.0
    
    p_values = 2 * (1 - norm.cdf(np.abs(Gi_star)))
    
    gdf = gdf.copy()
    gdf["Gi_star"] = Gi_star
    gdf["p_value"] = p_values
    gdf["hotspot"] = classify_hotspot(Gi_star, p_values)
    return gdf

def classify_hotspot(z, p):
    """Classify based on z-score and p-value"""
    labels = []
    for zi, pi in zip(z, p):
        if zi > 2.576 and pi < 0.01:
            labels.append("Hot Spot (99%)")
        elif zi > 1.960 and pi < 0.05:
            labels.append("Hot Spot (95%)")
        elif zi < -2.576 and pi < 0.01:
            labels.append("Cold Spot (99%)")
        elif zi < -1.960 and pi < 0.05:
            labels.append("Cold Spot (95%)")
        else:
            labels.append("Not Significant")
    return labels

def plot_hotspot_map(gdf):
    """Choropleth of hotspot classification"""
    colour_map = {
        "Hot Spot (99%)": "#BD0026",
        "Hot Spot (95%)": "#F03B20",
        "Not Significant": "#FFFFCC",
        "Cold Spot (95%)": "#2B8CBE",
        "Cold Spot (99%)": "#045A8D",
    }
    gdf = gdf.copy()
    gdf["colour"] = gdf["hotspot"].map(colour_map).fillna("#CCCCCC")
    
    fig, ax = plt.subplots(figsize=(13, 11))
    gdf.plot(color=gdf["colour"], edgecolor="white", linewidth=0.3, ax=ax)
    
    import matplotlib.patches as mpatches
    patches = [mpatches.Patch(color=v, label=k) for k,v in colour_map.items()]
    ax.legend(handles=patches, loc="lower right", title="Getis-Ord Gi*")
    
    ax.set_title("Getis-Ord Hotspot Analysis\nMean Permit Value — Saint John, NB",
                 fontsize=13, fontweight="bold")
    ax.set_axis_off()
    save_figure(fig, "05_hotspot_map.png", dpi=200)

def plot_gi_distribution(gdf):
    """Histogram of Gi* z-scores"""
    fig, ax = plt.subplots(figsize=(9, 4))
    ax.hist(gdf["Gi_star"], bins=30, color="#78909C", edgecolor="white", alpha=0.8)
    ax.axvline(1.96, color="#F03B20", linestyle="--", label="p<0.05")
    ax.axvline(-1.96, color="#2B8CBE", linestyle="--")
    style_axis(ax, "Distribution of Gi* Z-Scores", "Gi* Z-Score", "Count")
    ax.legend()
    save_figure(fig, "05_gi_distribution.png")

def main():
    logger.info("="*60)
    logger.info("STAGE 5 — Getis-Ord Hotspot Analysis")
    logger.info("="*60)
    
    gdf = load_grid_layer()
    
    if PYSAL_OK:
        gdf = run_getis_ord_pysal(gdf)
    else:
        gdf = run_getis_ord_manual(gdf)
    
    counts = gdf["hotspot"].value_counts()
    print("\nHotspot Classification:")
    print(counts.to_string())
    
    plot_hotspot_map(gdf)
    plot_gi_distribution(gdf)
    
    result_cols = ["GRID_ID", "mean_value", "permit_count", "Gi_star", "p_value", "hotspot"]
    gdf[result_cols].to_csv(OUT_CSV, index=False)
    logger.info(f"Hotspot results → {OUT_CSV}")
    
    hot = gdf[gdf["hotspot"].str.startswith("Hot", na=False)]
    print(f"\n{len(hot)} statistically significant HOT SPOTS:")
    print(hot[["GRID_ID", "Gi_star", "p_value", "mean_value"]].sort_values("Gi_star", ascending=False))

if __name__ == "__main__":
    main()
