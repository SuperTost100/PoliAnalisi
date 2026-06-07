import json
import httpx
import sys
import os
import re
import logging
from datetime import datetime

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('check_math.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL = "gemma3:12b"
TIMEOUT = 60.0

PROMPT_TEMPLATE = """Sei un professore universitario di Analisi Matematica 1 severo e rigoroso.
Devi valutare ESCLUSIVAMENTE la correttezza MATEMATICA della seguente domanda a risposta multipla e delle sue opzioni.

Il tuo compito:
- Verifica che la domanda abbia senso logico-matematico.
- Verifica che le formule non siano chiaramente errate o incomplete (es. \\frac{{1}}{{}} senza denominatore).
- Verifica che la domanda sia risolvibile matematicamente.
- IGNORA COMPLETAMENTE eventuali errori di sintassi LaTeX, rendering o formattazione.

RISPONDI TASSATIVAMENTE IN UNO DEI DUE MODI SEGUENTI, senza aggiungere altre parole o convenevoli:
- "OK" se la domanda è matematicamente valida.
- "ERRORE: [breve spiegazione dell'errore]" se c'è un errore matematico evidente o una formula incompleta/insensata.

Ecco la domanda:
DOMANDA:
{domanda}

OPZIONI DI RISPOSTA:
{opzioni}
"""

def load_json(filepath):
    if not os.path.exists(filepath):
        return {"quiz": []}
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        logging.error(f"Errore nel caricamento di {filepath}: {e}")
        return {"quiz": []}

def save_json(filepath, data):
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def evaluate_question(client, question_text, options_list):
    opts_str = "\n".join(f"- {opt}" for opt in options_list)
    prompt = PROMPT_TEMPLATE.format(domanda=question_text, opzioni=opts_str)
    
    payload = {
        "model": MODEL,
        "prompt": prompt,
        "stream": False,
        "options": {
            "temperature": 0.0, # Deterministic answers
        }
    }
    
    try:
        response = client.post(OLLAMA_URL, json=payload, timeout=TIMEOUT)
        response.raise_for_status()
        result = response.json()
        return result.get('response', '').strip()
    except httpx.ReadTimeout:
        logging.warning("Timeout di Ollama superato (60s).")
        return "TIMEOUT"
    except Exception as e:
        logging.error(f"Errore chiamata Ollama: {e}")
        return "ERRORE_API"

def process_file(filename, prefix, report):
    data = load_json(os.path.join("contenuti", filename))
    quizzes = data.get("quiz", [])
    
    if not quizzes:
        logging.info(f"Nessun quiz trovato in {filename}")
        return

    logging.info(f"Inizio elaborazione di {filename} ({len(quizzes)} quiz)")
    
    with httpx.Client() as client:
        for i, q in enumerate(quizzes):
            q_id = f"{prefix}_{i}"
            
            # Skip if already in report
            if q_id in report:
                continue
                
            q_text = q.get('d', '')
            q_opts = q.get('opts', [])
            
            logging.info(f"[{filename}] Processo {i+1}/{len(quizzes)}...")
            result = evaluate_question(client, q_text, q_opts)
            
            # Only save the ones that are NOT purely 'OK' to keep the report focused
            if "OK" not in result.upper()[:10]: # Look for OK at the beginning
                report[q_id] = {
                    "file": filename,
                    "index": i,
                    "d": q_text,
                    "gemma_eval": result
                }
                logging.info(f"TROVATO ERRORE in {q_id}: {result}")
            else:
                report[q_id] = "OK"
                
            # Salva progressi ogni volta
            save_json("report_matematico.json", report)

def main():
    logging.info("Inizio verifica matematica.")
    report_file = "report_matematico.json"
    
    report = {}
    if os.path.exists(report_file):
        report = load_json(report_file)
        logging.info(f"Ripreso report esistente con {len(report)} valutazioni.")
    
    process_file("quiz_suria.json", "suria", report)
    process_file("quiz_extra.json", "extra", report)
    
    # Crea un riassunto solo con gli errori
    error_report = {k: v for k, v in report.items() if v != "OK"}
    save_json("report_errori_matematici.json", error_report)
    
    logging.info(f"Verifica completata! Trovati {len(error_report)} errori su {len(report)} domande.")
    logging.info("Visualizza 'report_errori_matematici.json' per i dettagli.")

if __name__ == "__main__":
    main()
