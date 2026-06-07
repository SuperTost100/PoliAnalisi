import json
import re

def fix_spaces(s):
    if not isinstance(s, str): return s
    # Rimuove spazi vuoti immediatamente all'interno dei dollari: $ f(x) $ -> $f(x)$
    return re.sub(r'\$\s*([^\$]*?)\s*\$', r'$\1$', s)

for filename in ["contenuti/quiz_suria.json", "contenuti/quiz_extra.json"]:
    try:
        with open(filename, "r") as f:
            data = json.load(f)
            
        count = 0
        for q in data.get("quiz", []):
            old_d = q["d"]
            q["d"] = fix_spaces(q["d"])
            if old_d != q["d"]: count += 1
            
            for i in range(len(q["opts"])):
                old_o = q["opts"][i]
                q["opts"][i] = fix_spaces(q["opts"][i])
                if old_o != q["opts"][i]: count += 1
                
        with open(filename, "w") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
            
        print(f"{filename}: fixati {count} elementi.")
    except Exception as e:
        print(f"Errore su {filename}: {e}")
