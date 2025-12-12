import os
import sys
import subprocess
import re
import time
import threading
import signal
import argparse
from datetime import datetime

# Add parent directory to path to import shared utilities
sys.path.insert(0, '/scripts')
from dataset_properties import get_available_cpus
from get_mem_estimates import get_memory_budgets

src_dir = "/systems/ooc/graphchi-cpp"
app_dir = "/systems/ooc/graphchi-cpp/bin/example_apps"
graphchi_root = src_dir
dataset_dir = "/datasets"
dataset_cpy = "/extra_space/graphchi_datasets"
results_dir = "/results/graphchi"
pr_iters= 10
repeats = 5
# Note: membudget_mb and cachesize_mb are now set dynamically based on memory_estimates.json
# Memory budget percentages to test
memory_percentages = [50, 75, 100, 125, 150]

all_datasets = ["dota_league","graph500_26", "graph500_28", "graph500_30", "uniform_26", "twitter_mpi","uk-2007", "com-friendster"]
benchmarks = ["trianglecounting", "pagerank_functional"]#, "connectedcomponents"]

iostat_process = None

def get_container_ram_limit_mb():
  """
  Read container RAM limit from cgroup. Returns RAM limit in MB.
  Tries both cgroup v1 and v2 paths.
  """
  # Try cgroup v2 first (newer Docker versions)
  cgroup_v2_path = "/sys/fs/cgroup/memory.max"
  if os.path.exists(cgroup_v2_path):
    try:
      with open(cgroup_v2_path, 'r') as f:
        limit_bytes = f.read().strip()
        if limit_bytes != "max":
          return int(limit_bytes) / (1024 * 1024)  # Convert to MB
    except:
      pass

  # Try cgroup v1 (older Docker versions)
  cgroup_v1_path = "/sys/fs/cgroup/memory/memory.limit_in_bytes"
  if os.path.exists(cgroup_v1_path):
    try:
      with open(cgroup_v1_path, 'r') as f:
        limit_bytes = int(f.read().strip())
        # Check if it's not the default "unlimited" value (very large number)
        if limit_bytes < (1 << 60):  # 1 exabyte threshold
          return limit_bytes / (1024 * 1024)  # Convert to MB
    except:
      pass

  print("Warning: Could not detect container RAM limit from cgroups")
  return None

def validate_memory_budget(membudget_mb, container_ram_mb, dataset, mem_pct):
  """
  Validate that membudget fits within container RAM constraint.
  Container RAM should be >= 1.75 * membudget_mb
  """
  if container_ram_mb is None:
    print(f"  Warning: Cannot validate memory budget - container RAM limit unknown")
    return True

  required_ram_mb = 1.75 * membudget_mb
  if required_ram_mb > container_ram_mb:
    print(f"  ERROR: Memory budget {membudget_mb} MB ({mem_pct}%) requires {required_ram_mb:.0f} MB RAM")
    print(f"         but container has only {container_ram_mb:.0f} MB")
    print(f"         Skipping this memory percentage...")
    return False

  print(f"  Memory validation: {membudget_mb} MB budget -> {required_ram_mb:.0f} MB required RAM (container has {container_ram_mb:.0f} MB) ✓")
  return True

def start_iostat_monitoring(output_file):
  global iostat_process
  cmd = "iostat -d -x 1 | grep -v 'loop'"
  iostat_process = subprocess.Popen(cmd, shell=True, stdout=open(output_file, 'w'), stderr=subprocess.PIPE)
  return iostat_process

def stop_iostat_monitoring():
  global iostat_process
  if iostat_process:
    iostat_process.terminate()
    iostat_process.wait()
    iostat_process = None

def parse_preprocessing_log(filename):
  print("Parsing preprocessing log file: ", filename)
  regexes = {
    "preprocessing": re.compile(r'^preprocessing:\s+(\d+.\d+)\s*s'),
    "shard_final": re.compile(r'^shard_final:\s+(\d+.\d+)\s*s'),
    "execute_sharding": re.compile(r'^execute_sharding:\s+(\d+.\d+)\s*s'),
    "edata_flush": re.compile(r'^edata_flush:\s+(\d+.\d+)\s*s'),
  }
  # Dictionary to store extracted values
  extracted_data = {key: [] for key in regexes}
  with open(filename, "r") as file:
    for line in file:
      for key, pattern in regexes.items():
        match = pattern.search(line)
        if match :
          print(f"Matched {key} with value {match.group(1)}")
          extracted_data[key].append(float(match.group(1)))  # Capture first group
  #return the sum of average values of the preprocessing steps
  print("Extracted preprocessing data: ", extracted_data)
  pp_total = (sum(extracted_data['preprocessing'])/len(extracted_data['preprocessing']) +
              sum(extracted_data['shard_final'])/len(extracted_data['shard_final']) +
              sum(extracted_data['execute_sharding'])/len(extracted_data['execute_sharding']) +
              sum(extracted_data['edata_flush'])/len(extracted_data['edata_flush']))
  return pp_total

