#/bin/bash
#set -e
#set -x 
# This script clones the systems that are used in the evaluation

# The systems are cloned into systems directory
# First add the in-mem systems
mkdir -p systems/in-mem
cd systems/in-mem

#Now clone the systems
git clone git@github.com:artorhem/Galois.git #Galois
git clone git@github.com:artorhem/gapbs.git #GAPBS
git clone git@github.com:artorhem/ligra.git #Ligra
git clone git@github.com:artorhem/GeminiGraph.git #GeminiGraph
git clone git@github.com:artorhem/graphit.git #GraphIt

# Now add the out-of-core systems
cd ../../
mkdir -p systems/ooc
cd systems/ooc

#Now clone the systems
git clone git@github.com:artorhem/blaze.git #Blaze
git clone git@github.com:artorhem/graphchi-cpp.git #GraphChi
git clone git@github.com:artorhem/lumos.git #Lumos

#Clone X-Stream and checkout their sosp branch
git clone git@github.com:artorhem/x-stream.git 
cd x-stream
git checkout sosp