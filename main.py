"""
main.py — Master pipeline runner
"""
import argparse, sys, os, time
sys.path.insert(0, "src")
from utils import logger

STAGES = {
    1: ("Data Preprocessing", "01_preprocessing"),
    2: ("Spatial Analysis", "02_spatial_analysis"),
    3: ("K-Means Clustering", "03_kmeans_clustering"),
    4: ("DBSCAN Clustering", "04_dbscan_clustering"),
    5: ("Getis-Ord Hotspot", "05_getis_ord"),
    6: ("Temporal Analysis", "06_temporal_analysis"),
    7: ("Assessment Integration", "07_assessment_integration"),
    8: ("Final Visualizations", "08_final_visualizations"),
}

def run_stage(n):
    name, module = STAGES[n]
    logger.info(f"\n{'━'*60}")
    logger.info(f"  Stage {n}: {name}")
    logger.info(f"{'━'*60}")
    
    t0 = time.time()
    try:
        import importlib
        mod = importlib.import_module(module)
        mod.main()
        logger.info(f"✓  Stage {n} done ({time.time()-t0:.1f}s)")
        return True
    except Exception as e:
        logger.error(f"✗  Stage {n} failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--stage", type=int, choices=STAGES.keys())
    parser.add_argument("--from", dest="from_stage", type=int, choices=STAGES.keys())
    args = parser.parse_args()
    
    print("\n" + "═"*60)
    print("   THE RENOVATION ROADMAP")
    print("   Saint John Urban Investment Analysis")
    print("═"*60 + "\n")
    
    if args.stage:
        stages = [args.stage]
    elif args.from_stage:
        stages = list(range(args.from_stage, 9))
    else:
        stages = list(STAGES.keys())
    
    results = {}
    for n in stages:
        results[n] = run_stage(n)
    
    print(f"\n{'═'*60}")
    print("  PIPELINE COMPLETE")
    print(f"{'═'*60}")
    for n, ok in results.items():
        print(f"  Stage {n}: {'✓ OK' if ok else '✗ FAILED'}")
    
    if not all(results.values()):
        sys.exit(1)

if __name__ == "__main__":
    main()
