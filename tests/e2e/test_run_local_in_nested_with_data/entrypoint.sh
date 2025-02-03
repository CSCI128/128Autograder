#!/bin/sh

# build autograder

build_autograder -o /autograder/bin

# go to student directory
cd /autograder/bin/ || exit


# run the boi in a more realistic way
# we are just overriding the submission directory to point to the already correct submission
test_my_work --submission-directory /app/submission > /autograder/results/output.txt
