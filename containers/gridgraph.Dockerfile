FROM ubuntu:22.04 AS gridgraph
LABEL project="GridGraph"
LABEL maintainer="Puneet Mehrotra"
LABEL description="Build environment for GridGraph"
USER root
SHELL [ "/bin/bash" , "-c" ]

ARG PROJECT_HOME=/systems/ooc/GridGraph

RUN apt-get update && apt-get --no-install-recommends -y install build-essential cmake git libboost-all-dev libomp-dev wget gdb time gnupg2 python3 vim sysstat
RUN apt-get install --reinstall -y  ca-certificates

#Environment variables
ENV CC=/usr/bin/gcc
ENV CXX=/usr/bin/g++

# Build GridGraph
RUN mkdir -p ${PROJECT_HOME}
COPY systems/ooc/GridGraph ${PROJECT_HOME}/
ADD scripts/gridgraph/gridgraph.py /gridgraph.py
WORKDIR /
CMD python3 /gridgraph.py --parse
CMD sleep infinity
