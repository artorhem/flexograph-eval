import subprocess
import re
import os

datasets = ["graph500_23", "graph500_26", "graph500_28", "dota_league", "livejournal", "orkut", "road_asia", "road_usa", "twitter_mpi"] #"graph500_30",
directed = ["livejournal"]
benchmarks = ["cc", "pr", "sssp", "bfs"]
dataset_dir = "/datasets"
tempdir = "/extra_space"
num_threads =1
def parse_log(buffer):
    '''
    Returns the average preprocessing time (average read time + average build time),
    average trial time, and memory usage from the log file
    '''
    regex = r"^(Read|Build|Trial)\sTime:\s+(\d+\.\d+)"
    regex_mem = r"MemoryCounter:\s+\d+\s+MB\s->\s+\d+\s+MB,\s+(\d+)\s+MB\s+total"
    regex_faults = r"MemoryCounter:\s+(\d+)\s+major\s+faults,\s+(\d+)\s+minor\s+faults"
    regex_blockIO = r"MemoryCounter:\s+(\d+)\s+block\s+input operations,\s+(\d+)\s+block\s+output\s+operations"
    matches_time = re.finditer(regex, buffer, re.MULTILINE)
    matches_mem = re.finditer(regex_mem, buffer, re.MULTILINE)
    matches_faults = re.finditer(regex_faults, buffer, re.MULTILINE)
    matches_blockIO = re.finditer(regex_blockIO, buffer, re.MULTILINE)
    # Print the matches
    read_time = []
    build_time = []
    trial_times = []
    mem = []
    major_faults = []
    minor_faults = []
    block_in = []
    block_out = []
    for match in matches_time:
        #we want to print the sum of times if the first element of the tuple is 'Read' or 'Build'
        if match.group(1) == 'Read':
            read_time.append(float(match.group(2)))
        elif match.group(1) == 'Build':
            build_time.append(float(match.group(2)))
        else:
            trial_times.append(float(match.group(2)))
    for matches in matches_mem:
        mem.append(int(matches.group(1)))
    for matches in matches_faults:
        major_faults.append(int(matches.group(1)))
        minor_faults.append(int(matches.group(2)))
    for matches in matches_blockIO:
        block_in.append(int(matches.group(1)))
        block_out.append(int(matches.group(2)))

    # print(f"Read times: {read_time}\nBuild times: {build_time}\nTrial times: {trial_times}\nMemory: {mem}\n")
    if len(read_time) == 0:
        read_avg = 0
    else:
        read_avg = sum(read_time) / len(read_time)

    if len(build_time) == 0:
        build_avg = 0
    else:
        build_avg = sum(build_time) / len(build_time)

    if len(trial_times) == 0:
        trial_avg = 0
    else:
        trial_avg = round(sum(trial_times) / len(trial_times),4)

    if len(mem) == 0:
        mem_avg = int(round(sum(mem) / len(mem)))
    else:
        mem_avg = 0

    if len(major_faults) == 0:
        major_faults_avg = 0
    else:
        major_faults_avg = int(sum(major_faults) / len(major_faults))
    if len(minor_faults) == 0:
        minor_faults_avg = 0
    else:
        minor_faults_avg = int(sum(minor_faults) / len(minor_faults))

    if len(block_in) == 0:
        block_in_avg = 0
    else:
        block_in_avg = int(sum(block_in) / len(block_in))

    if len(block_out) == 0:
        block_out_avg = 0
    else:
        block_out_avg = sum(block_out) / len(block_out)

    pp_time = round(read_avg + build_avg, 4)
    return pp_time, trial_avg, mem_avg, major_faults_avg, minor_faults_avg, block_in_avg, block_out_avg

def main():
    num_threads = os.cpu_count()
    for dataset in datasets:
        src = f"/datasets/{dataset}/{dataset}"
        if not os.path.exists(src):
            print(f"Dataset {dataset} does not exist")
            continue
        dst = f"{tempdir}/{dataset}.el"
        print(f"Copying {src} to {dst}")
        os.system(f"cp {src} {dst}")

        bfsver_path = f"{src}.bfsver"
        if not os.path.exists(bfsver_path):
            print("BFS vertex start file does not exist. SKIPPING BFS")


        for benchmark in benchmarks[:-2]: #all benchmarks except bfs and sssp
            print(f"Running {benchmark} on {dataset}")
            result_file = f"/results/gapbs/{dataset}_{benchmark}.csv"
            log_file = f"/results/gapbs/{dataset}_{benchmark}.log"
            with open(result_file, "w") as f, open(log_file, "w") as flout:
                f.write("pp_time(s),algo_time(s),mem(MB),num_threads, maj_flt, min_flt, blk_in, blk_out\n")
                process = 0
                if dataset not in directed:
                    print(f"./{benchmark} -f {dst} -n 5 -s")
                    process = subprocess.run([f"./{benchmark}", "-f", f"{dst}", "-n", "5", "-s"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                else:
                    print(f"./{benchmark} -f {dst} -n 5")
                    process = subprocess.run([f"./{benchmark}", "-f", f"{dst}", "-n", "5"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                pp_time, algo_time, mem, maj_flt, min_flt, blk_in, blk_out = parse_log(process.stdout.decode("ASCII"))
                flout.write(process.stdout.decode("ASCII"))
                f.write(f"{pp_time},{algo_time},{mem},{num_threads}, {maj_flt}, {min_flt}, {blk_in}, {blk_out}\n")
        #run bfs and sssp
        for benchmark in benchmarks[-2:]:
            print(f"Running {benchmark} on {dataset}")
            result_file = f"/results/gapbs/{dataset}_{benchmark}.csv"
            log_file = f"/results/gapbs/{dataset}_{benchmark}.log"
            with open(bfsver_path, "r") as f:
                random_starts = f.read().splitlines()
                print(random_starts)
            with open(result_file, "w") as f, open ( log_file, "w") as flout:
                f.write("pp_time(s),algo_time(s),start_node,mem_used(MB),num_threads, maj_flt, min_flt, blk_in, blk_out\n")
                for start_vertex in random_starts:
                    process = 0
                    if dataset not in directed:
                        print(f"./{benchmark} -f {dst} -r {start_vertex} -n 5 -s")
                        process = subprocess.run([f"./{benchmark}", "-f", f"{dst}", "-r", f"{start_vertex}", "-n", "5", "-s"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                    else:
                        print(f"./{benchmark} -f {dst} -r {start_vertex} -n 5")
                        process = subprocess.run([f"./{benchmark}", "-f", f"{dst}", "-r", f"{start_vertex}", "-n", "5"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                    flout.write(process.stdout.decode("ASCII"))
                    pp_time, algo_time, mem, maj_flt, min_flt, blk_in, blk_out = parse_log(process.stdout.decode("ASCII"))
                    f.write(f"{pp_time}, {algo_time}, {start_vertex}, {mem}, {num_threads}, {maj_flt}, {min_flt}, {blk_in}, {blk_out}\n")
        os.remove(dst)

if __name__ == "__main__":
    main()