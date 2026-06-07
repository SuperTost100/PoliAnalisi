import json

try:
    with open("contenuti/quiz_suria.json", "r") as f:
        d = json.load(f)
        print(f"Quiz Suria salvati: {len(d.get('quiz', []))}")
except Exception as e:
    print(e)
