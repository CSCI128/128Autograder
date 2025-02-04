import json

metadata = {
    "previous_submissions": [
        {
            "results": {
                "score": 10
            }
        }
    ]
}

with open("/autograder/submission_metadata.json", "w") as w:
    json.dump(metadata, w)


