#!/bin/bash

PLANAR_DIR=/systems/ooc/Planar
FOLLY_DIR=/folly
FOLLY_BUILD_DIR=/folly_build

# Check that the pwd is /systems/ooc/plnar
if [ "$PWD" != "/systems/ooc/planar" ]; then
    cd /systems/ooc/planar
fi

echo "Building Planar"
echo "initializing submodules"
git submodule update --init --recursive
git submodule update

echo "Building yaml-cpp (required by Planar)"
#make yaml-cpp
cd $PLANAR_DIR/third_party/yaml-cpp
mkdir -p build
cd build
cmake ..
make -j


echo "Building liburing (required by Planar)"
#clone and build liburing
cd $PLANAR_DIR/third_party
git clone https://github.com/axboe/liburing.git
cd liburing
./configure && make -j && make install

echo "Building folly (required by Planar)"
#Now clone and build folly
cd / && git clone https://github.com/facebook/folly.git
cd $FOLLY_DIR
python3 ./build/fbcode_builder/getdeps.py --allow-system-packages --scratch-path=$FOLLY_BUILD_DIR build

echo "Now building Planar"
cd $PLANAR_DIR
mkdir -p build; cd build

PREFIX_PATH="$FOLLY_BUILD_DIR/installed/folly"
#Now we need to find where libfmt is installed
FMT_PATH=$(ls /folly_build/installed | grep fmt)
#append fmt to the prefix path
eval PREFIX_PATH="\"${PREFIX_PATH};${FOLLY_BUILD_DIR}/installed/${FMT_PATH}\""
cmake -DCMAKE_PREFIX_PATH=${PREFIX_PATH} ..
make -j

echo "Planar built successfully"

#Now we need to run the tests.