#/bin/bash
#set -e
#set -x

#the frst argument is the data directory where we download all the datasets, the second argument is the results directory where we store the results
if [ "$#" -ne 2 ]; then
    echo "Illegal number of parameters"
    echo "Usage: ./setup.sh <absolute_path_data_directory> <absolute_path_results_directory>"
    exit 1
fi
results=$3
datasets=$2
#make the directories
mkdir -p $datasets
mkdir -p $results

#run the get-systems script
./get-systems.sh



#download the datasets
./dataset.sh $datasets
