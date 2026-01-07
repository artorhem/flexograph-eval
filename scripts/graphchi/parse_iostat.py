#!/usr/bin/env python3
"""
Parse iostat log files and extract read/write bandwidth data to CSV.
"""

import re
import sys
import csv
import argparse
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend

def parse_iostat_log(log_file, output_csv):
    """
    Parse iostat log file and extract bandwidth data.

    Args:
        log_file: Path to iostat log file
        output_csv: Path to output CSV file
    """

    # Pattern to match iostat data lines (not the header)
    # The data line has the device name followed by numeric values
    data_pattern = re.compile(r'^(\S+)\s+' +  # Device name
                              r'(\d+\.?\d*)\s+' +  # r/s
                              r'(\d+\.?\d*)\s+' +  # rkB/s
                              r'.*?' +  # skip to w/s and wkB/s
                              r'\s+(\d+\.?\d*)\s+' +  # w/s (7th column)
                              r'(\d+\.?\d*)\s+')  # wkB/s (8th column)

    samples = []
    sample_number = 0

    with open(log_file, 'r') as f:
        for line in f:
            # Skip header lines and empty lines
            if line.startswith('Device') or line.strip() == '' or line.startswith('Linux'):
                continue

            # Try to parse the data line
            # Split the line and extract relevant fields
            fields = line.split()
            if len(fields) >= 8:
                try:
                    device = fields[0]
                    r_per_s = float(fields[1])
                    rkB_per_s = float(fields[2])
                    w_per_s = float(fields[6])
                    wkB_per_s = float(fields[7])

                    # Convert KB/s to MB/s for easier reading
                    read_MB_per_s = rkB_per_s / 1024.0
                    write_MB_per_s = wkB_per_s / 1024.0

                    # Convert to GB/s as well
                    read_GB_per_s = read_MB_per_s / 1024.0
                    write_GB_per_s = write_MB_per_s / 1024.0

                    sample_number += 1

                    samples.append({
                        'sample': sample_number,
                        'device': device,
                        'r_per_s': r_per_s,
                        'read_kB_per_s': rkB_per_s,
                        'read_MB_per_s': read_MB_per_s,
                        'read_GB_per_s': read_GB_per_s,
                        'w_per_s': w_per_s,
                        'write_kB_per_s': wkB_per_s,
                        'write_MB_per_s': write_MB_per_s,
                        'write_GB_per_s': write_GB_per_s,
                        'total_kB_per_s': rkB_per_s + wkB_per_s,
                        'total_MB_per_s': read_MB_per_s + write_MB_per_s,
                        'total_GB_per_s': read_GB_per_s + write_GB_per_s
                    })
                except (ValueError, IndexError):
                    # Skip lines that don't parse correctly
                    continue

    # Write to CSV
    if samples:
        fieldnames = ['sample', 'device', 'r_per_s', 'read_kB_per_s', 'read_MB_per_s',
                      'read_GB_per_s', 'w_per_s', 'write_kB_per_s', 'write_MB_per_s',
                      'write_GB_per_s', 'total_kB_per_s', 'total_MB_per_s', 'total_GB_per_s']

        with open(output_csv, 'w', newline='') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(samples)

        print(f"Parsed {len(samples)} samples from {log_file}")
        print(f"Output written to {output_csv}")

        # Print summary statistics
        if len(samples) > 0:
            total_read_MB = sum(s['read_MB_per_s'] for s in samples)
            total_write_MB = sum(s['write_MB_per_s'] for s in samples)
            avg_read_MB = total_read_MB / len(samples)
            avg_write_MB = total_write_MB / len(samples)
            max_read_MB = max(s['read_MB_per_s'] for s in samples)
            max_write_MB = max(s['write_MB_per_s'] for s in samples)

            print(f"\nSummary Statistics:")
            print(f"  Total samples: {len(samples)}")
            print(f"  Average read bandwidth:  {avg_read_MB:.2f} MB/s ({avg_read_MB/1024:.2f} GB/s)")
            print(f"  Average write bandwidth: {avg_write_MB:.2f} MB/s ({avg_write_MB/1024:.2f} GB/s)")
            print(f"  Peak read bandwidth:     {max_read_MB:.2f} MB/s ({max_read_MB/1024:.2f} GB/s)")
            print(f"  Peak write bandwidth:    {max_write_MB:.2f} MB/s ({max_write_MB/1024:.2f} GB/s)")
    else:
        print(f"No data samples found in {log_file}")

    return samples

