FROM flexograph/flexograph-eval-base:latest
LABEL project="Gemini"
LABEL maintainer="Puneet Mehrotra"
LABEL description="Build environment for Gemini"
USER root
SHELL [ "/bin/bash" , "-c" ]

# RUN apt-get update && apt-get --no-install-recommends -y install build-essential cmake git libboost-all-dev libomp-dev wget gdb time gnupg2 python3 vim
# RUN apt-get install --reinstall -y  ca-certificates

#Environment variables
ENV CC=/usr/bin/gcc
ENV CXX=/usr/bin/g++

ADD scripts/gemini/gemini.py /gemini.py
ADD scripts/dataset_properties.py /dataset_properties.py
WORKDIR /
# CMD python3 /gemini.py --parse
CMD sleep infinity
