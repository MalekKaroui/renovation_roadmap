"""
04_dbscan_clustering.py — Density-based clustering (finds arbitrary shapes + noise)
"""
import numpy as np
import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt
from sklearn.cluster import DBSCAN
from sklearn.neighbors import NearestNeighbors
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import silhouette_score
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from utils import logger, data_path, save_figure, style_axis

OUT_GPKG = data_path("permits_dbscan.gpkg")
OUT_STATS = data_path("dbscan_stats.csv")

def load_spatial():
    gdf = gpd.read_file(data_path("permits_spatial.gpkg"))
    return gdf

def build_features(gdf):
    gdf = gdf.copy()
    gdf["PROJ_X"] = gdf.geometry.x
    gdf["PROJ_Y"] = gdf.geometry.y
    gdf["LOG_EVAL"] = np.log10(gdf["BPEVAL"].clip(1))
    
    X_raw = gdf[["PROJ_X", "PROJ_Y", "LOG_EVAL", "YEAR"]].values
    scaler = StandardScaler()
    X = scaler.fit_transform(X_raw)
    return X, gdf

def k_distance_graph(X, k=5):
    """Estimate eps from k-nearest neighbor distances"""
    nbrs = NearestNeighbors(n_neighbors=k+1)
    nbrs.fit(X)
    distances, _ = nbrs.kneighbors(X)
    k_dist = np.sort(distances[:, k])[::-1]
    
    # Find elbow
    diffs2 = np.diff(np.diff(k_dist))
    elbow_idx = np.argmax(np.abs(diffs2)) + 1
    eps_est = k_dist[elbow_idx]
    
    fig, ax = plt.subplots(figsize=(10, 4))
    ax.plot(k_dist, color="#1565C0", linewidth=1.5)
    ax.axhline(eps_est, color="#E53935", linestyle="--", label=f"eps={eps_est:.3f}")
    style_axis(ax, f"k-Distance Graph (k={k})", "Points (sorted)", f"{k}-NN Distance")
    ax.legend()
    save_figure(fig, "04_k_distance.png")
    
    logger.info(f"Estimated eps from k-distance: {eps_est:.4f}")
    return eps_est

def fit_dbscan(X, eps=0.5, min_samples=10):
    db = DBSCAN(eps=eps, min_samples=min_samples)
    labels = db.fit_predict(X)
    
    n_clusters = len(set(labels)) - (1 if -1 in labels else 0)
    n_noise = (labels == -1).sum()
    logger.info(f"DBSCAN: {n_clusters} clusters, {n_noise:,} noise points ({n_noise/len(labels)*100:.1f}%)")
    return labels

def cluster_stats(gdf):
    core = gdf[gdf["DBSCAN_CLUSTER"] != -1]
    stats = (
        core.groupby("DBSCAN_CLUSTER")
        .agg(
            n_permits = ("BPEVAL", "count"),
            mean_value = ("BPEVAL", "mean"),
        )
        .reset_index()
    )
    return stats

def plot_dbscan(gdf):
    import matplotlib.cm as cm
    n_clusters = max(gdf["DBSCAN_CLUSTER"].max(), 0) + 1
    colours = cm.get_cmap("tab20", n_clusters)
    
    fig, ax = plt.subplots(figsize=(13, 11))
    
    # Noise first
    noise = gdf[gdf["DBSCAN_CLUSTER"] == -1]
    ax.scatter(noise.geometry.x, noise.geometry.y, c="lightgrey",
               s=2, alpha=0.3, label="Noise", rasterized=True)
    
    # Clusters
    for k in range(n_clusters):
        sub = gdf[gdf["DBSCAN_CLUSTER"] == k]
        ax.scatter(sub.geometry.x, sub.geometry.y, c=[colours(k)],
                   s=5, alpha=0.6, label=f"C{k} (n={len(sub):,})", rasterized=True)
    
    style_axis(ax, "DBSCAN Clusters\nSaint John Permits 2015-2025",
               "Easting (m)", "Northing (m)")
    ax.legend(loc="upper left", bbox_to_anchor=(1,1), fontsize=7)
    save_figure(fig, "04_dbscan_map.png", dpi=200)

def main():
    logger.info("="*60)
    logger.info("STAGE 4 — DBSCAN Clustering")
    logger.info("="*60)
    
    gdf = load_spatial()
    X, gdf = build_features(gdf)
    
    eps_est = k_distance_graph(X, k=5)
    
    # Use estimated eps
    labels = fit_dbscan(X, eps=eps_est, min_samples=10)
    gdf["DBSCAN_CLUSTER"] = labels
    
    stats = cluster_stats(gdf)
    print("\nDBSCAN Cluster Stats:")
    print(stats.to_string(index=False))
    
    plot_dbscan(gdf)
    
    gdf.to_file(OUT_GPKG, driver="GPKG")
    logger.info(f"DBSCAN labels → {OUT_GPKG}")
    
    stats.to_csv(OUT_STATS, index=False)

if __name__ == "__main__":
    main()
