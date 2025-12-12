"""
Utility for reading memory estimates from memory_estimates.json
"""

import json
import os

MEMORY_ESTIMATES_PATH = "/scripts/memory_estimates.json"

def get_memory_estimates():
    """
    Read memory estimates from the JSON file.

    Returns:
        dict: Dictionary mapping dataset names to their properties (num_nodes, num_edges, graph_size_disk)
    """
    if not os.path.exists(MEMORY_ESTIMATES_PATH):
        raise FileNotFoundError(f"Memory estimates file not found at {MEMORY_ESTIMATES_PATH}")

    with open(MEMORY_ESTIMATES_PATH, 'r') as f:
        return json.load(f)

def get_graph_size_mb(dataset_name):
    """
    Get the graph size in MB for a specific dataset.

    Args:
        dataset_name (str): Name of the dataset

    Returns:
        float: Graph size in MB, or None if not available
    """
    estimates = get_memory_estimates()

    if dataset_name not in estimates:
        raise ValueError(f"Dataset '{dataset_name}' not found in memory estimates")

    return estimates[dataset_name].get('graph_size_disk')

def get_memory_budgets(dataset_name, percentages=[50, 75, 100, 125, 150]):
    """
    Calculate memory budgets as percentages of the graph size.

    Args:
        dataset_name (str): Name of the dataset
        percentages (list): List of percentages to calculate (default: [50, 75, 100, 125, 150])

    Returns:
        list: List of tuples (percentage, memory_budget_mb)
              Returns empty list if graph_size_disk is not available
    """
    graph_size_mb = get_graph_size_mb(dataset_name)

    if graph_size_mb is None:
        print(f"Warning: graph_size_disk not available for dataset '{dataset_name}'")
        return []

    budgets = []
    for pct in percentages:
        budget_mb = int(graph_size_mb * pct / 100.0)
        budgets.append((pct, budget_mb))

    return budgets

if __name__ == "__main__":
    # Test the utility
    print("Memory Estimates Utility Test")
    print("=" * 50)

    estimates = get_memory_estimates()
    print(f"Found {len(estimates)} datasets in memory_estimates.json\n")

    # Test a few datasets
    test_datasets = ["dota_league", "graph500_26", "twitter_mpi"]

    for dataset in test_datasets:
        if dataset in estimates:
            print(f"Dataset: {dataset}")
            graph_size = get_graph_size_mb(dataset)
            if graph_size:
                print(f"  Graph size: {graph_size:.2f} MB")
                budgets = get_memory_budgets(dataset)
                print(f"  Memory budgets:")
                for pct, budget in budgets:
                    print(f"    {pct}%: {budget} MB")
            else:
                print(f"  Graph size: Not available")
            print()
