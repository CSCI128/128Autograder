import json
import os

assert os.path.exists("results/output.txt")


with open("results/output.txt", "r") as r:
    student_results = r.readlines()

# simply make sure that we had no errors or failures reported
for line in student_results:
    if "[" not in line:
        continue
    assert "error" not in line.lower()
    assert "fail" not in line.lower()
