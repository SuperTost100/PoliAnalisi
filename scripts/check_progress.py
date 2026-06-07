import json
with open("contenuti/quiz_suria.json", "r") as f:
    data = json.load(f)

missing = 0
for q in data["quiz"]:
    s = q["d"]
    if "$" not in s and ("\\" in s or "=" in s or "^" in s or "_" in s or "f(x)" in s):
        missing += 1

print(f"Mancano {missing} domande da formattare.")
