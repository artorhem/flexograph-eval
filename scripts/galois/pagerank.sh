#!/bin/bash
set -ex

BUILD_DIR="/systems/in-mem/Galois/build"

ITERATIONS=5
THREADS=$3
PRPULL=$BUILD_DIR/lonestar/pagerank/pagerank-pull
PRPUSH=$BUILD_DIR/lonestar/pagerank/pagerank-push

OUTFILE_PUSH="${2}-push.csv"
OUTFILE_PULL="${2}-pull.csv"

#add header if the file is empty or does not exist
if [ ! -s $OUTFILE_PULL ]; then
    echo "Real,User,Sys,Algorithm,Tolerance,Thread_Count" > $OUTFILE_PULL
fi

if [ ! -s $OUTFILE_PUSH ]; then
    echo "Real,User,Sys,Algorithm,Tolerance,Thread_Count" > $OUTFILE_PUSH
fi

for i in `seq 1 $ITERATIONS`;
do
    /usr/bin/time -f "%e,%U,%S" $PRPULL -algo=Topo -tolerance=0.0001 -t=$THREADS $1 2>>$OUTFILE_PULL
    sed -i '$s/$/,Async-Pull,0.0001,'$THREADS'/' $OUTFILE_PULL

    /usr/bin/time -f "%e,%U,%S" $PRPULL -algo=Residual -tolerance=0.0001 -t=$THREADS  $1 2>>$OUTFILE_PULL
    sed -i '$s/$/,Pull-Residual,0.0001,'$THREADS'/' $OUTFILE_PULL

    /usr/bin/time -f "%e,%U,%S" $PRPUSH -algo=Async -tolerance=0.0001 -t=$THREADS  $1 2>>$OUTFILE_PUSH
    sed -i '$s/$/,Push-Async,0.0001,'$THREADS'/' $OUTFILE_PUSH

    /usr/bin/time -f "%e,%U,%S" $PRPUSH -algo=Sync -tolerance=0.0001 -t=$THREADS $1 2>>$OUTFILE_PUSH
    sed -i '$s/$/,Push-Sync,0.0001,'$THREADS'/' $OUTFILE_PUSH
done

