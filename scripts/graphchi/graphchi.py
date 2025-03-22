import os
import subprocess
import re
import time

src_dir = "/systems/ooc/graphchi-cpp"
app_dir = "/systems/ooc/graphchi-cpp/bin/example_apps"
graphchi_root = src_dir
dataset_dir = "/datasets"
dataset_cpy = "/extra_space/graphchi_datasets"
results_dir = "/results/graphchi"
pr_iters= 10
repeats = 5
membudget_mb = 100000
cachesize_mb = 100000

datasets = [
  "graph500_23"]  # ,"road_asia", "road_usa", "livejournal", "orkut", "dota_league", "graph500_26", "graph500_28", "graph500_30"]
benchmarks = ["trianglecounting"] #["pagerank_functional", "connectedcomponents", "trianglecounting"]

def parse_log(filename):
  regexes = {
    "preprocessing": re.compile(r'^preprocessing:\s+(\d+.\d+)\s+s'),
    "shard_final": re.compile(r'^shard_final:\s+(\d+.\d+)\s+s'),
    "runtime": re.compile(r'runtime:\s+(\d+.\d+)\s+s'),
    "nshards": re.compile(r'nshards:\s+(\d+)'),
    "cachesize_mb": re.compile(r'cachesize_mb:\s+(\d+)'),
    "membudget_mb": re.compile(r'membudget_mb:\s+(\d+)'),
    "niters": re.compile(r'niters:\s+(\d+)'),
    "memory_total": re.compile(r"MemoryCounter:\s+\d+\s+MB\s->\s+\d+\s+MB,\s+(\d+)\s+MB\s+total"),
    "regex_faults": re.compile(r"FaultCounter:\s+(\d+)\s+major\s+faults,\s+(\d+)\s+minor\s+faults"),
    "regex_blockIO": re.compile(r"BIOCounter:\s+(\d+)\s+block\s+input operations,\s+(\d+)\s+block\s+output\s+operations")
  }
  # Dictionary to store extracted values
  extracted_data = {key: [] for key in regexes}

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
    os.system(f"cp {dataset_dir}/{dataset}/{dataset} {dataset_cpy}/{dataset}")

def cleanup(dataset):
  os.system(f"rm -rf {dataset_cpy}/*")

def make_pagerank_functional_cmd(dataset, benchmark):
  cmd = [f"{app_dir}/{benchmark}", "mode", "semisync", "filetype", "edgelist", "niters", f"{pr_iters}", "file",
         f"{dataset_cpy}/{dataset}", "cachesize_mb", f"{cachesize_mb}", "membudget_mb", f"{membudget_mb}"]
  return cmd

def make_connectedcomponents_cmd(dataset, benchmark):
  cmd = [f"{app_dir}/{benchmark}", "filetype", "edgelist", "file", f"{dataset_cpy}/{dataset}", "cachesize_mb",
         f"{cachesize_mb}", "membudget_mb", f"{membudget_mb}"]
  return cmd

def make_trianglecounting_cmd(dataset, benchmark):
  cmd = [f"{app_dir}/{benchmark}", "filetype", "edgelist", "file", f"{dataset_cpy}/{dataset}", "cachesize_mb",
         f"{cachesize_mb}", "membudget_mb", f"{membudget_mb}", "--nshards=2"]
  return cmd

