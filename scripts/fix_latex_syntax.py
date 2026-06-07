import json
import httpx
import sys
import os
import re
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('fix_latex.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL = "gemma3:12b"
TIMEOUT = 90.0

PROMPT_TEMPLATE = """Sei un revisore editoriale esperto di LaTeX e JSON.
Devi controllare ESCLUSIVAMENTE la sintassi LaTeX del seguente quiz.
Non giudicare la logica matematica, valuta solo se la formattazione LaTeX è tecnicamente valida e non rompe il parser KaTeX/LaTeX.

Regole del nostro sistema:
- La matematica inline è racchiusa tra singoli dollari (es. $x^2$).
- I comandi LaTeX (es. \\frac, \\lim, \\int, \\sqrt) devono avere le parentesi graffe {{}} aperte e chiuse correttamente.
- Non ci devono essere typo nei comandi (es. \\rac invece di \\frac).
- I doppi dollari $$ non sono supportati (devono essere singoli $).
- Qualsiasi formula matematica deve essere all'interno di un blocco $...$.

Ecco il quiz originale in formato JSON:
{quiz_json}

Il tuo compito:
1. Se la sintassi LaTeX in "d" e in "opts" è perfetta (o se non c'è LaTeX), rispondi ESATTAMENTE con la parola "OK".
2. Se c'è un errore di sintassi LaTeX, correggilo e restituisci ESCLUSIVAMENTE l'oggetto JSON del quiz corretto.

Regole TASSATIVE per l'output:
- Se correggi, devi restituire un JSON valido e ben formato, con tutte le chiavi originali.
- Non inserire il JSON in blocchi di codice markdown (niente ```json e niente ``` alla fine). L'output JSON deve iniziare con {{ e finire con }}.
- Non aggiungere MAI spiegazioni testuali prima o dopo il JSON o la parola "OK".
"""

def load_json(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_json(filepath, data):
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def evaluate_latex(client, quiz_obj):
    quiz_str = json.dumps(quiz_obj, ensure_ascii=False, indent=2)
    prompt = PROMPT_TEMPLATE.format(quiz_json=quiz_str)
    
    payload = {
        "model": MODEL,
        "prompt": prompt,
        "stream": False,
        "options": {
            "temperature": 0.0,
        }
    }
    
    try:
        response = client.post(OLLAMA_URL, json=payload, timeout=TIMEOUT)
        response.raise_for_status()
        return response.json().get('response', '').strip()
    except httpx.ReadTimeout:
        logging.warning("Timeout di Ollama superato.")
        return "TIMEOUT"
    except Exception as e:
        logging.error(f"Errore chiamata Ollama: {e}")
        return "ERRORE_API"

def process_file(filename, prefix, state, stats):
    data = load_json(os.path.join("contenuti", filename))
    quizzes = data.get("quiz", [])
    
    logging.info(f"Inizio controllo LaTeX su {filename} ({len(quizzes)} quiz)...")
    
    with httpx.Client() as client:
        for i, original_quiz in enumerate(quizzes):
            q_id = f"{prefix}_{i}"
            
            if q_id in state:
                continue
            
            logging.info(f"Processo {q_id}...")
            result = evaluate_latex(client, original_quiz)
            
            if result.startswith("OK") or result == '"OK"':
                state[q_id] = "OK"
                stats["OK"] += 1
                logging.info(f"[{q_id}] LaTeX perfetto.")
            elif result.startswith("{") or "{" in result:
                # E' probabile JSON (magari preceduto da testo, estraiamo via regex)
                match = re.search(r'(\{.*\})', result, re.DOTALL)
                if match:
                    cleaned = match.group(1)
                    try:
                        corrected_quiz = json.loads(cleaned)
                        if "d" in corrected_quiz:
                            data["quiz"][i] = corrected_quiz
                            state[q_id] = "CORRETTO"
                            stats["CORRETTI"] += 1
                            logging.info(f"[{q_id}] LaTeX corretto e salvato.")
                            save_json(os.path.join("contenuti", filename), data)
                        else:
                            raise ValueError("JSON mancante della chiave 'd'")
                    except Exception as e:
                        logging.error(f"[{q_id}] Regex ha trovato json, ma il parsing è fallito: {e}")
                        state[q_id] = "ERRORE_JSON"
                        stats["ERRORI"] += 1
                else:
                    logging.error(f"[{q_id}] Risposta imprevista e nessun JSON trovato.")
                    state[q_id] = "RISPOSTA_IMPREVISTA"
                    stats["ERRORI"] += 1
            else:
                logging.error(f"[{q_id}] Timeout o errore: {result}")
                state[q_id] = result
                stats["ERRORI"] += 1

            save_json("latex_state.json", state)

def main():
    state_file = "latex_state.json"
    state = load_json(state_file) if os.path.exists(state_file) else {}
    
    stats = {"OK": 0, "CORRETTI": 0, "ERRORI": 0}
    
    process_file("quiz_suria.json", "suria", state, stats)
    process_file("quiz_extra.json", "extra", state, stats)
    
    logging.info("PROCESSO TERMINATO.")
    logging.info(f"Statistiche della sessione corrente: {stats}")

if __name__ == "__main__":
    main()
