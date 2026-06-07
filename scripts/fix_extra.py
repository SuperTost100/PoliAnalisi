import json
with open("contenuti/quiz_extra.json") as f:
    data = json.load(f)
print(len(data.get("quiz", [])))
