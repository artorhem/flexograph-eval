import sys
import os
import subprocess
import time

datasets = ["graph500_23"] #, "graph500_26", "graph500_28", "graph500_30", "dota_league", "livejournal", "orkut", "road_asia",  "road_usa"]
directed = ["livejournal"]
benchmarks = ["BFS", "Components", "PageRank","Triangle"]
dataset_dir = "/datasets"
tempdir = "/extra_space"

# Compile the convertor utils
os.chdir("/systems/in-mem/ligra/utils")
os.system("make -j")

# Compile the Ligra applications
os.chdir("/systems/in-mem/ligra/apps")
os.system("make -e OPENMP=1 -j all")

os.chdir("/systems/in-mem/ligra/apps")

for dataset in datasets:
    # Measure the time to convert the dataset to adj format and save in a variable
    converted_file = f"{tempdir}/{dataset}"
    command = f"/systems/in-mem/ligra/utils/SNAPtoAdj {dataset_dir}/{dataset}/{dataset} {converted_file}"
    print(command)
    start_time = time.perf_counter()
    result = subprocess.run(
        [command],
        capture_output=True, text=True, shell=True
    )
    stop_time = time.perf_counter()
    time_taken = stop_time - start_time
    print(f"Time to convert {dataset}: {time_taken}s")

    for benchmark in benchmarks:
        result_path = f"/results/ligra/{dataset}_{benchmark}.txt"
        with open(result_path, "w") as f:
            f.write(f"Time to convert {dataset} to adj: {time_taken} seconds\n")
            f.write(f"Running {benchmark} on {dataset}\n")
        print(f"/systems/in-mem/ligra/apps/{benchmark} -rounds 5 {converted_file}")
        subprocess.run([f"/systems/in-mem/ligra/apps/{benchmark}", "-rounds", "5", f"{converted_file}"], stdout=open(result_path, "a"))

    # Remove temp dataset after processing
    os.remove(f"{converted_file}")
