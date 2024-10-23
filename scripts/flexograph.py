import os
import sys
import json
import re

SRC_DIR = "/systems/FlexoGraph"
BUILD_DIR = "/systems/FlexoGraph/build/release"
DB_DIR = "/systems/FlexoGraph/db"
RESULTS_DIR = "/results/flexograph"
BENCHMARK_DIR = "/systems/FlexoGraph/build/release/benchmark"

NUM_ITERATIONS = 25 # Number of iterations for PageRank



def main(self):
  #We need to edit config.json to match the values we want.
  with open(f'{SRC_DIR}/config.json', 'r+') as f:
    data = json.load(f)
    data['GRAPH_PROJECT_DIR'] = "/systems/FlexoGraph"
    data['GRAPH_DB_DIR'] = "/systems/FlexoGraph/db"
    data['num_threads'] = 25
    data['LOG_DIR'] = "/results/flexograph"
    f.seek(0)        # <--- should reset file position to the beginning.
    json.dump(data, f, indent=4)
    f.truncate()

  os.makedirs(BUILD_DIR, exist_ok=True)
  os.chdir(BUILD_DIR)
  #run make here
  os.system("cmake ../..")
  os.system("make")

  os.chdir(BENCHMARK_DIR)
  #run the benchmarks
  cmd = f"python3 run_benchmarks.py --log_dir {RESULTS_DIR} --dry_run"
  os.system(cmd) 
  


if __name__ == "__main__":
  main(sys.argv)