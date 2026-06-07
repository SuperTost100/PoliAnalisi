import json
import re

def is_bad_math(s):
    if not isinstance(s, str): return False
    # Controlla se la stringa intera è un blocco matematico
    m = re.match(r'^\$([^\$]*)\$$', s)
    if not m: return False
    inner = m.group(1)
    # Se contiene più di 2 spazi e non ha comandi latex complessi sparsi su tutta la stringa
    # è probabile che sia una frase intera
    words = re.findall(r'[a-zA-Z]{3,}', inner)
    if len(words) >= 2 and ' ' in inner:
        # Se ha molte parole lunghe, è sicuramente testo italiano
        # Ignoriamo comandi tipici come \sin, \cos, \lim, \int, \frac
        # Rimuoviamo i comandi latex dalla conta
        clean_inner = re.sub(r'\\[a-zA-Z]+', '', inner)
        clean_words = re.findall(r'[a-zA-Z]{3,}', clean_inner)
        if len(clean_words) >= 2:
            return True
    return False

with open("contenuti/quiz_suria.json", "r") as f:
    data = json.load(f)

bad_count = 0
for q in data["quiz"]:
    if is_bad_math(q["d"]):
        print("D:", q["d"])
        bad_count += 1
    for o in q["opts"]:
        if is_bad_math(o):
            print("O:", o)
            bad_count += 1

print(f"Trovate {bad_count} stringhe sospette.")
