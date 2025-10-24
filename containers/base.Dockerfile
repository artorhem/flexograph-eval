FROM ubuntu:22.04

LABEL project="Flexograph-Eval-Base"
LABEL maintainer="Puneet Mehrotra"
LABEL description="Common base image for all graph processing systems"
USER root
SHELL [ "/bin/bash" , "-c" ]

# Update package lists and install certificates first
RUN apt-get update && apt-get install --reinstall -y ca-certificates

# Install all common build tools and libraries in a single layer to optimize image size
RUN apt-get update && apt-get install --no-install-recommends -y \
    # Build essentials
    build-essential \
    make \
    g++ \
    cmake \
    git \
    # Boost libraries
    libboost-all-dev \
    # OpenMP support
    libomp-dev \
    # Development tools
    gdb \
    wget \
    time \
    vim \
    unzip \
    # GNU tools
    gnupg \
    gnupg2 \
    autotools-dev \
    autoconf \
    automake \
    libtool \
    binutils-dev \
    # Python
    python3 \
    python3-pip \
    # System monitoring and utilities
    sysstat \
    psmisc \
    software-properties-common \
    # Google performance tools
    google-perftools \
    # System libraries
    libnuma-dev \
    libevent-dev \
    libz-dev \
    libtbb-dev \
    libdouble-conversion-dev \
    libdwarf-dev \
    libgflags-dev \
    liblz4-dev \
    liblzma-dev \
    libsnappy-dev \
    libsodium-dev \
    libunwind-dev \
    libzstd-dev \
    libssl-dev \
    zlib1g-dev \
    zstd \
    # NUMA controls 
    numactl \
    # Build system
    ninja-build \
    && rm -rf /var/lib/apt/lists/*

# Install Python packages
RUN pip3 install --no-cache-dir pandas

# Create symbolic link for tcmalloc (needed by some systems)
RUN ln -sf /usr/lib/x86_64-linux-gnu/libtcmalloc.so.4 /usr/lib/x86_64-linux-gnu/libtcmalloc.so || true

# Set default environment variables
ENV CC=/usr/bin/gcc
ENV CXX=/usr/bin/g++
ENV LD_LIBRARY_PATH=/usr/local/lib

# Set working directory
WORKDIR /root

CMD sleep infinity
