#!/bin/bash

source galois.sh

DATASET=$1
xpath=${DATASET%/*} 
xbase=${DATASET##*/}
xfext=${xbase##*.}
xpref=${xbase%.*}
BASENAME=${xpath}/${xpref}

GC=$BUILD_DIR/tools/graph-convert/graph-convert
ISO=../../preprocessor/isomorph.py

convert_to_galois () {
    GR_NAME="${BASENAME}-default.gr"
    GR_DEGREE_NAME="${BASENAME}-degree.gr"
    GR_PDEGREE_NAME="${BASENAME}-pdegree.gr"
    GR_BFS_NAME="${BASENAME}-bfs.gr"
    #Create gr file from txt file
    echo "Converting original datasets to Galois format"
    $GC -edgelist2gr $DATASET $GR_NAME
    echo "Sorting by degree"
    $GC -gr2sorteddegreegr $GR_NAME $GR_DEGREE_NAME
    echo "Sorting in bfs order"
    $GC -gr2sortedbfsgr $GR_NAME $GR_BFS_NAME 
    # Galois BUG: Converting to parent's degree leads to a segfault
    #echo "Sorting by parent's degree"
    #$GC -gr2sortedparentdegreegr $GR_NAME $GR_PDEGREE_NAME
}

convert_to_random () {
    RANDOM_NAME="${BASENAME}-random.txt"
    python $ISO random $DATASET > $RANDOM_NAME
    GR_NAME="${BASENAME}-random.gr"
    $GC -edgelist2gr $RANDOM_NAME $GR_NAME
}

convert_to_isomorphisms () {
    REVDEGREE_NAME="${BASENAME}-revdegree.txt"
    GR_REVDEGREE_NAME="${BASENAME}-revdegree.gr"
    echo "Sorting by degree in descending order"
    python $ISO revdegree $DATASET > $REVDEGREE_NAME
    echo "Converting isomorphisms to Galois format"
    $GC -edgelist2gr $REVDEGREE_NAME $GR_REVDEGREE_NAME
}

remove_zeros () {
    DEGREE2_NAME="${BASENAME}-degree2.txt"
    REVDEGREE_NAME="${BASENAME}-revdegree.txt"
    SPACK_NAME="${BASENAME}-default_nz.txt"
    PACK_NAME="${BASENAME}-random_nz.txt"
    D2_SPACK_NAME="${BASENAME}-degree_nz.txt"
    RD_SPACK_NAME="${BASENAME}-revdegree_nz.txt"
    GR_SPACK_NAME="${BASENAME}-default_nz.gr"
    GR_PACK_NAME="${BASENAME}-random_nz.gr"
    GR_D2_SPACK_NAME="${BASENAME}-degree_nz.gr"
    GR_RD_SPACK_NAME="${BASENAME}-revdegree_nz.gr"
    GR_D2_NAME="${BASENAME}-degree.gr"
    echo "Converting to degree"
    $GC -edgelist2gr $DEGREE2_NAME $GR_D2_NAME
    echo "Packing graph Removing 0 edge vertices"
    python $ISO degreesort $DATASET > $DEGREE2_NAME
    python $ISO pack $DATASET > $PACK_NAME
    python $ISO spack $DATASET > $SPACK_NAME
    python $ISO spack $DEGREE2_NAME > $D2_SPACK_NAME
    python $ISO spack $REVDEGREE_NAME > $RD_SPACK_NAME
    echo "Converting isomorphisms to Galois format"
    $GC -edgelist2gr $PACK_NAME $GR_PACK_NAME
    $GC -edgelist2gr $SPACK_NAME $GR_SPACK_NAME
    $GC -edgelist2gr $D2_SPACK_NAME $GR_D2_SPACK_NAME
    $GC -edgelist2gr $RD_SPACK_NAME $GR_RD_SPACK_NAME
}

convert_to_galois_degree () {
    DEGREE2_NAME="${BASENAME}-degree2.txt"
    GR_D2_NAME="${BASENAME}-degree.gr"
    echo $DEGREE2_NAME
    echo $GR_D2_NAME
    $GC -edgelist2gr $DEGREE2_NAME $GR_D2_NAME
}

convert_weighted_graphs () {
    WEIGHT_BASENAME="${BASENAME}-default-weighted"
    for run in $(seq 1 5)
    do
        WEIGHT_NAME="${WEIGHT_BASENAME}-${run}.txt"
        GR_NAME="${WEIGHT_BASENAME}-${run}.gr"
        $GC -edgelist2gr -edgeType=int32 $WEIGHT_NAME $GR_NAME
    done
}

convert_to_galois
convert_to_random
#convert_to_isomorphisms
#remove_zeros
#convert_to_galois_degree
#convert_weighted_graphs
