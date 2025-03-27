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

datasets = ["graph500_23", "road_asia", "road_usa", "livejournal", "orkut", "dota_league", "graph500_26", "graph500_28", "twitter_mpi"] #"graph500_30"
benchmarks = ["trianglecounting", "pagerank_functional", "connectedcomponents"]


def parse_preprocessing_log(filename):
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
          extracted_data[key].append(float(match.group(1)))  # Capture first group
  #return the sum of average values of the preprocessing steps
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
    #the preprocessing step happens only once for the first benchmark. We have chosen the first benchmark to be TC
    #because it has an additional sort step, which is not present in the other benchmarks.
    #Even if another benchmark runs first, TC will run preprocessing again, so it is safe to choose TC as the first benchmark
    pp_file = f"{results_dir}/preprocess_{dataset}_trianglecounting.log"
    preprocessing_total = parse_preprocessing_log(pp_file)
    for benchmark in benchmarks:
      extracted_data = parse_log(f"{results_dir}/{dataset}_{benchmark}.out")
      print(f"Dataset: {dataset}, Benchmark: {benchmark}")
      with open (f"{results_dir}/{dataset}_{benchmark}.csv", "w") as f:
        f.write("preprocessing_total, num_shards, runtime_avg, cache_mb, membudget_mb, niters, runtime_mem_total_mb, preprocessing_mem_mb, maj_flt, min_flt, blk_in, blk_out\n")
        for key, values in extracted_data.items():
          print(key, values)
        mems = extracted_data['memory_total']
        mems.sort()
        f.write(f"{preprocessing_total}, "
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