#!/bin/bash

SRC_DIR="/systems/in-mem/Galois"
BUILD_DIR="/systems/in-mem/Galois/build"
ITERATIONS=1

DATASET=$1
OUTFILE_BASE=$2
START_NODE=$3
THREADS=$4
OUTFILE_deltaTile="${OUTFILE_BASE}-deltaTile.csv"
OUTFILE_dijkstraTile="${OUTFILE_BASE}-dijkstraTile.csv"
OUTFILE_topoTile="${OUTFILE_BASE}-topoTile.csv"


SSSP=$BUILD_DIR/lonestar/sssp/sssp

#add header if the file is empty or does not exist
if [ $(wc -l < "$OUTFILE_deltaTile") -eq 0 ] || [ -e "$OUTFILE_deltaTile" ]; then
    echo "Real,User,Sys,Algorithm,Vertex_ID,Thread_Count" > "$OUTFILE_deltaTile"
fi

if [ $(wc -l < $OUTFILE_deltaTile) -eq 0 ] || [ -e $OUTFILE_deltaTile ]; then
    echo "Real,User,Sys,Algorithm,Iteration,Vertex_ID,Thread_Count" > $OUTFILE_deltaTile
fi

if [ $(wc -l < $OUTFILE_dijkstraTile) -eq 0 ] || [ -e $OUTFILE_dijkstraTile ]; then
    echo "Real,User,Sys,Algorithm,Iteration,Vertex_ID,Thread_Count" > $OUTFILE_dijkstraTile
fi

if [ $(wc -l < $OUTFILE_topoTile) -eq 0 ] || [ -e $OUTFILE_topoTile ]; then
    echo "Real,User,Sys,Algorithm,Iteration,Vertex_ID,Thread_Count" > $OUTFILE_topoTile
fi

/usr/bin/time -f "%e,%U,%S" $SSSP -algo=deltaTile -startNode=$START_NODE -t=$3 $1 2>>$OUTFILE_deltaTile
sed -i '$s/$/,deltaTile,'$3','$4'/' $OUTFILE_deltaTile

/usr/bin/time -f "%e,%U,%S" $SSSP -algo=dijkstraTile -startNode=$START_NODE -t=$4 $1 2>>$OUTFILE_dijkstraTile
sed -i '$s/$/,dijkstraTile,'$3','$4'/' $OUTFILE_dijkstraTile

/usr/bin/time -f "%e,%U,%S" $SSSP -algo=topoTile -startNode=$START_NODE -t=$4 $1 2>>$OUTFILE_dijkstraTile
sed -i '$s/$/,topoTile,'$3','$4'/' $OUTFILE_dijkstraTile