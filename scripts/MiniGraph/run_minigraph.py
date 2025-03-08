import os
import multiprocessing
import sys
from os import mkdir

dry_run = False
#Check if the user has passed a dry_run option to the script
if len(sys.argv) > 1 and sys.argv[1] == "dry_run":
    dry_run = True

SRC_DIR = "/systems/ooc/MiniGraph"
BIN_DIR = os.path.join(SRC_DIR, "bin")

# Number of cores total
NUM_THREADS = multiprocessing.cpu_count()
print(f"NUM_THREADS={NUM_THREADS}")

# Number of compute threads to use
CC_THREADS = NUM_THREADS /2
print(f"COMPUTE_THREADS={CC_THREADS}")

# Number of dispatch threads to use
DC_THREADS = CC_THREADS / 2
print(f"DC_THREADS={DC_THREADS}"
# Number of loader threads to use
LD_THREADS = CC_THREADS/2
print(f"LD_THREADS={LD_THREADS}")

# Datasets
datasets = ["graph500_23"] #, "graph500_25", "graph500_26", "graph500_28"]

# Convert the graphs
for dataset in datasets:
    print(f"Converting {dataset}")
    output_dir = f"/datasets/{dataset}/minigraph/"
    if not dry_run:
        os.system(f"mkdir -p {output_dir}")
    
    cmd = (
        f"{BIN_DIR}/graph_partition_exec -t csr_bin -p -n 10 "
        f"-i /datasets/{dataset}/{dataset} -sep ' ' "
        f"-o {output_dir} -cores {NUM_THREADS} -tobin -partitioner edgecut"
    )
    print(cmd)
    if not dry_run:
        os.system(cmd)

# Run PageRank
for dataset in datasets:
    print(f"Running pagerank on {dataset}")
    workspace_dir = f"/datasets/{dataset}/minigraph_output"
    results_dir = f"/results/MiniGraph/{dataset}"
    print("Results Directory: {results_dir} \nWorkspace Directory: {workspace_dir}")
    if not dry_run:
        os.system(f"mkdir -p {results_dir}")

    #find the size of the graph in MBs
    graph_size = os.path.getsize(f"/datasets/{dataset}/{dataset}") / (1024 * 1024)
    print (f"Graph size: {graph_size} MB")

    #set the buffer size based on the graph size
    percentages = [0.5, 0.75, 1, 1.5, 2]
    for percentage in percentages:
        buffer_size = int(graph_size * percentage)
        print(f"Running pagerank on {dataset} with buffer size {buffer_size} MB")

        cmd = (
            f"{BIN_DIR}/pr_vc_exec -i {output_dir} "
            f"-lc {LD_THREADS} -cc {CC_THREADS} -dc {DC_THREADS} "
            f"-cores {NUM_THREADS} -buffer_size {buffer_size} -niters 10 > {results_dir}/pagerank_{buffer_size}.txt"
        )
        print(cmd)
        if not dry_run:
            os.system(cmd)
