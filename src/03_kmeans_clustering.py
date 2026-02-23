"""
03_kmeans_clustering.py — Spatial clustering of building permits
Feature vector: [X, Y, log(BPEVAL), YEAR]
"""
import numpy as np
import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from utils import logger, data_path, save_figure, style_axis

K_FINAL = 6
OUT_GPKG = data_path("permits_kmeans.gpkg")
OUT_STATS = data_path("kmeans_stats.csv")

def load_spatial():
    gdf = gpd.read_file(data_path("permits_spatial.gpkg"))
    logger.info(f"Loaded {len(gdf):,} spatial permits")
    return gdf

def build_features(gdf):
    gdf = gdf.copy()
    gdf["PROJ_X"] = gdf.geometry.x
    gdf["PROJ_Y"] = gdf.geometry.y
    gdf["LOG_EVAL"] = np.log10(gdf["BPEVAL"].clip(1))
    
    X_raw = gdf[["PROJ_X", "PROJ_Y", "LOG_EVAL", "YEAR"]].values
    scaler = StandardScaler()
    X = scaler.fit_transform(X_raw)
    logger.info(f"Feature matrix: {X.shape}")
    return X, gdf

def elbow_analysis(X):
    wcss = []
    sil = []
    K_range = range(2, 16)
    
    for k in K_range:
        km = KMeans(n_clusters=k, random_state=42, n_init=10)
        labels = km.fit_predict(X)
        wcss.append(km.inertia_)
        sil.append(silhouette_score(X, labels, sample_size=5000))
        logger.info(f"k={k}: WCSS={km.inertia_:,.0f}, Silhouette={sil[-1]:.4f}")
    
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(13, 5))
    ax1.plot(K_range, wcss, "o-", color="#1565C0", linewidth=2)
    ax1.axvline(K_FINAL, color="#E53935", linestyle="--", label=f"Chosen k={K_FINAL}")
    style_axis(ax1, "Elbow Method — WCSS", "k", "Within-Cluster Sum of Squares")
    ax1.legend()
    
    ax2.plot(K_range, sil, "s-", color="#2E7D32", linewidth=2)
    ax2.axvline(K_FINAL, color="#E53935", linestyle="--")
    style_axis(ax2, "Silhouette Score", "k", "Silhouette Score")
    
    save_figure(fig, "03_elbow_analysis.png")

def fit_kmeans(X, k=K_FINAL):
    km = KMeans(n_clusters=k, random_state=42, n_init=20, max_iter=500)
    labels = km.fit_predict(X)
    logger.info(f"K-Means fitted (k={k}), inertia={km.inertia_:,.0f}")
    return labels

def cluster_stats(gdf):
    stats = (
        gdf.groupby("CLUSTER")
        .agg(
            n_permits = ("BPEVAL", "count"),
            mean_value = ("BPEVAL", "mean"),
            median_value = ("BPEVAL", "median"),
        )
        .reset_index()
    )
    return stats

def plot_clusters(gdf):
    import matplotlib.cm as cm
    colours = cm.get_cmap("tab10", K_FINAL)
    
    fig, ax = plt.subplots(figsize=(12, 10))
    for k in range(K_FINAL):
        sub = gdf[gdf["CLUSTER"] == k]
        ax.scatter(sub.geometry.x, sub.geometry.y, c=[colours(k)],
                   s=4, alpha=0.4, label=f"Cluster {k}", rasterized=True)
    
    style_axis(ax, f"K-Means Clusters (k={K_FINAL})\nSaint John Permits 2015-2025",
               "Easting (m)", "Northing (m)")
    ax.legend(loc="lower right", markerscale=3)
    save_figure(fig, "03_kmeans_map.png", dpi=200)

def main():
    logger.info("="*60)
    logger.info("STAGE 3 — K-Means Clustering")
    logger.info("="*60)
    
    gdf = load_spatial()
    X, gdf = build_features(gdf)
    
    elbow_analysis(X)
    
    labels = fit_kmeans(X, K_FINAL)
    gdf["CLUSTER"] = labels
    
    stats = cluster_stats(gdf)
    print("\nCluster Statistics:")
    print(stats.to_string(index=False))
    
    plot_clusters(gdf)
    
    gdf.to_file(OUT_GPKG, driver="GPKG")
    logger.info(f"K-Means labels → {OUT_GPKG}")
    
    stats.to_csv(OUT_STATS, index=False)

if __name__ == "__main__":
    main()
