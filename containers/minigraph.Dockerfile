FROM ubuntu:22.04 AS minigraph

LABEL project="Planar"
LABEL maintainer="Puneet Mehrotra"
LABEL description="Build environment for MiniGraph"
USER root
SHELL [ "/bin/bash" , "-c" ]

RUN apt-get update && apt-get --no-install-recommends -y install build-essential cmake git libboost-all-dev \
    libomp-dev wget gdb time gnupg2 python3 unzip
RUN apt-get install --reinstall -y  ca-certificates
RUN apt install -y autoconf automake binutils-dev cmake libboost-all-dev libdouble-conversion-dev libdwarf-dev \
    libevent-dev libgflags-dev liblz4-dev liblzma-dev libsnappy-dev libsodium-dev libtool \
    libunwind-dev libzstd-dev ninja-build zlib1g-dev zstd libssl-dev

#install fmtlib
WORKDIR /root
RUN wget https://github.com/fmtlib/fmt/archive/refs/tags/11.1.3.zip && \
    unzip 11.1.3.zip && cd fmt-11.1.3 && \
    mkdir build && cd build && cmake .. && make -j && make install

#install gflags
WORKDIR /root
RUN git clone https://github.com/gflags/gflags && cd gflags && mkdir build && \
    cd build && cmake -DBUILD_SHARED_LIBS=ON .. && make -j && make install

#install glog
WORKDIR /root
RUN git clone https://github.com/google/glog.git && cd glog && \
    cmake -S . -B build -G "Unix Makefiles" && cmake --build build && cmake --build build --target install

#install folly
WORKDIR /root
RUN git clone https://github.com/facebook/folly && cd folly && mkdir target && \
    python3 ./build/fbcode_builder/getdeps.py --allow-system-packages build --install-prefix=/usr/local

#install jemalloc
WORKDIR /root
RUN wget https://github.com/jemalloc/jemalloc/archive/refs/tags/5.3.0.tar.gz && \
    tar -xvf 5.3.0.tar.gz && cd jemalloc-5.3.0 && ./autogen.sh && ./configure && make -j && make install

CMD sleep infinity
