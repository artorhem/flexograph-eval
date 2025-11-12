import os
import sys
import subprocess
import re
from os import readv
from pathlib import Path

# Add parent directory to path to import shared utilities
sys.path.insert(0, '/scripts')
from dataset_properties import PropertiesReader, get_available_cpus

SRC_DIR = "/systems/in-mem/Galois"
BUILD_DIR = "/systems/in-mem/Galois/build"
ITERATIONS = 5
THREADS = get_available_cpus()
print(f"Using {THREADS} threads based on available CPUs")

def parse_log(buffer, algo):
    '''Read the log file line by line and match the regex to get the required values:
    the lines look like:
    STAT, {ALGO}_MAIN, Time, TMAX, \d+
    STAT, ReadGraph, Time, TMAX, \d+
    '''
    regex_algo = re.compile(fr"STAT, {algo}_MAIN, Time, TMAX, (\d+)")
    regex_read = re.compile(r"STAT, ReadGraph, Time, TMAX, (\d+)")
    regex_mem = re.compile(r"MemoryCounter:\s+\d+\s+MB\s->\s+\d+\s+MB,\s+(\d+)\s+MB\s+total")
    regex_faults = re.compile(r"MemoryCounter:\s+(\d+)\s+major\s+faults,\s+(\d+)\s+minor\s+faults")
    regex_blockIO = re.compile(r"MemoryCounter:\s+(\d+)\s+block\s+input operations,\s+(\d+)\s+block\s+output\s+operations")
    algo_time =0
    read_time =0
    mem = 0
    major_faults = 0
    minor_faults = 0
    block_input = 0
    block_output = 0
    for line in buffer.splitlines():
        if "ReadGraph" in line:
            read_time = regex_read.search(line).group(1)
        elif f"{algo}_MAIN" in line:
            algo_time = regex_algo.search(line).group(1)
        elif "MB total" in line:
            mem = regex_mem.search(line).group(1)
        elif "faults" in line:
            major_faults = regex_faults.search(line).group(1)
            minor_faults = regex_faults.search(line).group(2)
        elif "output operations" in line:
            block_input = regex_blockIO.search(line).group(1)
            block_output = regex_blockIO.search(line).group(2)

    return read_time, algo_time, mem, major_faults, minor_faults, block_input, block_output

def do_bfs(gr_path, output_path, source_vertex, num_threads, conv_time):
    dataset = gr_path
    outfile = f"{output_path}_synctile_parallel_time.csv"
    outfile_stats = f"{output_path}_synctile_parallel_stats.log"
    # Run BFS
    with open (outfile, "w") as f:
        f.write("conv_time(s),read_time(ms),algo_time(ms),start_node,mem_used(MB),num_threads,major_faults,minor_faults,block_input,block_output\n")

    command = [f"{BUILD_DIR}/lonestar/bfs/bfs", "-algo=SyncTile", "-exec=PARALLEL", f"-t={num_threads}", f"-startNode={source_vertex}", "-noverify", f"{dataset}"]
    with open(outfile_stats, "a") as fout, open(outfile, "a") as f:
        print(command)
        for i in range(ITERATIONS):
            process = subprocess.run(command, stdout=subprocess.PIPE, text=True)
            fout.write(f"{process.stdout}\n----------------\n")
            read_time, algo_time, mem, maj_flt, min_flt, blck_in, blck_out = parse_log(process.stdout, "BFS")
            f.write(f"{conv_time},{read_time},{algo_time},{source_vertex},{mem},{num_threads},{maj_flt},{min_flt},{blck_in},{blck_out}\n")


def do_pagerank(gr_path, output_path, num_threads, conv_time):
    print("arguments are: ", gr_path, output_path, num_threads)
    dataset = gr_path
    outfile = f"{output_path}_residual.csv"
    outfile_stats = f"{output_path}_residual_stats.log"
    # Run PageRank
    with open (outfile, "w") as f:
        f.write("conv_time(s),read_time(ms),algo_time(ms),mem_used(MB),num_threads,major_faults,minor_faults,block_input,block_output\n")
    command = [f"{BUILD_DIR}/lonestar/pagerank/pagerank-pull", f"-t={num_threads}", "-tolerance=0.0001", "-algo=Residual", "-noverify", f"{dataset}"]
    with open(outfile_stats, "a") as fout, open(outfile, "a") as f:
        print(command)
        for i in range(ITERATIONS):
            process = subprocess.run(command, stdout=subprocess.PIPE, text=True)
            fout.write(f"{process.stdout}\n----------------\n")
            read_time, algo_time, mem, maj_flt, min_flt, blck_in, blck_out= parse_log(process.stdout, "PAGERANK")
            f.write(f"{conv_time},{read_time},{algo_time},{mem},{num_threads},{maj_flt},{min_flt},{blck_in},{blck_out}\n")

