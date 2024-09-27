#!/bin/bash

ITERATIONS=1

./triangle-counting.sh ../../datasets/cit-patents/cit-Patents tc_output/cp-tc $ITERATIONS 
./triangle-counting.sh ../../datasets/kron/kron tc_output/kron-tc $ITERATIONS 
./triangle-counting.sh ../../datasets/parmat/parmat tc_output/parmat-tc $ITERATIONS 
./triangle-counting.sh ../../datasets/soc-livejournal/soc-LiveJournal1 tc_output/soclj-tc $ITERATIONS 
./triangle-counting.sh ../../datasets/twitter_rv/twitter_rv tc_output/twitter-tc $ITERATIONS