def parse_log(filename):
  regexes = {
    "runtime": re.compile(r'runtime:\s+(\d+.\d+)\s+s'),
    "nshards": re.compile(r'nshards:\s+(\d+)'),
    "cachesize_mb": re.compile(r'cachesize_mb:\s+(\d+)'),
    "membudget_mb": re.compile(r'membudget_mb:\s+(\d+)'),
    "niters": re.compile(r'niters:\s+(\d+)'),
    "memory_total": re.compile(r"MemoryCounter:\s+\d+\s+MB\s->\s+\d+\s+MB,\s+(\d+)\s+MB\s+total"),
    "regex_faults": re.compile(r"MemoryCounter:\s+(\d+)\s+major\s+faults,\s+(\d+)\s+minor\s+faults"),
    "regex_blockIO": re.compile(r"MemoryCounter:\s+(\d+)\s+block\s+input operations,\s+(\d+)\s+block\s+output\s+operations")
  }
  # Dictionary to store extracted values
  extracted_data = {key: [] for key in regexes}
  extracted_data['maj_flt'] = []
  extracted_data['min_flt'] = []
  extracted_data['blk_in'] = []
  extracted_data['blk_out'] = []

  # Read the log file and match regex patterns
  with open(filename, "r") as file:
    for line in file:
      for key, pattern in regexes.items():
        match = pattern.search(line)
        if match :
          if key == "regex_faults":
            extracted_data['maj_flt'].append(int(match.group(1)))
            extracted_data['min_flt'].append(int(match.group(2)))
          elif key == "regex_blockIO":
            extracted_data['blk_in'].append(int(match.group(1)))
            extracted_data['blk_out'].append(int(match.group(2)))
          else:
            extracted_data[key].append(float(match.group(1)))  # Capture first group
  #remove the duplicate elements in the values of the dictionary
  for key, values in extracted_data.items():
    extracted_data[key] = list(set(values))

  return extracted_data

def copy_dataset(dataset):
  # Copy the dataset to the graphchi directory
  if not os.path.exists(f"{dataset_cpy}/{dataset}"):
    os.system(f"cp {dataset_dir}/{dataset}/{dataset}.e {dataset_cpy}/{dataset}")

def cleanup(dataset):
  os.system(f"rm -rf {dataset_cpy}/*")

def make_pagerank_functional_cmd(dataset, benchmark, membudget_mb, cachesize_mb):
  cmd = f"{app_dir}/{benchmark} --mode=semisync --filetype=edgelist --niters={pr_iters} --file={dataset_cpy}/{dataset} --cachesize={cachesize_mb} --membudget={membudget_mb}"
  return cmd

def make_connectedcomponents_cmd(dataset, benchmark, membudget_mb, cachesize_mb):
  cmd = f"{app_dir}/{benchmark} --filetype=edgelist --file={dataset_cpy}/{dataset} --cachesize={cachesize_mb} --membudget={membudget_mb}"
  return cmd

def make_trianglecounting_cmd(dataset, benchmark, membudget_mb, cachesize_mb):
  cmd = f"{app_dir}/{benchmark} --filetype=edgelist --file={dataset_cpy}/{dataset} --cachesize={cachesize_mb} --membudget={membudget_mb} --nshards=2"
  return cmd

def update_graphchi_config(membudget_mb, cachesize_mb):
  """Update GraphChi config file with specified memory budgets"""
  num_cpus = get_available_cpus()
  config_path = f"{app_dir}/conf/graphchi.local.conf"

  with open(config_path, "w") as f:
    f.write("# GraphChi configuration.\n")
    f.write("# Commandline parameters override values in the configuration file.\n")
    f.write(f"execthreads = {num_cpus}\n")
    f.write(f"loadthreads = {num_cpus}\n")
    f.write(f"niothreads = {num_cpus}\n")
    f.write(f"membudget_mb = {membudget_mb}\n")
    f.write(f"cachesize_mb = {cachesize_mb}\n")
    f.write("io.blocksize = 1048576\n")
    f.write("mmap = 0\n")

  print(f"Updated GraphChi config: membudget_mb={membudget_mb}, cachesize_mb={cachesize_mb}")

