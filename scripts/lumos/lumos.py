import argparse
import os
import sys
import json
import re
import time

SRC_DIR = "/systems/ooc/lumos"
TOOLS_DIR = "/systems/in-mem/lumos/toolkits"
DATASET_DIR = "/datasets"
RESULTS_DIR = "/results/lumos"

REPEATS = 5
PR_MAX_ITERS = 20

def parse_pagerank_log(dataset_name, program_name, iterations):
  """Parse PageRank log files with the new format"""
  input_file = f"{RESULTS_DIR}/{dataset_name}_{program_name}_iter{iterations}.log"
  
  if not os.path.exists(input_file):
    print(f"Warning: Log file {input_file} not found")
    return None
  
  # Regex patterns for the new format
  regex_iteration = r"Iteration\s+(\d+):\s+active\s+vertices\s+=\s+(\d+)"
  regex_exectime = r"(\d+)\s+iterations\s+of\s+pagerank\s+took\s+(\d+\.\d+)\s+seconds"
  regex_mem = r"MemoryCounter:\s+\d+\s+MB\s+->\s+(\d+)\s+MB,\s+(\d+)\s+MB\s+total"
  regex_faults = r"MemoryCounter:\s+(\d+)\s+major\s+faults,\s+(\d+)\s+minor\s+faults"
  regex_blockIO = r"MemoryCounter:\s+(\d+)\s+block\s+input\s+operations,\s+(\d+)\s+block\s+output\s+operations"
  
  exec_time = 0.0
  max_mem = 0
  total_mem = 0
  maj_faults = 0
  min_faults = 0
  blkio_in = 0
  blkio_out = 0
  requested_iterations = 0
  actual_iterations = 0
  convergence_iteration = None  # Only for pagerank_delta
  
  try:
    with open(input_file, 'r') as f:
      for line in f:
        line = line.strip()
        
        # Match iteration lines - only check for convergence in pagerank_delta
        match = re.search(regex_iteration, line)
        if match and program_name == "pagerank_delta":
          iter_num = int(match.group(1))
          active_vertices = int(match.group(2))
          # First iteration where active vertices = 0 is the convergence point
          if active_vertices == 0 and convergence_iteration is None:
            convergence_iteration = iter_num

        # Match execution time
        match = re.search(regex_exectime, line)
        if match:
          requested_iterations = int(match.group(1))
          exec_time = float(match.group(2))
        
        # Match memory usage
        match = re.search(regex_mem, line)
        if match:
          max_mem = int(match.group(1))
          total_mem = int(match.group(2))
        
        # Match page faults
        match = re.search(regex_faults, line)
        if match:
          maj_faults = int(match.group(1))
          min_faults = int(match.group(2))
        
        # Match block I/O
        match = re.search(regex_blockIO, line)
        if match:
          blkio_in = int(match.group(1))
          blkio_out = int(match.group(2))
    
    # Set actual iterations based on program type
    if program_name == "pagerank_delta" and convergence_iteration is not None:
      actual_iterations = convergence_iteration
    else:
      # For pagerank and pagerank_gg, actual iterations = requested iterations
      actual_iterations = requested_iterations
          
    return {
      'dataset': dataset_name,
      'program': program_name,
      'requested_iterations': requested_iterations,
      'actual_iterations': actual_iterations,
      'exec_time': exec_time,
      'max_mem_mb': max_mem,
      'total_mem_mb': total_mem,
      'major_faults': maj_faults,
      'minor_faults': min_faults,
      'block_input': blkio_in,
      'block_output': blkio_out
    }
    
  except Exception as e:
    print(f"Error parsing {input_file}: {e}")
    return None

def save_timing_data(conversion_times, preprocessing_times):
  """Save timing data to a JSON file for later use during parsing"""
  timing_file = f"{RESULTS_DIR}/lumos_timing_data.json"
  timing_data = {
    'conversion_times': conversion_times,
    'preprocessing_times': preprocessing_times
  }
  
  with open(timing_file, 'w') as f:
    json.dump(timing_data, f, indent=2)
  print(f"Timing data saved to {timing_file}")

