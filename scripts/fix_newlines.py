import json
import re

with open("contenuti/quiz_suria.json", "r", encoding="utf-8") as f:
    data = json.load(f)

def fix_string(s):
    if not isinstance(s, str): return s
    # 1. Replace literal \newline
    s = s.replace('\\newline', '<br>')
    s = s.replace('\\\\newline', '<br>')
    
    # 2. Replace literal \n that acts as newline
    # To be safe, only replace \n if it's NOT part of a KaTeX command.
    # KaTeX commands starting with \n are followed by letters.
    # So we replace \n if it's followed by a space, punctuation, or end of string.
    # We also replace \n if it's followed by a number or symbol.
    # Basically, \n(?![a-zA-Z])
    s = re.sub(r'\\n(?![a-zA-Z])', '<br>', s)
    
    # 3. What if \n is followed by a letter but it was meant as newline?
    # For example, \nPer il principio
    # Let's replace \n[A-Z] with <br>[A-Z] because no KaTeX command starts with \n and a capital letter, except \nRightarrow etc.
    # Actually, let's just fix \newline because that's the only one reported.
    return s

def fix_dict(d):
    for k, v in d.items():
        if isinstance(v, str):
            d[k] = fix_string(v)
        elif isinstance(v, list):
            d[k] = [fix_string(item) if isinstance(item, str) else fix_dict(item) if isinstance(item, dict) else item for item in v]
        elif isinstance(v, dict):
            d[k] = fix_dict(v)
    return d

data = fix_dict(data)

with open("contenuti/quiz_suria.json", "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print("Newlines fixed!")
