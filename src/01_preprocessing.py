"""
01_preprocessing.py

Clean and prepare the raw Saint John building permit data for analysis.

This script:
- loads the raw CSV,
- parses permit dates,
- filters the analysis period,
- fixes coordinates,
- removes invalid valuations and duplicates,
- and saves a cleaned CSV for later stages.
"""

import os
import sys

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(__file__))

from utils import logger, data_path, save_figure, style_axis


RAW_CSV = data_path("Building_Permits.csv")
OUT_CSV = data_path("permits_cleaned.csv")

YEAR_MIN = 2015
YEAR_MAX = 2025

# Approximate Saint John bounding box in WGS84
LON_MIN = -66.2
LON_MAX = -65.8
LAT_MIN = 45.1
LAT_MAX = 45.5


def load_raw_data():
    """
    Load the raw permit CSV using a fallback encoding strategy.
    """
    for encoding in ("utf-8", "latin-1"):
        try:
            df = pd.read_csv(RAW_CSV, encoding=encoding, low_memory=False)
            logger.info(f"Loaded {len(df):,} raw permits ({encoding})")
            return df
        except UnicodeDecodeError:
            continue

    raise ValueError(f"Could not read {RAW_CSV} with supported encodings.")


def parse_permit_dates(df):
    """
    Convert BPPISD from YYMMDD integer format into a pandas datetime column.
    """
    df["BPPISD"] = pd.to_numeric(df["BPPISD"], errors="coerce")

    def parse_yymmdd(value):
        if pd.isna(value) or value == 0:
            return pd.NaT

        text = str(int(value)).zfill(6)
        yy, mm, dd = text[:2], text[2:4], text[4:6]

        year = 1900 + int(yy) if int(yy) > 50 else 2000 + int(yy)

        try:
            return pd.Timestamp(year=year, month=int(mm), day=int(dd))
        except ValueError:
            return pd.NaT

    df["BPISDT"] = df["BPPISD"].apply(parse_yymmdd)
    df["YEAR"] = df["BPISDT"].dt.year

    before = len(df)
    df = df.dropna(subset=["BPISDT"]).copy()
    logger.info(f"Date parsing: {before - len(df):,} invalid dates dropped")

    return df


def filter_analysis_years(df, year_min=YEAR_MIN, year_max=YEAR_MAX):
    """
    Keep only permits issued between year_min and year_max.
    """
    before = len(df)
    df = df[(df["YEAR"] >= year_min) & (df["YEAR"] <= year_max)].copy()
    logger.info(f"Year filter ({year_min}-{year_max}): {before:,} → {len(df):,}")
    return df


def clean_coordinates(df):
    """
    Use the correct longitude/latitude columns and remove invalid points.
    """
    lon_col = "X_Long_East" if "X_Long_East" in df.columns else "POINT_X"
    lat_col = "Y_Lat_North" if "Y_Lat_North" in df.columns else "POINT_Y"

    df["POINT_X"] = pd.to_numeric(df[lon_col], errors="coerce")
    df["POINT_Y"] = pd.to_numeric(df[lat_col], errors="coerce")

    valid_mask = (
        df["POINT_X"].between(LON_MIN, LON_MAX) &
        df["POINT_Y"].between(LAT_MIN, LAT_MAX)
    )

    invalid_count = (~valid_mask).sum()
    valid_count = valid_mask.sum()

    logger.info(
        f"Coordinates: {invalid_count:,} invalid/missing, {valid_count:,} valid"
    )

    return df[valid_mask].copy()


def clean_valuations(df):
    """
    Remove missing, zero, and extreme permit valuations.
    Uses the 1st and 99th percentiles as cutoffs.
    """
    df["BPEVAL"] = pd.to_numeric(df["BPEVAL"], errors="coerce")
    before = len(df)

    df = df[df["BPEVAL"] > 0].copy()

    lower = df["BPEVAL"].quantile(0.01)
    upper = df["BPEVAL"].quantile(0.99)

    df = df[(df["BPEVAL"] >= lower) & (df["BPEVAL"] <= upper)].copy()

    logger.info(f"Valuation cleaning: {before - len(df):,} dropped")
    return df


def remove_duplicate_permits(df):
    """
    Remove duplicate permits using address, date, and valuation.
    """
    before = len(df)

    duplicate_keys = ["ENCIVSTNAM", "BPISDT", "BPEVAL"]
    duplicate_keys = [col for col in duplicate_keys if col in df.columns]

    if duplicate_keys:
        df = df.drop_duplicates(subset=duplicate_keys).copy()

    logger.info(f"Duplicates removed: {before - len(df):,}")
    return df


def plot_valuation_distribution(df):
    """
    Save a histogram of log-transformed permit values.
    """
    fig, ax = plt.subplots(figsize=(9, 4))

    log_values = np.log10(df["BPEVAL"].clip(lower=1))
    ax.hist(log_values, bins=60, color="#2196F3", edgecolor="white", alpha=0.85)

    style_axis(
        ax,
        "Project Valuation Distribution (log₁₀ CAD)",
        "log₁₀(BPEVAL)",
        "Count"
    )
    save_figure(fig, "01_valuation_distribution.png")


def plot_permits_per_year(df):
    """
    Save a bar chart showing permit counts by year.
    """
    yearly_counts = df.groupby("YEAR").size()

    fig, ax = plt.subplots(figsize=(10, 4))
    ax.bar(yearly_counts.index, yearly_counts.values, color="#4CAF50", edgecolor="white")

    style_axis(ax, "Permits Issued per Year", "Year", "Number of Permits")
    save_figure(fig, "01_permits_per_year.png")


def print_summary_stats(df):
    """
    Print a short summary of the cleaned permit dataset.
    """
    print("\n" + "=" * 60)
    print(f"Mean permit value: ${df['BPEVAL'].mean():,.0f}")
    print(f"Median permit value: ${df['BPEVAL'].median():,.0f}")
    print(f"Total investment: ${df['BPEVAL'].sum():,.0f}")


def main():
    logger.info("=" * 60)
    logger.info("STAGE 1 — Data Preprocessing")
    logger.info("=" * 60)

    df = load_raw_data()
    df = parse_permit_dates(df)
    df = filter_analysis_years(df)
    df = clean_coordinates(df)
    df = clean_valuations(df)
    df = remove_duplicate_permits(df)

    logger.info(f"Final cleaned dataset: {len(df):,} records")

    if len(df) == 0:
        logger.error("No valid records remained after cleaning.")
        df.to_csv(OUT_CSV, index=False)
        return

    plot_valuation_distribution(df)
    plot_permits_per_year(df)

    df.to_csv(OUT_CSV, index=False)
    logger.info(f"Saved → {OUT_CSV}")

    print_summary_stats(df)


if __name__ == "__main__":
    main()