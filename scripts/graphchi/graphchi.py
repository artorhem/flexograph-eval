import os
import sys
import subprocess
import re
import time
import threading
import signal
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
memory_percentages = [200]#, 75, 100, 125, 150]

datasets = ["graph500_26"] #dota-league"] #,"graph500_26", "graph500_28", "graph500_30", "uniform_26", "twitter_mpi","uk-2007", "com-friendster"]
benchmarks = ["pagerank_functional"]#trianglecounting"] #, #, "connectedcomponents"]

iostat_process = None

def get_device_for_path(path):
  """Get the block device for a given path"""
  try:
    # Use df to find the device for the path
    result = subprocess.run(f"df {path} --output=source | tail -n 1",
                          shell=True, capture_output=True, text=True, check=True)
    device = result.stdout.strip()
    # Extract just the device name (e.g., sda1, nvme1n1p2)
    # iostat expects device names without /dev/ prefix but WITH partition number
    if device.startswith('/dev/'):
      device = device[5:]  # Remove /dev/ prefix (e.g., /dev/nvme1n1p2 -> nvme1n1p2)
      return device
    return device
  except subprocess.CalledProcessError as e:
    print(f"Warning: Could not determine device for {path}, monitoring all devices")
    return None

def start_iostat_monitoring(output_file):
  global iostat_process
  # Get the device where /extra_space is mounted
  device = get_device_for_path("/extra_space")
  if device:
    cmd = f"iostat -d -x {device} 1"
    print(f"Monitoring I/O for device: {device}")
  else:
    # Fallback to monitoring all devices
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
    cmd = f"cp {dataset_dir}/{dataset}/{dataset}.e {dataset_cpy}/{dataset}"
    print(f"running command: {cmd}")
    os.system(cmd)
    #check if copy was successful
    if not os.path.exists(f"{dataset_cpy}/{dataset}"):
      print(f"Error: Dataset copy failed for {dataset}")
  else:
    print(f"Dataset {dataset} already exists in {dataset_cpy}, skipping copy")

def cleanup(dataset):
  os.system(f"rm -rf {dataset_cpy}/*")

def make_pagerank_functional_cmd(dataset, benchmark, membudget_mb, cachesize_mb):
  cmd = f"{app_dir}/{benchmark} --mode=semisync --filetype=edgelist --niters={pr_iters} --file={dataset_cpy}/{dataset} --cachesize_mb={cachesize_mb} --membudget_mb={membudget_mb}"
  return cmd

def make_connectedcomponents_cmd(dataset, benchmark, membudget_mb, cachesize_mb):
  cmd = f"{app_dir}/{benchmark} --filetype=edgelist --file={dataset_cpy}/{dataset} --cachesize_mb={cachesize_mb} --membudget_mb={membudget_mb}"
  return cmd

def make_trianglecounting_cmd(dataset, benchmark, membudget_mb, cachesize_mb):
  cmd = f"{app_dir}/{benchmark} --filetype=edgelist --file={dataset_cpy}/{dataset} --cachesize_mb={cachesize_mb} --membudget_mb={membudget_mb} --nshards=2"
  return cmd

def update_graphchi_config(membudget_mb, cachesize_mb):
  """Update GraphChi config file with specified memory budgets"""
  num_cpus = get_available_cpus()
  config_path = f"{app_dir}/conf/graphchi.local.cnf"
  print(f"Updating GraphChi config file at {config_path} with membudget_mb={membudget_mb}, cachesize_mb={cachesize_mb}")
  # Create config directory if it doesn't exist
  os.makedirs(os.path.dirname(config_path), exist_ok=True)

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

