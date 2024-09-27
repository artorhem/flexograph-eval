#!/bin/bash

source ./galois.sh

DATASET_BASE=$1
OUTFILE_BASE=$2
ITERATIONS=$3
CC=$BUILD_DIR/lonestar/connectedcomponents/connectedcomponents
#SUFFIXES=( "-default" "-degree" "-bfs" "-revdegree" "-random" )
#NZ_SUFFIXES=( "-default_nz" "-degree_nz" "-revdegree_nz" "-random_nz" )
SUFFIXES=( "-default" )
#pdegree not being generated because of segfault

connected_components () {
    (/usr/bin/time -f "%e,%U,%S" $CC -algo=Sync -noverify $1) 2>>$2
    echo "$(cat $2),Sync,$3" > $2
    #(/usr/bin/time -f "%e,%U,%S" $CC -algo=Async -noverify $1) 2>>$2
    #echo "$(cat $2),Async,$3" > $2
    #(/usr/bin/time -f "%e,%U,%S" $CC -algo=EdgeAsync -noverify $1) 2>>$2
    #echo "$(cat $2),EdgeAsync,$3" > $2
    #(/usr/bin/time -f "%e,%U,%S" $CC -algo=EdgetiledAsync -noverify $1) 2>>$2
    #echo "$(cat $2),EtiledAsync,$3" > $2
    #(/usr/bin/time -f "%e,%U,%S" $CC -algo=BlockedAsync -noverify $1) 2>>$2
    #echo "$(cat $2),BlkdAsync,$3" > $2
    #(/usr/bin/time -f "%e,%U,%S" $CC -algo=LabelProp -noverify $1) 2>>$2
    #echo "$(cat $2),LabelProc,$3" > $2
    #(/usr/bin/time -f "%e,%U,%S" $CC -algo=Serial -noverify $1) 2>>$2
    #echo "$(cat $2),Serial,$3" > $2
}

connected_components_cache () {
    echo "Sync" >> $2
    (sudo perf stat -e cache-references,cache-misses $CC -algo=Sync -noverify $1) 2>>$2
    echo "Async" >> $2
    (sudo perf stat -e cache-references,cache-misses $CC -algo=Async -noverify $1) 2>>$2
    echo "EdgeAsync" >> $2
    (sudo perf stat -e cache-references,cache-misses $CC -algo=EdgeAsync -noverify $1) 2>>$2
    echo "EdgetileAsync" >> $2
    (sudo perf stat -e cache-references,cache-misses $CC -algo=EdgetiledAsync -noverify $1) 2>>$2
    echo "BlockedAsync" >> $2
    (sudo perf stat -e cache-references,cache-misses $CC -algo=BlockedAsync -noverify $1) 2>>$2
    echo "LabelProp" >> $2
    (sudo perf stat -e cache-references,cache-misses $CC -algo=LabelProp -noverify $1) 2>>$2
    echo "Serial" >> $2
    (sudo perf stat -e cache-references,cache-misses $CC -algo=Serial -noverify $1) 2>>$2
}

for suffix in "${SUFFIXES[@]}"
do
    DATASET="${DATASET_BASE}${suffix}.gr"
    OUTFILE="${OUTFILE_BASE}${suffix}-cc.csv"
    OUTFILE_CACHE="${OUTFILE_BASE}${suffix}-cache-cc.txt"
    rm $OUTFILE
    #rm $OUTFILE_CACHE
    echo "Real,User,Sys,Algorithm,Iteration" > $OUTFILE
    for iteration in $(seq 1 $ITERATIONS)
    do
        connected_components $DATASET $OUTFILE $iteration
        #connected_components_cache $DATASET $OUTFILE_CACHE
    done
done

for suffix in "${NZ_SUFFIXES[@]}"
do
    DATASET="${DATASET_BASE}${suffix}.gr"
    OUTFILE="${OUTFILE_BASE}${suffix}-cc.csv"
    OUTFILE_CACHE="${OUTFILE_BASE}${suffix}-cache-cc.txt"
    #rm $OUTFILE
    rm $OUTFILE_CACHE
    #echo "Real,User,Sys,Algorithm,Iteration" > $OUTFILE
    for iteration in $(seq 1 $ITERATIONS)
    do
        #connected_components $DATASET $OUTFILE $iteration
        connected_components_cache $DATASET $OUTFILE_CACHE
    done
done
