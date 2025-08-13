import os
import subprocess
import re
import time

src_dir = "/xstream"
app_dir = "/xstream/bin"
llama_converter = "/llama/bin/snap-to-xs1"
dataset_cpy = "/extra_space/xstream_datasets"
dataset_dir = "/datasets"
results_dir = "/results/xstream"
mem = 1073741824 #1GB in Bytes
pr_iters = 10
RUNS = 5

datasets = [ "graph500_23","road_asia", "road_usa", "livejournal", "orkut", "dota_league", "graph500_26", "graph500_28", "twitter_mpi"] #graph500_30
benchmarks = ["bfs", "sssp", "cc", "pagerank"]#, "triangle_counting"] TC does not work/gets stuck

iostat_process = None

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

def parse_log(log):
  regexes = {
    "convert_time": re.compile(r'Time to convert:\s+(\d+\.*\d*)\s+seconds'),
    "setup": re.compile(r'CORE::TIME::SETUP\s+(\d+.\d+)\sseconds'),
    "algo_time": re.compile(r'TIME_IN_PC_FN\s+(\d+.\d+)\s+seconds'),
    "total_time": re.compile(r'Total\s+time:\s+(\d+.\d+)\s+'),
    "buffer_size": re.compile(r'CORE::CONFIG::BUFFER_SIZE\s+(\d+)'),
    "major_faults": re.compile(r'CORE::RUSAGE::MAJFLT\s+(\d+)'),
    "minor_faults": re.compile(r'CORE::RUSAGE::MINFLT\s+(\d+)'),
    "memory_total": re.compile(r"MemoryCounter:\s+\d+\s+MB\s->\s+\d+\s+MB,\s+(\d+)\s+MB\s+total")
  }
  #dictionary to store the extracted data
  extracted_data = {key: [] for key in regexes.keys()}
  print(extracted_data)
  #parse the log
  with open (log, "r") as f:
    for line in f:
      for key, regex in regexes.items():

        match = regex.search(line)
        if match:
          extracted_data[key].append(float(match.group(1))) #Capture the first group of the regex match

  for key,values in extracted_data.items():
    print(f"{key}: {values}")
    extracted_data[key] = list(set(values)) #remove duplicates

  return extracted_data

def make_convert_cmd(dataset):
  cmd = [f"{llama_converter}", "-o", f"{dataset_cpy}/{dataset}", f"{dataset_dir}/{dataset}/{dataset}"]
  print(cmd)
  return cmd

def make_pagerank_cmd(dataset):
  cmd = [f"{app_dir}/benchmark_driver", "-p", f"{nproc}", "-b", "pagerank", "-a", "-g", f"{dataset_cpy}/{dataset}", "--physical_memory", f"{mem}", "--pagerank::niters", f"{pr_iters}"]
  print(" ".join(cmd)) 
  return cmd

#bfs command
def make_bfs_cmd(dataset, start_vertex):
  cmd = [f"{app_dir}/benchmark_driver", "-p", f"{nproc}", "-b", "bfs", "-a", "-g", f"{dataset_cpy}/{dataset}", "--physical_memory", f"{mem}", "--bfs::root", f"{start_vertex}"]
  print(" ".join(cmd))
  return cmd

def make_sssp_cmd(dataset, source_vertex):
  cmd = [f"{app_dir}/benchmark_driver", "-p", f"{nproc}", "-b", "sssp", "-a", "-g", f"{dataset_cpy}/{dataset}", "--physical_memory", f"{mem}", "--sssp::source", f"{source_vertex}"]
  print(" ".join(cmd))
  return cmd

def make_cc_cmd(dataset):
  cmd = [f"{app_dir}/benchmark_driver", "-p", f"{nproc}", "-b", "cc", "-a", "-g", f"{dataset_cpy}/{dataset}", "--physical_memory", f"{mem}"]
  print(" ".join(cmd))
  return cmd

# TC does not work/gets stuck. Ignoring.
# def make_triangle_counting_cmd(dataset):
#   cmd = [f"{app_dir}/benchmark_driver", "-p", f"{nproc}", "-b", "triangle_counting", "-a", "-g", f"{dataset_cpy}/{dataset}", "--physical_memory", f"{mem}"]
#   print(" ".join(cmd))
#   return cmd