def exec_benchmarks(dataset, container_ram_mb=None):
  """
  Execute benchmarks for a single dataset with RAM validation.

  Args:
    dataset: Name of the dataset to benchmark
    container_ram_mb: Container RAM limit in MB (optional, will be auto-detected if None)
  """
  print(f"\n{'='*80}")
  print(f"Processing dataset: {dataset}")
  if container_ram_mb:
    print(f"Container RAM limit: {container_ram_mb:.0f} MB")
  print(f"{'='*80}")

  # Get memory budgets for this dataset
  memory_budgets = get_memory_budgets(dataset, memory_percentages)

  if not memory_budgets:
    print(f"Error: No memory estimates available for {dataset}")
    print(f"Make sure {dataset} exists in memory_estimates.json")
    sys.exit(1)

  os.system("mkdir -p %s" % dataset_cpy)
  # Now copy the dataset to the graphchi directory
  copy_dataset(dataset)

  # Loop through each memory budget percentage
  for mem_pct, membudget_mb in memory_budgets:
    # Validate memory budget against container RAM constraint
    if not validate_memory_budget(membudget_mb, container_ram_mb, dataset, mem_pct):
      continue  # Skip this memory percentage if it doesn't fit

    # Set cachesize_mb to the same value as membudget_mb
    cachesize_mb = membudget_mb

    print(f"\n{'-'*80}")
    print(f"Memory Budget: {mem_pct}% ({membudget_mb} MB)")
    print(f"{'-'*80}")

    # Update GraphChi config file with current memory budget
    update_graphchi_config(membudget_mb, cachesize_mb)

    for benchmark in benchmarks:
      print(f"Running benchmark: {benchmark} on dataset: {dataset} with {mem_pct}% memory budget")

      # Create result files with memory percentage in the name
      result_base = f"{results_dir}/{dataset}_{benchmark}_mem{mem_pct}pct"

      with open(f"{result_base}.out", "w") as fout, open(f"{result_base}.err", "w") as ferr:
        for i in range(repeats):
          print(f"  Running iteration {i}")

          # Start I/O monitoring for this specific run
          iostat_log = f"{result_base}_iter{i}_iostat.log"
          start_iostat_monitoring(iostat_log)

          start = time.time()
          cmd = globals()[f"make_{benchmark}_cmd"](dataset, benchmark, membudget_mb, cachesize_mb)
          process = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd=app_dir, shell=True)
          end = time.time()

          # Stop I/O monitoring
          stop_iostat_monitoring()

          fout.write(f"Time taken: {end - start}s\n")
          fout.write(f"command: {process.args}\n")
          # Parse the output
          fout.write(process.stdout.decode("ASCII"))
          ferr.write(process.stderr.decode("ASCII"))

          # Iter 0 is the preprocessing time
          if i == 0:
            preprocess_log = open(f"{results_dir}/preprocess_{dataset}_{benchmark}_mem{mem_pct}pct.log", "w")
            preprocess_log.write(f"Time for preprocessing: {end - start}s\n")
            preprocess_log.write(process.stdout.decode("ASCII"))
            preprocess_log.close()

  # Cleanup the dataset after all memory budgets are tested
  cleanup(dataset)
