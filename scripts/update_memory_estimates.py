#!/usr/bin/env python3
"""
Script to update memory_estimates.json with actual disk sizes and remove unwanted fields
"""

import json
import os
from pathlib import Path

# Dataset name mapping (JSON key -> directory name)
DATASET_MAPPING = {
    "dota_league": "dota-league",
    "graph500_23": "graph500_23",  # May not exist
    "graph500_26": "graph500_26",
    "graph500_28": "graph500_28",
    "graph500_30": "graph500_30",
    "road_asia": "road_asia",  # May not exist
    "road_usa": "road_usa",  # May not exist
    "livejournal": "soc-LiveJournal",
    "orkut": "orkut",  # May not exist
    "twitter_mpi": "twitter_mpi",
    "uk-2007": "uk-2007",
    "com-friendster": "com-friendster",
    "uniform_26": "uniform_26"
}

def get_file_size_mb(dataset_key):
    """Get the file size in MB of the .e file for a dataset"""
    dataset_dir = DATASET_MAPPING.get(dataset_key)
    if not dataset_dir:
        return None

    # Check datasets path (handle symlink)
    datasets_path = Path("/home/puneet89/flexograph-eval/datasets")
    if datasets_path.is_symlink():
        datasets_path = Path(os.readlink(datasets_path))

    # Construct file path
    dataset_path = datasets_path / dataset_dir
    if not dataset_path.exists():
        print(f"Warning: Dataset directory not found: {dataset_path}")
        return None

    # Look for the .e file
    e_file = dataset_path / f"{dataset_dir}.e"
    if not e_file.exists():
        # Try alternative naming patterns
        e_files = list(dataset_path.glob("*.e"))
        if e_files:
            e_file = e_files[0]  # Use the first .e file found
        else:
            print(f"Warning: No .e file found for {dataset_key} in {dataset_path}")
            return None

    # Get size in MB
    size_bytes = e_file.stat().st_size
    size_mb = size_bytes / (1024 * 1024)
    return round(size_mb, 2)

def update_json():
    """Update the memory_estimates.json file"""
    json_path = Path("/home/puneet89/flexograph-eval/scripts/memory_estimates.json")

    # Read existing JSON
    with open(json_path, 'r') as f:
        data = json.load(f)

    # Update each dataset entry
    for dataset_key in data.keys():
        entry = data[dataset_key]

        # Get actual file size in MB
        size_mb = get_file_size_mb(dataset_key)

        # Remove old field and unwanted fields
        entry.pop("graph_file_size_gb", None)
        entry.pop("estimated_working_memory_gb", None)
        entry.pop("rationale", None)
        entry.pop("category", None)

        # Add new field
        if size_mb is not None:
            entry["graph_size_disk"] = size_mb
            print(f"{dataset_key}: {size_mb:.2f} MB")
        else:
            entry["graph_size_disk"] = None
            print(f"{dataset_key}: File not found")

    # Write updated JSON with nice formatting
    with open(json_path, 'w') as f:
        json.dump(data, f, indent=2)

    print(f"\nUpdated {json_path}")

if __name__ == "__main__":
    update_json()
