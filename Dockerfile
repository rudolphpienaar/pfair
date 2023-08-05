#
# Dockerfile for pfair.
#
# Build with
#
#   docker build -t <name> .
#
# For example if building a local version, you could do:
#
#   docker build --build-arg UID=$UID -t local/pfair .
#
# In the case of a proxy (located at say 10.41.13.4:3128), do:
#
#    export PROXY="http://10.41.13.4:3128"
#    docker build --build-arg http_proxy=$PROXY --build-arg UID=$UID -t local/pfair .
#
# To run an interactive shell inside this container, do:
#
#   docker run -ti --entrypoint /bin/bash local/pfair
#
# To pass an env var HOST_IP to the container, do:
#
#   docker run -ti -e HOST_IP=$(ip route | grep -v docker | awk '{if(NF==11) print $9}') --entrypoint /bin/bash local/pfair
#
FROM docker.io/python:3.11.0-slim-bullseye

LABEL DEVELOPMENT="                                                        \
    docker run --rm -it                                                    \
    -p 55553:55553 \
    -v $PWD/pfair:/app:ro  local/pfair /start-reload.sh                    \
"

WORKDIR /pfair

ENV DEBIAN_FRONTEND=noninteractive


COPY requirements.txt $WORKDIR/requirements.txt
RUN pip install --upgrade pip
RUN pip install --no-cache-dir --upgrade -r /$WORKDIR/requirements.txt
RUN pip install tzlocal
RUN pip install ipython
COPY ./pfair $WORKDIR

RUN apt update                              && \
    apt-get install -y apt-transport-https  && \
    apt -y install vim telnet netcat procps

ENV PORT=55553
EXPOSE ${PORT}

CMD [ "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "55553" ]