def exec_benchmarks():
  for dataset in datasets:
    os.system("mkdir -p %s" % dataset_cpy)
    # Now copy the dataset to the graphchi directory
    copy_dataset(dataset)
    for benchmark in benchmarks:
      print("Running benchmark: ", benchmark, " on dataset: ", dataset)
      # Run the benchmark
      # start timer here
      with open(f"{results_dir}/{dataset}_{benchmark}.out", "w") as fout, open(f"{results_dir}/{dataset}_{benchmark}.err", "w") as ferr:
        for i in range(repeats):
          print(f"Running iteration {i}")
          start = time.time()
          cmd = globals() [f"make_{benchmark}_cmd"](dataset, benchmark)
          process = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd=app_dir)
          end = time.time()
          fout.write(f"Time taken: {end - start}s\n")
          fout.write(f"command: {process.args}\n")
          # Parse the output
          fout.write(process.stdout.decode("ASCII"))
          ferr.write(process.stderr.decode("ASCII"))
          # Iter 0 is the preprocessing time
          if(i == 0):
            preproccess_log = open(f"{results_dir}/preprocess_{dataset}_{benchmark}.log", "w")
            preproccess_log.write(f"Time for preprocessing: {end - start}s\n")
            preproccess_log.write(process.stdout.decode("ASCII"))
            preproccess_log.close()
    # Cleanup the dataset
    cleanup(dataset)
def main():
  # build GraphChi if not already built
  if not os.path.exists(f"{src_dir}/bin/example_apps/pagerank_functional"):
    os.system(f"cd {src_dir} && make -j apps")

  # make the graphchi local config file
  '''
    # GraphChi configuration.
    # Commandline parameters override values in the configuration file.
    execthreads= ${nproc -all}, loadthreads = $(nproc -all) , niothreads = $(nproc -all)
    # Memory budget for GraphChi engine (in MB) we will use 100GB
    membudget_mb = 100000
    cachesize_mb = 100000
    # I/O settings
    io.blocksize = 1048576, mmap = 0  # Use mmaped files where applicable
  '''
  with open(f"{app_dir}/graphchi_local.conf", "w") as f:
    f.write("# GraphChi configuration.\n")
    f.write("# Commandline parameters override values in the configuration file.\n")
    # setting all threads to the number of cores
    f.write(f"execthreads = {os.cpu_count()}\n")
    f.write(f"loadthreads = {os.cpu_count()}\n")
    f.write(f"niothreads = {os.cpu_count()}\n")
    f.write("membudget_mb = 100000\n")
    f.write("cachesize_mb = 100000\n")
    f.write("io.blocksize = 1048576\n")
    f.write("mmap = 0\n")

  #set the environment variable
  os.environ["GRAPHCHI_ROOT"] = graphchi_root

  #run the benchmarks
  exec_benchmarks()

  #now we can parse the logs
  for dataset in datasets:
    for benchmark in benchmarks:
      extracted_data = parse_log(f"{results_dir}/{dataset}_{benchmark}.out")
      print(f"Dataset: {dataset}, Benchmark: {benchmark}")
      with open (f"{results_dir}/{dataset}_{benchmark}.csv", "w") as f:
        f.write("preprocessing_total, num_shards, runtime_avg, cache_mb, membudget_mb, niters, runtime_mem_total_mb, preprocessing_mem_mb, maj_flt, min_flt, blk_in, blk_out\n")
        for key, values in extracted_data.items():
          print(key, values)
        mems = extracted_data['memory_total']
        mems.sort()
        f.write(f"{float(extracted_data['preprocessing'][0])}, "
                f"{int(extracted_data['nshards'][0])}, "
                f"{sum(extracted_data['runtime'])/len(extracted_data['runtime'])}, "
                f"{int(extracted_data['cachesize_mb'][0])}, "
                f"{int(extracted_data['membudget_mb'][0])}, "
                f"{int(pr_iters)}, "
                f"{sum(mems[:-1])/len(mems[:-1])}, "
                f"{int(mems[-1])},"
                f"{int(sum(extracted_data['maj_flt'])/len(extracted_data['maj_flt']))},"
                f"{int(sum(extracted_data['min_flt'])/len(extracted_data['min_flt']))},"
                f"{int(sum(extracted_data['blk_in'])/len(extracted_data['blk_in']))},"
                f"{int(sum(extracted_data['blk_out'])/len(extracted_data['blk_out']))}\n")
      print("Parsed log file: ", dataset, benchmark)
if __name__ == "__main__":
  main()