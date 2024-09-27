#!/bin/bash

ITERATIONS=25

echo "Cit Patents"
./sssp.sh ../../datasets/cit-patents/cit-Patents stats/cit_patents/cit_patents $ITERATIONS 5795784

echo "Soc Livejournal"
./sssp.sh ../../datasets/soc-livejournal/soc-LiveJournal1 stats/soc_livejournal/soc_livejournal $ITERATIONS 10009

echo "Twitter"
./sssp.sh ../../datasets/twitter_rv/twitter_rv stats/twitter_rv/twitter_rv $ITERATIONS 19058681
