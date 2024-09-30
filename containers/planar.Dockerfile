FROM ubuntu:22.04 AS planar

LABEL project="Planar"
LABEL maintainer="Puneet Mehrotra"
LABEL description="Build environment for Planar"
USER root
SHELL [ "/bin/bash" , "-c" ]

RUN apt-get update && apt-get --no-install-recommends -y install build-essential cmake git libboost-all-dev libomp-dev wget gdb time gnupg2 python3 vim libssl-dev
RUN apt-get install --reinstall -y  ca-certificates

ADD scripts/planar.sh /planar.sh

#move to Planar
WORKDIR /systems/ooc/Planar

CMD sleep infinity