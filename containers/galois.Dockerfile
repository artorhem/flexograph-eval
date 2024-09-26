FROM ubuntu:22.04 AS galois

LABEL project="Galois"
LABEL maintainer="Puneet Mehrotra"
LABEL description="Build environment for Galois"
USER root
SHELL [ "/bin/bash" , "-c" ]

RUN apt-get update && apt-get --no-install-recommends -y install build-essential cmake git libboost-all-dev libomp-dev wget gdb time gnupg2 python3 vim
RUN apt-get install --reinstall -y  ca-certificates

# #add llvm sources
RUN wget --no-check-certificate -O - https://apt.llvm.org/llvm-snapshot.gpg.key | apt-key add -
RUN echo "deb http://apt.llvm.org/jammy/ llvm-toolchain-jammy main" >> /etc/apt/sources.list
RUN echo "deb-src http://apt.llvm.org/jammy/ llvm-toolchain-jammy main" >> /etc/apt/sources.list

RUN apt-get update
RUN apt-get install libllvm20 llvm-20 llvm-20-dev llvm-20-runtime -y

#Environment variables
ENV CC=/usr/bin/gcc
ENV CXX=/usr/bin/g++

ADD scripts/galois.sh /galois.sh
ADD scripts/galois/bfs.sh /bfs.sh
ADD scripts/galois/sssp.sh /sssp.sh
RUN chmod +x /galois.sh
ADD scripts/graph_utils.py /graph_utils.py

# The volume containing the source code is mounted at /systems
WORKDIR /systems/in-mem/Galois
CMD sleep infinity