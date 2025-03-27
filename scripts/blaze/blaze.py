import os
import subprocess
import re
import argparse
from pathlib import Path

SRC_DIR = "/systems/ooc/blaze"
BUILD_DIR = "/systems/ooc/blaze/build"
DATASET_DIR = "/datasets"
RESULTS_DIR = "/results/blaze"
TEMP_DIR = "/extra_space"

REPEATS = 5
PR_MAX_ITERS = 20
NUM_WORKERS = 16
'''
Converts the Galois graph format to Blaze format. Blaze converter binary is at /systems/ooc/blaze/build/bin/convert. 
./convert <input_file> <output_index_file> <output_adj_file>
and it generates two files: <input_file>.index and <input_file>.adj.1.0 (since we have only one disk, partition_id is 0)
We need to move these files to the /extra_space directory.
'''
def convert_galois_to_blaze(args, dataset):
  # Create the output directory
  os.makedirs(f"{DATASET_DIR}/blaze", exist_ok=True)

  galois_file = f"{DATASET_DIR}/galois/{dataset}.gr"
  blaze_index_file = f"{DATASET_DIR}/blaze/{dataset}.gr.index"
  blaze_adj_file = f"{DATASET_DIR}/blaze/{dataset}.gr.adj.1.0" # <dataset>.adj.<num_disks>.<partition_id>

  # Run the conversion command
  cmd = [f"{BUILD_DIR}/bin/convert", f"{galois_file}", f"{blaze_index_file}" ,f"{blaze_adj_file}"]
  result = subprocess.run(["/usr/bin/time", "-p"] + cmd, stderr=subprocess.PIPE, universal_newlines=True)
  gal2blaze_time = float(re.search(r'user\s+(\d+\.\d+)', result.stderr).group(1))
  print(f"Gal2Blaze time: {gal2blaze_time}")

  # find time to convert from edge list to galois format by reading the log file
  el2galois_time = 0
  with open(f"/results/galois/conv_time_{dataset}.txt", "r") as f:
    el2galois_time = float(f.read().strip())
  print(f"EL2Galois time: {el2galois_time}")

  # Move the files to the /extra_space directory
  os.system(f"mv {galois_file}.index {TEMP_DIR}")
  os.system(f"mv {galois_file}.adj.1.0 {TEMP_DIR}")

  return el2galois_time, gal2blaze_time

def parse_log(buffer, algo):
  '''Read the log file line by line and match the regex to get the required values:
  the lines look like:
  STAT, {ALGO}_MAIN, Time, TMAX, \d+
  STAT, ReadGraph, Time, TMAX, \d+
  '''
  regex_algo = re.compile(fr"STAT, {algo}_MAIN, Time, TMAX, (\d+)")
  regex_read = re.compile(r"STAT, ReadGraph, Time, TMAX, (\d+)")
  regex_mem = re.compile(r"MemoryCounter:\s+\d+\s+MB\s->\s+\d+\s+MB,\s+(\d+)\s+MB\s+total")
  regex_faults = re.compile(r"MemoryCounter:\s+(\d+)\s+major\s+faults,\s+(\d+)\s+minor\s+faults")
  regex_block_io = re.compile(r"MemoryCounter:\s+(\d+)\s+block\s+input operations,\s+(\d+)\s+block\s+output\s+operations")

  algo_time = 0
  read_time = 0
  mem = 0
  maj_flt = 0
  min_flt = 0
  blk_in = 0
  blk_out = 0

  for line in buffer.splitlines():
    if "ReadGraph" in line:
      read_time = regex_read.search(line).group(1)
    elif f"{algo}_MAIN" in line:
      algo_time = regex_algo.search(line).group(1)
    elif "MB total" in line:
      mem = regex_mem.search(line).group(1)
    elif "faults" in line:
      maj_flt = regex_faults.search(line).group(1)
      min_flt = regex_faults.search(line).group(2)
    elif "output operations" in line:
      blk_in = regex_block_io.search(line).group(1)
      blk_out = regex_block_io.search(line).group(2)
  return read_time, algo_time, mem, maj_flt, min_flt, blk_in, blk_out


