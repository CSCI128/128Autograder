#!/bin/sh

# build autograder

build_autograder -o /autograder/bin || exit 1

# go to student directory
cd /autograder/bin/generation/prairielearn || exit 1

mkdir -p /grade/tests

cp -r /autograder/bin/generation/prairielearn/tests /grade/

cd /grade || exit 1

/grade/tests/run_autograder || exit 1