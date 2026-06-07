import json

def fix_string(s):
    if not isinstance(s, str):
        return s
    return s.replace('\x0c', '\\f').replace('\x09', '\\t').replace('\x08', '\\b').replace('\x0d', '\\r')

def fix_dict(d):
    for k, v in d.items():
        if isinstance(v, str):
            d[k] = fix_string(v)
        elif isinstance(v, list):
            d[k] = [fix_string(item) if isinstance(item, str) else fix_dict(item) if isinstance(item, dict) else item for item in v]
        elif isinstance(v, dict):
            d[k] = fix_dict(v)
    return d

with open("contenuti/quiz_suria.json", "r", encoding="utf-8") as f:
    data = json.load(f)

data = fix_dict(data)

with open("contenuti/quiz_suria.json", "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print("Fixed!")
