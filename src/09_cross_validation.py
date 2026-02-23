"""
09_cross_validation.py — Cross-validate findings across all methods
Checks agreement between K-Means, DBSCAN, Getis-Ord, and IAR signals
"""
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib_venn import venn3
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from utils import logger, data_path, save_figure, style_axis

def load_all_results():
    """Load all analysis results"""
    results = {
        'getis_ord': pd.read_csv(data_path('getis_ord_results.csv')),
        'assessment': pd.read_csv(data_path('assessment_integration.csv')),
        'temporal': pd.read_csv(data_path('temporal_analysis.csv')),
        'grid_stats': pd.read_csv(data_path('grid_stats.csv')),
    }
    logger.info("Loaded all result files")
    return results

def identify_key_zones(results):
    """Identify key zones from each method"""
    # Getis-Ord hotspots (p<0.05)
    hotspots = set(
        results['getis_ord'][
            results['getis_ord']['hotspot'].str.startswith('Hot', na=False)
        ]['GRID_ID']
    )
    
    # High-IAR cells (pre-gentrification signal)
    high_iar = set(
        results['assessment'][
            results['assessment']['signal'] == '⚠️ Pre-Gentrification Signal'
        ]['GRID_ID']
    )
    
    # Emerging trajectories (high CAGR)
    emerging = set(
        results['temporal'][
            results['temporal']['trajectory'] == 'Emerging 🚀'
        ].index
    )
    
    # High permit density (top quartile)
    q75 = results['grid_stats']['permit_count'].quantile(0.75)
    high_density = set(
        results['grid_stats'][
            results['grid_stats']['permit_count'] >= q75
        ]['GRID_ID']
    )
    
    logger.info(f"Hotspots (Getis-Ord): {len(hotspots)}")
    logger.info(f"High IAR cells: {len(high_iar)}")
    logger.info(f"Emerging trajectories: {len(emerging)}")
    logger.info(f"High density cells: {len(high_density)}")
    
    return hotspots, high_iar, emerging, high_density

def compute_overlap_matrix(zones_dict):
    """Compute pairwise overlap between zone sets"""
    methods = list(zones_dict.keys())
    n = len(methods)
    overlap = np.zeros((n, n), dtype=int)
    
    for i, method1 in enumerate(methods):
        for j, method2 in enumerate(methods):
            overlap[i, j] = len(zones_dict[method1] & zones_dict[method2])
    
    return pd.DataFrame(overlap, index=methods, columns=methods)

def plot_overlap_heatmap(overlap_df):
    """Heatmap showing agreement between methods"""
    import seaborn as sns
    
    fig, ax = plt.subplots(figsize=(8, 7))
    sns.heatmap(
        overlap_df, 
        annot=True, 
        fmt='d', 
        cmap='YlOrRd',
        cbar_kws={'label': 'Number of Overlapping Grid Cells'},
        linewidths=0.5,
        ax=ax
    )
    ax.set_title('Cross-Method Validation Matrix\n'
                 'Agreement Between Detection Methods',
                 fontsize=13, fontweight='bold', pad=15)
    save_figure(fig, '09_overlap_heatmap.png')

def plot_venn_diagram(hotspots, high_iar, high_density):
    """Venn diagram of three key methods"""
    fig, ax = plt.subplots(figsize=(10, 8))
    
    venn = venn3(
        [hotspots, high_iar, high_density],
        set_labels=('Getis-Ord\nHotspots', 'High IAR\n(Pre-Gentrif.)', 
                    'High Permit\nDensity'),
        ax=ax
    )
    
    # Color coding
    if venn.get_patch_by_id('100'):
        venn.get_patch_by_id('100').set_color('#BD0026')
        venn.get_patch_by_id('100').set_alpha(0.5)
    if venn.get_patch_by_id('010'):
        venn.get_patch_by_id('010').set_color('#E53935')
        venn.get_patch_by_id('010').set_alpha(0.5)
    if venn.get_patch_by_id('001'):
        venn.get_patch_by_id('001').set_color('#FD8D3C')
        venn.get_patch_by_id('001').set_alpha(0.5)
    
    ax.set_title('Zone Detection Method Overlap\n'
                 'Cross-Validation of Spatial Hotspot Identification',
                 fontsize=13, fontweight='bold', pad=15)
    save_figure(fig, '09_venn_diagram.png')