def load_timing_data():
  """Load timing data from JSON file"""
  timing_file = f"{RESULTS_DIR}/lumos_timing_data.json"
  
  if not os.path.exists(timing_file):
    print(f"Warning: Timing data file {timing_file} not found, using zeros")
    return {}, {}
  
  try:
    with open(timing_file, 'r') as f:
      timing_data = json.load(f)
    
    conversion_times = timing_data.get('conversion_times', {})
    preprocessing_times = timing_data.get('preprocessing_times', {})
    print(f"Timing data loaded from {timing_file}")
    return conversion_times, preprocessing_times
    
  except Exception as e:
    print(f"Error loading timing data: {e}, using zeros")
    return {}, {}

def discover_datasets_from_logs():
  """Discover datasets from existing log files"""
  if not os.path.exists(RESULTS_DIR):
    print(f"Results directory {RESULTS_DIR} does not exist")
    return []
  
  log_files = [f for f in os.listdir(RESULTS_DIR) if f.endswith('.log')]
  datasets = set()
  
  for log_file in log_files:
    # Extract dataset name from log filename: <dataset>_<program>_iter<N>.log
    parts = log_file.replace('.log', '').split('_')
    if len(parts) >= 3 and parts[-1].startswith('iter'):
      # Join all parts except the last two (program and iterN)
      dataset_name = '_'.join(parts[:-2])
      datasets.add(dataset_name)
  
  return sorted(list(datasets))

def parse_pagerank_logs(datasets, conversion_times, preprocessing_times):
  """Parse all PageRank log files and create CSV summary"""
  programs = ["pagerank", "pagerank_gg", "pagerank_delta"]
  iterations = [10, 20, 30]
  
  # Create main summary CSV
  csv_file = f"{RESULTS_DIR}/lumos_pagerank_results.csv"
  with open(csv_file, 'w') as f:
    f.write("dataset,program,requested_iterations,actual_iterations,exec_time_s,max_mem_mb,total_mem_mb,major_faults,minor_faults,block_input,block_output,conversion_time_s,preprocessing_time_s\n")
    
    for dataset_name in datasets:
      # Get conversion and preprocessing times for this dataset
      conv_time = conversion_times.get(dataset_name, 0.0)
      preproc_time = preprocessing_times.get(dataset_name, 0.0)
      
      for program in programs:
        for iters in iterations:
          result = parse_pagerank_log(dataset_name, program, iters)
          if result:
            f.write(f"{result['dataset']},{result['program']},{result['requested_iterations']},"
                   f"{result['actual_iterations']},{result['exec_time']},{result['max_mem_mb']},"
                   f"{result['total_mem_mb']},{result['major_faults']},{result['minor_faults']},"
                   f"{result['block_input']},{result['block_output']},{conv_time},{preproc_time}\n")
  
  print(f"PageRank results written to {csv_file}")
  
  # Create individual program CSV files
  for program in programs:
    program_csv = f"{RESULTS_DIR}/lumos_{program}_results.csv"
    with open(program_csv, 'w') as f:
      f.write("dataset,requested_iterations,actual_iterations,exec_time_s,max_mem_mb,total_mem_mb,major_faults,minor_faults,block_input,block_output\n")
      
      for dataset_name in datasets:
        for iters in iterations:
          result = parse_pagerank_log(dataset_name, program, iters)
          if result:
            f.write(f"{result['dataset']},{result['requested_iterations']},"
                   f"{result['actual_iterations']},{result['exec_time']},{result['max_mem_mb']},"
                   f"{result['total_mem_mb']},{result['major_faults']},{result['minor_faults']},"
                   f"{result['block_input']},{result['block_output']}\n")
    
    print(f"{program} results written to {program_csv}")


