#!/bin/bash

SRC_DIR="/systems/in-mem/Galois"
BUILD_DIR="/systems/in-mem/Galois/build"

DATASET=$1
OUTFILE_BASE=$2
ITERATIONS=5
THREADS=$3
TC=$BUILD_DIR/lonestar/triangles/triangles

OUTFILE_nodeiterator="${OUTFILE_BASE}-nodeiterator.csv"
OUTFILE_edgeiterator="${OUTFILE_BASE}-edgeiterator.csv"
OUTFILE_orderedcount="${OUTFILE_BASE}-orderedcount.csv"

if [ ! -s $OUTFILE_nodeiterator ]; then
    echo "Real,User,Sys,Algorithm,Thread_Count" > $OUTFILE_nodeiterator
fi

if [ ! -s $OUTFILE_edgeiterator ]; then
    echo "Real,User,Sys,Algorithm,Thread_Count" > $OUTFILE_edgeiterator
fi

if [ ! -s $OUTFILE_orderedcount ]; then
    echo "Real,User,Sys,Algorithm,Thread_Count" > $OUTFILE_orderedcount
fi

for iteration in $(seq 1 $ITERATIONS)
do
    /usr/bin/time -f "%e,%U,%S" $TC -algo=nodeiterator -t=$THREADS -noverify -statFile=$OUTFILE_BASE-nodeiterator.stat $DATASET 2>>$OUTFILE_nodeiterator
    sed -i '$s/$/,nodeIterator,'$THREADS'/' $OUTFILE_nodeiterator


    /usr/bin/time -f "%e,%U,%S" $TC -algo=edgeiterator -t=$THREADS -noverify -statFile=$OUTFILE_BASE-edgeiterator.stat $DATASET 2>>$OUTFILE_edgeiterator
    sed -i '$s/$/,edgeIterator,'$THREADS'/' $OUTFILE_edgeiterator

    /usr/bin/time -f "%e,%U,%S" $TC -algo=orderedCount -t=$THREADS -noverify -statFile=$OUTFILE_BASE-orderedCount.stat $DATASET 2>>$OUTFILE_orderedcount
    sed -i '$s/$/,orderedCount,'$THREADS'/' $OUTFILE_orderedcount
done