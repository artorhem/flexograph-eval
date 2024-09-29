#!/bin/bash

PLANAR_DIR=/systems/ooc/planar
FOLLY_DIR=/folly
FOLLY_BUILD_DIR=/folly_build

# Check that the pwd is /systems/ooc/plnar
if [ "$PWD" != "/systems/ooc/planar" ]; then
    cd /systems/ooc/planar
fi

git submodule update --init --recursive
git submodule update

#make yaml-cpp
cd $PLANAR_DIR/third_party/yaml-cpp
mkdir -p build
cd build
cmake ..
make -j

#clone and build liburing
cd $PLANAR_DIR/third_party
git clone https://github.com/axboe/liburing.git
cd liburing
./configure && make -j && make install

#Now clone and build folly
cd / && git clone https://github.com/facebook/folly.git
cd $FOLLY_DIR
python3 ./build/fbcode_builder/getdeps.py --allow-system-packages --scratch-path=$FOLLY_BUILD_DIR build