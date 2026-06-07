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

for filename in ["contenuti/quiz_suria.json", "contenuti/quiz_extra.json"]:
    with open(filename, "r") as f:
        data = json.load(f)

    count = 0
    for q in data.get("quiz", []):
        if is_bad_math(q["d"]):
            q["d"] = q["d"][1:-1]  # strip outer $
            count += 1
        for i in range(len(q["opts"])):
            if is_bad_math(q["opts"][i]):
                q["opts"][i] = q["opts"][i][1:-1]
                count += 1

    with open(filename, "w") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"{filename}: Spazi ripristinati su {count} stringhe.")
