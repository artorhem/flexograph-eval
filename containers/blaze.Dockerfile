FROM flexograph/flexograph-eval-base:latest

LABEL project="Blaze"
ARG PROJECT_HOME=/systems/ooc/blaze
ARG BLAZE_BUILD_TYPE=Release
ARG NUM_CORES=8

# Build Blaze
RUN mkdir -p ${PROJECT_HOME}
COPY systems/ooc/blaze ${PROJECT_HOME}/
WORKDIR ${PROJECT_HOME}
RUN mkdir -p build && \
    cd build && cmake -DCMAKE_BUILD_TYPE=${BLAZE_BUILD_TYPE} .. && make -j${NUM_CORES}

ADD scripts/blaze/blaze.py /blaze.py
WORKDIR /
CMD sleep infinity