def plot_bandwidth(samples, output_plot):
    """
    Plot bandwidth over time.

    Args:
        samples: List of sample dictionaries
        output_plot: Path to output plot file
    """
    if not samples:
        print("No data to plot")
        return

    # Extract time in minutes (each sample is 1 second apart)
    time_minutes = [s['sample'] / 60.0 for s in samples]
    read_MB = [s['read_MB_per_s'] for s in samples]
    write_MB = [s['write_MB_per_s'] for s in samples]
    total_MB = [s['total_MB_per_s'] for s in samples]

    # Create figure with higher DPI for better quality
    fig, ax = plt.subplots(figsize=(12, 6), dpi=100)

    # Plot bandwidth lines
    ax.plot(time_minutes, read_MB, label='Read', linewidth=1.5, alpha=0.8)
    ax.plot(time_minutes, write_MB, label='Write', linewidth=1.5, alpha=0.8)
    ax.plot(time_minutes, total_MB, label='Total', linewidth=1.5, alpha=0.8, linestyle='--')

    # Labels and title
    ax.set_xlabel('Time (minutes)', fontsize=12)
    ax.set_ylabel('Bandwidth (MB/s)', fontsize=12)
    ax.set_title('I/O Bandwidth Over Time', fontsize=14, fontweight='bold')
    ax.legend(loc='best', fontsize=10)
    ax.grid(True, alpha=0.3)

    # Format y-axis to show bandwidth values
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'{x:.0f}'))

    # Tight layout to prevent label cutoff
    plt.tight_layout()

    # Save the plot
    plt.savefig(output_plot, dpi=150, bbox_inches='tight')
    print(f"Plot saved to {output_plot}")
    plt.close()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description='Parse iostat log files and extract read/write bandwidth data to CSV.',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Examples:
  python parse_iostat.py pr_cleanPageCache_100GCgroup_9Gmembudget_4.5Gcache.log
  python parse_iostat.py pr_cleanPageCache_100GCgroup_9Gmembudget_4.5Gcache.log --plot
  python parse_iostat.py pr_cleanPageCache_100GCgroup_9Gmembudget_4.5Gcache.log -o output.csv --plot
        '''
    )

    parser.add_argument('log_file', help='iostat log file to parse')
    parser.add_argument('-o', '--output', dest='output_csv',
                        help='output CSV file (default: <log_file>_bandwidth.csv)')
    parser.add_argument('--plot', action='store_true',
                        help='generate bandwidth plot (saves as <csv_file>.png)')

    args = parser.parse_args()

    log_file = args.log_file

    # Generate output CSV name if not provided
    if args.output_csv:
        output_csv = args.output_csv
    else:
        # Remove .log extension and add _bandwidth.csv
        if log_file.endswith('.log'):
            output_csv = log_file[:-4] + '_bandwidth.csv'
        else:
            output_csv = log_file + '_bandwidth.csv'

    # Parse the iostat log
    samples = parse_iostat_log(log_file, output_csv)

    # Generate plot if requested
    if args.plot and samples:
        # Generate plot filename from CSV filename
        if output_csv.endswith('.csv'):
            output_plot = output_csv[:-4] + '.png'
        else:
            output_plot = output_csv + '.png'

        plot_bandwidth(samples, output_plot)
