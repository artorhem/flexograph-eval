FROM ubuntu:22.04 AS gapbs

LABEL project="GAPBS"
LABEL maintainer="Puneet Mehrotra"
LABEL description="Build environment for GAPBS"
USER root
SHELL [ "/bin/bash" , "-c" ]

# Install dependencies
RUN apt-get update && apt-get --no-install-recommends -y install build-essential cmake git libboost-all-dev libomp-dev wget gdb time
RUN apt-get install --reinstall -y  ca-certificates

#Environment variables
ENV CC=/usr/bin/gcc
ENV CXX=/usr/bin/g++

ADD scripts/gapbs.sh /gapbs.sh
# The volume containing the source code is mounted at /systems
WORKDIR /systems/in-mem/gapbs

# Make the project
RUN make all

CMD sleep infinity