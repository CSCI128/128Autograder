FROM python:3.12-alpine


RUN apk add --no-cache git && \
    apk add --no-cache build-base && \
    apk add --no-cache bash

ADD . /tmp/source
RUN python3 -m pip install --break-system-packages /tmp/source


RUN mkdir -p /autograder/{bin,submission,tests}

WORKDIR /autograder
