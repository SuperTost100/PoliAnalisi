import json
import httpx
import time

def add_delimiters_ai(questions_list):
    prompt = """Sei un esperto di formattazione LaTeX per la matematica.
    Ti fornirò un array JSON di stringhe. Ognuna è il testo di una domanda di matematica.
    Il tuo UNICO compito è identificare le formule matematiche o i simboli all'interno di queste stringhe e racchiuderli tra dollari ($...$).
    REGOLE FONDAMENTALI:
    1. NON TRADURRE E NON ALTERARE in alcun modo le parole e la punteggiatura del testo italiano.
    2. Aggiungi SOLO il simbolo del dollaro $ all'inizio e alla fine dei blocchi puramente matematici.
    3. Rispondi SOLO ed ESCLUSIVAMENTE con l'array JSON contenente le stringhe modificate, senza markdown extra o spiegazioni.

    Esempio Input:
    [
      "L'integrale I = \\int_{0}^{1} \\frac{\\sin t}{t^{\\alpha}} dt = +∞ se: e x - ∞",
      "Il dominio della funzione f(x) è D = [0, 1]"
    ]
    Esempio Output Atteso:
    [
      "L'integrale $I = \\int_{0}^{1} \\frac{\\sin t}{t^{\\alpha}} dt = +∞$ se: $e x - ∞$",
      "Il dominio della funzione $f(x)$ è $D = [0, 1]$"
    ]

    Array Input Reale:
    """ + json.dumps(questions_list, ensure_ascii=False)
    
    payload = {
        "model": "gemma3:12b",
        "prompt": prompt,
        "stream": False,
        "options": {
            "temperature": 0.0
        }
    }
    
    try:
        resp = httpx.post("http://localhost:11434/api/generate", json=payload, timeout=120)
        resp.raise_for_status()
        raw_resp = resp.json().get("response", "").strip()
        
        # Clean markdown if present
        if raw_resp.startswith("```"):
            lines = raw_resp.split("\n")
            lines = [l for l in lines if not l.startswith("```")]
            raw_resp = "\n".join(lines).strip()
            
        return json.loads(raw_resp)
    except Exception as e:
        print("Errore Ollama:", e)
        return None

def main():
    print("Avvio elaborazione testo domande con Gemma...")
    with open("contenuti/quiz_suria.json", "r") as f:
        data = json.load(f)
        
    quiz_list = data["quiz"]
    
    # Raccogliamo solo le domande che necessitano di dollari
    # e che non ne hanno già
    to_process = []
    for idx, q in enumerate(quiz_list):
        s = q["d"]
        if "$" not in s and ("\\" in s or "=" in s or "^" in s or "_" in s or "f(x)" in s):
            to_process.append(idx)
            
    print(f"Trovate {len(to_process)} domande da fixare.")
    
    chunk_size = 10
    processed_count = 0
    
    for i in range(0, len(to_process), chunk_size):
        chunk_indices = to_process[i:i+chunk_size]
        chunk_texts = [quiz_list[idx]["d"] for idx in chunk_indices]
        
        print(f"Elaborazione chunk {i//chunk_size + 1}/{(len(to_process)+chunk_size-1)//chunk_size}...")
        t0 = time.time()
        
        fixed_texts = add_delimiters_ai(chunk_texts)
        
        if fixed_texts and isinstance(fixed_texts, list) and len(fixed_texts) == len(chunk_texts):
            for j, idx in enumerate(chunk_indices):
                quiz_list[idx]["d"] = fixed_texts[j]
                
            with open("contenuti/quiz_suria.json", "w") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
                
            processed_count += len(chunk_indices)
            print(f"  OK! ({time.time() - t0:.1f}s) - Progresso: {processed_count}/{len(to_process)}")
        else:
            print("  Errore parsing o mismatch lunghezza. Riprovo più tardi o ignoro chunk.")
            
    print("Elaborazione completata!")

if __name__ == "__main__":
    main()