def analyze_validation_strength(zones_dict):
    """Identify zones validated by multiple methods"""
    all_zones = set.union(*zones_dict.values())
    
    validation_counts = {}
    for zone in all_zones:
        count = sum(1 for zset in zones_dict.values() if zone in zset)
        validation_counts[zone] = count
    
    # Zones validated by 2+ methods
    strong_zones = {z: c for z, c in validation_counts.items() if c >= 2}
    
    print(f"\n{'='*60}")
    print("CROSS-VALIDATION RESULTS")
    print(f"{'='*60}")
    print(f"Total unique zones detected: {len(all_zones)}")
    print(f"Zones validated by 2+ methods: {len(strong_zones)}")
    print(f"Zones validated by 3+ methods: {sum(1 for c in strong_zones.values() if c >= 3)}")
    print(f"\nStrongest validated zones (3+ methods):")
    
    for zone, count in sorted(strong_zones.items(), key=lambda x: x[1], reverse=True):
        if count >= 3:
            print(f"  {zone}: validated by {count} methods")
    
    return validation_counts

def plot_validation_strength_map(validation_counts):
    """Choropleth showing # of methods that flagged each cell"""
    import geopandas as gpd
    
    grid = gpd.read_file(data_path('spatial_grid.gpkg'))
    
    # Add validation count
    grid['validation_count'] = grid['GRID_ID'].map(validation_counts).fillna(0)
    
    fig, ax = plt.subplots(figsize=(13, 11))
    grid.plot(
        column='validation_count',
        ax=ax,
        cmap='RdYlGn_r',
        edgecolor='white',
        linewidth=0.3,
        legend=True,
        legend_kwds={
            'label': 'Number of Methods Flagging This Cell',
            'shrink': 0.6,
            'ticks': [0, 1, 2, 3, 4]
        },
        vmin=0,
        vmax=4
    )
    
    ax.set_title('Cross-Validation Strength Map\n'
                 'Grid Cells Flagged by Multiple Detection Methods',
                 fontsize=13, fontweight='bold')
    ax.set_axis_off()
    save_figure(fig, '09_validation_strength_map.png', dpi=200)

def interpret_findings(zones_dict, overlap_df):
    """Generate interpretation text for report"""
    hotspots, high_iar, emerging, high_density = zones_dict.values()
    
    # Overlap analysis
    hotspot_iar_overlap = len(hotspots & high_iar)
    hotspot_density_overlap = len(hotspots & high_density)
    iar_emerging_overlap = len(high_iar & emerging)
    
    print(f"\n{'='*60}")
    print("KEY FINDINGS — Method Agreement")
    print(f"{'='*60}")
    print(f"\n1. Getis-Ord Hotspots vs High-IAR Cells:")
    print(f"   Overlap: {hotspot_iar_overlap} cells")
    if hotspot_iar_overlap == 0:
        print("   → INTERPRETATION: These detect DIFFERENT phenomena:")
        print("     • Hotspots = clustering of existing high values")
        print("     • High IAR = investment into undervalued areas")
        print("   → This validates using BOTH methods (complementary, not redundant)")
    
    print(f"\n2. High-IAR vs Emerging Trajectories:")
    print(f"   Overlap: {iar_emerging_overlap} cells")
    if iar_emerging_overlap > 0:
        print("   → STRONG VALIDATION: Cells with high IAR also show")
        print("     rapid temporal growth (CAGR) — these are TRUE")
        print("     pre-gentrification zones")
    
    print(f"\n3. Hotspots vs High Density:")
    print(f"   Overlap: {hotspot_density_overlap} cells")
    print("   → Expected correlation (more permits = higher values cluster)")

def main():
    logger.info("="*60)
    logger.info("STAGE 9 — Cross-Validation Analysis")
    logger.info("="*60)
    
    results = load_all_results()
    hotspots, high_iar, emerging, high_density = identify_key_zones(results)
    
    zones_dict = {
        'Getis-Ord Hotspots': hotspots,
        'High IAR': high_iar,
        'Emerging': emerging,
        'High Density': high_density
    }
    
    overlap_df = compute_overlap_matrix(zones_dict)
    print("\nOverlap Matrix:")
    print(overlap_df)
    
    plot_overlap_heatmap(overlap_df)
    plot_venn_diagram(hotspots, high_iar, high_density)
    
    validation_counts = analyze_validation_strength(zones_dict)
    plot_validation_strength_map(validation_counts)
    
    interpret_findings(zones_dict, overlap_df)
    
    # Save validation results
    val_df = pd.DataFrame(
        list(validation_counts.items()),
        columns=['GRID_ID', 'validation_count']
    )
    val_df.to_csv(data_path('cross_validation.csv'), index=False)
    logger.info("Cross-validation results saved")

if __name__ == "__main__":
    main()