import json
import re

def is_bad_math(s):
    if not isinstance(s, str): return False
    m = re.match(r'^\$([^\$]*)\$$', s)
    if not m: return False
    inner = m.group(1)
    clean_inner = re.sub(r'\\[a-zA-Z]+', '', inner)
    clean_words = re.findall(r'[a-zA-Z]{3,}', clean_inner)
    if len(clean_words) >= 2 and ' ' in inner:
        return True
    return False

def has_math(s):
    # Controlla se la stringa senza i $ esterni contiene matematica (comandi latex, numeri, simboli matematici complessi)
    s = s.strip('$')
    if "\\" in s or "_" in s or "^" in s or "=" in s or "f(x)" in s:
        return True
    return False

with open("contenuti/quiz_suria.json", "r") as f:
    data = json.load(f)

count_text_only = 0
count_with_math = 0

for q in data["quiz"]:
    if is_bad_math(q["d"]):
        if has_math(q["d"]): count_with_math += 1
        else: count_text_only += 1
    for o in q["opts"]:
        if is_bad_math(o):
            if has_math(o): count_with_math += 1
            else: count_text_only += 1

print(f"Testo puro: {count_text_only}, Con matematica: {count_with_math}")
