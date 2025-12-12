#!/usr/bin/env python3
"""
Parse Ligra benchmark result CSV files and generate a consolidated CSV with performance metrics.

Usage:
    python parse_ligra_results.py [--output OUTPUT_FILE] [--results-dir RESULTS_DIR]
"""

import os
import csv
import argparse
from pathlib import Path


def parse_csv_file(csv_path):
    """
    Parse a Ligra result CSV file to extract performance metrics.

    Returns a dict with the following keys:
        - dataset: dataset name
        - algo: algorithm name
        - avg_time: average execution time (seconds)
        - pre_processing_time: graph conversion + loading time (seconds)
        - memory_used: total memory used (MB)
        - major_faults: number of major page faults
        - minor_faults: number of minor page faults
        - block_in: block input operations
        - block_out: block output operations
    """
    # Extract dataset and algorithm from filename
    # Format: <dataset>_<Algorithm>.csv
    # Examples:
    #   graph500_26_PageRank.csv -> graph500_26, pagerank
    #   graph500_26_Components.csv -> graph500_26, cc
    #   graph500_26_Triangle.csv -> graph500_26, tc
    #   graph500_26_BFS.csv -> graph500_26, bfs
    #   graph500_26_BC.csv -> graph500_26, bc
    #   graph500_26_BellmanFord.csv -> graph500_26, sssp
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

    dataset, ligra_algo = parts

    # Normalize algorithm names to match FlexoGraph conventions
    algo_mappings = {
        'PageRank': 'pagerank',
        'Components': 'cc',
        'Triangle': 'tc',
        'BFS': 'bfs',
        'BC': 'bc',
        'BellmanFord': 'sssp'
    }

    algo = algo_mappings.get(ligra_algo, ligra_algo.lower())

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

            # Parse data based on whether it has start_vertex or not
            values = [v.strip() for v in data_line.split(',')]

            # Two possible formats:
            # 1. convert_time(s), read_time(s), algo_time(s), memory(MB), maj_flt, min_flt, blk_in, blk_out
            # 2. convert_time(s), read_time(s), algo_time(s), memory(MB), start_vertex, maj_flt, min_flt, blk_in, blk_out

            if 'start_vertex' in header:
                # Format with start_vertex
                if len(values) >= 8:
                    conv_time = float(values[0])
                    read_time = float(values[1])
                    algo_time = float(values[2])
                    memory = int(float(values[3]))
                    # values[4] is start_vertex, skip it
                    maj_flt = int(float(values[5]))
                    min_flt = int(float(values[6]))
                    blk_in = int(float(values[7]))
                    blk_out = int(float(values[8])) if len(values) > 8 else 0
                else:
                    print(f"Warning: Unexpected format in {filename}")
                    return None
            else:
                # Format without start_vertex
                if len(values) >= 7:
                    conv_time = float(values[0])
                    read_time = float(values[1])
                    algo_time = float(values[2])
                    memory = int(float(values[3]))
                    maj_flt = int(float(values[4]))
                    min_flt = int(float(values[5]))
                    blk_in = int(float(values[6]))
                    blk_out = int(float(values[7])) if len(values) > 7 else 0
                else:
                    print(f"Warning: Unexpected format in {filename}")
                    return None

            # Pre-processing time = conversion time + read time
            pp_time = conv_time + read_time

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
        description='Parse Ligra result files and generate CSV report'
    )
    parser.add_argument(
        '--results-dir',
        default='results/ligra',
        help='Directory containing result files (default: results/ligra)'
    )
    parser.add_argument(
        '--output',
        default='ligra_results.csv',
        help='Output CSV file (default: ligra_results.csv)'
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
