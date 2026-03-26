"""
03_kmeans_clustering.py

Run K-Means clustering on the spatial permit dataset using location,
valuation, and year as features.
"""

import os
import sys

import geopandas as gpd
import matplotlib.cm as cm
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score
from sklearn.preprocessing import StandardScaler

sys.path.insert(0, os.path.dirname(__file__))

from utils import logger, data_path, save_figure, style_axis


K_FINAL = 6
K_RANGE = range(2, 16)
RANDOM_STATE = 42

OUT_GPKG = data_path("permits_kmeans.gpkg")
OUT_STATS = data_path("kmeans_stats.csv")


def load_spatial_permits():
    """
    Load the spatial permit dataset created in Stage 2.
    """
    gdf = gpd.read_file(data_path("permits_spatial.gpkg"))
    logger.info(f"Loaded {len(gdf):,} spatial permits")
    return gdf


def build_feature_matrix(gdf):
    """
    Build the feature matrix used for clustering.

    Features:
    - projected X coordinate
    - projected Y coordinate
    - log-transformed permit value
    - permit year
    """
    gdf = gdf.copy()

    gdf["PROJ_X"] = gdf.geometry.x
    gdf["PROJ_Y"] = gdf.geometry.y
    gdf["LOG_EVAL"] = np.log10(gdf["BPEVAL"].clip(lower=1))

    feature_columns = ["PROJ_X", "PROJ_Y", "LOG_EVAL", "YEAR"]
    X_raw = gdf[feature_columns].values

    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X_raw)

    logger.info(f"Feature matrix: {X_scaled.shape}")
    return X_scaled, gdf


def run_elbow_analysis(X):
    """
    Compute WCSS and silhouette scores for a range of k values.
    Save the elbow plot for the final report.
    """
    wcss_scores = []
    silhouette_scores = []

    for k in K_RANGE:
        model = KMeans(
            n_clusters=k,
            random_state=RANDOM_STATE,
            n_init=10
        )

        labels = model.fit_predict(X)

        wcss_scores.append(model.inertia_)
        silhouette_scores.append(
            silhouette_score(X, labels, sample_size=min(5000, len(X)))
        )

        logger.info(
            f"k={k}: WCSS={model.inertia_:,.0f}, "
            f"Silhouette={silhouette_scores[-1]:.4f}"
        )

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(13, 5))

    ax1.plot(K_RANGE, wcss_scores, "o-", color="#1565C0", linewidth=2)
    ax1.axvline(
        K_FINAL,
        color="#E53935",
        linestyle="--",
        label=f"Chosen k = {K_FINAL}"
    )
    style_axis(ax1, "Elbow Method — WCSS", "k", "Within-Cluster Sum of Squares")
    ax1.legend()

    ax2.plot(K_RANGE, silhouette_scores, "s-", color="#2E7D32", linewidth=2)
    ax2.axvline(K_FINAL, color="#E53935", linestyle="--")
    style_axis(ax2, "Silhouette Score", "k", "Silhouette Score")

    save_figure(fig, "03_elbow_analysis.png")


def fit_kmeans_model(X, k=K_FINAL):
    """
    Fit the final K-Means model and return cluster labels.
    """
    model = KMeans(
        n_clusters=k,
        random_state=RANDOM_STATE,
        n_init=20,
        max_iter=500
    )

    labels = model.fit_predict(X)
    logger.info(f"K-Means fitted (k={k}), inertia={model.inertia_:,.0f}")

    return labels


def compute_cluster_statistics(gdf):
    """
    Summarize the number of permits and valuation by cluster.
    """
    stats = (
        gdf.groupby("CLUSTER")
        .agg(
            n_permits=("BPEVAL", "count"),
            mean_value=("BPEVAL", "mean"),
            median_value=("BPEVAL", "median"),
        )
        .reset_index()
    )

    return stats


def plot_cluster_map(gdf):
    """
    Plot the spatial distribution of K-Means clusters.
    """
    colors = cm.get_cmap("tab10", K_FINAL)

    fig, ax = plt.subplots(figsize=(12, 10))

    for cluster_id in range(K_FINAL):
        cluster_data = gdf[gdf["CLUSTER"] == cluster_id]

        ax.scatter(
            cluster_data.geometry.x,
            cluster_data.geometry.y,
            c=[colors(cluster_id)],
            s=4,
            alpha=0.4,
            label=f"Cluster {cluster_id}",
            rasterized=True
        )

    style_axis(
        ax,
        f"K-Means Clusters (k={K_FINAL})\nSaint John Permits (2015–2025)",
        "Easting (m)",
        "Northing (m)"
    )
    ax.legend(loc="lower right", markerscale=3)

    save_figure(fig, "03_kmeans_map.png", dpi=200)


def print_cluster_statistics(stats_df):
    """
    Print a readable table of cluster results.
    """
    print("\nCluster Statistics:")
    print(stats_df.to_string(index=False))


def main():
    logger.info("=" * 60)
    logger.info("STAGE 3 — K-Means Clustering")
    logger.info("=" * 60)

    permits_gdf = load_spatial_permits()
    X, permits_gdf = build_feature_matrix(permits_gdf)

    run_elbow_analysis(X)

    cluster_labels = fit_kmeans_model(X)
    permits_gdf["CLUSTER"] = cluster_labels

    stats_df = compute_cluster_statistics(permits_gdf)
    print_cluster_statistics(stats_df)

    plot_cluster_map(permits_gdf)

    permits_gdf.to_file(OUT_GPKG, driver="GPKG")
    logger.info(f"K-Means labels → {OUT_GPKG}")

    stats_df.to_csv(OUT_STATS, index=False)


if __name__ == "__main__":
    main()