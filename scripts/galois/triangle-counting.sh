#!/bin/bash

source ./galois.sh

DATASET=$1
OUTFILE="${OUTFILE_BASE}_tc.csv"
STATFILE="${OUTFILE_BASE}_stat_tc.txt"
ITERATIONS=$3
TC=$BUILD_DIR/lonestar/triangles/triangles
#pdegree not being generated because of segfault

triangle_counting () {
    (/usr/bin/time -f "%e,%U,%S" $TC -algo=nodeiterator -t=1 -statFile=$3 $1) 2>>$2
    echo "$(cat $2),NodeIterator,$4" > $2
    (/usr/bin/time -f "%e,%U,%S" $TC -algo=edgeiterator -t=1 -statFile=$3 $1) 2>>$2
    echo "$(cat $2),EdgeIterator,$4" > $2
    (/usr/bin/time -f "%e,%U,%S" $TC -algo=directed -t=16 -statFile=$3 $1) 2>>$2
    echo "$(cat $2),Directed,$4" > $2
}


echo $DATASET, $OUTFILE
rm $OUTFILE
echo "Real,User,Sys,Algorithm,Iteration" > $OUTFILE
for iteration in $(seq 1 $ITERATIONS)
do
    triangle_counting $DATASET $OUTFILE $STATFILE $iteration
done