def main():
  # Parse command-line arguments
  parser = argparse.ArgumentParser(
    description='Run GraphChi benchmarks for a single dataset in RAM-constrained container',
    formatter_class=argparse.RawDescriptionHelpFormatter,
    epilog='''
Examples:
  # Run for graph500_26 dataset
  python graphchi_1by1.py --dataset graph500_26

  # Run with explicit RAM limit override (in MB)
  python graphchi_1by1.py --dataset graph500_26 --ram-limit 32000

Available datasets:
  ''' + ', '.join(all_datasets)
  )
  parser.add_argument('--dataset', type=str, required=True,
                      choices=all_datasets,
                      help='Dataset to benchmark (required)')
  parser.add_argument('--ram-limit', type=float, default=None,
                      help='Container RAM limit in MB (auto-detected from cgroups if not specified)')

  args = parser.parse_args()
  dataset = args.dataset

  # Detect or use provided container RAM limit
  container_ram_mb = args.ram_limit if args.ram_limit else get_container_ram_limit_mb()

  print(f"\n{'='*80}")
  print(f"GraphChi RAM-Constrained Benchmark")
  print(f"{'='*80}")
  print(f"Dataset: {dataset}")
  if container_ram_mb:
    print(f"Container RAM Limit: {container_ram_mb:.0f} MB")
  else:
    print(f"Container RAM Limit: Not detected (will run without validation)")
  print(f"Memory Percentages: {memory_percentages}")
  print(f"Benchmarks: {benchmarks}")
  print(f"Repeats per benchmark: {repeats}")
  print(f"{'='*80}\n")

  # build GraphChi if not already built
  if not os.path.exists(f"{src_dir}/bin/example_apps/pagerank_functional"):
    print("Building GraphChi...")
    os.system(f"cd {src_dir} && make -j apps")

  # Set the environment variable
  os.environ["GRAPHCHI_ROOT"] = app_dir

  # Note: GraphChi config file is now created/updated dynamically for each memory budget
  # in the exec_benchmarks() function

  # Run the benchmarks for the specified dataset
  exec_benchmarks(dataset, container_ram_mb)

  # Now parse the logs for the dataset
  print(f"\n{'='*80}")
  print(f"Parsing results for {dataset}")
  print(f"{'='*80}\n")

  # Get memory budgets for this dataset
  memory_budgets = get_memory_budgets(dataset, memory_percentages)

  if not memory_budgets:
    print(f"Error: No memory estimates available for {dataset}")
    sys.exit(1)

  for mem_pct, membudget_mb in memory_budgets:
    # Skip if this memory budget was skipped during execution
    if container_ram_mb and not validate_memory_budget(membudget_mb, container_ram_mb, dataset, mem_pct):
      continue

    # The preprocessing step happens only once for the first benchmark. We have chosen the first benchmark to be TC
    # because it has an additional sort step, which is not present in the other benchmarks.
    # Even if another benchmark runs first, TC will run preprocessing again, so it is safe to choose TC as the first benchmark
    pp_file = f"{results_dir}/preprocess_{dataset}_trianglecounting_mem{mem_pct}pct.log"

    if not os.path.exists(pp_file):
      print(f"Warning: Preprocessing log not found: {pp_file}")
      continue

    preprocessing_total = parse_preprocessing_log(pp_file)

    for benchmark in benchmarks:
      result_base = f"{results_dir}/{dataset}_{benchmark}_mem{mem_pct}pct"

      if not os.path.exists(f"{result_base}.out"):
        print(f"Warning: Result file not found: {result_base}.out")
        continue

      extracted_data = parse_log(f"{result_base}.out")
      print(f"Dataset: {dataset}, Benchmark: {benchmark}, Memory Budget: {mem_pct}%")

      with open(f"{result_base}.csv", "w") as f:
        f.write("mem_budget_pct, preprocessing_total, num_shards, runtime_avg, cache_mb, membudget_mb, niters, runtime_mem_total_mb, preprocessing_mem_mb, maj_flt, min_flt, blk_in, blk_out\n")
        for key, values in extracted_data.items():
          print(key, values)
        mems = extracted_data['memory_total']
        mems.sort()
        # Handle case where memory data may be sparse
        mem_avg = sum(mems[:-1])/len(mems[:-1]) if len(mems) > 1 else (mems[0] if mems else 0)
        mem_peak = int(mems[-1]) if mems else 0
        f.write(f"{mem_pct}, "
                f"{preprocessing_total}, "
                f"{int(extracted_data['nshards'][0])}, "
                f"{sum(extracted_data['runtime'])/len(extracted_data['runtime'])}, "
                f"{int(extracted_data['cachesize_mb'][0])}, "
                f"{int(extracted_data['membudget_mb'][0])}, "
                f"{int(pr_iters)}, "
                f"{mem_avg}, "
                f"{mem_peak},"
                f"{int(sum(extracted_data['maj_flt'])/len(extracted_data['maj_flt']))},"
                f"{int(sum(extracted_data['min_flt'])/len(extracted_data['min_flt']))},"
                f"{int(sum(extracted_data['blk_in'])/len(extracted_data['blk_in']))},"
                f"{int(sum(extracted_data['blk_out'])/len(extracted_data['blk_out']))}\n")
      print(f"Parsed log file: {dataset} {benchmark} {mem_pct}%")

  print(f"\n{'='*80}")
  print(f"Benchmarking complete for {dataset}!")
  print(f"Results saved to: {results_dir}/")
  print(f"{'='*80}\n")
if __name__ == "__main__":
  main()