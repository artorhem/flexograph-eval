#!/usr/bin/env python3

import os
import re
import matplotlib.pyplot as plt
import pandas as pd
import argparse
import glob
import numpy as np
from datetime import datetime
from collections import defaultdict
import seaborn as sns

# Set style for prettier plots
plt.style.use('seaborn-v0_8')
sns.set_palette("husl")

def parse_iostat_log(filename):
    """
    Parse iostat log file and extract read/write bandwidth data.
    Expected format from 'iostat -d -x 1 | grep -v loop':
    
    Device            r/s     rMB/s   rrqm/s  %rrqm r_await rareq-sz     w/s     wMB/s   wrqm/s  %wrqm w_await wareq-sz     d/s     dMB/s   drqm/s  %drqm d_await dareq-sz     f/s f_await  aqu-sz  %util
    """
    data = []
    current_timestamp = 0  # Use sequential timestamps since iostat outputs every second
    
    with open(filename, 'r') as f:
        lines = f.readlines()
    
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        
        # Skip header lines and empty lines
        if not line or 'Device' in line or 'Linux' in line or '_x86_64_' in line:
            i += 1
            continue
        
        # Look for device lines with stats
        # Split by whitespace and expect at least 23 columns
        parts = line.split()
        if len(parts) >= 23:
            device = parts[0]
            try:
                read_kb_s = float(parts[2])   # rkB/s (column 2)
                write_kb_s = float(parts[7])  # wkB/s (column 7)
                read_mb_s = read_kb_s / 1024  # Convert kB/s to MB/s
                write_mb_s = write_kb_s / 1024  # Convert kB/s to MB/s
                
                data.append({
                    'timestamp': current_timestamp,
                    'device': device,
                    'read_mb_s': read_mb_s,
                    'write_mb_s': write_mb_s,
                    'total_mb_s': read_mb_s + write_mb_s
                })
                
            except (ValueError, IndexError):
                pass
        
        # Check if this looks like the end of a time interval (empty line or new header)
        if i + 1 < len(lines) and (not lines[i + 1].strip() or 'Device' in lines[i + 1]):
            current_timestamp += 1
        
        i += 1
    
    return data

def group_iostat_files_by_benchmark(iostat_files):
    """
    Group iostat files by benchmark (algorithm and dataset).
    Returns a dictionary where keys are benchmark names and values are lists of files.
    """
    groups = defaultdict(list)
    
    for file_path in iostat_files:
        basename = os.path.basename(file_path)
        # Remove _iterN_iostat.log suffix to get benchmark name
        # Example: graph500_23_connectedcomponents_iter0_iostat.log -> graph500_23_connectedcomponents
        if '_iter' in basename and '_iostat.log' in basename:
            benchmark_name = basename.split('_iter')[0]
            groups[benchmark_name].append(file_path)
    
    return groups

def compute_average_bandwidth(iostat_files, target_device):
    """
    Compute average bandwidth across multiple iostat files for a specific device.
    Returns a DataFrame with averaged bandwidth data.
    """
    all_data = []
    
    # Parse all files and collect data
    for file_path in iostat_files:
        data = parse_iostat_log(file_path)
        if data:
            df = pd.DataFrame(data)
            device_data = df[df['device'] == target_device]
            if not device_data.empty:
                # Add iteration identifier
                basename = os.path.basename(file_path)
                iter_match = re.search(r'_iter(\d+)_', basename)
                iteration = int(iter_match.group(1)) if iter_match else 0
                device_data = device_data.copy()
                device_data['iteration'] = iteration
                all_data.append(device_data)
    
    if not all_data:
        return None
    
    # Combine all data
    combined_df = pd.concat(all_data, ignore_index=True)
    
    # Find the maximum timestamp across all iterations to determine alignment
    max_timestamps = combined_df.groupby('iteration')['timestamp'].max()
    min_length = max_timestamps.min()
    
    # Truncate all iterations to the same length
    truncated_data = []
    for iteration in combined_df['iteration'].unique():
        iter_data = combined_df[combined_df['iteration'] == iteration]
        iter_data = iter_data[iter_data['timestamp'] <= min_length].copy()
        truncated_data.append(iter_data)
    
    if not truncated_data:
        return None
    
    combined_df = pd.concat(truncated_data, ignore_index=True)
    
    # Compute averages for each timestamp
    avg_data = combined_df.groupby('timestamp').agg({
        'read_mb_s': ['mean', 'std'],
        'write_mb_s': ['mean', 'std'],
        'total_mb_s': ['mean', 'std']
    }).reset_index()
    
    # Flatten column names
    avg_data.columns = ['timestamp', 'read_mb_s_mean', 'read_mb_s_std',
                       'write_mb_s_mean', 'write_mb_s_std',
                       'total_mb_s_mean', 'total_mb_s_std']
    
    return avg_data

