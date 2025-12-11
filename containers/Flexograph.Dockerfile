FROM flexograph/flexograph-eval-base:latest

LABEL project="FlexoGraph"
LABEL maintainer="Puneet Mehrotra"
LABEL description="Build environment for FlexoGraph"
USER root
SHELL [ "/bin/bash" , "-c" ]

#Environment variables
ENV CC=/usr/bin/gcc
ENV CXX=/usr/bin/g++

#Build and install FlexoGraph
# COPY . /FlexoGraph
ENV GRAPH_PROJECT_DIR="/FlexoGraph"
WORKDIR /FlexoGraph

#Release build
# RUN rm -rf /FlexoGraph/build/release
# RUN mkdir -p build/release && cd build/release && cmake ../.. && make -j
# #Debug build
# RUN rm -rf /FlexoGraph/build/debug
# RUN mkdir -p build/debug && cd build/debug && cmake -DCMAKE_BUILD_TYPE=Debug ../.. && make -j

# ADD scripts/flexograph.py /flexograph.py
# RUN chmod +x /flexograph.py
# ADD datasets.json /data.json

CMD sleep infinity