FROM ubuntu:22.04

ARG PROJECT_HOME=/systems/ooc/x-stream
ARG DATASET_HOME=/datasets


RUN apt-get update && apt-get install ca-certificates -y
RUN apt-get --no-install-recommends -y install build-essential cmake git libboost-all-dev \
    libomp-dev wget gdb automake libtool time gnupg2 python3 vim

# Copy the source code
COPY systems/ooc/x-stream /xstream
WORKDIR /xstream
ENV LD_RUN_PATH="$LD_RUN_PATH:/usr/lib/x86_64-linux-gnu/"

ADD scripts/xstream/xstream.py /xstream.py
WORKDIR /
CMD sleep infinity