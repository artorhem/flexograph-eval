FROM flexograph/flexograph-eval-base:latest

LABEL project="GAPBS"
LABEL maintainer="Puneet Mehrotra"
LABEL description="Build environment for GAPBS"
USER root
SHELL [ "/bin/bash" , "-c" ]

#Environment variables
ENV CC=/usr/bin/gcc
ENV CXX=/usr/bin/g++

# Copy the source code
COPY systems/in-mem/gapbs /gapbs
WORKDIR /gapbs
RUN cd /gapbs && make clean && make -j

COPY scripts/dataset_properties.py /gapbs
COPY scripts/gapbs/gapbs.py /gapbs

CMD sleep infinity
# CMD ["python3", "gapbs.py"]