def create_bandwidth_plots(systems, input_dir, output_dir, device, pattern='*_iostat.log'):
    """
    Create read and write bandwidth plots for specified systems.
    
    Args:
        systems: List of system names to process
        input_dir: Directory containing iostat log files  
        output_dir: Directory to save plots and CSV files
        device: Target device name (e.g., 'sda', 'nvme0n1')
        pattern: File pattern to match iostat files
    """
    os.makedirs(output_dir, exist_ok=True)
    
    # Collect data for all systems, organized by algorithm
    algorithm_data = defaultdict(dict)
    
    for system in systems:
        system_dir = os.path.join(input_dir, system)
        if not os.path.exists(system_dir):
            print(f"Warning: Directory {system_dir} not found, skipping {system}")
            continue
            
        iostat_files = glob.glob(os.path.join(system_dir, pattern))
        if not iostat_files:
            print(f"Warning: No iostat files found for {system}")
            continue
            
        print(f"Processing {system}: found {len(iostat_files)} files")
        
        # Group files by benchmark
        benchmark_groups = group_iostat_files_by_benchmark(iostat_files)
        
        for benchmark_name, files in benchmark_groups.items():
            # Compute average bandwidth for this benchmark
            avg_data = compute_average_bandwidth(files, device)
            if avg_data is not None and not avg_data.empty:
                algorithm_data[benchmark_name][system] = avg_data
                
                # Save individual CSV for this system and benchmark
                csv_filename = f"{output_dir}/{system}_{benchmark_name}_{device}_bandwidth.csv"
                avg_data.to_csv(csv_filename, index=False)
                print(f"Saved CSV: {csv_filename}")
    
    # Create consolidated plots - one per algorithm
    if algorithm_data:
        for algorithm in algorithm_data.keys():
            create_read_bandwidth_plot_per_algorithm(algorithm_data[algorithm], algorithm, output_dir, device)
            create_write_bandwidth_plot_per_algorithm(algorithm_data[algorithm], algorithm, output_dir, device)
        print(f"Algorithm-specific plots saved to {output_dir}")

def create_read_bandwidth_plot_per_algorithm(systems_data, algorithm, output_dir, device):
    """
    Create a read bandwidth plot for one algorithm showing different systems as lines.
    
    Args:
        systems_data: Dict with system names as keys and bandwidth data as values
        algorithm: Algorithm name for this plot
        output_dir: Output directory
        device: Device name
    """
    plt.figure(figsize=(12, 8))
    
    colors = plt.cm.Set3(np.linspace(0, 1, len(systems_data)))
    
    # Track data ranges for tight axis limits
    all_times = []
    all_reads = []
    
    for (system, color) in zip(systems_data.keys(), colors):
        data = systems_data[system]
        if data is not None and not data.empty:
            # Plot with some transparency for overlapping lines
            plt.plot(data['timestamp'], data['read_mb_s_mean'], 
                    label=system, linewidth=2.5, alpha=0.85, color=color, marker='o', markersize=2)
            
            all_times.extend(data['timestamp'].tolist())
            all_reads.extend(data['read_mb_s_mean'].tolist())
    
    plt.xlabel('Time (seconds)', fontsize=14, fontweight='bold')
    plt.ylabel('Read Bandwidth (MB/s)', fontsize=14, fontweight='bold')
    plt.title(f'Read Bandwidth - {algorithm} - Device: {device}', fontsize=16, fontweight='bold', pad=20)
    
    # Set tight axis limits to minimize whitespace
    if all_times and all_reads:
        time_margin = (max(all_times) - min(all_times)) * 0.02
        read_margin = (max(all_reads) - min(all_reads)) * 0.05 if max(all_reads) > min(all_reads) else max(all_reads) * 0.1
        
        plt.xlim(max(0, min(all_times) - time_margin), max(all_times) + time_margin)
        plt.ylim(max(0, min(all_reads) - read_margin), max(all_reads) + read_margin)
    
    plt.legend(fontsize=12, frameon=True, fancybox=True, shadow=True)
    plt.grid(True, alpha=0.3, linestyle='--')
    plt.tick_params(axis='both', which='major', labelsize=12)
    
    plt.tight_layout()
    
    # Clean algorithm name for filename
    clean_algorithm = algorithm.replace('/', '_').replace(' ', '_')
    read_plot_filename = f"{output_dir}/{clean_algorithm}_read_bandwidth_{device}.png"
    plt.savefig(read_plot_filename, dpi=300, bbox_inches='tight', facecolor='white')
    plt.close()
    
    print(f"Saved read bandwidth plot: {read_plot_filename}")