def convert_to_binary(dataset_path, dry_run=False):
  """Convert dataset to binary format if .bin file doesn't exist"""
  bin_file = dataset_path + ".bin"
  if os.path.exists(bin_file):
    print(f"Binary file {bin_file} already exists, skipping conversion")
    return bin_file, 0.0
  
  print(f"Converting {dataset_path} to binary format...")
  convert_cmd = f"{SRC_DIR}/bin/convert2bin {dataset_path}"
  print(f"Running: {convert_cmd}")
  
  conversion_time = 0.0
  if not dry_run:
    start_time = time.time()
    result = os.system(convert_cmd)
    end_time = time.time()
    conversion_time = end_time - start_time
    
    if result != 0:
      print(f"Error: Conversion failed with exit code {result}")
      sys.exit(1)
    if not os.path.exists(bin_file):
      print(f"Error: Expected binary file {bin_file} was not created")
      sys.exit(1)
    
    print(f"Conversion completed in {conversion_time:.2f} seconds")
  
  return bin_file, conversion_time

def get_max_vertex_id(dataset_name):
  """Get the highest vertex ID from the .v file"""
  v_file = f"{DATASET_DIR}/{dataset_name}/{dataset_name}.v"
  
  if not os.path.exists(v_file):
    print(f"Warning: Vertex file {v_file} not found")
    return None
  
  try:
    with open(v_file, 'r') as f:
      # Read all lines and get the last one (highest vertex ID)
      lines = f.readlines()
      if not lines:
        print(f"Warning: Vertex file {v_file} is empty")
        return None
      
      # Get the last line, strip whitespace, and convert to int
      max_vertex_id = int(lines[-1].strip())
      print(f"Max vertex ID for {dataset_name}: {max_vertex_id}")
      return max_vertex_id
      
  except (IOError, ValueError) as e:
    print(f"Error reading vertex file {v_file}: {e}")
    return None

def run_preprocessing(dataset_name, bin_file, num_vertices, dry_run=False):
  """Run the Lumos preprocessing step"""
  output_file = f"{dataset_name}.pl"
  partitions = 8
  
  preprocess_cmd = (f"{SRC_DIR}/bin/preprocess "
                   f"-i {bin_file} "
                   f"-o {output_file} "
                   f"-v {num_vertices} "
                   f"-p {partitions} "
                   f"-t 0 "
                   f"-m 0")
  
  print(f"Running preprocessing for {dataset_name}...")
  print(f"Command: {preprocess_cmd}")
  
  preprocessing_time = 0.0
  if not dry_run:
    start_time = time.time()
    result = os.system(preprocess_cmd)
    end_time = time.time()
    preprocessing_time = end_time - start_time
    
    if result != 0:
      print(f"Error: Preprocessing failed with exit code {result}")
      return False, preprocessing_time
    
    # Check if output file was created
    if not os.path.exists(output_file):
      print(f"Error: Expected output file {output_file} was not created")
      return False, preprocessing_time
    
    print(f"Preprocessing completed successfully in {preprocessing_time:.2f} seconds. Output: {output_file}")
  else:
    print("Dry run: preprocessing command would be executed")
  
  return True, preprocessing_time

def run_pagerank_programs(dataset_name, preprocessed_file, dry_run=False):
  """Run the three PageRank programs: pagerank, pagerank_gg, and pagerank_delta"""
  programs = ["pagerank", "pagerank_gg", "pagerank_delta"]
  iterations = [10, 20, 30]
  memory_budget = 100  # GB
  
  for program in programs:
    print(f"\nRunning {program} for {dataset_name}...")
    
    for iters in iterations:
      print(f"  Running {program} with {iters} iterations...")
      
      # Construct command: <program> <preprocessed_file> <iterations> <memory_budget_GB>
      cmd = f"{SRC_DIR}/bin/{program} {preprocessed_file} {iters} {memory_budget}"
      print(f"  Command: {cmd}")
      
      if not dry_run:
        # Create log file for this specific run
        log_file = f"{RESULTS_DIR}/{dataset_name}_{program}_iter{iters}.log"
        cmd_with_log = f"{cmd} >> {log_file} 2>&1"
        
        start_time = time.time()
        result = os.system(cmd_with_log)
        end_time = time.time()
        execution_time = end_time - start_time
        
        if result != 0:
          print(f"  Warning: {program} with {iters} iterations failed with exit code {result}")
        else:
          print(f"  {program} with {iters} iterations completed successfully in {execution_time:.2f} seconds")
      else:
        print(f"  Dry run: would execute {cmd}")

