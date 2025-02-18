#/bin/bash
#set -e
#set -x 
# This script clones the systems that are used in the evaluation

# The systems are cloned into systems directory
# First add the in-mem systems
SYS_DIR=`pwd`
mkdir -p systems/in-mem
cd systems/in-mem

#Now clone the systems
systems=( "Galois" "gapbs" "ligra" "GeminiGraph" "graphit" )
for system in "${systems[@]}"
do
    if [ -d "$system" ]; then
        echo "$system exists"
    else
        git clone git@github.com:artorhem/$system.git
    fi
done

# Now add the out-of-core systems
cd ../../
mkdir -p systems/ooc
cd systems/ooc

#Now clone the systems
systems=("blaze" "graphchi-cpp" "lumos" )
for system in "${systems[@]}"
do
    if [ -d "$system" ]; then
        echo "$system exists"
    else
        git clone git@github.com:artorhem/$system.git
    fi
done

#git clone git@github.com:SICS-Fundamental-Research-Center/Planar.git #Planar, VLDB2024
git clone git@github.com:SICS-Fundamental-Research-Center/MiniGraph.git #MiniGraph, VLDB 2023

#Clone X-Stream and checkout their sosp branch
if [ -d "x-stream" ]; then
  echo "X-Stream already cloned"
else
  git clone git@github.com:artorhem/x-stream.git 
fi
cd x-stream
git checkout sosp

# Clone FlexoGraph and checkout the iter_fix branch
cd $SYS_DIR
mkdir -p systems/FlexoGraph
git clone git@github.com:ubc-systopia/margraphita.git systems/FlexoGraph/
cd systems/FlexoGraph
git fetch && git checkout iter_fix
