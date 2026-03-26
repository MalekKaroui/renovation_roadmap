"""
utils.py

Shared helper functions used across the Renovation Roadmap project.
"""

import logging
import os

import matplotlib.pyplot as plt


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)

logger = logging.getLogger("renovation_roadmap")


def project_root():
    """
    Return the absolute path to the project root directory.
    """
    return os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))


def data_path(*parts):
    """
    Build a path inside the data folder.
    """
    return os.path.join(project_root(), "data", *parts)


def figures_path(*parts):
    """
    Build a path inside outputs/figures and create missing folders if needed.
    """
    path = os.path.join(project_root(), "outputs", "figures", *parts)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    return path


def maps_path(*parts):
    """
    Build a path inside outputs/maps and create missing folders if needed.
    """
    path = os.path.join(project_root(), "outputs", "maps", *parts)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    return path


def save_figure(fig, filename, dpi=150):
    """
    Save a matplotlib figure to the outputs/figures folder.
    """
    path = figures_path(filename)
    fig.savefig(path, dpi=dpi, bbox_inches="tight")
    plt.close(fig)
    logger.info(f"Figure saved → {path}")


def style_axis(ax, title="", xlabel="", ylabel=""):
    """
    Apply a consistent style to a matplotlib axis.
    """
    ax.set_title(title, fontsize=13, fontweight="bold", pad=10)
    ax.set_xlabel(xlabel, fontsize=10)
    ax.set_ylabel(ylabel, fontsize=10)

    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.grid(axis="y", linestyle="--", alpha=0.4)