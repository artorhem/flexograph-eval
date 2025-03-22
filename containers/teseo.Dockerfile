FROM ubuntu:22.04
USER root

# Install dependencies
RUN apt update && apt-get install -y \
    make g++ autotools-dev autoconf libnuma-dev libevent-dev \
    cmake git libz-dev wget unzip

WORKDIR /root

# Install PAPI
RUN wget https://icl.utk.edu/projects/papi/downloads/papi-7.2.0b1.tar.gz && \
    tar -xvzf papi-7.2.0b1.tar.gz && \
    cd papi-7.2.0b1/src && \
    ./configure && make -j && make install

# Install SQLite
RUN wget https://sqlite.org/2025/sqlite-src-3490000.zip && \
    unzip sqlite-src-3490000.zip && \
    cd sqlite-src-3490000 && \
    ./configure && make -j && make install

#add the library path to the environment variable
ENV LD_LIBRARY_PATH=/usr/local/lib

#copy teseo source code \
WORKDIR /systems
COPY systems/teseo /systems/teseo

#copy gfe_driver source code \
WORKDIR /gfe_driver
COPY gfe_driver /gfe_driver

#copy the entrypoint script and run it.
COPY teseo_entrypoint.sh /teseo_entrypoint.sh
RUN chmod +x /teseo_entrypoint.sh

CMD /teseo_entrypoint.sh && sleep infinity