FROM flexograph/flexograph-eval-base:latest
LABEL project="Lumos"
LABEL maintainer="Puneet Mehrotra"
LABEL description="Build environment for Lumos"
USER root
SHELL [ "/bin/bash" , "-c" ]

ARG PROJECT_HOME=/systems/ooc/lumos
ARG GG_HOME=/systems/ooc/GridGraph

# RUN apt-get update && apt-get --no-install-recommends -y install build-essential cmake git libboost-all-dev libomp-dev wget gdb time gnupg2 python3 vim sysstat
# RUN apt-get install --reinstall -y  ca-certificates

#Environment variables
ENV CC=/usr/bin/gcc
ENV CXX=/usr/bin/g++

# Build Lumos
RUN mkdir -p ${PROJECT_HOME}
COPY systems/ooc/lumos ${PROJECT_HOME}/
COPY systems/ooc/GridGraph ${GG_HOME}/
# Scripts are now mounted as volumes, not copied
WORKDIR /
# CMD python3 /lumos.py --parse
CMD sleep infinity
