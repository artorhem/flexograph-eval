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

def plot_bandwidth_vs_time(iostat_files, output_dir, target_device=None):
    """
    Create bandwidth vs time plots for each iostat log file.
    """
    os.makedirs(output_dir, exist_ok=True)
    
    for iostat_file in iostat_files:
        if not os.path.exists(iostat_file):
            print(f"Warning: {iostat_file} not found")
            continue
            
        print(f"Processing {iostat_file}")
        data = parse_iostat_log(iostat_file)
        
        if not data:
            print(f"No data found in {iostat_file}")
            continue
            
        df = pd.DataFrame(data)
        
        # Group by device and create plots
        devices = df['device'].unique()
        
        # Filter to target device if specified
        if target_device:
            if target_device not in devices:
                print(f"Warning: Device '{target_device}' not found in {iostat_file}. Available devices: {list(devices)}")
                continue
            devices = [target_device]
        
        for device in devices:
            device_data = df[df['device'] == device].sort_values('timestamp')
            
            if len(device_data) < 2:
                continue
                
            plt.figure(figsize=(12, 8))
            
            plt.subplot(2, 1, 1)
            plt.plot(device_data['timestamp'], device_data['read_mb_s'], 'b-', label='Read MB/s', linewidth=2)
            plt.plot(device_data['timestamp'], device_data['write_mb_s'], 'r-', label='Write MB/s', linewidth=2)
            plt.xlabel('Time (seconds)')
            plt.ylabel('Bandwidth (MB/s)')
            plt.title(f'I/O Bandwidth vs Time - {device} ({os.path.basename(iostat_file)})')
            plt.legend()
            plt.grid(True, alpha=0.3)
            
            plt.subplot(2, 1, 2)
            plt.plot(device_data['timestamp'], device_data['total_mb_s'], 'g-', label='Total MB/s', linewidth=2)
            plt.xlabel('Time (seconds)')
            plt.ylabel('Total Bandwidth (MB/s)')
            plt.title(f'Total I/O Bandwidth vs Time - {device}')
            plt.legend()
            plt.grid(True, alpha=0.3)
            
            plt.tight_layout()
            
            # Save plot
            base_name = os.path.basename(iostat_file).replace('.log', '')
            plot_filename = f"{output_dir}/{base_name}_{device}_bandwidth.png"
            plt.savefig(plot_filename, dpi=300, bbox_inches='tight')
            plt.close()
            
            print(f"Saved plot: {plot_filename}")
            
            # Also save CSV data
            csv_filename = f"{output_dir}/{base_name}_{device}_bandwidth.csv"
            device_data.to_csv(csv_filename, index=False)
            print(f"Saved data: {csv_filename}")

def plot_average_bandwidth_vs_time(iostat_files, output_dir, target_device):
    """
    Create average bandwidth vs time plots across multiple benchmark iterations.
    """
    os.makedirs(output_dir, exist_ok=True)
    
    # Group files by benchmark
    benchmark_groups = group_iostat_files_by_benchmark(iostat_files)
    
    if not benchmark_groups:
        print("No benchmark groups found")
        return
    
    for benchmark_name, files in benchmark_groups.items():
        print(f"Processing benchmark: {benchmark_name}")
        
        # Sort files to ensure consistent ordering
        files.sort()
        
        # Compute average bandwidth
        avg_data = compute_average_bandwidth(files, target_device)
        
        if avg_data is None or avg_data.empty:
            print(f"No data found for device '{target_device}' in benchmark {benchmark_name}")
            continue
        
        # Create separate plots for read and write bandwidth
        
        # Read bandwidth plot
        plt.figure(figsize=(10, 6))
        plt.plot(avg_data['timestamp'], avg_data['read_mb_s_mean'], 
                 'b-', label='Average Read Bandwidth', linewidth=2)
        plt.xlabel('Time (seconds)')
        plt.ylabel('Read Bandwidth (MB/s)')
        plt.title(f'Average Read Bandwidth vs Time - {target_device} ({benchmark_name})')
        plt.legend()
        plt.grid(True, alpha=0.3)
        plt.tight_layout()
        
        # Save read bandwidth plot
        read_plot_filename = f"{output_dir}/{benchmark_name}_{target_device}_avg_read_bandwidth.png"
        plt.savefig(read_plot_filename, dpi=300, bbox_inches='tight')
        plt.close()
        print(f"Saved read bandwidth plot: {read_plot_filename}")
        
        # Write bandwidth plot
        plt.figure(figsize=(10, 6))
        plt.plot(avg_data['timestamp'], avg_data['write_mb_s_mean'], 
                 'r-', label='Average Write Bandwidth', linewidth=2)
        plt.xlabel('Time (seconds)')
        plt.ylabel('Write Bandwidth (MB/s)')
        plt.title(f'Average Write Bandwidth vs Time - {target_device} ({benchmark_name})')
        plt.legend()
        plt.grid(True, alpha=0.3)
        plt.tight_layout()
        
        # Save write bandwidth plot
        write_plot_filename = f"{output_dir}/{benchmark_name}_{target_device}_avg_write_bandwidth.png"
        plt.savefig(write_plot_filename, dpi=300, bbox_inches='tight')
        plt.close()
        print(f"Saved write bandwidth plot: {write_plot_filename}")
        
        # Save CSV data
        csv_filename = f"{output_dir}/{benchmark_name}_{target_device}_avg_bandwidth.csv"
        avg_data.to_csv(csv_filename, index=False)
        print(f"Saved average data: {csv_filename}")

def main():
    parser = argparse.ArgumentParser(description='Plot I/O bandwidth from iostat logs')
    parser.add_argument('--input-dir', required=True, help='Directory containing iostat log files')
    parser.add_argument('--output-dir', default='./io_plots', help='Output directory for plots')
    parser.add_argument('--pattern', default='*_iostat.log', help='File pattern to match')
    parser.add_argument('--device', help='Specific device name to analyze (e.g., sda, nvme0n1). If not specified, all devices will be processed')
    parser.add_argument('--average', action='store_true', help='Compute average bandwidth across iterations (requires --device)')
    
    args = parser.parse_args()
    
    # Find all iostat log files
    iostat_files = glob.glob(os.path.join(args.input_dir, args.pattern))
    
    if not iostat_files:
        print(f"No iostat log files found matching pattern {args.pattern} in {args.input_dir}")
        return
    
    print(f"Found {len(iostat_files)} iostat log files")
    
    if args.average:
        if not args.device:
            print("Error: --average mode requires --device to be specified")
            return
        print(f"Computing average bandwidth for device: {args.device}")
        plot_average_bandwidth_vs_time(iostat_files, args.output_dir, args.device)
        print(f"Average plots saved to {args.output_dir}")
    else:
        if args.device:
            print(f"Analyzing only device: {args.device}")
        plot_bandwidth_vs_time(iostat_files, args.output_dir, args.device)
        print(f"Plots saved to {args.output_dir}")

if __name__ == "__main__":
    main()