def do_bfs(blaze_index_file, blaze_adj_file, dataset):
  # Read random start nodes from .bfsver file
  bfsver_path = Path(f"/datasets/{dataset}/{dataset}").with_suffix(".bfsver")
  with open(bfsver_path, "r") as f:
    random_starts = f.read().splitlines()
    print(random_starts)

  outfile_csv = f"/results/blaze/{dataset}_bfs.csv"
  outfile_log = f"/results/blaze/{dataset}_bfs.log"
  # Run serial BFS
  with open(outfile_csv, "w") as f:
    f.write("read_time(ms),algo_time(ms),mem_used(MB),start_node,num_threads, maj_flt, min_flt, blk_in, blk_out\n")
  for start_node in random_starts:
    command = [f"{BUILD_DIR}/bin/bfs", f"-startNode={start_node}", f"-computeWorkers={NUM_WORKERS}", f"{blaze_index_file}", f"{blaze_adj_file}"]
    with open(outfile_log, "a") as flog, open(outfile_csv, "a") as fcsv:
      print(command)
      for _ in range(REPEATS):
        process = subprocess.run(command, stdout=subprocess.PIPE, universal_newlines=True, check=True)
        flog.write(process.stdout)
        read_time, algo_time, mem, maj_flt, min_flt, blk_in, blk_out = parse_log(process.stdout, "BFS")
        fcsv.write(f"{read_time},{algo_time},{mem},{start_node},{NUM_WORKERS},{maj_flt},{min_flt}, {blk_in},{blk_out}\n")


def do_pagerank(blaze_index_file, blaze_adj_file, dataset):
  outfile_csv = f"/results/blaze/{dataset}_pagerank.csv"
  outfile_log = f"/results/blaze/{dataset}_pagerank.log"

  with open(outfile_csv, "w") as f:
    f.write("read_time(ms),algo_time(ms),mem_used(MB),num_threads, maj_flt, min_flt, blk_in, blk_out\n")
  command = [f"{BUILD_DIR}/bin/pagerank", f"-computeWorkers={NUM_WORKERS}", f"{blaze_index_file}", f"{blaze_adj_file}"]
  print(command)
  with open(outfile_log, "a") as flog, open(outfile_csv, "a") as fcsv:
    for i in range(REPEATS):
      process = subprocess.run(command, stdout=subprocess.PIPE, universal_newlines=True, check=True)
      flog.write(process.stdout)
      read_time, algo_time, mem, maj_flt, min_flt, blk_in, blk_out = parse_log(process.stdout, "PAGERANK")
      fcsv.write(f"{read_time},{algo_time},{mem},{NUM_WORKERS}, {maj_flt},{min_flt},{blk_in},{blk_out}\n")


def main():
  parser = argparse.ArgumentParser(description="run gemini benchmarks")
  parser.add_argument("-d", "--dry_run", action="store_true", default=False, help="don't delete prior logs or run any commands.")
  parser.add_argument("-p", "--parse", action="store_true", default=False, help="parse the logs to make th csv")
  parser.add_argument("-c", "--clean", action="store_true", default=False, help="cleanup the converted datasets")
  args = parser.parse_args()

  # find the number of threads available
  NUM_WORKERS = os.cpu_count() - 8

  # No need to build the project -- done in dockerfile
  datasets = ["graph500_23", "road_asia", "road_usa", "livejournal", "orkut", "dota_league", "graph500_26", "graph500_28", "twitter_mpi"]#, "graph500_30"]

  # Blaze needs the galois format to begin with. Galois stores the graph in a binary .gr format in /datasets/galois directory.
  # We need to convert this to blaze format. Once we are done, we can delete the galois format and the blaze format.
  for dataset in datasets:
    galois_file = f"{DATASET_DIR}/galois/{dataset}.gr"
    blaze_index_file = f"{TEMP_DIR}/{dataset}.gr.index" # <dataset>.adj.<num_disks>.<partition_id>
    blaze_adj_file = f"{TEMP_DIR}/{dataset}.gr.adj.1.0"
    el2gal_time, gal2blaze_time = convert_galois_to_blaze(args, dataset)
    with open(f"/results/blaze/conv_time_{dataset}.txt", "w") as f:
      f.write("e2gal, gal2blaze, total\n")
      f.write( f"{round(el2gal_time, 2)}, {round(gal2blaze_time, 2)}, {round(el2gal_time + gal2blaze_time, 2)}\n")

    do_bfs(blaze_index_file, blaze_adj_file, dataset)
    do_pagerank(blaze_index_file, blaze_adj_file, dataset)

if __name__ == '__main__':
  main()