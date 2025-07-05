FROM ghcr.io/csci128/128autograder/core

ADD languages/python /tmp/python

RUN pip install /tmp/python
