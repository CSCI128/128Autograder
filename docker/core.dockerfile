FROM python:3.12-alpine


RUN apk add --no-cache git && \
    apk add --no-cache bash

ADD core /tmp/core
RUN python3 -m pip install --break-system-packages '/tmp/core/'


RUN mkdir -p /autograder/bin && \
    mkdir -p /autograder/submission && \
    mkdir -p /autograder/tests && \
    mkdir -p /autograder/results

WORKDIR /autograder
