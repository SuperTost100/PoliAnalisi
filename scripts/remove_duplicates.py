import json
import re
from collections import defaultdict

def normalize(text):
    if not text: return ""
    t = re.sub(r'\s+', '', text)
    t = t.replace('$', '')
    t = t.replace('\\displaystyle', '')
    return t.lower()

def score_quiz(q):
    score = 0
    # Prefer those correctly fixed by gemma
    if q.get('gemma_fixed', False):
        score += 10
    
    opts = q.get('opts', [])
    ok = q.get('ok', -1)
    
    # Must have valid options
    if isinstance(opts, list) and len(opts) > 0:
        score += 5
        # Must have valid ok index
        if isinstance(ok, int) and 0 <= ok < len(opts):
            score += 15
    else:
        score -= 50
        
    # Prefer longer question text
    d = q.get('d', '')
    score += min(len(d), 500) / 100.0  # Max +5 for length
    
    return score

def deduplicate_file(filename):
    with open(filename, 'r', encoding='utf-8') as f:
        data = json.load(f)
        
    seen = defaultdict(list)
    quizzes = data.get('quiz', [])
    for q in quizzes:
        norm_d = normalize(q.get('d', ''))
        seen[norm_d].append(q)
        
    new_quizzes = []
    removed = 0
    for norm_d, group in seen.items():
        if len(group) == 1:
            new_quizzes.append(group[0])
        else:
            # Sort by score descending
            group.sort(key=score_quiz, reverse=True)
            new_quizzes.append(group[0]) # keep the best
            removed += (len(group) - 1)
            
    data['quiz'] = new_quizzes
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
        
    print(f"{filename}: kept {len(new_quizzes)}, removed {removed}")

deduplicate_file('contenuti/quiz_suria.json')
deduplicate_file('contenuti/quiz_extra.json')
