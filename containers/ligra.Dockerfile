FROM ubuntu:22.04 AS ligra

LABEL project="Ligra"
LABEL maintainer="Puneet Mehrotra"
LABEL description="Build environment for Ligra"
USER root
SHELL [ "/bin/bash" , "-c" ]

RUN apt-get update && apt-get --no-install-recommends -y install build-essential cmake git libboost-all-dev libomp-dev wget gdb time
RUN apt-get install --reinstall -y  ca-certificates

#Environment variables
ENV CC=/usr/bin/gcc
ENV CXX=/usr/bin/g++

ADD scripts/ligra.sh /ligra.sh

# The volume containing the source code is mounted at /systems
WORKDIR /systems/in-mem/ligra/apps

CMD bash /ligra.sh > /results/ligra/ligra.log 2>&1