def do_connectedcomponents(gr_path, output_path, num_threads, conv_time):
    dataset = gr_path
    outfile = f"{output_path}_labelprop.csv"
    outfile_stats = f"{output_path}_labelprop_stats.log"
    # Run Connected Components
    with open (outfile, "w") as f:
        f.write("conv_time(s),read_time(ms),algo_time(ms),mem_used(MB),num_threads,major_faults,minor_faults,block_input,block_output\n")
    command = [f"{BUILD_DIR}/lonestar/connectedcomponents/connectedcomponents", f"-t={num_threads}", "-algo=LabelProp", "-noverify", f"{dataset}"]
    with open(outfile_stats, "a") as fout, open(outfile, "a") as f:
        print(command)
        for i in range(ITERATIONS):
            process = subprocess.run(command, stdout=subprocess.PIPE, text=True)
            fout.write(f"{process.stdout}\n----------------\n")
            read_time, algo_time, mem, maj_flt, min_flt, blck_in, blck_out  = parse_log(process.stdout, "LABELPROP")
            f.write(f"{conv_time},{read_time},{algo_time},{mem},{num_threads},{maj_flt},{min_flt},{blck_in},{blck_out}\n")

def do_triangles(gr_path, output_path, num_threads, conv_time):
    dataset = gr_path
    outfile = f"{output_path}_orderedCount.csv"
    outfile_stats = f"{output_path}_orderedCount_stats.log"
    # Run Triangle Counting
    with open (outfile, "w") as f:
        f.write("conv_time(s),read_time(ms),algo_time(ms),mem_used(MB),num_threads,major_faults,minor_faults,block_input,block_output\n")
    command = [f"{BUILD_DIR}/lonestar/triangles/triangles", f"-t={num_threads}", "-algo=orderedCount", "-noverify", f"{dataset}"]
    with open(outfile_stats, "a") as fout, open(outfile, "a") as f:
        print(command)
        for i in range(ITERATIONS):
            process = subprocess.run(command, stdout=subprocess.PIPE, text=True)
            fout.write(f"{process.stdout}\n----------------\n")
            read_time, algo_time, mem, maj_flt, min_flt, blck_in, blck_out  = parse_log(process.stdout, "ORDEREDCOUNT")
            f.write(f"{conv_time},{read_time},{algo_time},{mem},{num_threads},{maj_flt},{min_flt},{blck_in},{blck_out}\n")

def do_bc(gr_path, output_path, source_vertex, num_threads, conv_time):
    dataset = gr_path
    outfile = f"{output_path}_bc.csv"
    outfile_stats = f"{output_path}_bc_stats.log"
    # Run Betweenness Centrality
    with open (outfile, "w") as f:
        f.write("conv_time(s),read_time(ms),algo_time(ms),mem_used(MB),num_threads,major_faults,minor_faults,block_input,block_output\n")
    command = [f"{BUILD_DIR}/lonestar/betweennesscentrality/bc-async", f"-t={num_threads}", f"-sourcesToUse={source_vertex}", "-numOfSources=1", "-noverify", f"{dataset}"]
    with open(outfile_stats, "a") as fout, open(outfile, "a") as f:
        print(command)
        for i in range(ITERATIONS):
            process = subprocess.run(command, stdout=subprocess.PIPE, text=True)
            fout.write(f"{process.stdout}\n----------------\n")
            read_time, algo_time, mem, maj_flt, min_flt, blck_in, blck_out  = parse_log(process.stdout, "BC")
            f.write(f"{conv_time},{read_time},{algo_time},{mem},{num_threads},{maj_flt},{min_flt},{blck_in},{blck_out}\n")

def do_sssp(gr_path, output_path, source_vertex, num_threads, conv_time):
    dataset = gr_path
    outfile = f"{output_path}_sssp.csv"
    outfile_stats = f"{output_path}_sssp_stats.log"
    # Run SSSP
    with open (outfile, "w") as f:
        f.write("conv_time(s),read_time(ms),algo_time(ms),mem_used(MB),num_threads,major_faults,minor_faults,block_input,block_output\n")
    command = [f"{BUILD_DIR}/lonestar/sssp/sssp", f"-t={num_threads}", f"-startNode={source_vertex}", "-algo=deltaStep", "-noverify", f"{dataset}"]
    with open(outfile_stats, "a") as fout, open(outfile, "a") as f:
        print(command)
        for i in range(ITERATIONS):
            process = subprocess.run(command, stdout=subprocess.PIPE, text=True)
            fout.write(f"{process.stdout}\n----------------\n")
            read_time, algo_time, mem, maj_flt, min_flt, blck_in, blck_out  = parse_log(process.stdout, "SSSP")
            f.write(f"{conv_time},{read_time},{algo_time},{mem},{num_threads},{maj_flt},{min_flt},{blck_in},{blck_out}\n")


