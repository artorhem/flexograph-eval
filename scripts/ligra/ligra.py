import sys
import os
import subprocess
import time
import re

# Add parent directory to path to import shared utilities
sys.path.insert(0, '/scripts')
from dataset_properties import PropertiesReader

datasets = ["dota_league","graph500_26", "graph500_28", "graph500_30", "uniform_26", "twitter_mpi","uk-2007", "com-friendster"]
directed = ["livejournal"]
dataset_dir = "/datasets"
tempdir = "/extra_space"

def parse_log(buffer):
    regex_read = re.compile(r"^Reading\stime\s+:\s+(\d+\.*\d+)")
    regex_algo = re.compile(r"^Running\s+time\s+:\s+(\d+\.*\d+)")
    regex_mem = re.compile(r"MemoryCounter:\s+\d+\s+MB\s->\s+\d+\s+MB,\s+(\d+)\s+MB\s+total")
    regex_faults = re.compile(r"MemoryCounter:\s+(\d+)\s+major\s+faults,\s+(\d+)\s+minor\s+faults")
    regex_block_io = re.compile(r"MemoryCounter:\s+(\d+)\s+block\s+input operations,\s+(\d+)\s+block\s+output\s+operations")

    # Print the matches
    read_time = 0
    algo_time = []
    mem = 0
    maj_faults = []
    min_faults = []
    blk_in = []
    blk_out = []
    print(buffer)
    for line in buffer.splitlines():
        #we want to print the sum of times if the first element of the tuple is 'Read' or 'Build'
        if "Reading" in line:
            read_time = regex_read.search(line).group(1)
        elif "Running" in line:
            algo_time.append(float(regex_algo.search(line).group(1)))
        elif "->" in line:
            mem = regex_mem.search(line).group(1)
        elif "faults" in line:
            maj_faults.append(int(regex_faults.search(line).group(1)))
            min_faults.append(int(regex_faults.search(line).group(2)))
        elif "input operations" in line:
            blk_in.append(int(regex_block_io.search(line).group(1)))
            blk_out.append(int(regex_block_io.search(line).group(2)))

    print(f"Read time: {read_time}, Algo time: {algo_time}, Memory: {mem}"
          f"Major Faults: {maj_faults}, Minor Faults: {min_faults}, "
          f"Block Input: {blk_in}, Block Output: {blk_out}")

    # Handle empty results gracefully
    algo_avg = round(sum(algo_time)/len(algo_time), 4) if algo_time else 0
    maj_avg = round(sum(maj_faults)/len(maj_faults), 4) if maj_faults else 0
    min_avg = round(sum(min_faults)/len(min_faults), 4) if min_faults else 0
    blk_in_avg = round(sum(blk_in)/len(blk_in), 4) if blk_in else 0
    blk_out_avg = round(sum(blk_out)/len(blk_out), 4) if blk_out else 0

    return read_time, algo_avg, mem, maj_avg, min_avg, blk_in_avg, blk_out_avg

