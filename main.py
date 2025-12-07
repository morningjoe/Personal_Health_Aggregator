"""
Personal Health Data Aggregator - Main Module
==============================================

Merges sleep and workout data from different sources with different timezone formats.

Key Design Decisions:
1. Uses `zoneinfo` (Python 3.9+) for robust timezone handling - NOT manual math
2. All data normalized to UTC before merging
3. Day attribution is based on UTC date (configurable)
4. Explicitly handles day boundary crossings

This module serves as the CLI entry point and orchestrates the workflow by
importing functions and classes from specialized modules.
"""

import argparse

# Import from modules
from tool.data_loader import load_sleep_data, load_workout_data
from tool.merger import merge_by_day, calculate_correlations
from tool.reporter import (
    print_day_boundary_analysis,
    print_merged_data,
    print_correlations,
    generate_json_output,
    save_json_output
)


# =============================================================================
# CLI INTERFACE
# =============================================================================

def create_parser():
    """Create and return the argument parser for CLI."""
    parser = argparse.ArgumentParser(
        prog='Personal Health Data Aggregator',
        description='Merges sleep and workout data from different sources with timezone normalization.',
        epilog='Example: python main.py --sleep data/sleep.json --workouts data/workouts.json --output merged_data.json --show-summary',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    parser.add_argument(
        '--sleep',
        type=str,
        default='data/sleep.json',
        help='Path to sleep data JSON file (default: data/sleep.json)'
    )

    parser.add_argument(
        '--workouts',
        type=str,
        default='data/workouts.json',
        help='Path to workout data JSON file (default: data/workouts.json)'
    )

    parser.add_argument(
        '--output',
        type=str,
        default='merged_health_data.json',
        help='Output file path for merged JSON data (default: merged_health_data.json)'
    )

    parser.add_argument(
        '--show-summary',
        action='store_true',
        help='Print human-readable summary to console (default: False)'
    )

    parser.add_argument(
        '--show-boundaries',
        action='store_true',
        help='Show day boundary crossing analysis (default: False)'
    )

    parser.add_argument(
        '--show-correlations',
        action='store_true',
        help='Show correlation analysis between sleep and exercise (default: False)'
    )

    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Show all outputs (boundaries, summary, correlations)'
    )

    return parser


def main():
    """Main entry point for the application."""
    parser = create_parser()
    args = parser.parse_args()

    print("\nPersonal Health Data Aggregator")
    print("=" * 70)

    try:
        # Load data
        print("\nLoading data...")
        sleep_data = load_sleep_data(args.sleep)
        print(f"  Loaded {len(sleep_data)} sleep records (UTC)")

        workout_data = load_workout_data(args.workouts)
        print(f"  Loaded {len(workout_data)} workout records (converted from local time)")

        # Show day boundary analysis if requested
        if args.verbose or args.show_boundaries:
            print_day_boundary_analysis(workout_data)

        # Merge data
        print("\nMerging data by UTC date...")
        merged = merge_by_day(sleep_data, workout_data)
        print(f"  Created {len(merged)} daily aggregates")

        # Show summary if requested
        if args.verbose or args.show_summary:
            print_merged_data(merged)

        # Calculate correlations
        correlations = calculate_correlations(merged)

        # Show correlations if requested
        if args.verbose or args.show_correlations:
            print_correlations(correlations)

        # Generate and save JSON output
        print("\nGenerating JSON output...")
        json_output = generate_json_output(merged, workout_data, correlations)
        save_json_output(json_output, args.output)

        print("\n" + "=" * 70)
        print("Aggregation complete!")
        print("=" * 70 + "\n")

    except FileNotFoundError as e:
        print(f"\nFile Error: {e}", flush=True)
        print("   Check that the input files exist and paths are correct.\n", flush=True)
        return 1
    except (KeyError, TypeError) as e:
        print(f"\nData Structure Error: {e}", flush=True)
        print("   The JSON file structure is invalid.", flush=True)
        print("   Sleep data must contain 'records' key, workout data must contain 'workout_log' key.\n", flush=True)
        return 1
    except ValueError as e:
        print(f"\nData Validation Error: {e}", flush=True)
        print("   Check your input data for invalid values, missing fields, or incorrect formats.\n", flush=True)
        return 1
    except Exception as e:
        print(f"\nUnexpected error: {e}\n", flush=True)
        return 1

    return 0


if __name__ == '__main__':
    exit(main())