def create_write_bandwidth_plot_per_algorithm(systems_data, algorithm, output_dir, device):
    """
    Create a write bandwidth plot for one algorithm showing different systems as lines.
    
    Args:
        systems_data: Dict with system names as keys and bandwidth data as values
        algorithm: Algorithm name for this plot
        output_dir: Output directory
        device: Device name
    """
    plt.figure(figsize=(12, 8))
    
    colors = plt.cm.Set3(np.linspace(0, 1, len(systems_data)))
    
    # Track data ranges for tight axis limits
    all_times = []
    all_writes = []
    
    for (system, color) in zip(systems_data.keys(), colors):
        data = systems_data[system]
        if data is not None and not data.empty:
            # Plot with some transparency for overlapping lines
            plt.plot(data['timestamp'], data['write_mb_s_mean'], 
                    label=system, linewidth=2.5, alpha=0.85, color=color, marker='s', markersize=2)
            
            all_times.extend(data['timestamp'].tolist())
            all_writes.extend(data['write_mb_s_mean'].tolist())
    
    plt.xlabel('Time (seconds)', fontsize=14, fontweight='bold')
    plt.ylabel('Write Bandwidth (MB/s)', fontsize=14, fontweight='bold')
    plt.title(f'Write Bandwidth - {algorithm} - Device: {device}', fontsize=16, fontweight='bold', pad=20)
    
    # Set tight axis limits to minimize whitespace
    if all_times and all_writes:
        time_margin = (max(all_times) - min(all_times)) * 0.02
        write_margin = (max(all_writes) - min(all_writes)) * 0.05 if max(all_writes) > min(all_writes) else max(all_writes) * 0.1
        
        plt.xlim(max(0, min(all_times) - time_margin), max(all_times) + time_margin)
        plt.ylim(max(0, min(all_writes) - write_margin), max(all_writes) + write_margin)
    
    plt.legend(fontsize=12, frameon=True, fancybox=True, shadow=True)
    plt.grid(True, alpha=0.3, linestyle='--')
    plt.tick_params(axis='both', which='major', labelsize=12)
    
    plt.tight_layout()
    
    # Clean algorithm name for filename
    clean_algorithm = algorithm.replace('/', '_').replace(' ', '_')
    write_plot_filename = f"{output_dir}/{clean_algorithm}_write_bandwidth_{device}.png"
    plt.savefig(write_plot_filename, dpi=300, bbox_inches='tight', facecolor='white')
    plt.close()
    
    print(f"Saved write bandwidth plot: {write_plot_filename}")

def main():
    parser = argparse.ArgumentParser(description='Create consolidated I/O bandwidth plots for multiple systems')
    parser.add_argument('--input-dir', required=True, help='Base directory containing system subdirectories with iostat log files')
    parser.add_argument('--output-dir', default='./consolidated_io_plots', help='Output directory for plots and CSV files')
    parser.add_argument('--device', required=True, help='Device name to analyze (e.g., sda, nvme0n1)')
    parser.add_argument('--systems', nargs='+', 
                       default=['xstream', 'graphchi', 'blaze', 'gridgraph', 'lumos'],
                       help='List of system names to process')
    parser.add_argument('--pattern', default='*_iostat.log', help='File pattern to match')
    
    args = parser.parse_args()
    
    print(f"Processing systems: {args.systems}")
    print(f"Target device: {args.device}")
    print(f"Input directory: {args.input_dir}")
    print(f"Output directory: {args.output_dir}")
    
    create_bandwidth_plots(
        systems=args.systems,
        input_dir=args.input_dir,
        output_dir=args.output_dir,
        device=args.device,
        pattern=args.pattern
    )

if __name__ == "__main__":
    main()