import json

with open("contenuti/quiz_suria.json", "r") as f:
    data = json.load(f)

count_no_dollar_d = 0
for q in data["quiz"]:
    if "pretest" not in q["arg"]:
        q["arg"] = "pretest"
        
    if "$" not in q["d"] and "\\(" not in q["d"] and "\\[" not in q["d"]:
        count_no_dollar_d += 1

print(f"Domande senza dollari: {count_no_dollar_d} su {len(data['quiz'])}")
