import json
with open("contenuti/quiz_suria.json") as f:
    data = json.load(f)
fixed = sum(1 for q in data["quiz"] if q.get("gemma_fixed"))
print(f"Fixed: {fixed} / {len(data['quiz'])}")
