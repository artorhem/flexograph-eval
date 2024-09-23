set -x
#Compile the convertor utils
cd /systems/in-mem/ligra/utils
make -j

# Compile the Ligra applications
cd /systems/in-mem/ligra/apps
make -e OPENMP=1 -j all

datasets=(
  "graph500_23"
  "graph500_26"
  "graph500_28"
  "graph500_30"
  "dota_league"
  "livejournal"
  "orkut"
  "road_asia"
  "road_usa"
)

cd /systems/in-mem/ligra/apps

benchmarks=(
  "BFS"
  "Components"
  "PageRank"
  "Triangle"
)

for dataset in "${datasets[@]}"
do
  #measure the time to convert the dataset to adj format and save in a variable
  COMMAND="/systems/in-mem/ligra/utils/SNAPtoAdj /datasets/${dataset}/${dataset} ${dataset}"
  TIME_OUTPUT=$(/usr/bin/time -p $COMMAND 2>&1)
  TIME_TAKEN=$(echo "$TIME_OUTPUT" | grep real | awk '{print $2}')
  
  echo "Time to convert $dataset to adj: $time"
  for benchmark in "${benchmarks[@]}"
  do
    echo "Time to convert $dataset to adj: $TIME_TAKEN seconds" > /results/ligra/${dataset}_${benchmark}.txt
    echo "Running $benchmark on $dataset"
        ./${benchmark} -rounds 5 ${dataset} >> /results/ligra/${dataset}_${benchmark}.txt
  done
  rm ${dataset}
done
