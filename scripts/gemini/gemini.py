import argparse
import os
import sys
import json
import re

SRC_DIR = "/systems/in-mem/GeminiGraph"
TOOLS_DIR = "/systems/in-mem/GeminiGraph/toolkits"
DATASET_DIR = "/datasets"
RESULTS_DIR = "/results/gemini"

REPEATS = 5
PR_MAX_ITERS = 20
def make_gemini_csv():
  csv_file = f"{RESULTS_DIR}/gemini_runs.csv"
  with open (csv_file, 'w') as f:
    f.write(f"dataset_name, benchmark_name, runs, max_iterations, threads, sockets, convert_time, read_time(s), exec_time(s)\n")

def parse_log_single(dataset_name, benchmark_name):
  convert_log_file = f"{RESULTS_DIR}/{dataset_name}_gemini_convert.log"
  input_file = f"{RESULTS_DIR}/{dataset_name}_{benchmark_name}.log"
  csv_file = f"{RESULTS_DIR}/gemini_runs.csv"
  regex_threads = r"^(\d+)\s(\d+)$"
  regex_exectime = r"exec_time=(\d+.\d+)\(s\)"
  regex_readtime = r"read_time=(\d+.\d+)\(s\)"
  regex_convert_time = r"^time=(\d+.\d+)"

  #extract the dataset name and benchmark name from the logfile name:
  threads =0
  sockets = 0
  read_time = []
  convert_time = 0
  times = []
  re.compile(regex_threads)
  re.compile(regex_exectime)

  with open(convert_log_file, 'r') as f:
    for line in f:
      #regex_thread matches number of cores and number of sockets and returns 2 groups
      match = re.match(regex_convert_time, line)
      if match:
        convert_time = int(match.group(1))

  with open(input_file, 'r') as f:
    for line in f:
      #regex_thread matches number of cores and number of sockets and returns 2 groups
      match = re.match(regex_threads, line)
      if match:
        threads = int(match.group(1))
        sockets = int(match.group(2))
      #regex_exectime matches the execution time and returns 1 group with the time. append to list
      match = re.match(regex_exectime, line)
      if match:
        times.append(float(match.group(1)))
      #regex_readtime matches the read time and returns 1 group with the time.
      match = re.match(regex_readtime, line)
      if match:
        read_time.append(float(match.group(1)))

  if(benchmark_name == "pagerank"):
    max_iters = PR_MAX_ITERS
  else:
    max_iters = 1

  with open (csv_file, 'w') as f:
    f.write(f"dataset_name, benchmark_name, runs, max_iterations, threads, sockets, convert_time, read_time(s), exec_time(s)\n")
    f.write(f"{dataset_name}, {benchmark_name}, {REPEATS}, {max_iters},{threads}, {sockets}, {convert_time}, {sum(read_time)/len(read_time)}, {sum(times)/len(times)}\n")

def parse_log(datasets, benchmarks):
  make_gemini_csv()
  for dataset_name in datasets:
    for benchmark_name in benchmarks:
      parse_log_single(dataset_name, benchmark_name)


def main(self):
  parser = argparse.ArgumentParser(description="run gemini benchmarks")
  parser.add_argument("-d", "--dry_run",action="store_true",default=False, help="don't delete prior logs or run any commands.")
  parser.add_argument("-p","--parse",action="store_true",default=False, help="parse the logs to make the csv")
  args = parser.parse_args()

  os.chdir(SRC_DIR)
  #run make here
  os.system("make -j")

  os.chdir(TOOLS_DIR)

  datasets = ["road_asia", "road_usa", "livejournal", "orkut", "dota_league", "graph500_23", "graph500_26", "graph500_28"]

  for dataset_name in datasets:
    print (f"Running for dataset: {dataset_name}")

    #read the random start nodes from the .bfsver file
    start_nodes = []
    with open(f"{DATASET_DIR}/{dataset_name}/{dataset_name}.bfsver") as f:
      for line in f:
        start_nodes.append(int(line.strip()))
    #remove duplicates
    start_nodes = list(set(start_nodes))


    cmd = f"{TOOLS_DIR}/convert {DATASET_DIR}/{dataset_name}/{dataset_name} >> {RESULTS_DIR}/{dataset_name}_gemini_convert.log"
    print(cmd)
    if not args.dry_run:
      os.system(cmd)

    #now find the max_vertex_id in the convert.log file
    max_vertex_id = 0
    with open(f"{RESULTS_DIR}/{dataset_name}_gemini_convert.log") as f:
      lines = f.readlines()
      if lines[-1].startswith("max_vertex_id"):
        max_vertex_id = int(lines[-1].split()[1])

    num_vertices = max_vertex_id + 1

    #Now we can run each benchmark:
    print("PageRank...")
    #delete the previous log file
    if not args.dry_run and os.path.exists(f"{RESULTS_DIR}/{dataset_name}_pagerank.log"):
        os.remove(f"{RESULTS_DIR}/{dataset_name}_pagerank.log")
    max_iters = 20
    cmd = f"{TOOLS_DIR}/pagerank {DATASET_DIR}/{dataset_name}/{dataset_name}.bin {num_vertices} {max_iters} >> {RESULTS_DIR}/{dataset_name}_pagerank.log"
    print(cmd)
    for iter in range(REPEATS):
      if not args.dry_run:
        os.system(cmd)

    print("BFS...")
    #delete the previous log file
    if not args.dry_run and os.path.exists(f"{RESULTS_DIR}/{dataset_name}_bfs.log"):
      os.remove(f"{RESULTS_DIR}/{dataset_name}_bfs.log")
    for start_node in start_nodes:
      cmd = f"{TOOLS_DIR}/bfs {DATASET_DIR}/{dataset_name}/{dataset_name}.bin {num_vertices} {start_node} >> {RESULTS_DIR}/{dataset_name}_bfs.log"
      print(cmd)
      if not args.dry_run:
        os.system(cmd)


    print("CC...")
    #delete the previous log file
    if not args.dry_run and os.path.exists(f"{RESULTS_DIR}/{dataset_name}_cc.log"):
      os.remove(f"{RESULTS_DIR}/{dataset_name}_cc.log")
    cmd = f"{TOOLS_DIR}/cc {DATASET_DIR}/{dataset_name}/{dataset_name}.bin {num_vertices} >> {RESULTS_DIR}/{dataset_name}_cc.log"
    print(cmd)
    for iter in range(REPEATS):
      if not args.dry_run:
        os.system(cmd)

    print("SSSP...")
    #delete the previous log file
    if not args.dry_run and os.path.exists(f"{RESULTS_DIR}/{dataset_name}_sssp.log"):
      os.remove(f"{RESULTS_DIR}/{dataset_name}_sssp.log")
    for start_node in start_nodes:
      cmd = f"{TOOLS_DIR}/sssp {DATASET_DIR}/{dataset_name}/{dataset_name}.bin {num_vertices} {start_node} >> {RESULTS_DIR}/{dataset_name}_sssp.log"
      print(cmd)
      if not args.dry_run:
        os.system(cmd)

  if args.parse:
    parse_log( ["graph500_23"], ["pagerank"])#, "bfs", "cc", "sssp"])

if __name__ == "__main__":
  main(sys.argv)