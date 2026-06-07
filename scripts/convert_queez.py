import json

with open("contenuti/queez-analisi-export.json", "r", encoding="utf-8") as f:
    data = json.load(f)

out_quiz = []
for idx, q in enumerate(data):
    question = q.get("question", "")
    options_dict = q.get("options", {})
    correct_letter = q.get("correct_answer", "")
    
    # options_dict usually has a, b, c, d, e
    keys = sorted(options_dict.keys())
    opts = []
    correct_idx = 0
    
    for i, k in enumerate(keys):
        opts.append(options_dict[k])
        if k == correct_letter:
            correct_idx = i
            
    # mapping to DATA.quiz format
    new_q = {
        "arg": "esame", # generic fallback
        "dif": "medio",
        "d": question,
        "opts": opts,
        "ok": correct_idx,
        "spieg": "Tratto dai queez extra."
    }
    out_quiz.append(new_q)

with open("contenuti/quiz_extra.json", "w", encoding="utf-8") as f:
    json.dump({"quiz": out_quiz}, f, ensure_ascii=False, indent=2)

print(f"Convertiti {len(out_quiz)} quiz.")
