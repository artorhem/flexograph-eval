set -x

SRC_DIR="/systems/in-mem/Galois"
BUILD_DIR="/systems/in-mem/Galois/build"
ITERATIONS=5

mkdir -p $BUILD_DIR
cmake -S $SRC_DIR -B $BUILD_DIR -DCMAKE_BUILD_TYPE=Release

make -C $BUILD_DIR/lonestar/bfs -j
make -C $BUILD_DIR/lonestar/connectedcomponents -j
make -C $BUILD_DIR/lonestar/pagerank -j
make -C $BUILD_DIR/lonestar/triangles -j
make -C $BUILD_DIR/lonestar/sssp -j

cd $BUILD_DIR
make graph-convert -j

if [ ! -d /results/galois ]; then
  mkdir -p /results/galois
fi

if [ ! -d /datasets/galois ]; then
  mkdir -p /datasets/galois
fi

datasets=(
  "graph500_23"
  "graph500_26"
  "graph500_28"
  "graph500_30"
  "dota_league"
  "livejournal"
  "orkut"
  "road_asia"
  "road_usa"
)

benchmarks=(
  "pagerank"
  "bfs"
  "connectedcomponents"
  "triangles"
)
#sssp is not working; segfaults

THREADS=`nproc --all`

for dataset in "${datasets[@]}"
do
  #if the dataset.bfsver file does not exist, create it usign the bfsver command
  if [ ! -f /datasets/${dataset}/${dataset}.bfsver ]; then
    python3 /graph_utils.py bfsver /datasets/${dataset}/${dataset} /datasets/${dataset}/${dataset}.bfsver
  fi
  
  #measure the time to convert the dataset to lonestar .gr format and save in a variable
  if [ ! -f /datasets/galois/${dataset}.gr ]; then
    COMMAND="$BUILD_DIR/tools/graph-convert/graph-convert -edgelist2gr /datasets/${dataset}/${dataset} /datasets/galois/${dataset}.gr"
    TIME_OUTPUT=$(/usr/bin/time -p $COMMAND 2>&1)
    echo "Time to convert $dataset to gr: $TIME_OUTPUT"
    TIME_TAKEN=$(echo "$TIME_OUTPUT" | grep real | awk '{print $2}')
    echo "$TIME_TAKEN" >> /results/galois/conv_time_${dataset}.txt
  else
    echo "Dataset ${dataset} already exists in .gr format"
    #read the time taken to convert the dataset to lonestar .gr format from the file
    TIME_TAKEN=$(cat /results/galois/conv_time_${dataset}.txt)
  fi
  
  #Read the random start nodes from the dataset.bfsver file and save in an array
  IFS=$'\n' read -d '' -r -a random_starts < /datasets/${dataset}/${dataset}.bfsver

  for benchmark in "${benchmarks[@]}"
  do
    #cleanup the output files from previous runs
    rm -f /results/galois/${dataset}_${benchmark}-*.csv

    #check if benchmark is bfs
    if [ "$benchmark" == "bfs" ]; then
      for nodes in "${random_starts[@]}"
      do
        /${benchmark}.sh /datasets/galois/${dataset}.gr /results/galois/${dataset}_${benchmark} ${nodes} ${THREADS}
      done
    else
      /${benchmark}.sh /datasets/galois/${dataset}.gr /results/galois/${dataset}_${benchmark} ${THREADS}
    fi
  done
done