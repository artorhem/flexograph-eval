FROM ubuntu:22.04 AS galois

LABEL project="Galois"
LABEL maintainer="Puneet Mehrotra"
LABEL description="Build environment for Galois"
USER root
SHELL [ "/bin/bash" , "-c" ]

RUN apt-get update && apt-get --no-install-recommends -y install build-essential cmake git libboost-all-dev libomp-dev wget gdb time gnupg2 python3 vim software-properties-common
RUN apt-get install --reinstall -y  ca-certificates

# #add llvm sources
RUN wget -O - https://apt.llvm.org/llvm-snapshot.gpg.key| apt-key add -
RUN echo "deb http://apt.llvm.org/jammy/ llvm-toolchain-jammy-15 main restricted" >> /etc/apt/sources.list
RUN apt-get update && apt-get install -y llvm-15 llvm-15-dev llvm-15-runtime

#Environment variables
ENV CC=/usr/bin/gcc
ENV CXX=/usr/bin/g++
#
ADD scripts/galois/galois.py /galois.py

#CMD python3 /galois.py
CMD sleep infinity