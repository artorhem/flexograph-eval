#!/bin/bash
set -e
set -x

#Accepts two arguments, the dataset directory, and the dataset name. If the dataset name is "all", it downloads all the datasets
echo $#
if [ "$#" -ne 2 ]; then
    echo "Illegal number of parameters"
    echo "Usage: ./setup.sh <absolute_path_data_directory> <dataset name or all>"
    echo "Valid dataset names: livejournal, orkut, road_usa, road_asia, dota_league, graph500_22, graph500_23, graph500_26, graph500_28, graph500_30"
    echo "Example: ./setup.sh /home/user/data livejournal"
    exit 1
fi

datasets=()
if [ "$2" == "all" ]; then
  datasets+=("livejournal" "orkut" "road_usa" "road_asia" "dota_league" "graph500_22" "graph500_23" "graph500_26" "graph500_28" "graph500_30")
else
  datasets+=($2)
fi

#download the datasets in the datasets list
for dataset in ${datasets[@]}
do
  echo "Downloading $dataset"
  mkdir -p $1/$dataset
  cd $1/$dataset
  
  if [[ $dataset = "road_asia" ]];
  then
    wget https://nrvis.com/download/data/road/road-asia-osm.zip
    unzip road-asia-osm.zip
    rm road-asia-osm.zip
    rm readme.html
    sed -i '1,147d' road-asia-osm.mtx
    # sort -n road-asia-osm.mtx > road_asia
    mv road-asia-osm.mtx road_asia
    # sed -i '1i 11950757 12711603' road_asia
  elif [[ $dataset = "road_usa" ]];
  then
    wget https://nrvis.com/download/data/road/road-road-usa.zip
    unzip road-road-usa.zip
    rm road-road-usa.zip
    rm readme.html
    sed -i '1,163d' road-road-usa.mtx
    # sort -n road-road-usa.mtx > road_usa
    mv road-road-usa.mtx road_usa
    # sed -i '1i 23947347 28854312' road_usa
  elif [[ $dataset = "orkut" ]];
  then
    wget https://snap.stanford.edu/data/bigdata/communities/com-orkut.ungraph.txt.gz
    gunzip com-orkut.ungraph.txt.gz
    mv com-orkut.ungraph.txt orkut
    sed -i '1,4d' orkut
    # sed -i '1i 3072441 117184899' orkut

  elif [[ $dataset = "livejournal" ]];
  then
    wget https://snap.stanford.edu/data/soc-LiveJournal1.txt.gz
    gunzip soc-LiveJournal1.txt.gz
    mv soc-LiveJournal1.txt ./livejournal
    sed -i '1,4d' livejournal
    sed -i 's/\t/ /g' livejournal
    #The node ID strts from 0, so we need to add 1 to each node ID
    awk '{print $1+1, $2+1}' livejournal > livejournal_temp
    # sed -i '1i 4847571 68993773' livejournal_temp
    mv livejournal_temp livejournal

  elif [[ $dataset = "dota_league" ]];
  then
    wget https://pub-383410a98aef4cb686f0c7601eddd25f.r2.dev/graphalytics/dota-league.tar.zst
    mkdir dota-league
    mv dota-league.tar.zst dota-league/dota-league.tar.zst
    cd dota-league
    tar -xf dota-league.tar.zst
    mv dota-league.e ../dota_league
    cd ..
    rm -r dota-league

  elif [[ $dataset = "graph500_22" ]];
  then
    wget https://pub-383410a98aef4cb686f0c7601eddd25f.r2.dev/graphalytics/graph500-22.tar.zst
    mkdir graph500
    mv graph500-22.tar.zst graph500/graph500-22.tar.zst
    cd graph500
    tar -xf graph500-22.tar.zst
    mv graph500-22.e ../graph500_22
    cd ..
    rm -r graph500

  elif [[ $dataset = "graph500_23" ]];
  then
    wget https://pub-383410a98aef4cb686f0c7601eddd25f.r2.dev/graphalytics/graph500-23.tar.zst
    mkdir graph500
    mv graph500-23.tar.zst graph500/graph500-23.tar.zst
    cd graph500
    tar -xf graph500-23.tar.zst
    mv graph500-23.e ../graph500_23
    cd ..
    rm -r graph500
    
  elif [[ $dataset = "graph500_26" ]];
  then
    wget https://pub-383410a98aef4cb686f0c7601eddd25f.r2.dev/graphalytics/graph500-26.tar.zst
    mkdir graph500
    mv graph500-26.tar.zst graph500/graph500-26.tar.zst
    cd graph500
    tar -xf graph500-26.tar.zst
    mv graph500-26.e ../graph500_26
    cd ..
    rm -r graph500
    
  elif [[ $dataset = "graph500_28" ]];
  then
    wget https://pub-383410a98aef4cb686f0c7601eddd25f.r2.dev/graphalytics/graph500-28.tar.zst
    mkdir graph500
    mv graph500-28.tar.zst graph500/graph500-28.tar.zst
    cd graph500
    tar -xf graph500-28.tar.zst
    mv graph500-28.e ../graph500_28
    cd ..
    rm -r graph500

  elif [[ $dataset = "graph500_30" ]];
  then
    wget https://pub-383410a98aef4cb686f0c7601eddd25f.r2.dev/graphalytics/graph500-30.tar.zst
    mkdir graph500
    mv graph500-30.tar.zst graph500/graph500-30.tar.zst
    cd graph500
    tar -xf graph500-30.tar.zst
    mv graph500-30.e ../graph500-30
    cd ..
    rm -r graph500
  fi
done
