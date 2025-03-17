import os
import subprocess
import re
import time

src_dir = "/systems/ooc/xstream"
app_dir = "/systems/ooc/xstream/bin"

datasets = [
  "graph500_23"]  # ,"road_asia", "road_usa", "livejournal", "orkut", "dota_league", "graph500_26", "graph500_28", "graph500_30"]
benchmarks = ["pagerank_functional", "connectedcomponents", "trianglecounting"]

def main():
  #build xstream
  os.chdir(src_dir)
  os.system("make clean && make -j && make install")



if __name__ == "__main__":
  main()