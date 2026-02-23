"""
01_preprocessing.py — Data cleaning (FIXED coordinate columns)
"""
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from utils import logger, data_path, save_figure, style_axis

RAW_CSV = data_path("Building_Permits.csv")
OUT_CSV = data_path("permits_cleaned.csv")

def load_raw():
    for enc in ("utf-8", "latin-1"):
        try:
            df = pd.read_csv(RAW_CSV, encoding=enc, low_memory=False)
            logger.info(f"Loaded {len(df):,} raw permits ({enc})")
            return df
        except:
            continue
    raise ValueError(f"Cannot read {RAW_CSV}")

def parse_dates(df):
    """Parse BPPISD (Permit Issue Date) — format: YYMMDD integer"""
    df["BPPISD"] = pd.to_numeric(df["BPPISD"], errors="coerce")
    
    def parse_yymmdd(x):
        if pd.isna(x) or x == 0:
            return pd.NaT
        s = str(int(x)).zfill(6)
        yy, mm, dd = s[:2], s[2:4], s[4:6]
        year = 1900 + int(yy) if int(yy) > 50 else 2000 + int(yy)
        try:
            return pd.Timestamp(year=year, month=int(mm), day=int(dd))
        except:
            return pd.NaT
    
    df["BPISDT"] = df["BPPISD"].apply(parse_yymmdd)
    df["YEAR"] = df["BPISDT"].dt.year
    
    before = len(df)
    df = df.dropna(subset=["BPISDT"])
    logger.info(f"Date parsing: {before - len(df):,} invalid dates dropped")
    return df

def filter_years(df, year_min=2015, year_max=2025):
    before = len(df)
    df = df[(df["YEAR"] >= year_min) & (df["YEAR"] <= year_max)].copy()
    logger.info(f"Year filter ({year_min}-{year_max}): {before:,} → {len(df):,}")
    return df

def clean_coordinates(df):
    """
    FIX: Use X_Long_East (longitude) and Y_Lat_North (latitude)
    These are the ACTUAL WGS84 coordinates in your CSV
    """
    # Try both column name variants
    lon_col = "X_Long_East" if "X_Long_East" in df.columns else "POINT_X"
    lat_col = "Y_Lat_North" if "Y_Lat_North" in df.columns else "POINT_Y"
    
    df["POINT_X"] = pd.to_numeric(df[lon_col], errors="coerce")
    df["POINT_Y"] = pd.to_numeric(df[lat_col], errors="coerce")
    
    # Saint John bounding box
    valid = (
        df["POINT_X"].between(-66.2, -65.8) &
        df["POINT_Y"].between(45.1, 45.5)
    )
    
    n_invalid = (~valid).sum()
    logger.info(f"Coordinates: {n_invalid:,} invalid/missing, {valid.sum():,} valid")
    return df[valid].copy()

def clean_valuations(df):
    """BPEVAL = project valuation in CAD"""
    df["BPEVAL"] = pd.to_numeric(df["BPEVAL"], errors="coerce")
    before = len(df)
    
    # Remove zeros and NaNs
    df = df[df["BPEVAL"] > 0].copy()
    
    # Remove extreme outliers (keep 1st to 99th percentile)
    p01 = df["BPEVAL"].quantile(0.01)
    p99 = df["BPEVAL"].quantile(0.99)
    df = df[(df["BPEVAL"] >= p01) & (df["BPEVAL"] <= p99)].copy()
    
    logger.info(f"Valuation cleaning: {before - len(df):,} dropped")
    return df

def remove_duplicates(df):
    before = len(df)
    # Use street name + date + value as duplicate key
    subset = ["ENCIVSTNAM", "BPISDT", "BPEVAL"]
    subset = [c for c in subset if c in df.columns]
    if subset:
        df = df.drop_duplicates(subset=subset)
    logger.info(f"Duplicates removed: {before - len(df):,}")
    return df

def plot_valuation_dist(df):
    fig, ax = plt.subplots(figsize=(9, 4))
    log_vals = np.log10(df["BPEVAL"].clip(1))
    ax.hist(log_vals, bins=60, color="#2196F3", edgecolor="white", alpha=0.85)
    style_axis(ax, "Project Valuation Distribution (log₁₀ CAD)", 
               "log₁₀(BPEVAL)", "Count")
    save_figure(fig, "01_valuation_distribution.png")

def plot_permits_per_year(df):
    counts = df.groupby("YEAR").size()
    fig, ax = plt.subplots(figsize=(10, 4))
    ax.bar(counts.index, counts.values, color="#4CAF50", edgecolor="white")
    style_axis(ax, "Permits Issued per Year", "Year", "Number of Permits")
    save_figure(fig, "01_permits_per_year.png")

def main():
    logger.info("="*60)
    logger.info("STAGE 1 — Data Preprocessing")
    logger.info("="*60)
    
    df = load_raw()
    df = parse_dates(df)
    df = filter_years(df)
    df = clean_coordinates(df)
    df = clean_valuations(df)
    df = remove_duplicates(df)
    
    logger.info(f"Final cleaned dataset: {len(df):,} records")
    
    if len(df) > 0:
        plot_valuation_dist(df)
        plot_permits_per_year(df)
        
        df.to_csv(OUT_CSV, index=False)
        logger.info(f"Saved → {OUT_CSV}")
        
        print("\n" + "="*60)
        print(f"Mean permit value: ${df['BPEVAL'].mean():,.0f}")
        print(f"Median permit value: ${df['BPEVAL'].median():,.0f}")
        print(f"Total investment: ${df['BPEVAL'].sum():,.0f}")
    else:
        logger.error("NO VALID RECORDS after cleaning — check your data!")
        df.to_csv(OUT_CSV, index=False)  # Save empty file to prevent downstream errors

if __name__ == "__main__":
    main()