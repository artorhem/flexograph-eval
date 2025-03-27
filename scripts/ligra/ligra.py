import sys
import os
import subprocess
import time
import re

datasets = ["graph500_23", "graph500_26", "graph500_28", "twitter_mpi", "dota_league", "livejournal", "orkut", "road_asia",  "road_usa"] #graph500_30
directed = ["livejournal"]
benchmarks = ["Components", "PageRank","Triangle", "BFS"]
dataset_dir = "/datasets"
tempdir = "/extra_space"

def parse_log(buffer):
    regex_read = re.compile(r"^Reading\stime\s+:\s+(\d+\.\d+)")
    regex_algo = re.compile(r"^Running\s+time\s+:\s+(\d+\.\d+)")
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
    return read_time, round(sum(algo_time)/len(algo_time),4), mem, round(sum(maj_faults)/len(maj_faults),4), round(sum(min_faults)/len(min_faults),4), round(sum(blk_in)/len(blk_in),4), round(sum(blk_out)/len(blk_out),4)

def main():
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
        convert_time = stop_time - start_time
        print(f"Time to convert {dataset}: {convert_time}s")

        for benchmark in benchmarks:
            result_path = f"/results/ligra/{dataset}_{benchmark}.csv"
            log_path = f"/results/ligra/{dataset}_{benchmark}.log"
            with open(result_path, "w") as fout, open(log_path, "w") as flog:
                flog.write(f"Time to convert {dataset} to adj: {convert_time} seconds\n")
                flog.write(f"Running {benchmark} on {dataset}\n")
                flog.write(f"/systems/in-mem/ligra/apps/{benchmark} -rounds 5 {converted_file}")
                process = 0
                if(benchmark != "BFS"):
                    process = subprocess.run([f"/systems/in-mem/ligra/apps/{benchmark}", "-rounds", "5", f"{converted_file}"], stdout=subprocess.PIPE)
                    read_t, algo_t, mem, maj_flt, min_flt, blk_in, blk_out = parse_log(process.stdout.decode("ASCII"))
                    fout.write("convert_time(s), read_time(s), algo_time(s), memory(MB), maj_flt, min_flt, blk_in, blk_out \n")
                    fout.write(f"{convert_time}, {read_t}, {algo_t}, {mem}, {maj_flt}, {min_flt}, {blk_in}, {blk_out} \n")
                # read_time, round(sum(algo_time)/len(algo_time),4), mem, round(sum(maj_faults)/len(maj_faults),4), round(sum(min_faults)/len(min_faults),4), round(sum(blk_in)/len(blk_in),4), round(sum(blk_out)/len(blk_out),4)

                else:
                    # Read random start nodes from .bfsver file
                    with open(f"/datasets/{dataset}/{dataset}.bfsver", "r") as f:
                        random_starts = f.read().splitlines()
                    print(random_starts)
                    for start_vertex in random_starts:
                        process = subprocess.run([f"/systems/in-mem/ligra/apps/{benchmark}", "-rounds", "5", "-r", f"{start_vertex}", f"{converted_file}"], stdout=subprocess.PIPE)
                        flog.write(process.stdout.decode("ASCII"))
                        read_t, algo_t, mem, maj_flt, min_flt, blk_in, blk_out = parse_log(process.stdout.decode("ASCII"))
                        fout.write("convert_time(s), read_time(s), algo_time(s), memory(MB),start_vertex, maj_flt, min_flt, blk_in, blk_out \n")
                        fout.write(f"{convert_time}, {read_t}, {algo_t}, {mem}, {start_vertex}, {maj_flt}, {min_flt}, {blk_in}, {blk_out} \n")

        # Remove temp dataset after processing
        os.remove(f"{converted_file}")

if __name__ == "__main__":
    main()