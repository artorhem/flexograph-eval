#!/usr/bin/env python3
"""
Parse FlexoGraph benchmark log files and generate a CSV with performance metrics.

Usage:
    python parse_flexograph_logs.py [--output OUTPUT_FILE] [--log-dir LOG_DIR]
"""

import os
import re
import csv
import argparse
from pathlib import Path


def parse_log_file(log_path):
    """
    Parse a FlexoGraph log file to extract performance metrics.

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
    # Format: <dataset_name>_<algorithm>_adj.log
    filename = os.path.basename(log_path)

    # Skip non-matching files
    if not filename.endswith('_adj.log'):
        return None

    # Remove _adj.log suffix
    name_part = filename[:-8]  # Remove '_adj.log'

    # Split to get dataset and algorithm
    # Algorithm is the last part, dataset is everything before
    parts = name_part.rsplit('_', 1)
    if len(parts) != 2:
        print(f"Warning: Could not parse filename: {filename}")
        return None

    dataset, algo = parts

    # Read the log file
    try:
        with open(log_path, 'r') as f:
            content = f.read()
    except Exception as e:
        print(f"Error reading {log_path}: {e}")
        return None

    # Initialize result dict
    result = {
        'dataset': dataset,
        'algo': algo,
        'avg_time': None,
        'pre_processing_time': None,
        'memory_used': None,
        'major_faults': None,
        'minor_faults': None,
        'block_in': None,
        'block_out': None
    }

    # Parse preprocessing time: "Graph loaded in X.XXXs"
    preprocess_match = re.search(r'Graph loaded in ([\d.]+)s?', content)
    if preprocess_match:
        result['pre_processing_time'] = float(preprocess_match.group(1))

    # Parse average time: "Average time: X.XXX" or "Average BFS time: X.XXXs" or "Average time Trust: X.XXX"
    # Try multiple patterns to handle different algorithm output formats
    avg_time_patterns = [
        r'Average time taken for \d+ trials: ([\d.]+)s?',  # BC format (e.g., "Average time taken for 16 trials: 8.23065")
        r'Average CC took ([\d.]+)\s*s?',      # CC format (e.g., "Average CC took 3.38782 s")
        r'Average time: ([\d.]+)s?',           # Standard format
        r'Average \w+ time: ([\d.]+)s?',       # Algorithm-specific (e.g., "Average BFS time:")
        r'Average time \w+: ([\d.]+)s?',       # Triangle counting format (e.g., "Average time Trust:")
    ]

    for pattern in avg_time_patterns:
        avg_time_match = re.search(pattern, content)
        if avg_time_match:
            result['avg_time'] = float(avg_time_match.group(1))
            break

    # Parse memory: "MemoryCounter: X MB -> Y MB, Z MB total"
    memory_match = re.search(r'MemoryCounter: \d+ MB -> \d+ MB, (\d+) MB total', content)
    if memory_match:
        result['memory_used'] = int(memory_match.group(1))

    # Parse page faults: "MemoryCounter: X major faults, Y minor faults"
    faults_match = re.search(r'MemoryCounter: (\d+) major faults, (\d+) minor faults', content)
    if faults_match:
        result['major_faults'] = int(faults_match.group(1))
        result['minor_faults'] = int(faults_match.group(2))

    # Parse block I/O: "MemoryCounter: X block input operations, Y block output operations"
    io_match = re.search(r'MemoryCounter: (\d+) block input operations, (\d+) block output operations', content)
    if io_match:
        result['block_in'] = int(io_match.group(1))
        result['block_out'] = int(io_match.group(2))

    return result


def main():
    parser = argparse.ArgumentParser(
        description='Parse FlexoGraph log files and generate CSV report'
    )
    parser.add_argument(
        '--log-dir',
        default='results/flexograph',
        help='Directory containing log files (default: results/flexograph)'
    )
    parser.add_argument(
        '--output',
        default='flexograph_results.csv',
        help='Output CSV file (default: flexograph_results.csv)'
    )

    args = parser.parse_args()

    log_dir = Path(args.log_dir)

    if not log_dir.exists():
        print(f"Error: Log directory '{log_dir}' does not exist")
        return 1

    # Find all log files
    log_files = sorted(log_dir.glob('*_adj.log'))

    if not log_files:
        print(f"No log files found in {log_dir}")
        return 1

    print(f"Found {len(log_files)} log files")

    # Parse all log files
    results = []
    for log_file in log_files:
        print(f"Parsing {log_file.name}...")
        result = parse_log_file(log_file)
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
