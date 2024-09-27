#!/bin/bash

SRC_DIR="/systems/in-mem/Galois"
BUILD_DIR="/systems/in-mem/Galois/build"
DATASET=$1
OUTFILE_BASE=$2
CC=$BUILD_DIR/lonestar/connectedcomponents/connectedcomponents
THREADS=$3
ITERATIONS=5

OUTFILE="${2}-LabelProp.csv"

if [ ! -s $OUTFILE_BASE ]; then
    echo "Real,User,Sys,Algorithm,Thread_Count" > $OUTFILE
fi

#run this iterations number of times
for i in `seq 1 $ITERATIONS`;
do
    /usr/bin/time -f "%e,%U,%S" $CC -algo=LabelProp -edgeType=void -t=$THREADS -noverify $1 2>>$OUTFILE
    sed -i '$s/$/,LabelProp,'$THREADS'/' $OUTFILE
done





