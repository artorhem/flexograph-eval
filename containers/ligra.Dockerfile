FROM flexograph/flexograph-eval-base:latest

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

COPY scripts/ligra/ligra.py /ligra.py

# The volume containing the source code is mounted at /systems
WORKDIR /
#CMD python3 ligra.py > /results/ligra/ligra.log 2>&1
CMD sleep infinity
