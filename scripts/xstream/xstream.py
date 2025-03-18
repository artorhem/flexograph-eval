import os
import subprocess
import re
import time

src_dir = "/systems/ooc/xstream"
app_dir = "/systems/ooc/xstream/bin"
llama_converter = "/llama/bin/snap-to-xs1"

datasets = [
  "graph500_23"]  # ,"road_asia", "road_usa", "livejournal", "orkut", "dota_league", "graph500_26", "graph500_28", "graph500_30"]
benchmarks = ["pagerank_functional", "connectedcomponents", "trianglecounting"]

def main():
  for dataset in datasets:
    #we must first use the llama converter to convert the graph to the xstream format

  "benchmark_driver -p 16 -a -b pagerank -g test --physical_memory 8589934592"
  
  
  

if __name__ == "__main__":
  main()