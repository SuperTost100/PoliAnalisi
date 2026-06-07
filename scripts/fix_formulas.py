import json
import re
from pathlib import Path

MATH_OPS = {"sin", "cos", "tan", "cot", "sec", "csc", "arcsin", "arccos", "arctan", "sinh", "cosh", "tanh", "log", "ln", "exp", "max", "min", "sup", "inf", "lim", "sgn", "det", "arg"}

def fix_text_in_formula(formula):
    if not formula or formula == "null":
        return formula
    if "\\text{" in formula:
        return formula

    # Replace specific whole words or phrases that are clearly text
    # Let's extract all alphabetical words
    words = re.findall(r'[a-zA-Zàèéìòù]{2,}', formula)
    text_words = [w for w in words if w.lower() not in MATH_OPS]
    
    if not text_words:
        return formula

    # If the formula is almost entirely text (e.g. > 50% words), just wrap the whole thing or specific parts?
    # Better: substitute sequences of words and spaces/punctuation
    
    # We want to match: (word or space or punctuation like comma/colon, where at least one text word is present, and NO math ops/numbers/symbols like +, -, ^, =, <, >)
    # Actually, a simpler targeted replace is safer to avoid breaking LaTeX.
    
    # Let's just wrap specific known Italian stop words and phrases, and any sequence of normal words.
    def repl(m):
        match_str = m.group(0)
        # Check if match contains only math ops
        wds = re.findall(r'[a-zA-Zàèéìòù]+', match_str)
        if all(w.lower() in MATH_OPS for w in wds):
            return match_str
        return f"\\text{{ {match_str.strip()} }} "

    # Pattern: match at least one non-math word, possibly surrounded by other words/spaces/commas.
    # We'll use a specific list of strings seen in the formulas to be 100% safe and perfect.
    
    targets = [
        r"Integrale Generale",
        r"Integrale Particolare",
        r"dove .*? iniziali",
        r"dove [a-zA-Z0-9_]+ è determinato.*",
        r"simboli che rappresentano le proposizioni",
        r"dove P e Q sono i nomi dei predicati.*",
        r"è sufficiente per",
        r"è necessario per",
        r"Equivalentemente.*equivalente a",
        r"Se ",
        r" allora ",
        r" tale che ",
        r"è strettamente monotona su",
        r"esiste un unico",
        r"continua;",
        r"Regola della Potenza:",
        r"then", # from english
        r"ha un massimo/minimo locale in",
        r"tutti i numeri che possono essere rappresentati.*",
        r"condizione necessaria, ma non sufficiente.*",
        r"Regole specifiche a seconda.*",
        r"è un limite superiore di",
        r"è un limite inferiore di",
        r"è iniettiva",
        r"è suriettiva",
        r"è un punto di max assoluto",
        r"è un punto di min assoluto",
        r"per ogni"
    ]
    
    new_form = formula
    for t in targets:
        # case insensitive replace for some
        new_form = re.sub(f"({t})", r"\\text{ \1 }", new_form, flags=re.IGNORECASE)
        
    return new_form

def process_dir(d):
    for p in Path(d).glob("*.json"):
        try:
            with open(p, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            changed = False
            # Fix concetti
            if "concetti" in data:
                for c in data["concetti"]:
                    if "formula" in c and c["formula"]:
                        orig = c["formula"]
                        fixed = fix_text_in_formula(orig)
                        if orig != fixed:
                            c["formula"] = fixed
                            changed = True
                            
            if changed:
                with open(p, 'w', encoding='utf-8') as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)
                print(f"Fixed {p.name}")
        except Exception as e:
            pass

process_dir("contenuti")
