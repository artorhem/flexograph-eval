FROM ubuntu:22.04

ARG PROJECT_HOME=/systems/ooc/x-stream
ARG DATASET_HOME=/datasets


RUN apt-get update && apt-get install ca-certificates -y
RUN apt-get --no-install-recommends -y install build-essential cmake git libboost-all-dev \
    libomp-dev wget gdb automake libtool time gnupg2 python3 vim sysstat

# Copy the source code
COPY systems/ooc/x-stream /xstream
WORKDIR /xstream
ENV LD_RUN_PATH="$LD_RUN_PATH:/usr/lib/x86_64-linux-gnu/"
RUN make clean && make -j && make install

# Clone LLAMA
WORKDIR /
RUN git clone https://github.com/artorhem/llama.git /llama && \
    cd llama && git checkout puneet_local && \
    make -j

ADD scripts/xstream/xstream.py /xstream.py
CMD sleep infinity
