#!/bin/bash

PLANAR_DIR=/systems/ooc/Planar
PLANAR_BIN_DIR=/systems/ooc/Planar/bin
FOLLY_DIR=/folly
FOLLY_BUILD_DIR=/scratch/folly_build
GLOG_DIR=/scratch/glog

# Check that the pwd is /systems/ooc/plnar
if [ "$PWD" != "/systems/ooc/planar" ]; then
    cd /systems/ooc/planar
fi

echo "Building Planar"
echo "initializing submodules"
git submodule update --init --recursive
git submodule update

echo "Building yaml-cpp (required by Planar)"
#make yaml-cpp
cd $PLANAR_DIR/third_party/yaml-cpp
mkdir -p build
cd build
cmake ..
make -j


echo "Building liburing (required by Planar)"
#clone and build liburing
cd $PLANAR_DIR/third_party
git clone https://github.com/axboe/liburing.git
cd liburing
./configure && make -j && make install

echo "Building folly (required by Planar)"
#check if folly is already built (the directory is not empty)
if [ -z "$(ls -A ${FOLLY_BUILD_DIR})" ]; then
   cd / && git clone https://github.com/facebook/folly.git
   cd $FOLLY_DIR
   python3 ./build/fbcode_builder/getdeps.py --allow-system-packages --scratch-path=$FOLLY_BUILD_DIR build
else 
    echo "Folly already built"
fi

#We need to build glog from source
if [ -z "$(ls -A ${GLOG_DIR})" ]; then
    cd / && git clone https://github.com/google/glog.git $GLOG_DIR
fi
cd $GLOG_DIR
cmake -S . -B build -G "Unix Makefiles"
cmake --build build -j
cmake --build build --target install

echo "Now building Planar"
cd $PLANAR_DIR
mkdir -p build; cd build

PREFIX_PATH="$FOLLY_BUILD_DIR/installed/folly"
#Now we need to find where libfmt is installed
FMT_PATH=$(ls /folly_build/installed | grep fmt)
#append fmt to the prefix path
eval PREFIX_PATH="\"${PREFIX_PATH};${FOLLY_BUILD_DIR}/installed/${FMT_PATH}\""
cmake -DCMAKE_PREFIX_PATH=${PREFIX_PATH} ..
make -j



echo "Planar built successfully"

#Now we need to run the tests.

# datasets=(
#   "graph500_23"
#   "graph500_26"
#   "graph500_28"
#   "graph500_30"
#   "dota_league"
#   "livejournal"
#   "orkut"
#   "road_asia"
#   "road_usa"
# )

# benchmarks=(
#   "pagerank"
#   "sssp"
#   "wcc"
# )

# THREADS=`nproc --all`

# for dataset in "${datasets[@]}"
# do
#     #We first need to convert the dataset to Planar format
#     if [ ! -f /datasets/${dataset}/${dataset}.planar ]; then
#     #./bin/tools/graph_converter_exec -i /datasets/dota_league/dota_league -o /tmp/dotaCSR.test -convert_mode=edgelistcsv2edgelistbin -store_strategy=kUnconstrained -sep="\t"
#     fi



# done