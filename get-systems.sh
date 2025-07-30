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
systems=( "Galois" "gapbs" "ligra" "GeminiGraph" )
for system in "${systems[@]}"
do
    if [ -d "$system" ]; then
        echo "$system exists"
    else
        git clone https://github.com/artorhem/$system.git
    fi
done

# Now add the out-of-core systems
cd ../../
mkdir -p systems/ooc
cd systems/ooc

#Now clone the systems
systems=("blaze" "graphchi-cpp" "lumos" "MiniGraph" "Graphene")
for system in "${systems[@]}"
do
    if [ -d "$system" ]; then
        echo "$system exists"
    else
        git clone https://github.com/artorhem/$system.git
    fi
done

#Clone X-Stream and checkout their sosp branch
if [ -d "x-stream" ]; then
  echo "X-Stream already cloned"
else
  git clone https://github.com/artorhem/x-stream.git
fi
cd x-stream
git checkout sosp

# Clone FlexoGraph and checkout the iter_fix branch
cd $SYS_DIR
mkdir -p systems/FlexoGraph
git clone https://github.com/artorhem/margraphita.git systems/FlexoGraph/
cd systems/FlexoGraph
git fetch && git checkout iter_fix


#CLone the gfe-driver for dynamic systems
cd $SYS_DIR
mkdir -p systems/gfe-driver
