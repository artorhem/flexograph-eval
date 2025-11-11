import argparse
import os
import sys
import json
import re

# Add parent directory to path to import shared utilities
sys.path.insert(0, '/scripts')
from dataset_properties import PropertiesReader

SRC_DIR = "/systems/in-mem/GeminiGraph"
TOOLS_DIR = "/systems/in-mem/GeminiGraph/toolkits"
DATASET_DIR = "/datasets"
RESULTS_DIR = "/results/gemini"

REPEATS = 5
PR_MAX_ITERS = 20

# NUMA control settings
NUMA_CPU_NODE = 0
NUMA_MEM_NODE = 0

def make_numactl_prefix():
  """
  Create numactl command prefix to restrict GeminiGraph to specific NUMA node.
  This prevents the segfault when container only has access to node 0 but
  GeminiGraph tries to use all detected NUMA nodes.
  """
  if NUMA_CPU_NODE is None and NUMA_MEM_NODE is None:
    return ""

  numa_cmd = "numactl"
  if NUMA_CPU_NODE is not None:
    numa_cmd += f" --cpunodebind={NUMA_CPU_NODE}"
  if NUMA_MEM_NODE is not None:
    numa_cmd += f" --membind={NUMA_MEM_NODE}"

  return numa_cmd + " "

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

  # Get numactl prefix
  numactl_prefix = make_numactl_prefix()
  if numactl_prefix:
    print(f"Using NUMA control: {numactl_prefix.strip()}")
    print(f"  CPU node: {NUMA_CPU_NODE}")
    print(f"  Memory node: {NUMA_MEM_NODE}")
  else:
    print("NUMA control disabled - using all available nodes")

  os.chdir(SRC_DIR)
  #run make here
  os.system("make clean && make -j")

  os.chdir(TOOLS_DIR)

  datasets = ["dota_league","graph500_26", "graph500_28", "graph500_30", "uniform_26", "twitter_mpi","uk-2007", "com-friendster"]

  for dataset_name in datasets:
    print (f"Running for dataset: {dataset_name}")

    dataset_path = f"{DATASET_DIR}/{dataset_name}"

    # Read properties file using PropertiesReader
    props_reader = PropertiesReader(dataset_name, dataset_path, system_name='gemini')
    properties = props_reader.read()

    if properties is None:
      print(f"Could not read properties for {dataset_name}, skipping")
      continue

    # Get mapped algorithms for Gemini
    supported_benchmarks = props_reader.get_mapped_algorithms()

    if not supported_benchmarks:
      print(f"No supported Gemini algorithms found for {dataset_name}, skipping")
      continue

    # Filter benchmarks based on weighted/unweighted graph type
    # GeminiGraph SSSP uses Graph<Weight> and requires weighted graphs
    # GeminiGraph BFS, PageRank, CC, BC use Graph<Empty> and can work on both weighted/unweighted (they ignore weights)
    if not props_reader.is_weighted():
      # Unweighted graphs: run all algorithms except SSSP (which requires weights)
      supported_benchmarks = [b for b in supported_benchmarks if b != 'sssp']
      print(f"  Graph is unweighted - will skip SSSP")
    else:
      # Weighted graphs: can run all algorithms (SSSP uses weights, others ignore them)
      print(f"  Graph is weighted - will run all supported algorithms")

    if not supported_benchmarks:
      print(f"No compatible Gemini algorithms for this graph type, skipping")
      continue

    print(f"  Supported algorithms from properties: {properties['algorithms']}")
    print(f"  Gemini benchmarks to run: {supported_benchmarks}")
    print(f"  Directed: {props_reader.is_directed()}")
    print(f"  Weighted: {props_reader.is_weighted()}")

    # Get edge file name from properties
    edge_file = props_reader.get_edge_file()
    if edge_file is None:
      print(f"Could not find edge file in properties for {dataset_name}, skipping")
      continue

    print(f"  Edge file: {edge_file}")

    # Convert command with numactl wrapper
    cmd = f"{numactl_prefix}{TOOLS_DIR}/convert {DATASET_DIR}/{dataset_name}/{edge_file} >> {RESULTS_DIR}/{dataset_name}_gemini_convert.log"
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

    #Now we can run each benchmark based on properties
    for benchmark in supported_benchmarks:
      print(f"{benchmark}...")
      #delete the previous log file
      if not args.dry_run and os.path.exists(f"{RESULTS_DIR}/{dataset_name}_{benchmark}.log"):
        os.remove(f"{RESULTS_DIR}/{dataset_name}_{benchmark}.log")

      # Check if this benchmark needs a source vertex
      if benchmark in ['bfs', 'sssp']:
        # Get source vertex from properties
        source_vertex = props_reader.get_source_vertex()
        if source_vertex is None:
          print(f"  No source vertex found in properties for {benchmark}, skipping")
          continue

        print(f"  Using source vertex: {source_vertex}")
        # Add numactl prefix to command
        cmd = f"{numactl_prefix}{TOOLS_DIR}/{benchmark} {DATASET_DIR}/{dataset_name}/{edge_file}.bin {num_vertices} {source_vertex} >> {RESULTS_DIR}/{dataset_name}_{benchmark}.log"
        print(cmd)
        for iter in range(REPEATS):
          if not args.dry_run:
            os.system(cmd)
      else:
        # Benchmarks that don't need source vertex (pagerank, cc)
        if benchmark == "pagerank":
          max_iters = PR_MAX_ITERS
          cmd = f"{numactl_prefix}{TOOLS_DIR}/{benchmark} {DATASET_DIR}/{dataset_name}/{edge_file}.bin {num_vertices} {max_iters} >> {RESULTS_DIR}/{dataset_name}_{benchmark}.log"
        else:
          cmd = f"{numactl_prefix}{TOOLS_DIR}/{benchmark} {DATASET_DIR}/{dataset_name}/{edge_file}.bin {num_vertices} >> {RESULTS_DIR}/{dataset_name}_{benchmark}.log"

        print(cmd)
        for iter in range(REPEATS):
          if not args.dry_run:
            os.system(cmd)

  if args.parse:
    # Collect all benchmarks that were run
    all_benchmarks = set()
    for dataset_name in datasets:
      dataset_path = f"{DATASET_DIR}/{dataset_name}"
      props_reader = PropertiesReader(dataset_name, dataset_path, system_name='gemini')
      properties = props_reader.read()
      if properties:
        benchmarks = props_reader.get_mapped_algorithms()
        all_benchmarks.update(benchmarks)

    parse_log(datasets, list(all_benchmarks))

if __name__ == "__main__":
  main(sys.argv)