import fitz
import re
import json
import httpx
import os
import time

PDF_PATH = "materiale/quiz Paola Suria.pdf"
OUT_JSON = "contenuti/quiz_suria.json"
OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL = "gemma3:12b"

def parse_json_safe(testo: str):
    testo = testo.strip()
    if testo.startswith("```"):
        lines = testo.split("\n")
        lines = [l for l in lines if not l.startswith("```")]
        testo = "\n".join(lines).strip()
    
    # Rimuove pre/post text extra
    start = testo.find('[')
    end = testo.rfind(']')
    if start != -1 and end != -1:
        testo = testo[start:end+1]
        
    try:
        return json.loads(testo)
    except json.JSONDecodeError as e:
        print("Errore JSON:", e)
        return None

PROMPT_TEMPLATE = """Sei un esperto di LaTeX e Analisi Matematica.
Il seguente testo contiene {n_domande} domande a risposta multipla estratte grezzamente da un PDF.
Il testo grezzo ha perso la formattazione di apici, pedici e frazioni matematiche.
Devi ricostruire ESATTAMENTE le formule originali in formato LaTeX all'interno di un array JSON.
NON inventare risposte, limitati a riformattare il testo fornito.
Per ogni domanda devi produrre un oggetto JSON con le chiavi:
- "d": il testo della domanda in LaTeX
- "opts": un array di stringhe contenente le opzioni (esattamente nello stesso ordine in cui appaiono, a, b, c, d, e)

TESTO GREZZO DELLE {n_domande} DOMANDE:
{testo_grezzo}

Rispondi SOLO ed ESCLUSIVAMENTE con un array JSON di oggetti, senza altro testo.
Esempio output atteso:
[
  {
    "d": "La derivata della funzione $f(x) = \\sqrt[3]{e^{4x} \cos(8x)}$ è:",
    "opts": ["opzione 1 in LaTeX", "opzione 2 in LaTeX", "opzione 3 in LaTeX", "opzione 4 in LaTeX", "opzione 5 in LaTeX"]
  }
]
"""

def extract_simulations():
    doc = fitz.open(PDF_PATH)
    simulazioni = []
    
    current_sim_text = ""
    for i in range(len(doc)):
        page_text = doc[i].get_text()
        current_sim_text += page_text + "\n"
        
        if "RISPOSTE AI QUESITI" in page_text:
            simulazioni.append(current_sim_text)
            current_sim_text = ""
            
    doc.close()
    return simulazioni

def parse_simulation(sim_text):
    # 1. Trova la tabella delle risposte (alla fine)
    # Esempio: 
    # Item n◦ 1 2 3
    # Risposta a b c
    # Useremo una regex per estrarre la mappa 1->a
    answers_map = {}
    
    # Isoliamo la parte dopo "RISPOSTE AI QUESITI"
    idx = sim_text.find("RISPOSTE AI QUESITI")
    if idx != -1:
        tabella_text = sim_text[idx:]
        
        # Cerchiamo di estrarre le sequenze di numeri e lettere
        # Normalmente c'è una riga di numeri e una riga di lettere (a,b,c,d,e)
        numeri = re.findall(r'\b(?:1[0-9]|20|[1-9])\b', tabella_text.replace('Item n◦', ''))
        lettere = re.findall(r'\b[a-e]\b', tabella_text.replace('Risposta', ''))
        
        # Facciamo match diretto
        min_len = min(len(numeri), len(lettere))
        for i in range(min_len):
            try:
                q_num = int(numeri[i])
                let = lettere[i]
                
                # Mappa let a index (a=0, b=1, c=2, d=3, e=4)
                let_idx = ord(let) - ord('a')
                answers_map[q_num] = let_idx
            except:
                pass

    # 2. Raccogliamo i blocchi di domande
    # Le domande iniziano per "1. ", "2. ", ecc.
    questions_blocks = []
    
    # Regex per trovare "numero. testo"
    # Cerchiamo di splittare il testo in base ai numeri delle domande
    lines = sim_text[:idx].split('\n')
    
    current_q_num = None
    current_q_text = []
    
    q_pattern = re.compile(r'^(\d+)\.\s+(.*)')
    
    for line in lines:
        m = q_pattern.match(line.strip())
        if m:
            if current_q_num is not None:
                questions_blocks.append((current_q_num, "\n".join(current_q_text)))
            current_q_num = int(m.group(1))
            current_q_text = [line]
        elif current_q_num is not None:
            current_q_text.append(line)
            
    if current_q_num is not None:
        questions_blocks.append((current_q_num, "\n".join(current_q_text)))
        
    return questions_blocks, answers_map

