import json
import re
from collections import defaultdict

def normalize(text):
    if not text: return ""
    # Remove all whitespace
    t = re.sub(r'\s+', '', text)
    # Remove $ signs
    t = t.replace('$', '')
    # Remove \displaystyle
    t = t.replace('\\displaystyle', '')
    # Lowercase
    t = t.lower()
    return t

def check_file(filename):
    with open(filename, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    seen = defaultdict(list)
    for i, q in enumerate(data['quiz']):
        norm_d = normalize(q.get('d', ''))
        seen[norm_d].append((i, q))
        
    duplicates = {k: v for k, v in seen.items() if len(v) > 1}
    print(f"--- {filename} ---")
    print(f"Total questions: {len(data['quiz'])}")
    print(f"Unique questions (normalized): {len(seen)}")
    print(f"Number of duplicate groups: {len(duplicates)}")
    
    total_dups = sum(len(v) - 1 for v in duplicates.values())
    print(f"Questions to remove: {total_dups}")
    print()

check_file('contenuti/quiz_suria.json')
check_file('contenuti/quiz_extra.json')
