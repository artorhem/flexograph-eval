#/bin/bash
#set -e
#set -x 
# This script clones the systems that are used in the evaluation

# The systems are cloned into systems directory
# First add the in-mem systems
mkdir -p systems/in-mem
cd systems/in-mem

#Now clone the systems
systems=( "galois" "gapbs" "ligra" "gemini" "graphit" )
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

#Clone X-Stream and checkout their sosp branch
if [ -d "x-stream" ]; then
  echo "X-Stream already cloned"
else
  git clone git@github.com:artorhem/x-stream.git 
fi
cd x-stream
git checkout sosp

# Clone FlexoGraph and checkout the iter_fix branch
mkdir -p systems/FlexoGraph
git clone git@github.com:ubc-systopia/margraphita.git systems/FlexoGraph/
cd systems/FlexoGraph
git fetch && git checkout iter_fix
