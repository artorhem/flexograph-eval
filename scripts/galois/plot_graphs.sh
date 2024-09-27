#!/bin/bash

BENCHMARK=$1
OUTFILE_BASE=$2
DATAFILES=()
NZ_DATAFILES=()
SUFFIXES=( "-default" "-degree" "-revdegree" "-bfs" )
NZ_SUFFIXES=( "-default_nz" "-degree_nz" "-revdegree_nz" "-random_nz" )
NZ_BENCHMARK="${BENCHMARK}_nz"
#pdegree not being generated because of segfault

for suffix in "${SUFFIXES[@]}"
do
    OUTFILE="${OUTFILE_BASE}${suffix}-${BENCHMARK}.csv"
    DATAFILES+=(${OUTFILE})
done

#echo ${DATAFILES[@]}
python ../viz/parser.py vstackerr $BENCHMARK ${DATAFILES[@]}
    
for suffix in "${NZ_SUFFIXES[@]}"
do
    OUTFILE="${OUTFILE_BASE}${suffix}-${BENCHMARK}.csv"
    NZ_DATAFILES+=(${OUTFILE})
done

#echo ${NZ_DATAFILES[@]}
python ../viz/parser.py vstackerr $NZ_BENCHMARK ${NZ_DATAFILES[@]}

DEFAULT_FILE="${OUTFILE_BASE}-default-${BENCHMARK}.csv"
DEFAULT_NZ_FILE="${OUTFILE_BASE}-default_nz-${BENCHMARK}.csv"
NAME="${BENCHMARK}-default_comparison"
python ../viz/parser.py vstackerr $NAME $DEFAULT_FILE $DEFAULT_NZ_FILE

DEGREE_FILE="${OUTFILE_BASE}-degree-${BENCHMARK}.csv"
DEGREE_NZ_FILE="${OUTFILE_BASE}-degree_nz-${BENCHMARK}.csv"
NAME="${BENCHMARK}-degree_comparison"
python ../viz/parser.py vstackerr $NAME $DEGREE_FILE $DEGREE_NZ_FILE 

RDEGREE_FILE="${OUTFILE_BASE}-revdegree-${BENCHMARK}.csv"
RDEGREE_NZ_FILE="${OUTFILE_BASE}-revdegree_nz-${BENCHMARK}.csv"
NAME="${BENCHMARK}-revdegree_comparison"
python ../viz/parser.py vstackerr $NAME $RDEGREE_FILE $RDEGREE_NZ_FILE
