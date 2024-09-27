#!/bin/bash

ITERATIONS=25

echo "Cit_patents"
./connected-components.sh ../../datasets/cit-patents/cit-Patents stats/cit_patents/cit_patents $ITERATIONS 
echo "Kron"
./connected-components.sh ../../datasets/kron/kron stats/kron/kron $ITERATIONS 
echo "Parmat"
./connected-components.sh ../../datasets/parmat/parmat stats/parmat/parmat $ITERATIONS 
echo "Soc_livejournal"
./connected-components.sh ../../datasets/soc-livejournal/soc-LiveJournal1 stats/soc_livejournal/soc-livejournal $ITERATIONS 
echo "Twitter"
./connected-components.sh ../../datasets/twitter_rv/twitter_rv stats/twitter_rv/twitter_rv $ITERATIONS 
