import json

with open("contenuti/quiz_suria.json", "r") as f:
    data = json.load(f)

for i in range(10):
    print(data["quiz"][i]["d"])