def call_ollama(testo_grezzo, n_domande):
    prompt = PROMPT_TEMPLATE.replace("{n_domande}", str(n_domande)).replace("{testo_grezzo}", testo_grezzo)
    
    payload = {
        "model": MODEL,
        "prompt": prompt,
        "stream": False,
        "options": {
            "temperature": 0.1
        }
    }
    
    try:
        resp = httpx.post(OLLAMA_URL, json=payload, timeout=120)
        resp.raise_for_status()
        return resp.json().get("response", "")
    except Exception as e:
        print("Errore httpx:", e)
        return ""

def main():
    print("Inizio estrazione da PDF...")
    simulazioni = extract_simulations()
    print(f"Trovate {len(simulazioni)} simulazioni.")
    
    # Carichiamo i quiz esistenti se presenti
    if os.path.exists(OUT_JSON):
        with open(OUT_JSON, "r", encoding="utf-8") as f:
            try:
                data = json.load(f)
                all_quizzes = data.get("quiz", [])
            except:
                all_quizzes = []
    else:
        all_quizzes = []
        
    # Saltiamo le simulazioni già processate
    processed_sims = set()
    for q in all_quizzes:
        spieg = q.get("spieg", "")
        m = re.search(r"Simulazione (\d+)", spieg)
        if m:
            processed_sims.add(int(m.group(1)) - 1)
            
    # Poiché 521 pagine sono moltissime, elaboriamo 1 simulazione alla volta e salviamo.
    for s_idx, sim in enumerate(simulazioni):
        if s_idx in processed_sims:
            print(f"--- Saltata Simulazione {s_idx+1}/{len(simulazioni)} (già processata in precedenza) ---")
            continue
            
        print(f"\n--- Processando Simulazione {s_idx+1}/{len(simulazioni)} ---")
        q_blocks, a_map = parse_simulation(sim)
        print(f"Domande estratte grezze: {len(q_blocks)}, Risposte lette: {len(a_map)}")
        
        if not q_blocks or not a_map:
            print("Saltata, non valida.")
            continue
            
        # Processiamo a blocchi di 5 domande per volta per non confondere Gemma
        chunk_size = 5
        for i in range(0, len(q_blocks), chunk_size):
            chunk = q_blocks[i:i+chunk_size]
            
            chunk_text = ""
            for num, testog in chunk:
                chunk_text += testog + "\n\n"
                
            print(f"  Inviando chunk di {len(chunk)} domande a Gemma...")
            t0 = time.time()
            risposta_llm = call_ollama(chunk_text, len(chunk))
            dt = time.time() - t0
            
            parsed = parse_json_safe(risposta_llm)
            
            if parsed and isinstance(parsed, list):
                # Unisci le risposte di questo chunk
                for idx_in_chunk, (num, _) in enumerate(chunk):
                    if idx_in_chunk < len(parsed):
                        q_obj = parsed[idx_in_chunk]
                        
                        # Recupera la risposta corretta dalla mappa
                        correct_idx = a_map.get(num, 0)
                        
                        final_q = {
                            "arg": "esame",
                            "dif": "avanzato",
                            "d": q_obj.get("d", f"Domanda {num}"),
                            "opts": q_obj.get("opts", []),
                            "ok": correct_idx,
                            "spieg": f"Tratto dalla Simulazione {s_idx+1} (PDF Paola Suria)."
                        }
                        all_quizzes.append(final_q)
            else:
                print("  Errore parsing JSON su questo chunk.")
                print("  Risposta grezza:", risposta_llm[:200])
                
            # Salva frequentemente
            with open(OUT_JSON, "w", encoding="utf-8") as f:
                json.dump({"quiz": all_quizzes}, f, ensure_ascii=False, indent=2)
                
            print(f"  Fatto in {dt:.1f}s. Totale salvati finora: {len(all_quizzes)}")

if __name__ == "__main__":
    main()
