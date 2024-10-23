FROM ubuntu:22.04
LABEL project="FlexoGraph"
LABEL version="0.1.0"
LABEL maintainer="Puneet Mehrotra"
LABEL description="Build environment for FlexoGraph"
ENV HOME=/root
SHELL [ "/bin/bash" , "-c" ]

# Install dependencies
RUN apt-get update && apt-get install ca-certificates -y
RUN apt-get --no-install-recommends -y install build-essential cmake git libboost-all-dev libomp-dev wget gdb autotools-dev autoconf automake libtool 

#Environment variables
ENV CC=/usr/bin/gcc
ENV CXX=/usr/bin/g++

#Build and install FlexoGraph
# COPY . /FlexoGraph
ENV GRAPH_PROJECT_DIR="/FlexoGraph"
WORKDIR /FlexoGraph

#Release build
RUN rm -rf /FlexoGraph/build/
RUN mkdir -p build/release 
RUN cd build/release 
RUN cmake ../.. && make

# #Debug build
# RUN mkdir -p build/debug && cd build/debug && cmake -DCMAKE_BUILD_TYPE=Debug ../.. && make -j

#check if build is successful
#RUN cd build/release/test && ./test_adj_list
CMD sleep infinity
