import os
import multiprocessing

SRC_DIR = "/systems/ooc/MiniGraph"
BIN_DIR = os.path.join(SRC_DIR, "bin")

# Number of cores total
NUM_THREADS = multiprocessing.cpu_count()
print(f"NUM_THREADS={NUM_THREADS}")

# Number of compute threads to use
CC_THREADS = NUM_THREADS // 2
print(f"COMPUTE_THREADS={CC_THREADS}")

# Number of dispatch threads to use
DC_THREADS = CC_THREADS // 2
print(f"DC_THREADS={DC_THREADS}")

# Number of loader threads to use
LD_THREADS = CC_THREADS // 2
print(f"LD_THREADS={LD_THREADS}")

# Datasets
datasets = ["graph500_23", "graph500_25", "graph500_26", "graph500_28"]

# Convert the graphs
for dataset in datasets:
    print(f"Converting {dataset}")
    output_dir = f"/datasets/{dataset}/minigraph_output"
    print(f"mkdir -p {output_dir}")
    
    cmd = (
        f"{BIN_DIR}/graph_partition_exec -t csr_bin -p -n 10 "
        f"-i /datasets/{dataset}/{dataset} -sep ' ' "
        f"-o {output_dir} -cores {NUM_THREADS} -tobin -partitioner edgecut"
    )
    print(cmd)

# Run PageRank
for dataset in datasets:
    print(f"Running pagerank on {dataset}")
    output_dir = f"/datasets/{dataset}/minigraph_output"
    
    cmd = (
        f"{BIN_DIR}/pagerank -i {output_dir} "
        f"-o {output_dir}/pagerank_output -t {NUM_THREADS} "
        f"-v 1000000 -e 10000000 -d 0.85 -max 100 -tol 0.0001"
    )
    print(cmd)
