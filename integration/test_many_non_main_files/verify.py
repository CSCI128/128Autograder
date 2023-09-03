import json
import os

assert os.path.exists("results/results.json")

with open("results/results.json") as r:
    results = json.load(r)

testResult = results['tests'][0]

assert results['score'] == 0

files = os.listdir('./submission')
files.sort()

assert "Validation Error" in testResult["output"]
assert str(files) in testResult["output"]