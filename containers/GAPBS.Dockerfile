#FROM ubuntu:22.04 AS gapbs
FROM flexograph/flexograph-eval-base:latest

LABEL project="GAPBS"
LABEL maintainer="Puneet Mehrotra"
LABEL description="Build environment for GAPBS"
USER root
SHELL [ "/bin/bash" , "-c" ]

# Install dependencies
#RUN apt-get update && apt-get --no-install-recommends -y install build-essential cmake git libboost-all-dev libomp-dev wget gdb time python3
#RUN apt-get install --reinstall -y  ca-certificates

#Environment variables
ENV CC=/usr/bin/gcc
ENV CXX=/usr/bin/g++

# Copy the source code
COPY systems/in-mem/gapbs /gapbs
WORKDIR /gapbs
RUN cd /gapbs && make clean && make -j

COPY scripts/gapbs/gapbs.py /gapbs

#CMD sleep infinity
CMD ["python3", "gapbs.py"]
