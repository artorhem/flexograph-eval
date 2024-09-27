#!/bin/bash

SRC_DIR="/systems/in-mem/Galois"
BUILD_DIR="/systems/in-mem/Galois/build"

DATASET=$1
OUTFILE_BASE=$2

TC=$BUILD_DIR/lonestar/triangles/triangles

OUTFILE_nodeiterator="${OUTFILE_BASE}-nodeiterator.csv"
OUTFILE_edgeiterator="${OUTFILE_BASE}-edgeiterator.csv"
OUTFILE_orderedcount="${OUTFILE_BASE}-orderedcount.csv"

triangle_counting () {
    /usr/bin/time -f "%e,%U,%S" $TC -algo=nodeiterator -t=28 -noverify -statFile=$OUTFILE_BASE-nodeiterator.stat $DATASET 2>>$OUTFILE_nodeiterator
    sed -i '$s/$/,nodeIterator,'$THREADS'/' $OUTFILE_nodeiterator


    /usr/bin/time -f "%e,%U,%S" $TC -algo=edgeiterator -t=28 -noverify -statFile=$OUTFILE_BASE-edgeiterator.stat $DATASET 2>>$OUTFILE_edgeiterator
    sed -i '$s/$/,edgeIterator,'$THREADS'/' $OUTFILE_edgeiterator

    /usr/bin/time -f "%e,%U,%S" $TC -algo=orderedCount -t=28 -noverify -statFile=$OUTFILE_BASE-orderedCount.stat $DATASET 2>>$OUTFILE_orderedcount
    sed -i '$s/$/,orderedCount,'$THREADS'/' $OUTFILE_orderedcount
}


if [ ! -s $OUTFILE ]; then
    echo "Real,User,Sys,Algorithm,Thread_Count" > $OUTFILE
fi

for iteration in $(seq 1 $ITERATIONS)
do
    triangle_counting $DATASET $OUTFILE $STATFILE $iteration
done