def main(self):
  parser = argparse.ArgumentParser(description="run Lumos benchmarks")
  parser.add_argument("-d", "--dry_run",action="store_true",default=False, help="don't delete prior logs or run any commands.")
  parser.add_argument("-p","--parse",action="store_true",default=False, help="parse the logs to make the csv")
  parser.add_argument("--parse-only",action="store_true",default=False, help="only parse existing logs without running benchmarks")
  args = parser.parse_args()

  # Ensure results directory exists
  if not os.path.exists(RESULTS_DIR):
    os.makedirs(RESULTS_DIR)

  # Handle parse-only mode
  if args.parse_only:
    print("Running in parse-only mode...")
    
    # Discover datasets from existing log files
    datasets = discover_datasets_from_logs()
    if not datasets:
      print("No log files found to parse")
      return
    
    print(f"Found datasets in logs: {datasets}")
    
    # Load timing data
    conversion_times, preprocessing_times = load_timing_data()
    
    # Parse the logs
    parse_pagerank_logs(datasets, conversion_times, preprocessing_times)
    return

  os.chdir(SRC_DIR)
  #run make here
  os.system("make clean && make -j")

  datasets = ["graph500_23", "road_asia", "road_usa", "livejournal", "orkut", "dota_league", "graph500_26", "graph500_28"]
  
  # Track timing data for parsing
  conversion_times = {}
  preprocessing_times = {}
  
  for dataset_name in datasets:
    print(f"Processing dataset: {dataset_name}")
    dataset_path = f"{DATASET_DIR}/{dataset_name}/{dataset_name}"
    
    # Check if dataset file exists
    if not os.path.exists(dataset_path):
      print(f"Warning: Dataset file {dataset_path} not found, skipping")
      continue
    
    # Convert to binary format if needed
    bin_file, conversion_time = convert_to_binary(dataset_path, args.dry_run)
    print(f"Using binary file: {bin_file}")
    conversion_times[dataset_name] = conversion_time
    
    # Get the maximum vertex ID
    max_vertex_id = get_max_vertex_id(dataset_name)
    if max_vertex_id is None:
      print(f"Warning: Could not determine max vertex ID for {dataset_name}, skipping")
      continue
    
    num_vertices = max_vertex_id + 1
    print(f"Number of vertices: {num_vertices}")
    
    # Run preprocessing
    preprocessing_success, preprocessing_time = run_preprocessing(dataset_name, bin_file, num_vertices, args.dry_run)
    if not preprocessing_success:
      print(f"Warning: Preprocessing failed for {dataset_name}, skipping")
      continue
    preprocessing_times[dataset_name] = preprocessing_time
    
    # Run PageRank programs
    preprocessed_file = f"{dataset_name}.pl"
    run_pagerank_programs(dataset_name, preprocessed_file, args.dry_run)
    
    # Print timing summary
    total_time = conversion_time + preprocessing_time
    print(f"\nTiming summary for {dataset_name}:")
    print(f"  Conversion time: {conversion_time:.2f} seconds")
    print(f"  Preprocessing time: {preprocessing_time:.2f} seconds")
    print(f"  Total time: {total_time:.2f} seconds")

  # Save timing data for later parsing
  if not args.dry_run:
    save_timing_data(conversion_times, preprocessing_times)

  if args.parse:
    parse_pagerank_logs(datasets, conversion_times, preprocessing_times)

if __name__ == "__main__":
  main(sys.argv)