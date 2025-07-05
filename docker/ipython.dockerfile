FROM ghcr.io/csci128/128autograder/core

ADD languages/python /tmp/python
ADD languages/ipython /tmp/ipython

RUN pip install /tmp/python && \
    pip install /tmp/ipython