def exec_benchmarks():
  for dataset in datasets:
    #we must first use the llama converter to convert the graph to the xstream format
    process = subprocess.run(make_convert_cmd(dataset), stderr=subprocess.PIPE)
    print(process.stderr)
    conv = re.search(r"Elapsed time: (\d+\.*\d*)", process.stderr.decode())
    print(f"Conversion time: {conv.group(1)} seconds")
    convert_time = conv.group(1)

    for benchmark in benchmarks[2:] : #skip bfs and sssp for now
      cmd = globals() [f"make_{benchmark}_cmd"](dataset)
      with open(f"{results_dir}/{dataset}_{benchmark}.log", "w") as flog:
        flog.write(f"Time to convert: {convert_time} seconds\n")
        for i in range(0, RUNS):
          # Start I/O monitoring for this specific run
          iostat_log = f"{results_dir}/{dataset}_{benchmark}_iter{i}_iostat.log"
          start_iostat_monitoring(iostat_log)
          
          process = subprocess.run(cmd, stderr=subprocess.PIPE, cwd=dataset_cpy)
          
          # Stop I/O monitoring
          stop_iostat_monitoring()
          
          flog.write(f"Args: {process.args}\n")
          flog.write(process.stderr.decode("ASCII"))

    #now run bfs and sssp
    for benchmark in benchmarks[:2]:
      bfsver_path = f"/datasets/{dataset}/{dataset}.bfsver"
      if not os.path.exists(bfsver_path):
        print("BFS vertex start file does not exist. SKIPPING BFS and SSSP")
      else:
        with open(bfsver_path, "r") as f:
          random_starts = f.read().splitlines()
        with open (f"{results_dir}/{dataset}_{benchmark}.log", "a") as flog:
          flog.write(f"Time to convert: {convert_time} seconds\n")
          for i, start_vertex in enumerate(random_starts):
            # Start I/O monitoring for this specific run
            iostat_log = f"{results_dir}/{dataset}_{benchmark}_iter{i}_iostat.log"
            start_iostat_monitoring(iostat_log)
            
            cmd = globals() [f"make_{benchmark}_cmd"](dataset, start_vertex)
            process = subprocess.run(cmd, stderr=subprocess.PIPE, cwd=dataset_cpy)
            
            # Stop I/O monitoring
            stop_iostat_monitoring()
            
            flog.write(f"Args: {process.args}\n")
            flog.write(process.stderr.decode("ASCII"))

def main():
  os.makedirs(dataset_cpy, exist_ok=True)
  
  #X-Stream needs the processor count to be a power of 2
  global nproc
  nproc = 2 ** (os.cpu_count().bit_length() - 1)

  #get the physcial memory in Bytes
  mem = os.sysconf('SC_PAGE_SIZE') * os.sysconf('SC_PHYS_PAGES')

  exec_benchmarks()

  #parse the logs
  for dataset in datasets:
    for benchmark in benchmarks:
      extracted_data = parse_log(f"{results_dir}/{dataset}_{benchmark}.log")
      print(f"Extracting data for {dataset}_{benchmark}\n")
      with open (f"{results_dir}/{dataset}_{benchmark}.csv", "w") as f:
        f.write("convert_time, setup_time, runtime_avg(setup+algo), buffer_size, major_faults, minor_faults, memory_avg\n")
        for key,values in extracted_data.items():
          print(key, values)
        f.write(f"{extracted_data['convert_time'][0]}, "
                f"{sum(extracted_data['setup'])/len(extracted_data['setup'])}, "
                f"{sum(extracted_data['total_time'])/len(extracted_data['total_time'])}, "
                f"{int(extracted_data['buffer_size'][0])}, "
                f"{int(sum(extracted_data['major_faults'])/len(extracted_data['major_faults']))}, "
                f"{int(sum(extracted_data['minor_faults'])/len(extracted_data['minor_faults']))}, "
                f"{sum(extracted_data['memory_total'])/len(extracted_data['memory_total'])}\n")
        print("Parsed log file: ", dataset, benchmark)


if __name__ == "__main__":
  main()