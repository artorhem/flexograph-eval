import os
import sys
import json
import re

SRC_DIR = "/systems/in-mem/GeminiGraph"
TOOLS_DIR = "/systems/in-mem/GeminiGraph/toolkits"
DATASET_DIR = "/datasets"
RESULTS_DIR = "/results/gemini"

NUM_ITERATIONS = 25 # Number of iterations for PageRank

def parse_log(dataset_name, benchmark_name):
  
  input_file = f"{RESULTS_DIR}/{dataset_name}_{benchmark_name}.log"
  csv_file = f"{RESULTS_DIR}/{dataset_name}_{benchmark_name}.csv"
  regex_threads = r"^(\d+)\s(\d+)$"
  regex_exectime = r"exec_time=(\d+.\d+)\(s\)"

  #extract the dataset name and benchmark name from the logfile name:
  threads =0
  cores = 0
  times = []
  re.compile(regex_threads)
  re.compile(regex_exectime)

  with open(input_file, 'r') as f:
    for line in f:
      #regex_thread matches number of cores and number of sockets and returns 2 groups
      match = re.match(regex_threads, line)
      if match:
        cores = int(match.group(1))
        threads = int(match.group(2))
      #regex_exectime matches the execution time and returns 1 group with the time. append to list
      match = re.match(regex_exectime, line)
      if match:
        times.append(float(match.group(1)))
  with open (csv_file, 'w') as f:
    f.write(f"dataset_name, benchmark_name, cores, threads, time(s)\n")
    for i in range(len(times)):
      f.write(f"{dataset_name}, {benchmark_name}, {cores}, {threads}, {times[i]}\n")

def main(self):
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
    cmd = f"{TOOLS_DIR}/pagerank {DATASET_DIR}/{dataset_name}/{dataset_name}.bin {num_vertices} {NUM_ITERATIONS} >> {RESULTS_DIR}/{dataset_name}_pagerank.log"
    print(cmd)
    for iter in range(NUM_ITERATIONS):
      # os.system(cmd)
      pass
    parse_log( dataset_name, "pagerank")
      

    print("BFS...")
    for start_node in start_nodes:
      cmd = f"{TOOLS_DIR}/bfs {DATASET_DIR}/{dataset_name}/{dataset_name}.bin {num_vertices} {start_node} >> {RESULTS_DIR}/{dataset_name}_bfs.log"
      print(cmd)
      # os.system(cmd)
    parse_log( dataset_name, "bfs")

    print("CC...")
    cmd = f"{TOOLS_DIR}/cc {DATASET_DIR}/{dataset_name}/{dataset_name}.bin {num_vertices} >> {RESULTS_DIR}/{dataset_name}_cc.log"
    print(cmd)
    for iter in range(NUM_ITERATIONS):
      # os.system(cmd)
      pass
    parse_log( dataset_name, "cc")

    print("SSSP...")
    for start_node in start_nodes:
      cmd = f"{TOOLS_DIR}/sssp {DATASET_DIR}/{dataset_name}/{dataset_name}.bin {num_vertices} {start_node} >> {RESULTS_DIR}/{dataset_name}_sssp.log"
      print(cmd)
      # os.system(cmd)
    parse_log(dataset_name, "sssp")

if __name__ == "__main__":
  main(sys.argv)


