FROM flexograph/flexograph-eval-base:latest
USER root

# RUN apt update && apt-get install -y make && apt-get install -y g++
# RUN apt update && \
#     apt-get install -y autotools-dev autoconf libnuma-dev libevent-dev cmake git libz-dev wget unzip

WORKDIR /root
RUN wget https://icl.utk.edu/projects/papi/downloads/papi-7.2.0b1.tar.gz  && tar -xvzf papi-7.2.0b1.tar.gz
WORKDIR /root/papi-7.2.0b1/src
RUN ./configure && make -j && make install

WORKDIR /root
RUN wget https://sqlite.org/2025/sqlite-src-3490000.zip && unzip sqlite-src-3490000.zip
WORKDIR /root/sqlite-src-3490000
RUN ./configure && make -j && make install

#add the library path to the environment variable
ENV LD_LIBRARY_PATH=/usr/local/lib

#install TBB
WORKDIR /root
# RUN apt update && apt install -y libtbb-dev

#now copy LiveGraph and GFE driver
COPY systems/livegraph /systems/livegraph
COPY gfe_driver /gfe_driver

#copy the entrypoint script and run it
COPY livegraph_entrypoint.sh /livegraph_entrypoint.sh
RUN chmod +x /livegraph_entrypoint.sh

CMD /livegraph_entrypoint.sh && sleep infinity