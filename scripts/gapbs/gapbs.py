import subprocess
import re
import os

datasets = ["graph500_23", "graph500_26", "graph500_28", "graph500_30", "dota_league", "livejournal", "orkut", "road_asia", "road_usa"]
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
    matches_time = re.finditer(regex, buffer, re.MULTILINE)
    matches_mem = re.finditer(regex_mem, buffer, re.MULTILINE)
    # Print the matches
    read_time = []
    build_time = []
    trial_times = []
    mem = []
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
    # print(f"Read times: {read_time}\nBuild times: {build_time}\nTrial times: {trial_times}\nMemory: {mem}\n")
    read_avg = sum(read_time) / len(read_time)
    build_avg = sum(build_time) / len(build_time)
    trial_avg = round(sum(trial_times) / len(trial_times),4)
    mem_avg = round(sum(mem) / len(mem))
    pp_time = round(read_avg + build_avg, 4)
    return pp_time, trial_avg, mem_avg

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
                f.write("pp_time(s),algo_time(s),mem(MB),num_threads\n")
                process = 0
                if dataset not in directed:
                    print(f"./{benchmark} -f {dst} -n 5 -s")
                    process = subprocess.run([f"./{benchmark}", "-f", f"{dst}", "-n", "5", "-s"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                else:
                    print(f"./{benchmark} -f {dst} -n 5")
                    process = subprocess.run([f"./{benchmark}", "-f", f"{dst}", "-n", "5"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                pp_time, algo_time, mem = parse_log(process.stdout.decode("ASCII"))
                flout.write(process.stdout.decode("ASCII"))
                f.write(f"{pp_time},{algo_time},{mem},{num_threads}\n")
        #run bfs and sssp
        for benchmark in benchmarks[-2:]:
            print(f"Running {benchmark} on {dataset}")
            result_file = f"/results/gapbs/{dataset}_{benchmark}.csv"
            log_file = f"/results/gapbs/{dataset}_{benchmark}.log"
            with open(bfsver_path, "r") as f:
                random_starts = f.read().splitlines()
                print(random_starts)
            with open(result_file, "w") as f, open ( log_file, "w") as flout:
                f.write("pp_time(s),algo_time(s),start_node,mem_used(MB),num_threads\n")
                for start_vertex in random_starts:
                    process = 0
                    if dataset not in directed:
                        print(f"./benchmark -f {dst} -r {start_vertex} -n 5 -s")
                        process = subprocess.run([f"./{benchmark}", "-f", f"{dst}", "-r", f"{start_vertex}", "-n", "5", "-s"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                    else:
                        print(f"./benchmark -f {dst} -r {start_vertex} -n 5")
                        process = subprocess.run([f"./{benchmark}", "-f", f"{dst}", "-r", f"{start_vertex}", "-n", "5"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                    flout.write(process.stdout.decode("ASCII"))
                    pp_time, algo_time, mem = parse_log(process.stdout.decode("ASCII"))
                    f.write(f"{pp_time},{algo_time},{start_vertex},{mem},{num_threads}\n")
        os.remove(dst)

if __name__ == "__main__":
    main()