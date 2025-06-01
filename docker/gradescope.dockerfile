# You can change these variables to use a different base image, but
# you must ensure that your base image inherits from one of ours.
# You can also override these at build time with --build-arg flags
ARG BASE_REPO=gradescope/autograder-base
ARG TAG=latest

FROM ${BASE_REPO}:${TAG}

ADD source/setup.sh /autograder/setup.sh
ADD ../core/source/requirements.txt /autograder/source/requirements.txt

RUN apt update && \
    sh /autograder/setup.sh \
    apt clean

ADD ../core/source /autograder/source

RUN cp /autograder/source/run_autograder /autograder/run_autograder

# Ensure that scripts are Unix-friendly and executable
RUN chmod +x /autograder/run_autograder

WORKDIR /autograder

ENTRYPOINT [ "/autograder/run_autograder" ]
