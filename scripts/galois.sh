set -x

SRC_DIR=`pwd` # Or top-level Galois source dir
BUILD_DIR=build
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
  "bfs"
  "connectedcomponents"
  "pagerank"
  "triangles"
  "sssp"
)

# cd $BUILD_DIR

# for dataset in "${datasets[@]}"
# do
#   #measure the time to convert the dataset to lonestar .gr format and save in a variable
#   COMMAND="$BUILD_DIR/tools/graph-convert/graph-convert -edgelist2gr /datasets/${dataset}/${dataset} ${dataset}.gr"
#   TIME_OUTPUT=$(/usr/bin/time -p $COMMAND 2>&1)
#   echo "Time to convert $dataset to gr: $TIME_OUTPUT"
#   TIME_TAKEN=$(echo "$TIME_OUTPUT" | grep real | awk '{print $2}')

#   #Now run the benchmarks using the Metastudy scripts
#   ./triangle-counting.sh ../../datasets/cit-patents/cit-Patents tc_output/cp-tc $ITERATIONS 
 