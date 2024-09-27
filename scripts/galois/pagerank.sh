#!/bin/bash

source ./galois.sh

DATASET_BASE=$1
OUTFILE_BASE=$2
ITERATIONS=$3
PRPULL=$BUILD_DIR/lonestar/pagerank/pagerank-pull
PRPUSH=$BUILD_DIR/lonestar/pagerank/pagerank-push
#SUFFIXES=( "-default" "-degree" "-bfs" "-revdegree" "-random" )
#SUFFIXES=( "-default" "-revdegree" "-degree" )
SUFFIXES=( "-random" )
#NZ_SUFFIXES=( "-default_nz" "-degree_nz" "-revdegree_nz" "-random_nz" )
#pdegree not being generated because of segfault

pagerank () {
    (/usr/bin/time -f "%e,%U,%S" $PRPULL -algo=Topo -tolerance=0.01 $1) 2>>$2
    echo "$(cat $2),Pull-Topo,$3" > $2
    (/usr/bin/time -f "%e,%U,%S" $PRPULL -algo=Residual -tolerance=0.01 $1) 2>>$2
    echo "$(cat $2),Pull-Residual,$3" > $2
    (/usr/bin/time -f "%e,%U,%S" $PRPUSH -algo=Async -tolerance=0.01 $1) 2>>$2
    echo "$(cat $2),Push-Async,$3" > $2
    (/usr/bin/time -f "%e,%U,%S" $PRPUSH -algo=Sync -tolerance=0.01 $1) 2>>$2
    echo "$(cat $2),Push-Sync,$3" > $2 
}

pagerank_cache () {
    echo "Pull-Topo" >> $2
    (sudo perf stat -e cache-references,cache-misses $PRPULL -algo=Topo -tolerance=0.01 $1) 2>>$2
    echo "Pull-Residual" >> $2
    (sudo perf stat -e cache-references,cache-misses $PRPULL -algo=Residual -tolerance=0.01 $1) 2>>$2
    echo "Push-Async" >> $2
    (sudo perf stat -e cache-references,cache-misses $PRPUSH -algo=Async -tolerance=0.01 $1) 2>>$2
    echo "Push-Sync" >> $2
    (sudo perf stat -e cache-references,cache-misses $PRPUSH -algo=Sync -tolerance=0.01 $1) 2>>$2
}

for suffix in "${SUFFIXES[@]}"
do
    DATASET="${DATASET_BASE}${suffix}.gr"
    OUTFILE="${OUTFILE_BASE}${suffix}-pr.csv"
    OUTFILE_CACHE="${OUTFILE_BASE}${suffix}-cache-pr.csv"
    rm $OUTFILE
    #rm $OUTFILE_CACHE
    echo "Real,User,Sys,Algorithm,Iteration" > $OUTFILE
    for iteration in $(seq 1 $ITERATIONS)
    do
        pagerank $DATASET $OUTFILE $iteration
        #pagerank_cache $DATASET $OUTFILE_CACHE
    done
done

for suffix in "${NZ_SUFFIXES[@]}"
do
    DATASET="${DATASET_BASE}${suffix}.gr"
    OUTFILE="${OUTFILE_BASE}${suffix}-pr.csv"
    OUTFILE_CACHE="${OUTFILE_BASE}${suffix}-cache-pr.csv"
    #rm $OUTFILE
    rm $OUTFILE_CACHE
    #echo "Real,User,Sys,Algorithm,Iteration" > $OUTFILE
    for iteration in $(seq 1 $ITERATIONS)
    do
        #pagerank $DATASET $OUTFILE $iteration
        pagerank_cache $DATASET $OUTFILE_CACHE
    done
done

