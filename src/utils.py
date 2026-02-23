"""
utils.py — Shared utility functions
"""
import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("renovation_roadmap")

def project_root():
    return os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

def data_path(*parts):
    return os.path.join(project_root(), "data", *parts)

def figures_path(*parts):
    path = os.path.join(project_root(), "outputs", "figures", *parts)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    return path

def maps_path(*parts):
    path = os.path.join(project_root(), "outputs", "maps", *parts)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    return path

def save_figure(fig, filename, dpi=150):
    path = figures_path(filename)
    fig.savefig(path, dpi=dpi, bbox_inches="tight")
    plt.close(fig)
    logger.info(f"Figure saved → {path}")

def style_axis(ax, title="", xlabel="", ylabel=""):
    ax.set_title(title, fontsize=13, fontweight="bold", pad=10)
    ax.set_xlabel(xlabel, fontsize=10)
    ax.set_ylabel(ylabel, fontsize=10)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.grid(axis="y", linestyle="--", alpha=0.4)
