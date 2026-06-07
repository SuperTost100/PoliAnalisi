import json
import re

def fix_string(s):
    if not isinstance(s, str): return s
    if "$" in s or "\\(" in s or "\\[" in s:
        return s

    # Se la stringa è vuota
    if not s.strip(): return s

    # Heuristic per determinare se è per la maggior parte matematica
    # Se contiene pochi caratteri alfabetici normali o molti operatori
    letters = len(re.findall(r'[a-zA-Z]', s))
    math_chars = len(re.findall(r'[=+\-*/\^_\\{}\[\]\(\)0-9]', s))
    
    # Lista di parole italiane comuni
    ita_words = ["quale", "della", "funzione", "parte", "principale", "se", "allora", "sicuramente", "nessuna", "delle", "altre", "risposte", "soluzione", "equazione", "differenziale", "vero", "falso", "derivata", "integrale", "insieme", "dato", "data", "tale", "che", "numero", "complesso"]
    
    words_in_s = [w.lower() for w in re.findall(r'\b[a-zA-Z]{2,}\b', s)]
    has_ita = any(w in ita_words for w in words_in_s)
    
    if not has_ita and (math_chars > letters / 2 or "\\" in s):
        # Quasi sicuramente è solo matematica
        return f"$ {s} $"
        
    # Altrimenti cerchiamo di wrappare le cose che sembrano math
    # Ad esempio, tutto ciò che inizia per f(x), \lim, \int, \frac, ecc e finisce con qualcosa
    # E' rischioso. Invece proviamo a wrappare pezzi specifici?
    # Un approccio ingenuo: se ha testo, usa regex per isolare la math?
    # Spesso la math è della forma: f(x) = ... o \lim ... o w = ...
    
    # Molto più semplice: usiamo un trucco. Sostituiamo i comandi noti
    # e avvolgiamo la stringa se non è possibile, o facciamo un rimpiazzo manuale mirato.
    
    # Rimpiazzo molto semplice per i quiz:
    # Cerchiamo blocchi di testo che assomigliano a formule
    
    # Per ora wrappiamo tutto ciò che contiene "\\" o "=", ma in \text{} per le parole
    pass

    return s

def fix_opts(opts):
    new_opts = []
    for o in opts:
        if "$" in o or "\\(" in o or "\\[" in o:
            new_opts.append(o)
            continue
            
        ita_words = ["nessuna", "delle", "altre", "risposte", "tutte", "le", "precedenti", "vero", "falso", "esiste", "non", "solo"]
        words_in_o = [w.lower() for w in re.findall(r'\b[a-zA-Z]{3,}\b', o)]
        has_ita = any(w in ita_words for w in words_in_o)
        
        if not has_ita:
            new_opts.append(f"$ {o} $")
        else:
            new_opts.append(o)
            
    return new_opts

with open("contenuti/quiz_suria.json", "r") as f:
    data = json.load(f)

for q in data["quiz"]:
    # 1. Cambia arg
    if q["arg"] == "esame":
        q["arg"] = "pretest"
        
    # 2. Fix opts
    q["opts"] = fix_opts(q["opts"])
    
    # 3. Fix d
    s = q["d"]
    if "$" not in s and "\\(" not in s and "\\[" not in s:
        # Se c'è \int, \lim, \frac, \sum, \sqrt, \mathbb, \left, \right
        # proviamo a delimitare l'intera stringa in modo smart
        if "\\" in s or "^" in s or "_" in s or "f(x)" in s:
            # Dividiamo la stringa in parole e math in base a una regex? No.
            # Convertiamo l'intera stringa in LaTeX math, ma proteggiamo il testo con \text{}
            # Regex per trovare parole italiane
            s_new = re.sub(r'([a-zA-Zàèéìòù\'’]{2,})', r'\\text{\1}', s)
            # Rimuoviamo \text{} attorno a funzioni note
            for fn in ["sin", "cos", "tan", "log", "ln", "sinh", "cosh", "lim", "int", "frac", "sqrt", "cdot", "cup", "cap", "setminus"]:
                s_new = s_new.replace(f"\\text{{{fn}}}", fn)
            q["d"] = f"$ {s_new} $"

with open("contenuti/quiz_suria.json", "w") as f:
    json.dump(data, f, ensure_ascii=False, indent=2)
    
print("Fix completato.")
