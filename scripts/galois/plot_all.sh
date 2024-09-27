#!/bin/bash

#DATASETS=( "stats/kron/kron" "stats/parmat/parmat" "stats/twitter_rv/twitter_rv" "stats/cit_patents/cit_patents" )
DATASETS=( "stats/kron/kron" "stats/parmat/parmat" "stats/cit_patents/cit_patents" )
BENCHMARK=$1

for dataset in "${DATASETS[@]}"
do
    ./plot_graphs.sh $BENCHMARK $dataset
done
