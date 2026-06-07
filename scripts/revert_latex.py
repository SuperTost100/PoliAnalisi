import json
import re

with open("contenuti/quiz_suria.json", "r") as f:
    data = json.load(f)

for q in data["quiz"]:
    # Ripristiniamo opts
    new_opts = []
    for o in q["opts"]:
        if o.startswith("$ ") and o.endswith(" $"):
            # Era stato wrappato da fix_opts
            new_opts.append(o[2:-2])
        else:
            new_opts.append(o)
    q["opts"] = new_opts
    
    # Ripristiniamo d
    d = q["d"]
    if d.startswith("$ ") and d.endswith(" $"):
        # Era stato modificato
        inner = d[2:-2]
        # Ripristiniamo i \text{...}
        inner = re.sub(r'\\text\{([^\}]+)\}', r'\1', inner)
        q["d"] = inner

with open("contenuti/quiz_suria.json", "w") as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print("Revert completato.")
