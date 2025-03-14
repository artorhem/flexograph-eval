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
ENV GRAPH_PROJECT_DIR="/systems/FlexoGraph"
WORKDIR /

ADD scripts/flexograph.py /flexograph.py
RUN chmod +x /flexograph.py
ADD datasets.json /data.json

CMD sleep infinity
