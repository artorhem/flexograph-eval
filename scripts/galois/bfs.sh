#!/bin/bash

SRC_DIR="/systems/in-mem/Galois"
BUILD_DIR="/systems/in-mem/Galois/build"
ITERATIONS=1

DATASET=$1
OUTFILE_BASE=$2
START_NODE=$3
THREADS=$4
OUTFILE_P="${OUTFILE_BASE}-parallel.csv"
OUTFILE_S="${OUTFILE_BASE}-serial.csv"

BFS=$BUILD_DIR/lonestar/bfs/bfs

bfs () {
    #run the parallel bfs and save the output to a variable
    /usr/bin/time -f "%e,%U,%S" $BFS -algo=Async -exec=$3 -startNode=$4 -t=$5 -noverify $1 2>>$2
    #edit the last line to have the algoname, thread count and start node
    sed -i '$s/$/,'$3','$4','$5'/' $2

}

#add the header if the file is empty or if it does not exist

if [ $(wc -l < $OUTFILE_P) -eq 0 || -e $OUTFILE_P ]; then
    echo "Real,User,Sys,Algorithm,Vertex_ID,Thread_Count" > $OUTFILE_P
fi


if [ $(wc -l < $OUTFILE_S) -eq 0 || -e $OUTFILE_S ]; then
    echo "Real,User,Sys,Algorithm,Vertex_ID,Thread_Count" > $OUTFILE_S
fi

bfs $DATASET $OUTFILE_P PARALLEL ${START_NODE} ${THREADS}
bfs $DATASET $OUTFILE_S SERIAL ${START_NODE} ${THREADS}