def main():
    # Ensure build directory exists
    os.makedirs(BUILD_DIR, exist_ok=True)

    # Run CMake
    subprocess.run(["cmake", "-S", SRC_DIR, "-B", BUILD_DIR, "-DCMAKE_BUILD_TYPE=Release"], check=True)

    # Build necessary targets
    benchmarks = ["bfs", "connectedcomponents", "pagerank", "triangles", "sssp", "betweennesscentrality"]
    for benchmark in benchmarks:
        subprocess.run(["make", "-C", f"{BUILD_DIR}/lonestar/{benchmark}", "-j"], check=True)

    # Build graph-convert tool
    subprocess.run(["make", "-C", BUILD_DIR, "graph-convert", "-j"], check=True)

    # Ensure results and datasets directories exist
    os.makedirs("/results/galois", exist_ok=True)
    os.makedirs("/datasets/galois", exist_ok=True)
    os.makedirs("/extra_space/galois", exist_ok=True)

    datasets = ["dota_league","graph500_26", "graph500_28", "graph500_30", "uniform_26", "twitter_mpi","uk-2007", "com-friendster"]

    for dataset in datasets:
        dataset_path = Path(f"/datasets/{dataset}/{dataset}")
        dataset_dir = f"/datasets/{dataset}"
        gr_path = Path(f"/extra_space/galois/{dataset}.gr")
        conv_time_file = Path(f"/results/galois/conv_time_{dataset}.txt")

        # Read properties file using PropertiesReader
        props_reader = PropertiesReader(dataset, dataset_dir, system_name='galois')
        properties = props_reader.read()

        if properties is None:
            print(f"Could not read properties for {dataset}, skipping")
            continue

        # Get mapped algorithms for Galois
        supported_benchmarks = props_reader.get_mapped_algorithms()

        if not supported_benchmarks:
            print(f"No supported Galois algorithms found for {dataset}, skipping")
            continue

        print(f"Dataset: {dataset}")
        print(f"  Supported algorithms from properties: {properties['algorithms']}")
        print(f"  Galois benchmarks to run: {supported_benchmarks}")
        print(f"  Directed: {props_reader.is_directed()}")
        print(f"  Weighted: {props_reader.is_weighted()}")

        # Determine graph format requirements
        graph_format_notes = []
        if not props_reader.is_directed():
            graph_format_notes.append("Will convert to .sgr (symmetric)")
        if 'pagerank' in supported_benchmarks and props_reader.is_directed():
            graph_format_notes.append("Will generate .tgr (transpose) for PageRank")

        if graph_format_notes:
            print(f"  Graph conversions: {', '.join(graph_format_notes)}")

        # Convert to .gr format if needed
        if not gr_path.exists() or not conv_time_file.exists():
            command = [
                f"{BUILD_DIR}/tools/graph-convert/graph-convert", "-edgelist2gr"]
            if props_reader.is_weighted():
                command.append("-edgeType=float64")
            
            command.extend([str(dataset_path), str(gr_path)])
            result = subprocess.run(["/usr/bin/time", "-p"] + command, stderr=subprocess.PIPE, universal_newlines=True)

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

        # After initial .gr conversion, handle undirected graphs
        if not props_reader.is_directed():
            sgr_path = Path(f"/extra_space/galois/{dataset}.sgr")
            sgr_conv_time_file = Path(f"/results/galois/conv_time_{dataset}_sgr.txt")

            if not sgr_path.exists() or not sgr_conv_time_file.exists():
                print(f"Converting {dataset} to symmetric graph format (.sgr)")
                command = [
                    f"{BUILD_DIR}/tools/graph-convert/graph-convert",
                    "-gr2sgr",
                    str(gr_path),
                    str(sgr_path)
                ]

                result = subprocess.run(
                    ["/usr/bin/time", "-p"] + command,
                    stderr=subprocess.PIPE,
                    universal_newlines=True,
                    check=True
                )

                time_taken_sgr = ""
                for line in result.stderr.splitlines():
                    if line.startswith("real"):
                        time_taken_sgr = line.split()[1]

                with open(sgr_conv_time_file, "w") as f:
                    f.write(time_taken_sgr + "\n")
                print(f"Time to convert {dataset} to .sgr: {time_taken_sgr}")
            else:
                print(f"Dataset {dataset} already exists in .sgr format")
                with open(sgr_conv_time_file, "r") as f:
                    time_taken_sgr = f.read().strip()

            # Use symmetric graph for all subsequent algorithms
            gr_path = sgr_path

        # Calculate base conversion time for most algorithms
        # For undirected graphs: base time = .gr + .sgr
        # For directed graphs: base time = .gr only
        if not props_reader.is_directed():
            base_conv_time = float(time_taken) + float(time_taken_sgr)
        else:
            base_conv_time = float(time_taken)

        # Run benchmarks based on supported algorithms from properties
        print( "Supported benchmarks: ", supported_benchmarks)
        if 'bfs' in supported_benchmarks:
            # Get source vertex from properties
            source_vertex = props_reader.get_source_vertex()
            if source_vertex is None:
                print(f"  No source vertex found in properties for BFS, skipping")
            else:
                print(f"  Using BFS source vertex: {source_vertex}")
                do_bfs(gr_path, f"/results/galois/{dataset}_bfs", source_vertex, THREADS, base_conv_time)

        if 'pagerank' in supported_benchmarks:
            # PageRank-pull requires transpose graph for directed graphs
            if props_reader.is_directed():
                tgr_path = Path(f"/extra_space/galois/{dataset}.tgr")
                tgr_conv_time_file = Path(f"/results/galois/conv_time_{dataset}_tgr.txt")

                if not tgr_path.exists() or not tgr_conv_time_file.exists():
                    print(f"Generating transpose graph (.tgr) for PageRank-pull")
                    command = [
                        f"{BUILD_DIR}/tools/graph-convert/graph-convert",
                        "-gr2tgr",
                        str(gr_path),
                        str(tgr_path)
                    ]

                    result = subprocess.run(
                        ["/usr/bin/time", "-p"] + command,
                        stderr=subprocess.PIPE,
                        universal_newlines=True,
                        check=True
                    )

                    time_taken_tgr = ""
                    for line in result.stderr.splitlines():
                        if line.startswith("real"):
                            time_taken_tgr = line.split()[1]

                    with open(tgr_conv_time_file, "w") as f:
                        f.write(time_taken_tgr + "\n")
                    print(f"Time to convert {dataset} to .tgr: {time_taken_tgr}")
                else:
                    print(f"Transpose graph {dataset}.tgr already exists")
                    with open(tgr_conv_time_file, "r") as f:
                        time_taken_tgr = f.read().strip()

                # For directed graphs with PageRank: conv_time = .gr + .tgr
                pagerank_conv_time = float(time_taken) + float(time_taken_tgr)
                do_pagerank(tgr_path, f"/results/galois/{dataset}_pagerank-pull", THREADS, pagerank_conv_time)
            else:
                # For undirected graphs, use symmetric .sgr (which is already in gr_path)
                # conv_time = .gr + .sgr (which is base_conv_time)
                do_pagerank(gr_path, f"/results/galois/{dataset}_pagerank-pull", THREADS, base_conv_time)

        if 'connectedcomponents' in supported_benchmarks:
            if props_reader.is_directed():
                print(f"  Skipping Connected Components - requires undirected graph (graph is directed)")
            else:
                do_connectedcomponents(gr_path, f"/results/galois/{dataset}_connectedcomponents", THREADS, base_conv_time)

        if 'triangles' in supported_benchmarks:
            if props_reader.is_directed():
                print(f"  Skipping Triangle Counting - requires undirected graph (graph is directed)")
            else:
                do_triangles(gr_path, f"/results/galois/{dataset}_triangle", THREADS, base_conv_time)

        if 'betweennesscentrality' in supported_benchmarks:
            # Get source vertex from properties
            source_vertex = props_reader.get_source_vertex()
            if source_vertex is None:
                print(f"  No source vertex found in properties for BC, skipping")
            else:
                print(f"  Using BFS source vertex for BC: {source_vertex}")
                do_bc(gr_path, f"/results/galois/{dataset}_bc", source_vertex, THREADS, base_conv_time)

        if 'sssp' in supported_benchmarks:
            # Get source vertex from properties
            source_vertex = props_reader.get_source_vertex()
            if source_vertex is None:
                print(f"  No source vertex found in properties for SSSP, skipping")
            else:
                print(f"  Using SSSP source vertex: {source_vertex}")
                do_sssp(gr_path, f"/results/galois/{dataset}_sssp", source_vertex, THREADS, base_conv_time)

if __name__ == "__main__":
    main()