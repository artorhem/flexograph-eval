#!/bin/bash

ITERATIONS=25

./pagerank.sh ../../datasets/cit-patents/cit-Patents stats/cit_patents/cit_patents $ITERATIONS 
./pagerank.sh ../../datasets/kron/kron stats/kron/kron $ITERATIONS 
./pagerank.sh ../../datasets/parmat/parmat stats/parmat/parmat $ITERATIONS 
./pagerank.sh ../../datasets/soc-livejournal/soc-LiveJournal1 stats/soc_livejournal/soc-livejournal $ITERATIONS 
./pagerank.sh ../../datasets/twitter_rv/twitter_rv stats/twitter_rv/twitter_rv $ITERATIONS 

