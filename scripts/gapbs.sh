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

benchmarks=(
  "bfs"
  "cc"
  "pr"
  "sssp"
)

for dataset in "${datasets[@]}"
do
  cp /datasets/${dataset}/${dataset} ./${dataset}.el
  for benchmark in "${benchmarks[@]}"
  do
    echo "Running $benchmark on $dataset"
        ./${benchmark} -f ${dataset}.el -n 5 -l > /results/gapbs/${dataset}_${benchmark}.txt
  done
  rm ${dataset}.el
done