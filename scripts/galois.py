import os
import subprocess
from pathlib import Path

SRC_DIR = "/systems/in-mem/Galois"
BUILD_DIR = "/systems/in-mem/Galois/build"
ITERATIONS = 5
THREADS = os.cpu_count()

# Ensure build directory exists
os.makedirs(BUILD_DIR, exist_ok=True)

# Run CMake
subprocess.run(["cmake", "-S", SRC_DIR, "-B", BUILD_DIR, "-DCMAKE_BUILD_TYPE=Release"], check=True)

# Build necessary targets
benchmarks = ["bfs", "connectedcomponents", "pagerank", "triangles", "sssp"]
for benchmark in benchmarks:
    subprocess.run(["make", "-C", f"{BUILD_DIR}/lonestar/{benchmark}", "-j"], check=True)

# Build graph-convert tool
subprocess.run(["make", "-C", BUILD_DIR, "graph-convert", "-j"], check=True)

# Ensure results and datasets directories exist
os.makedirs("/results/galois", exist_ok=True)
os.makedirs("/datasets/galois", exist_ok=True)

datasets = [
    "graph500_23", "graph500_26", "graph500_28", "graph500_30",
    "dota_league", "livejournal", "orkut", "road_asia", "road_usa"
]

benchmarks = ["pagerank", "bfs", "connectedcomponents", "triangles"]

for dataset in datasets:
    dataset_path = Path(f"/datasets/{dataset}/{dataset}")
    bfsver_path = dataset_path.with_suffix(".bfsver")
    gr_path = Path(f"/datasets/galois/{dataset}.gr")
    conv_time_file = Path(f"/results/galois/conv_time_{dataset}.txt")
    
    # Generate .bfsver if not exists
    if not bfsver_path.exists():
        subprocess.run(["python3", "/graph_utils.py", "bfsver", str(dataset_path), str(bfsver_path)], check=True)
    
    # Convert to .gr format if needed
    if not gr_path.exists():
        command = [
            f"{BUILD_DIR}/tools/graph-convert/graph-convert", "-edgelist2gr",
            str(dataset_path), str(gr_path)
        ]
        result = subprocess.run(["/usr/bin/time", "-p"] + command, capture_output=True, text=True)
        
        time_taken = ""
        for line in result.stderr.splitlines():
            if line.startswith("real"):
                time_taken = line.split()[1]
        
        with open(conv_time_file, "w") as f:
            f.write(time_taken + "\n")
        print(f"Time to convert {dataset} to gr: {time_taken}")
    else:
        print(f"Dataset {dataset} already exists in .gr format")
        with open(conv_time_file, "r") as f:
            time_taken = f.read().strip()
    
    # Read random start nodes from .bfsver file
    with open(bfsver_path, "r") as f:
        random_starts = f.read().splitlines()
    
    # Run benchmarks
    for benchmark in benchmarks:
        # Cleanup previous results
        for file in Path("/results/galois").glob(f"{dataset}_{benchmark}-*.csv"):
            file.unlink()
        
        if benchmark == "bfs":
            for nodes in random_starts:
                subprocess.run([f"/{benchmark}.sh", str(gr_path), f"/results/galois/{dataset}_{benchmark}", nodes, str(THREADS)], check=True)
        else:
            subprocess.run([f"/{benchmark}.sh", str(gr_path), f"/results/galois/{dataset}_{benchmark}", str(THREADS)], check=True)
