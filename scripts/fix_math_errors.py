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
        logging.FileHandler('fix_math.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL = "gemma3:12b"
TIMEOUT = 90.0

PROMPT_TEMPLATE = """Sei un matematico esperto incaricato di riparare un database di quiz universitari.
Un revisore precedente ha sollevato la seguente eccezione per un quiz:
ECCEZIONE DEL REVISORE: {errore}

Ecco il quiz originale in formato JSON:
{quiz_json}

Il tuo compito è decidere come gestire questa eccezione:
1. FALSO_ALLARME: Se l'eccezione è solo una pignoleria accademica (es. "la funzione non è definita a infinito") ma il quiz è comunque perfettamente risolvibile e ha senso logico, rispondi ESATTAMENTE con la parola "FALSO_ALLARME".
2. IRRECUPERABILE: Se c'è un VERO errore che rende il quiz irrisolvibile (es. formula incompleta) e NON c'è modo di dedurre la formula corretta dalle opzioni in modo inequivocabile, rispondi ESATTAMENTE con la parola "IRRECUPERABILE".
3. CORREZIONE: Se c'è un VERO errore (es. manca un denominatore) ma puoi DEDURRE con certezza la formula corretta guardando il contesto o le opzioni di risposta, allora correggi il testo del quiz. In questo caso, devi rispondere ESCLUSIVAMENTE fornendo l'oggetto JSON del quiz corretto.

Regole TASSATIVE per il JSON corretto:
- Devi restituire un JSON valido con tutte le chiavi originali ("d", "opts", "ans", "arg").
- Non inserire il JSON in blocchi di codice markdown (niente ```json e niente ``` alla fine). L'output deve iniziare con {{ e finire con }}.
- Non aggiungere testo di spiegazione prima o dopo il JSON.
"""

def load_json(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_json(filepath, data):
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def evaluate_fix(client, quiz_obj, error_text):
    quiz_str = json.dumps(quiz_obj, ensure_ascii=False, indent=2)
    prompt = PROMPT_TEMPLATE.format(errore=error_text, quiz_json=quiz_str)
    
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

def main():
    if not os.path.exists("report_errori_matematici.json"):
        logging.error("report_errori_matematici.json non trovato!")
        return

    report = load_json("report_errori_matematici.json")
    
    # Load original databases into memory
    db_files = {
        "quiz_suria.json": load_json("contenuti/quiz_suria.json"),
        "quiz_extra.json": load_json("contenuti/quiz_extra.json")
    }
    
    # Load state
    state_file = "fix_state.json"
    state = load_json(state_file) if os.path.exists(state_file) else {}
    
    logging.info(f"Inizio correzione di {len(report)} errori...")
    
    stats = {"FALSO_ALLARME": 0, "IRRECUPERABILE": 0, "CORRETTI": 0, "ERRORI": 0}
    
    with httpx.Client() as client:
        for q_id, q_info in report.items():
            if q_id in state:
                continue
                
            filename = q_info["file"]
            idx = q_info["index"]
            error_text = q_info["gemma_eval"]
            
            # Retrieve original quiz from memory
            try:
                original_quiz = db_files[filename]["quiz"][idx]
            except Exception as e:
                logging.error(f"Impossibile trovare quiz per {q_id}: {e}")
                continue
            
            logging.info(f"Processo {q_id}...")
            result = evaluate_fix(client, original_quiz, error_text)
            
            if result.startswith("FALSO_ALLARME"):
                state[q_id] = "FALSO_ALLARME"
                stats["FALSO_ALLARME"] += 1
                logging.info(f"[{q_id}] Falso allarme. Ignorato.")
                
            elif result.startswith("IRRECUPERABILE"):
                state[q_id] = "IRRECUPERABILE"
                stats["IRRECUPERABILE"] += 1
                logging.info(f"[{q_id}] Irrecuperabile. Ignorato.")
                
            elif result.startswith("{") and result.endswith("}"):
                # E' un JSON
                try:
                    corrected_quiz = json.loads(result)
                    # Verify it has at least 'd'
                    if "d" in corrected_quiz:
                        db_files[filename]["quiz"][idx] = corrected_quiz
                        state[q_id] = "CORRETTO"
                        stats["CORRETTI"] += 1
                        logging.info(f"[{q_id}] Corretto con successo.")
                        
                        # Save the updated DB immediately
                        save_json(os.path.join("contenuti", filename), db_files[filename])
                    else:
                        raise ValueError("JSON mancante della chiave 'd'")
                except Exception as e:
                    logging.error(f"[{q_id}] Gemma ha restituito un JSON invalido: {e}")
                    state[q_id] = "ERRORE_JSON"
                    stats["ERRORI"] += 1
            else:
                # Cerca di estrarre il blocco JSON se c'è testo prima o markdown
                match = re.search(r'(\{.*\})', result, re.DOTALL)
                if match:
                    cleaned = match.group(1)
                    try:
                        corrected_quiz = json.loads(cleaned)
                        if "d" in corrected_quiz:
                            db_files[filename]["quiz"][idx] = corrected_quiz
                            state[q_id] = "CORRETTO"
                            stats["CORRETTI"] += 1
                            logging.info(f"[{q_id}] Corretto con successo (estratto via regex).")
                            save_json(os.path.join("contenuti", filename), db_files[filename])
                        else:
                            raise ValueError("JSON mancante della chiave 'd'")
                    except Exception as e:
                        logging.error(f"[{q_id}] Regex ha trovato json, ma il parsing è fallito: {e}")
                        state[q_id] = "ERRORE_JSON"
                        stats["ERRORI"] += 1
                else:
                    logging.error(f"[{q_id}] Risposta imprevista e nessun JSON trovato: {result[:50]}...")
                    state[q_id] = "RISPOSTA_IMPREVISTA"
                    stats["ERRORI"] += 1

            save_json(state_file, state)

    logging.info("PROCESSO TERMINATO.")
    logging.info(f"Statistiche: {stats}")

if __name__ == "__main__":
    main()
