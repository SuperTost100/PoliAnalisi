import json
import httpx
import time

def fix_latex_syntax(s):
    if not isinstance(s, str): return s
    return s.replace("\\_", "_").replace("→", "\\to ").replace("`e", "è").replace("`", "'")

def add_delimiters_ai(questions_list):
    prompt = """Sei un esperto di formattazione LaTeX per la matematica.
Il tuo UNICO compito è identificare le formule matematiche all'interno di queste stringhe e racchiuderle tra dollari ($...$).
REGOLE FONDAMENTALI:
1. NON TRADURRE E NON ALTERARE le parole.
2. Aggiungi SOLO $ all'inizio e alla fine dei blocchi matematici.
3. Le stringhe di input sono separate da "---SPLIT---".
4. Devi restituire le stringhe modificate separate da "---SPLIT---". NESSUN ALTRO TESTO.

INPUT:
""" + "\n---SPLIT---\n".join(questions_list)
    
    payload = {
        "model": "gemma3:12b",
        "prompt": prompt,
        "stream": False,
        "options": { "temperature": 0.0 }
    }
    
    try:
        resp = httpx.post("http://localhost:11434/api/generate", json=payload, timeout=120)
        resp.raise_for_status()
        raw = resp.json().get("response", "").strip()
        # Rimuovi eventuali backticks markdown
        if raw.startswith("```"):
            raw = "\n".join([l for l in raw.split("\n") if not l.startswith("```")])
            
        res = raw.split("---SPLIT---")
        return [r.strip() for r in res]
    except Exception as e:
        print("Errore Ollama:", e)
        return None

def main():
    with open("contenuti/quiz_suria.json", "r") as f:
        data = json.load(f)
        
    quiz_list = data["quiz"]
    
    # 1. Fix rapido della sintassi su tutti
    for q in quiz_list:
        q["d"] = fix_latex_syntax(q["d"])
        q["opts"] = [fix_latex_syntax(o) for o in q["opts"]]
        
    # 2. Troviamo quelli senza dollari
    to_process = []
    for idx, q in enumerate(quiz_list):
        s = q["d"]
        if "$" not in s and ("\\" in s or "=" in s or "^" in s or "_" in s or "f(x)" in s):
            to_process.append(idx)
            
    print(f"Trovate {len(to_process)} domande da fixare con AI.")
    
    chunk_size = 10
    for i in range(0, len(to_process), chunk_size):
        chunk_indices = to_process[i:i+chunk_size]
        chunk_texts = [quiz_list[idx]["d"] for idx in chunk_indices]
        
        print(f"Elaborazione chunk {i//chunk_size + 1}...")
        fixed_texts = add_delimiters_ai(chunk_texts)
        
        if fixed_texts and len(fixed_texts) == len(chunk_texts):
            for j, idx in enumerate(chunk_indices):
                quiz_list[idx]["d"] = fixed_texts[j]
            with open("contenuti/quiz_suria.json", "w") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            print("  OK!")
        else:
            print(f"  Errore parsing (attesi {len(chunk_texts)}, ottenuti {len(fixed_texts) if fixed_texts else 0}).")
            
    print("Finito!")

if __name__ == "__main__":
    main()
