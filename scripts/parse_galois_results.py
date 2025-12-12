#!/usr/bin/env python3
"""
Parse Galois benchmark result CSV files and generate a consolidated CSV with performance metrics.

Usage:
    python parse_galois_results.py [--output OUTPUT_FILE] [--results-dir RESULTS_DIR]
"""

import os
import csv
import argparse
from pathlib import Path


def parse_csv_file(csv_path):
    """
    Parse a Galois result CSV file to extract performance metrics.

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
    # Format: <dataset>_<algo>_<variant>.csv
    # Examples:
    #   graph500_26_bfs_synctile_parallel_time.csv -> graph500_26, bfs
    #   graph500_26_pagerank-pull_residual.csv -> graph500_26, pagerank
    #   graph500_26_connectedcomponents_labelprop.csv -> graph500_26, connectedcomponents
    #   graph500_26_triangle_orderedCount.csv -> graph500_26, triangle (tc)
    #   graph500_26_bc_bc.csv -> graph500_26, bc
    filename = os.path.basename(csv_path)

    # Skip non-matching files
    if not filename.endswith('.csv'):
        return None

    # Remove .csv suffix
    name_part = filename[:-4]

    # Parse the filename to extract dataset and algorithm
    # Known algorithm patterns in Galois filenames
    algo_mappings = {
        'bfs_synctile_parallel_time': 'bfs',
        'pagerank-pull_residual': 'pagerank',
        'connectedcomponents_labelprop': 'cc',
        'triangle_orderedCount': 'tc',
        'bc_bc': 'bc',
        'sssp_sssp': 'sssp'
    }

    dataset = None
    algo = None

    for pattern, algo_name in algo_mappings.items():
        if name_part.endswith('_' + pattern):
            # Extract dataset by removing the pattern
            dataset = name_part[:-(len(pattern) + 1)]
            algo = algo_name
            break

    if dataset is None or algo is None:
        print(f"Warning: Could not parse filename: {filename}")
        return None

    # Read the CSV file
    try:
        with open(csv_path, 'r') as f:
            lines = f.readlines()
            if len(lines) < 2:
                print(f"Warning: Empty or invalid CSV: {filename}")
                return None

            # Skip header line, read data lines (multiple trials)
            header = lines[0].strip()
            data_lines = [line.strip() for line in lines[1:] if line.strip()]

            if not data_lines:
                print(f"Warning: No data in CSV: {filename}")
                return None

            # Parse all trials
            conv_times = []
            read_times = []
            algo_times = []
            memories = []
            maj_faults = []
            min_faults = []
            blk_ins = []
            blk_outs = []

            for data_line in data_lines:
                values = [v.strip() for v in data_line.split(',')]

                # Two possible formats:
                # 1. conv_time(s),read_time(ms),algo_time(ms),start_node,mem_used(MB),num_threads,major_faults,minor_faults,block_input,block_output
                # 2. conv_time(s),read_time(ms),algo_time(ms),mem_used(MB),num_threads,major_faults,minor_faults,block_input,block_output

                if 'start_node' in header:
                    # Format with start_node
                    if len(values) >= 9:
                        conv_times.append(float(values[0]))
                        read_times.append(float(values[1]))  # milliseconds
                        algo_times.append(float(values[2]))  # milliseconds
                        # values[3] is start_node, skip it
                        memories.append(int(values[4]))
                        # values[5] is num_threads, skip it
                        maj_faults.append(int(values[6]))
                        min_faults.append(int(values[7]))
                        blk_ins.append(int(values[8]))
                        blk_outs.append(int(values[9])) if len(values) > 9 else 0
                else:
                    # Format without start_node
                    if len(values) >= 8:
                        conv_times.append(float(values[0]))
                        read_times.append(float(values[1]))  # milliseconds
                        algo_times.append(float(values[2]))  # milliseconds
                        memories.append(int(values[3]))
                        # values[4] is num_threads, skip it
                        maj_faults.append(int(values[5]))
                        min_faults.append(int(values[6]))
                        blk_ins.append(int(values[7]))
                        blk_outs.append(int(values[8])) if len(values) > 8 else 0

            # Calculate averages
            if not algo_times:
                print(f"Warning: No valid data parsed from {filename}")
                return None

            conv_time = conv_times[0] if conv_times else 0  # Same for all trials
            read_time_avg = sum(read_times) / len(read_times) / 1000.0  # Convert ms to s
            algo_time_avg = sum(algo_times) / len(algo_times) / 1000.0  # Convert ms to s
            memory_avg = int(sum(memories) / len(memories))
            maj_flt_avg = int(sum(maj_faults) / len(maj_faults))
            min_flt_avg = int(sum(min_faults) / len(min_faults))
            blk_in_avg = int(sum(blk_ins) / len(blk_ins))
            blk_out_avg = int(sum(blk_outs) / len(blk_outs))

            # Pre-processing time = conversion time + read time
            pp_time = conv_time + read_time_avg

    except Exception as e:
        print(f"Error reading {csv_path}: {e}")
        return None

    # Initialize result dict
    result = {
        'dataset': dataset,
        'algo': algo,
        'avg_time': algo_time_avg,
        'pre_processing_time': pp_time,
        'memory_used': memory_avg,
        'major_faults': maj_flt_avg,
        'minor_faults': min_flt_avg,
        'block_in': blk_in_avg,
        'block_out': blk_out_avg
    }

    return result


def main():
    parser = argparse.ArgumentParser(
        description='Parse Galois result files and generate CSV report'
    )
    parser.add_argument(
        '--results-dir',
        default='results/galois',
        help='Directory containing result files (default: results/galois)'
    )
    parser.add_argument(
        '--output',
        default='galois_results.csv',
        help='Output CSV file (default: galois_results.csv)'
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
