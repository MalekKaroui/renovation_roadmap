"""
04_dbscan_clustering.py

Run DBSCAN on the spatial permit dataset to explore density-based
structure and identify possible noise points.
"""

import os
import sys

import geopandas as gpd
import matplotlib.cm as cm
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.cluster import DBSCAN
from sklearn.neighbors import NearestNeighbors
from sklearn.preprocessing import StandardScaler

sys.path.insert(0, os.path.dirname(__file__))

from utils import logger, data_path, save_figure, style_axis


OUT_GPKG = data_path("permits_dbscan.gpkg")
OUT_STATS = data_path("dbscan_stats.csv")

K_NEIGHBORS = 5
DBSCAN_MIN_SAMPLES = 10


def load_spatial_permits():
    """
    Load the spatial permit dataset created in Stage 2.
    """
    gdf = gpd.read_file(data_path("permits_spatial.gpkg"))
    logger.info(f"Loaded {len(gdf):,} spatial permits")
    return gdf


def build_feature_matrix(gdf):
    """
    Build the feature matrix used for DBSCAN.

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

    return X_scaled, gdf


def estimate_eps_from_k_distance(X, k=K_NEIGHBORS):
    """
    Estimate a DBSCAN epsilon value using the k-distance graph.
    """
    neighbors = NearestNeighbors(n_neighbors=k + 1)
    neighbors.fit(X)

    distances, _ = neighbors.kneighbors(X)
    k_distances = np.sort(distances[:, k])[::-1]

    # Use the second derivative as a simple elbow estimate
    second_diff = np.diff(np.diff(k_distances))
    elbow_index = np.argmax(np.abs(second_diff)) + 1
    eps_estimate = k_distances[elbow_index]

    fig, ax = plt.subplots(figsize=(10, 4))
    ax.plot(k_distances, color="#1565C0", linewidth=1.5)
    ax.axhline(
        eps_estimate,
        color="#E53935",
        linestyle="--",
        label=f"eps = {eps_estimate:.3f}"
    )

    style_axis(ax, f"k-Distance Graph (k={k})", "Points (sorted)", f"{k}-NN Distance")
    ax.legend()

    save_figure(fig, "04_k_distance.png")

    logger.info(f"Estimated eps from k-distance: {eps_estimate:.4f}")
    return eps_estimate


def fit_dbscan_model(X, eps_value, min_samples=DBSCAN_MIN_SAMPLES):
    """
    Fit DBSCAN and return cluster labels.
    """
    model = DBSCAN(eps=eps_value, min_samples=min_samples)
    labels = model.fit_predict(X)

    n_clusters = len(set(labels)) - (1 if -1 in labels else 0)
    n_noise = (labels == -1).sum()
    noise_pct = 100 * n_noise / len(labels)

    logger.info(
        f"DBSCAN: {n_clusters} clusters, "
        f"{n_noise:,} noise points ({noise_pct:.1f}%)"
    )

    return labels


def compute_cluster_statistics(gdf):
    """
    Summarize the non-noise DBSCAN clusters.
    """
    clustered = gdf[gdf["DBSCAN_CLUSTER"] != -1]

    stats = (
        clustered.groupby("DBSCAN_CLUSTER")
        .agg(
            n_permits=("BPEVAL", "count"),
            mean_value=("BPEVAL", "mean"),
        )
        .reset_index()
    )

    return stats


def plot_dbscan_clusters(gdf):
    """
    Plot DBSCAN clusters and noise points.
    """
    max_cluster = max(gdf["DBSCAN_CLUSTER"].max(), 0)
    n_clusters = max_cluster + 1
    colors = cm.get_cmap("tab20", n_clusters)

    fig, ax = plt.subplots(figsize=(13, 11))

    # Plot noise points first
    noise = gdf[gdf["DBSCAN_CLUSTER"] == -1]
    ax.scatter(
        noise.geometry.x,
        noise.geometry.y,
        c="lightgrey",
        s=2,
        alpha=0.3,
        label="Noise",
        rasterized=True
    )

    # Plot clusters
    for cluster_id in range(n_clusters):
        cluster_data = gdf[gdf["DBSCAN_CLUSTER"] == cluster_id]

        ax.scatter(
            cluster_data.geometry.x,
            cluster_data.geometry.y,
            c=[colors(cluster_id)],
            s=5,
            alpha=0.6,
            label=f"C{cluster_id} (n={len(cluster_data):,})",
            rasterized=True
        )

    style_axis(
        ax,
        "DBSCAN Clusters\nSaint John Permits (2015–2025)",
        "Easting (m)",
        "Northing (m)"
    )
    ax.legend(loc="upper left", bbox_to_anchor=(1, 1), fontsize=7)

    save_figure(fig, "04_dbscan_map.png", dpi=200)


def print_cluster_statistics(stats_df):
    """
    Print a readable table of DBSCAN cluster results.
    """
    print("\nDBSCAN Cluster Stats:")
    print(stats_df.to_string(index=False))


def main():
    logger.info("=" * 60)
    logger.info("STAGE 4 — DBSCAN Clustering")
    logger.info("=" * 60)

    permits_gdf = load_spatial_permits()
    X, permits_gdf = build_feature_matrix(permits_gdf)

    eps_estimate = estimate_eps_from_k_distance(X, k=K_NEIGHBORS)

    cluster_labels = fit_dbscan_model(
        X,
        eps_value=eps_estimate,
        min_samples=DBSCAN_MIN_SAMPLES
    )
    permits_gdf["DBSCAN_CLUSTER"] = cluster_labels

    stats_df = compute_cluster_statistics(permits_gdf)
    print_cluster_statistics(stats_df)

    plot_dbscan_clusters(permits_gdf)

    permits_gdf.to_file(OUT_GPKG, driver="GPKG")
    logger.info(f"DBSCAN labels → {OUT_GPKG}")

    stats_df.to_csv(OUT_STATS, index=False)


if __name__ == "__main__":
    main()