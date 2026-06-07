import json
import re

def is_math_opt(opt):
    # If it already has delimiters, leave it alone
    if "$" in opt or "\\(" in opt or "\\[" in opt:
        return False
        
    # Parole che indicano un'opzione di testo puro o misto,
    # che non vogliamo wrappare interamente in dollari.
    ita_words = [
        "nessuna", "delle", "altre", "risposte", "tutte", "precedenti",
        "vero", "falso", "esiste", "non", "solo", "funzione", "sempre",
        "mai", "nessun", "valore", "se", "allora", "per"
    ]
    
    # Estraiamo le parole lunghe almeno 3 caratteri per evitare variabili (x, y, a, b)
    words = [w.lower() for w in re.findall(r'\b[a-zA-Z]{3,}\b', opt)]
    
    # Conta quante parole italiane "comuni" ci sono
    ita_count = sum(1 for w in words if w in ita_words)
    
    # Se ha parole italiane, probabile testo
    if ita_count > 0:
        return False
        
    # Se è composto per lo più da testo (più di 2 parole lunghe), skip
    if len(words) > 2:
        return False
        
    return True

with open("contenuti/quiz_suria.json", "r") as f:
    data = json.load(f)

count_opts_fixed = 0

for q in data["quiz"]:
    new_opts = []
    for o in q["opts"]:
        if is_math_opt(o):
            new_opts.append(f"$ {o} $")
            count_opts_fixed += 1
        else:
            new_opts.append(o)
    q["opts"] = new_opts

with open("contenuti/quiz_suria.json", "w") as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print(f"Completato! Opzioni fixate in automatico: {count_opts_fixed}")