def exec_benchmarks():
  for dataset in datasets:
    print(f"\n{'='*80}")
    print(f"Processing dataset: {dataset}")
    print(f"{'='*80}")

    # Get memory budgets for this dataset
    memory_budgets = get_memory_budgets(dataset, memory_percentages)

    if not memory_budgets:
      print(f"Warning: No memory estimates available for {dataset}, skipping...")
      continue

    os.system("mkdir -p %s" % dataset_cpy)
    # Now copy the dataset to the graphchi directory
    copy_dataset(dataset)

    #check if dataset copy was successful
    if not os.path.exists(f"{dataset_cpy}/{dataset}"):
      print(f"Error: Dataset copy failed for {dataset}, Aborting...")
      exit(1)

    # Loop through each memory budget percentage
    for mem_pct, membudget_mb in memory_budgets:
      # Calculate available cache size based on container headroom
      # Container RAM = membudget_mb * 1.25 (from launch script)
      # Available for cache = (membudget_mb * 0.25) - overhead
      # Use conservative estimate: cap at 1500 MB or available headroom
      overhead_mb = 200  # Conservative estimate for system overhead
      available_for_cache = int(membudget_mb * 0.25 - overhead_mb)
      cachesize_mb = 1400 #min(1500, max(0, available_for_cache))  # Cap at 1500 MB, minimum 0
      membudget_mb = 2800 
      print(f"\n{'-'*80}")
      print(f"Memory Budget: {mem_pct}% ({membudget_mb} MB)")
      print(f"Cache Size: {cachesize_mb} MB")
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
            fout.write(f"return_code: {process.returncode}\n")
            # Parse the output
            fout.write(process.stdout.decode("ASCII"))
            ferr.write(process.stderr.decode("ASCII"))

            # Check if process was killed or failed
            if process.returncode == -9:
              error_msg = f"\n{'='*80}\nERROR: Process was KILLED (likely OOM - Out of Memory)\n"
              error_msg += f"Dataset: {dataset}, Benchmark: {benchmark}, Memory: {mem_pct}%\n"
              error_msg += f"This typically means the container ran out of memory.\n"
              error_msg += f"Container limit may be too low for this configuration.\n"
              error_msg += f"{'='*80}\n"
              print(error_msg)
              ferr.write(error_msg)
              # Stop this benchmark configuration and move to next memory percentage
              print(f"Skipping remaining iterations for {dataset}_{benchmark}_mem{mem_pct}pct")
              break
            elif process.returncode != 0:
              error_msg = f"\n{'='*80}\nERROR: Process exited with non-zero return code: {process.returncode}\n"
              error_msg += f"Dataset: {dataset}, Benchmark: {benchmark}, Memory: {mem_pct}%\n"
              error_msg += f"{'='*80}\n"
              print(error_msg)
              ferr.write(error_msg)
              # Stop on first failure - don't waste time on remaining iterations
              print(f"Skipping remaining iterations for {dataset}_{benchmark}_mem{mem_pct}pct")
              break

            # Iter 0 is the preprocessing time
            if i == 0:
              preprocess_log = open(f"{results_dir}/preprocess_{dataset}_{benchmark}_mem{mem_pct}pct.log", "w")
              preprocess_log.write(f"Time for preprocessing: {end - start}s\n")
              preprocess_log.write(f"Return code: {process.returncode}\n")
              preprocess_log.write(process.stdout.decode("ASCII"))
              preprocess_log.close()

    # Cleanup the dataset after all memory budgets are tested
    cleanup(dataset)
def main():
  # build GraphChi if not already built
  if not os.path.exists(f"{src_dir}/bin/example_apps/pagerank_functional"):
    os.system(f"cd {src_dir} && make -j apps")

  # Set the environment variable
  os.environ["GRAPHCHI_ROOT"] = app_dir

  # Note: GraphChi config file is now created/updated dynamically for each memory budget
  # in the exec_benchmarks() function

  # Run the benchmarks
  exec_benchmarks()

  # Now we can parse the logs
  for dataset in datasets:
    # Get memory budgets for this dataset
    memory_budgets = get_memory_budgets(dataset, memory_percentages)

    if not memory_budgets:
      print(f"Warning: No memory estimates available for {dataset}, skipping parsing...")
      continue

    for mem_pct, membudget_mb in memory_budgets:
      # The preprocessing step happens only once for the first benchmark. We have chosen the first benchmark to be TC
      # because it has an additional sort step, which is not present in the other benchmarks.
      # Even if another benchmark runs first, TC will run preprocessing again, so it is safe to choose TC as the first benchmark
      pp_file = f"{results_dir}/preprocess_{dataset}_trianglecounting_mem{mem_pct}pct.log"
      preprocessing_total = parse_preprocessing_log(pp_file)

      for benchmark in benchmarks:
        result_base = f"{results_dir}/{dataset}_{benchmark}_mem{mem_pct}pct"
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
if __name__ == "__main__":
  main()
