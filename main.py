"""
main.py

Master pipeline runner for The Renovation Roadmap project.
This script lets me run the full analysis pipeline or start from a
specific stage.
"""

import argparse
import importlib
import sys
import time
import traceback

# Make sure Python can find modules inside src/
sys.path.insert(0, "src")

from utils import logger


STAGES = {
    1: ("Data Preprocessing", "01_preprocessing"),
    2: ("Spatial Analysis", "02_spatial_analysis"),
    3: ("K-Means Clustering", "03_kmeans_clustering"),
    4: ("DBSCAN Clustering", "04_dbscan_clustering"),
    5: ("Getis-Ord Hotspot Analysis", "05_getis_ord"),
    6: ("Temporal Analysis", "06_temporal_analysis"),
    7: ("Assessment Integration", "07_assessment_integration"),
    8: ("Final Visualizations", "08_final_visualizations"),
}


def run_stage(stage_number):
    """
    Import and run one pipeline stage by its number.
    Returns True if the stage succeeds, otherwise False.
    """
    stage_name, module_name = STAGES[stage_number]

    logger.info(f"\n{'━' * 60}")
    logger.info(f"  Stage {stage_number}: {stage_name}")
    logger.info(f"{'━' * 60}")

    start_time = time.time()

    try:
        module = importlib.import_module(module_name)
        module.main()

        elapsed = time.time() - start_time
        logger.info(f"✓  Stage {stage_number} done ({elapsed:.1f}s)")
        return True

    except Exception as exc:
        logger.error(f"✗  Stage {stage_number} failed: {exc}")
        traceback.print_exc()
        return False


def get_requested_stages(args):
    """
    Return the list of stages to run based on command-line arguments.
    """
    if args.stage:
        return [args.stage]

    if args.from_stage:
        return list(range(args.from_stage, len(STAGES) + 1))

    return list(STAGES.keys())


def print_header():
    """Print the project header."""
    print("\n" + "═" * 60)
    print("   THE RENOVATION ROADMAP")
    print("   Saint John Urban Investment Analysis")
    print("═" * 60 + "\n")


def print_summary(results):
    """Print the final pipeline summary."""
    print(f"\n{'═' * 60}")
    print("  PIPELINE COMPLETE")
    print(f"{'═' * 60}")

    for stage_number, success in results.items():
        status = "✓ OK" if success else "✗ FAILED"
        print(f"  Stage {stage_number}: {status}")


def parse_args():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Run the Renovation Roadmap analysis pipeline."
    )
    parser.add_argument(
        "--stage",
        type=int,
        choices=STAGES.keys(),
        help="Run only one specific stage"
    )
    parser.add_argument(
        "--from",
        dest="from_stage",
        type=int,
        choices=STAGES.keys(),
        help="Run all stages starting from this stage number"
    )
    return parser.parse_args()


def main():
    args = parse_args()

    print_header()

    stages_to_run = get_requested_stages(args)

    results = {}
    for stage_number in stages_to_run:
        results[stage_number] = run_stage(stage_number)

    print_summary(results)

    if not all(results.values()):
        sys.exit(1)


if __name__ == "__main__":
    main()