FROM flexograph/flexograph-eval-base:latest

ARG PROJECT_HOME=/systems/ooc/graphchi
ARG DATASET_HOME=/datasets

# RUN apt-get update && apt-get install ca-certificates -y
# RUN apt-get --no-install-recommends -y install build-essential cmake git libboost-all-dev \
#     libomp-dev wget gdb automake libtool time gnupg2 python3 vim sysstat

ADD scripts/graphchi/graphchi.py /graphchi.py
WORKDIR /
CMD sleep infinity
