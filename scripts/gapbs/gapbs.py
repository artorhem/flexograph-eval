import subprocess
import shutil
import os

datasets = ["graph500_23", "graph500_26", "graph500_28", "graph500_30", "dota_league", "livejournal", "orkut", "road_asia", "road_usa"]
directed = ["livejournal"]
benchmarks = ["bfs", "cc", "pr", "sssp"]
dataset_dir = "/datasets"
tempdir = "/extra_space"

for dataset in datasets:
    src = f"/datasets/{dataset}/{dataset}"
    dst = f"{tempdir}/{dataset}.el"
    print(f"Copying {src} to {dst}")
    os.system(f"cp {src} {dst}")
    
    for benchmark in benchmarks:
        print(f"Running {benchmark} on {dataset}")
        result_file = f"/results/gapbs/{dataset}_{benchmark}.txt"
        if dataset not in directed:
            with open(result_file, "w") as f:
                print(f"./{benchmark} -f {dst} -n 5 -l -s")
                subprocess.run([f"./{benchmark}", "-f", f"{dst}", "-n", "5", "-l", "-s"], stdout=f, stderr=subprocess.STDOUT)
        else:
            with open(result_file, "w") as f:
                subprocess.run([f"./{benchmark}", "-f", f"{dst}", "-n", "5", "-l"], stdout=f, stderr=subprocess.STDOUT)
    
    os.remove(dst)