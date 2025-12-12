#!/usr/bin/env python3
"""
Parse GAPBS benchmark result CSV files and generate a consolidated CSV with performance metrics.

Usage:
    python parse_gapbs_results.py [--output OUTPUT_FILE] [--results-dir RESULTS_DIR]
"""

import os
import csv
import argparse
from pathlib import Path


def parse_csv_file(csv_path):
    """
    Parse a GAPBS result CSV file to extract performance metrics.

    Returns a dict with the following keys:
        - dataset: dataset name
        - algo: algorithm name
        - avg_time: average execution time (seconds)
        - pre_processing_time: graph loading time (seconds)
        - memory_used: total memory used (MB)
        - major_faults: number of major page faults
        - minor_faults: number of minor page faults
        - block_in: block input operations
        - block_out: block output operations
    """
    # Extract dataset and algorithm from filename
    # Format: <dataset>_<algorithm>.csv
    filename = os.path.basename(csv_path)

    # Skip non-matching files
    if not filename.endswith('.csv'):
        return None

    # Remove .csv suffix
    name_part = filename[:-4]

    # Split to get dataset and algorithm
    # Algorithm is the last part, dataset is everything before
    parts = name_part.rsplit('_', 1)
    if len(parts) != 2:
        print(f"Warning: Could not parse filename: {filename}")
        return None

    dataset, algo = parts

    # Read the CSV file
    try:
        with open(csv_path, 'r') as f:
            lines = f.readlines()
            if len(lines) < 2:
                print(f"Warning: Empty or invalid CSV: {filename}")
                return None

            # Skip header line, read data line
            header = lines[0].strip()
            data_line = lines[1].strip()

            # Parse data based on whether it has start_node or not
            values = [v.strip() for v in data_line.split(',')]

            # Two possible formats:
            # 1. pp_time(s),algo_time(s),mem(MB),num_threads, maj_flt, min_flt, blk_in, blk_out
            # 2. pp_time(s),algo_time(s),start_node,mem_used(MB),num_threads, maj_flt, min_flt, blk_in, blk_out

            if 'start_node' in header or 'start_vertex' in header:
                # Format with start_node
                if len(values) >= 8:
                    pp_time = float(values[0])
                    algo_time = float(values[1])
                    # values[2] is start_node, skip it
                    memory = int(float(values[3]))
                    # values[4] is num_threads, skip it
                    maj_flt = int(float(values[5]))
                    min_flt = int(float(values[6]))
                    blk_in = int(float(values[7]))
                    blk_out = int(float(values[8])) if len(values) > 8 else 0
                else:
                    print(f"Warning: Unexpected format in {filename}")
                    return None
            else:
                # Format without start_node
                if len(values) >= 7:
                    pp_time = float(values[0])
                    algo_time = float(values[1])
                    memory = int(float(values[2]))
                    # values[3] is num_threads, skip it
                    maj_flt = int(float(values[4]))
                    min_flt = int(float(values[5]))
                    blk_in = int(float(values[6]))
                    blk_out = int(float(values[7])) if len(values) > 7 else 0
                else:
                    print(f"Warning: Unexpected format in {filename}")
                    return None

    except Exception as e:
        print(f"Error reading {csv_path}: {e}")
        return None

    # Initialize result dict
    result = {
        'dataset': dataset,
        'algo': algo,
        'avg_time': algo_time,
        'pre_processing_time': pp_time,
        'memory_used': memory,
        'major_faults': maj_flt,
        'minor_faults': min_flt,
        'block_in': blk_in,
        'block_out': blk_out
    }

    return result


def main():
    parser = argparse.ArgumentParser(
        description='Parse GAPBS result files and generate CSV report'
    )
    parser.add_argument(
        '--results-dir',
        default='results/gapbs',
        help='Directory containing result files (default: results/gapbs)'
    )
    parser.add_argument(
        '--output',
        default='gapbs_results.csv',
        help='Output CSV file (default: gapbs_results.csv)'
    )

    args = parser.parse_args()

    results_dir = Path(args.results_dir)

    if not results_dir.exists():
        print(f"Error: Results directory '{results_dir}' does not exist")
        return 1

    # Find all CSV files
    csv_files = sorted(results_dir.glob('*.csv'))

    if not csv_files:
        print(f"No CSV files found in {results_dir}")
        return 1

    print(f"Found {len(csv_files)} CSV files")

    # Parse all CSV files
    results = []
    for csv_file in csv_files:
        print(f"Parsing {csv_file.name}...")
        result = parse_csv_file(csv_file)
        if result:
            results.append(result)

    if not results:
        print("No valid results parsed")
        return 1

    # Write CSV
    fieldnames = [
        'dataset',
        'algo',
        'avg_time',
        'pre_processing_time',
        'memory_used',
        'major_faults',
        'minor_faults',
        'block_in',
        'block_out'
    ]

    output_path = Path(args.output)
    with open(output_path, 'w', newline='') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(results)

    print(f"\nSuccessfully wrote {len(results)} results to {output_path}")
    print(f"\nSummary:")
    print(f"  Datasets: {len(set(r['dataset'] for r in results))}")
    print(f"  Algorithms: {len(set(r['algo'] for r in results))}")

    return 0


if __name__ == '__main__':
    exit(main())
