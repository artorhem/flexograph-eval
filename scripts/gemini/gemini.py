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

def parse_log_single(dataset_name, benchmark_name):
  convert_log_file = f"{RESULTS_DIR}/{dataset_name}_gemini_convert.log"
  input_file = f"{RESULTS_DIR}/{dataset_name}_{benchmark_name}.log"
  regex_threads = r"^(\d+)\s(\d+)$"
  regex_exectime = r"exec_time=(\d+.\d+)\(s\)"
  regex_readtime = r"read_time=(\d+.\d+)\(s\)"
  regex_convert_time = r"^time=(\d+.\d+)"
  regex_mem = r"MemoryCounter:\s+\d+\s+MB\s->\s+\d+\s+MB,\s+(\d+)\s+MB\s+total"
  regex_faults = r"MemoryCounter:\s+(\d+)\s+major\s+faults,\s+(\d+)\s+minor\s+faults"
  regex_blockIO = r"MemoryCounter:\s+(\d+)\s+block\s+input operations,\s+(\d+)\s+block\s+output\s+operations"

#extract the dataset name and benchmark name from the logfile name:
  threads =0
  sockets = 0
  read_time = []
  convert_time = 0
  times = []
  mem = 0
  maj_faults = []
  min_faults = []
  blkio_in = []
  blkio_out = []
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
      print(line)
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

      match = re.match(regex_mem, line)
      if match:
        mem = int(match.group(1))

      match = re.match(regex_faults, line)
      if match:
        maj_faults.append(int(match.group(1)))
        min_faults.append(int(match.group(2)))

      match = re.match(regex_blockIO, line)
      if match:
        blkio_in.append(int(match.group(1)))
        blkio_out.append(int(match.group(2)))
  return threads, sockets, convert_time, read_time, times, mem, maj_faults, min_faults, blkio_in, blkio_out

def parse_log(datasets, benchmarks):
  csv_file = f"{RESULTS_DIR}/gemini_runs.csv"
  with (open (csv_file, 'w') as fmain):
    fmain.write(f"dataset_name, benchmark_name, runs, max_iterations, threads, sockets, convert_time, read_time(s), exec_time(s), mem_used(MB)\n")
    for dataset_name in datasets:
      for benchmark_name in benchmarks:
        with open (f"{RESULTS_DIR}/{dataset_name}_{benchmark_name}.csv", 'w') as frun:
          frun.write("convert_time(s),read_time(s),algo_time(s),mem(MB),num_threads, maj_flt, min_flt, blk_in, blk_out\n")
          if(benchmark_name == "pagerank"):
            max_iters = PR_MAX_ITERS
          else:
            max_iters = 1
          threads, sockets, convert_time, read_time, times, mem, maj_faults, min_faults, blkio_in, blkio_out = parse_log_single(dataset_name, benchmark_name)
          #calculate the average read time if len(read_time) > 0
          if len(read_time) > 0:
            avg_read_time = sum(read_time)/len(read_time)
          else:
            avg_read_time = 0
          if len(times) > 0:
            avg_time = sum(times)/len(times)
          else:
            avg_time = 0

          if len(maj_faults) > 0:
            avg_maj_faults = int(sum(maj_faults)/len(maj_faults))
          else:
            avg_maj_faults = 0

          if len(min_faults) > 0:
            avg_min_faults = int(sum(min_faults)/len(min_faults))
          else:
            avg_min_faults = 0

          if len(blkio_in) > 0:
            avg_blkin = int(sum(blkio_in)/len(blkio_in))
          else:
            avg_blkin = 0

          if len(blkio_out) > 0:
            avg_blkout = int(sum(blkio_out)/len(blkio_out))
          else:
            avg_blkout = 0

          fmain.write(f"{dataset_name}, {benchmark_name}, {REPEATS}, {max_iters},{threads}, {sockets}, {convert_time}, "
                      f"{round(avg_read_time,4)}, {round(avg_time,4)}, {mem}\n")
          frun.write(f"{convert_time}, "
                     f"{round(avg_read_time,4)}, "
                     f"{round(avg_time,4)}, "
                     f"{mem}, "
                     f"{threads}, "
                     f"{int(avg_maj_faults)}, "
                     f"{int(avg_min_faults)}, "
                     f"{int(avg_blkin)}, "
                     f"{int(avg_blkout)}\n")


def main(self):
  parser = argparse.ArgumentParser(description="run gemini benchmarks")
  parser.add_argument("-d", "--dry_run",action="store_true",default=False, help="don't delete prior logs or run any commands.")
  parser.add_argument("-p","--parse",action="store_true",default=False, help="parse the logs to make the csv")
  args = parser.parse_args()

  os.chdir(SRC_DIR)
  #run make here
  os.system("make clean && make -j")

  os.chdir(TOOLS_DIR)

  datasets = ["road_asia", "road_usa", "livejournal", "orkut", "dota_league", "graph500_23", "graph500_26", "graph500_28", "twitter_mpi"]

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
    parse_log( datasets, ["pagerank", "bfs", "cc", "sssp"])

if __name__ == "__main__":
  main(sys.argv)