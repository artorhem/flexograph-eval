FROM ubuntu:22.04 AS lumos
LABEL project="Lumos"
LABEL maintainer="Puneet Mehrotra"
LABEL description="Build environment for Lumos"
USER root
SHELL [ "/bin/bash" , "-c" ]

ARG PROJECT_HOME=/systems/ooc/lumos

RUN apt-get update && apt-get --no-install-recommends -y install build-essential cmake git libboost-all-dev libomp-dev wget gdb time gnupg2 python3 vim
RUN apt-get install --reinstall -y  ca-certificates

#Environment variables
ENV CC=/usr/bin/gcc
ENV CXX=/usr/bin/g++

# Build Lumos
RUN mkdir -p ${PROJECT_HOME}
COPY systems/ooc/lumos ${PROJECT_HOME}/

ADD scripts/lumos/lumos.py /lumos.py
WORKDIR /
CMD python3 /lumos.py --parse
CMD sleep infinity