def main():
    # Compile the convertor utils
    os.chdir("/systems/in-mem/ligra/utils")
    os.system("make -j")

    # Compile the Ligra applications
    os.chdir("/systems/in-mem/ligra/apps")
    os.system("make -e OPENMP=1 -j all")

    os.chdir("/systems/in-mem/ligra/apps")

    for dataset in datasets:
        dataset_path = f"{dataset_dir}/{dataset}"

        # Read properties file using PropertiesReader
        props_reader = PropertiesReader(dataset, dataset_path, system_name='ligra')
        properties = props_reader.read()

        if properties is None:
            print(f"Could not read properties for {dataset}, skipping")
            continue

        # Get mapped algorithms for Ligra
        supported_benchmarks = props_reader.get_mapped_algorithms()

        if not supported_benchmarks:
            print(f"No supported Ligra algorithms found for {dataset}, skipping")
            continue

        print(f"Dataset: {dataset}")
        print(f"  Supported algorithms from properties: {properties['algorithms']}")
        print(f"  Ligra benchmarks to run: {supported_benchmarks}")
        print(f"  Directed: {props_reader.is_directed()}")

        # Measure the time to convert the dataset to adj format and save in a variable
        converted_file = f"{tempdir}/{dataset}"
        converted_file_wgh = f"{tempdir}/{dataset}_wgh"

        # Determine if we need to symmetrize (for undirected graphs)
        sym_flag = "-s" if not props_reader.is_directed() else ""

        # Always create unweighted version (needed by BFS, PageRank, Components, Triangle, BC)
        print(f"  Converting to unweighted format using SNAPtoAdj")
        command = f"/systems/in-mem/ligra/utils/SNAPtoAdj {sym_flag} {dataset_dir}/{dataset}/{dataset} {converted_file}".strip()
        print(command)
        start_time = time.perf_counter()
        result = subprocess.run(
            [command],
            capture_output=True, text=True, shell=True
        )
        stop_time = time.perf_counter()
        convert_time = stop_time - start_time
        print(f"  Time to convert (unweighted): {convert_time}s")

        # Also create weighted version if graph is weighted (needed by BellmanFord)
        convert_time_wgh = 0
        if props_reader.is_weighted():
            print(f"  Converting to weighted format using wghSNAPtoAdj")
            command_wgh = f"/systems/in-mem/ligra/utils/wghSNAPtoAdj {sym_flag} {dataset_dir}/{dataset}/{dataset} {converted_file_wgh}".strip()
            print(command_wgh)
            start_time = time.perf_counter()
            result = subprocess.run(
                [command_wgh],
                capture_output=True, text=True, shell=True
            )
            stop_time = time.perf_counter()
            convert_time_wgh = stop_time - start_time
            print(f"  Time to convert (weighted): {convert_time_wgh}s")

        print("Supported benchmarks to run:", supported_benchmarks)
        print("benchmarks needing source vertex:", props_reader.get_benchmarks_requiring_source())
        print("benchmarks not needing source vertex:", props_reader.get_benchmarks_no_source())

        # Run benchmarks that don't need source vertex
        for benchmark in props_reader.get_benchmarks_no_source():
            print(f"Running {benchmark} on {dataset}")
            result_path = f"/results/ligra/{dataset}_{benchmark}.csv"
            log_path = f"/results/ligra/{dataset}_{benchmark}.log"
            with open(result_path, "w") as fout, open(log_path, "w") as flog:
                flog.write(f"Time to convert {dataset} to adj: {convert_time} seconds\n")
                flog.write(f"Running {benchmark} on {dataset}\n")
                flog.write(f"/systems/in-mem/ligra/apps/{benchmark} {sym_flag} -rounds 5 {converted_file}\n")
                process = subprocess.run([f"/systems/in-mem/ligra/apps/{benchmark}", "-rounds", "5", f"{sym_flag}" , f"{converted_file}"], stdout=subprocess.PIPE)
                read_t, algo_t, mem, maj_flt, min_flt, blk_in, blk_out = parse_log(process.stdout.decode("ASCII"))
                fout.write("convert_time(s), read_time(s), algo_time(s), memory(MB), maj_flt, min_flt, blk_in, blk_out\n")
                fout.write(f"{convert_time}, {read_t}, {algo_t}, {mem}, {maj_flt}, {min_flt}, {blk_in}, {blk_out}\n")
                flog.write(process.stdout.decode("ASCII"))

        # Run benchmarks that need source vertex (BFS, BellmanFord, BC)
        for benchmark in props_reader.get_benchmarks_requiring_source():
            print(f"Running {benchmark} on {dataset}")

            # BellmanFord requires integer weights - skip if graph has floating-point weights
            if benchmark == 'BellmanFord' and props_reader.is_weighted():
                # Check if weights are floating-point by reading a sample edge
                try:
                    with open(f"{dataset_dir}/{dataset}/{dataset}", 'r') as f:
                        for line in f:
                            if line.strip() and not line.startswith('#'):
                                parts = line.strip().split()
                                if len(parts) >= 3:
                                    weight = parts[2]
                                    # Check if weight has decimal point
                                    if '.' in weight:
                                        print(f"  Skipping BellmanFord - graph has floating-point weights (Ligra requires integer weights)")
                                        break
                                break
                        else:
                            # No edges found or couldn't determine - skip to be safe
                            continue
                        # If we found floating-point weight, skip this benchmark
                        if '.' in weight:
                            continue
                except Exception as e:
                    print(f"  Error checking weights for {benchmark}: {e}, skipping")
                    continue

            result_path = f"/results/ligra/{dataset}_{benchmark}.csv"
            log_path = f"/results/ligra/{dataset}_{benchmark}.log"

            # Get source vertex from properties
            source_vertex = props_reader.get_source_vertex()
            if source_vertex is None:
                print(f"  No source vertex found in properties for {benchmark}, skipping")
                continue

            print(f"  Using source vertex: {source_vertex}")

            # Use weighted file for BellmanFord, unweighted file for others
            input_file = converted_file_wgh if benchmark == 'BellmanFord' else converted_file
            file_convert_time = convert_time_wgh if benchmark == 'BellmanFord' else convert_time

            with open(result_path, "w") as fout, open(log_path, "w") as flog:
                flog.write(f"Time to convert {dataset} to adj: {file_convert_time} seconds\n")
                flog.write(f"Running {benchmark} on {dataset}\n")
                flog.write(f"/systems/in-mem/ligra/apps/{benchmark} -rounds 5 -r {source_vertex} {sym_flag} {input_file}\n")
                process = subprocess.run([f"/systems/in-mem/ligra/apps/{benchmark}", "-rounds", "5", "-r", f"{source_vertex}",f"{sym_flag}" ,f"{input_file}"], stdout=subprocess.PIPE)
                flog.write(process.stdout.decode("ASCII"))
                read_t, algo_t, mem, maj_flt, min_flt, blk_in, blk_out = parse_log(process.stdout.decode("ASCII"))
                fout.write("convert_time(s), read_time(s), algo_time(s), memory(MB), start_vertex, maj_flt, min_flt, blk_in, blk_out\n")
                fout.write(f"{file_convert_time}, {read_t}, {algo_t}, {mem}, {source_vertex}, {maj_flt}, {min_flt}, {blk_in}, {blk_out}\n")

        # Remove temp dataset files after processing
        os.remove(f"{converted_file}")
        if props_reader.is_weighted() and os.path.exists(converted_file_wgh):
            os.remove(f"{converted_file_wgh}")

if __name__ == "__main__":
    main()
