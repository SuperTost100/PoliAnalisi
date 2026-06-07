import json
import httpx
import asyncio
import re
import sys
import time
import os

PROMPT_TEMPLATE = """Sei un correttore esperto di matematica e testo italiano.
Il seguente quiz ha difetti di OCR da PDF:
- Parole incollate senza spazi (es: "Lasuccessione" -> "La successione", "Determinareilvalore" -> "Determinare il valore"). DEVI rimettere gli spazi.
- Andate a capo '\\n' errate a metà frase (rimuovile per fare una frase fluida).
- Formule fuori posto o sintassi rotta (es: "$/ x" diventi "\int x").

REGOLE TASSATIVE:
1. Correggi TUTTI gli spazi mancanti tra le parole italiane.
2. Avvolgi TUTTA E SOLO la matematica nei dollari `$ ... $`. 
   ATTENZIONE: NON avvolgere intere frasi nei dollari.
   ESEMPIO CORRETTO: `Sia $f(x)$ una funzione continua in $[0, 1]$.`
   ESEMPIO SBAGLIATO: `$Sia f(x) una funzione continua in [0, 1].$`
3. Usa solo sintassi supportata da KaTeX (es. `\int`, `\lim_{x \to 0}`).
4. Restituisci ESATTAMENTE ED ESCLUSIVAMENTE un JSON VALIDO, senza markdown ` ```json ` e senza alcun testo prima o dopo. Nessuna spiegazione.

QUIZ DA CORREGGERE:
Domanda:
{d}

Opzioni:
{opts}

OUTPUT ATTESO (SOLO JSON):
{{
  "d": "domanda corretta con testo separato dalla matematica",
  "opts": [
    "opzione 1 corretta",
    "opzione 2 corretta",
    "..."
  ]
}}
"""

async def fix_quiz(client, sem, q, index):
    async with sem:
        if q.get("gemma_fixed"):
            return q
            
        prompt = PROMPT_TEMPLATE.replace("{d}", q["d"]).replace("{opts}", json.dumps(q["opts"], ensure_ascii=False))
        
        for attempt in range(3):
            try:
                resp = await client.post("http://localhost:11434/api/generate", json={
                    "model": "gemma3:12b",
                    "prompt": prompt,
                    "stream": False
                }, timeout=180.0)
                
                resp.raise_for_status()
                text = resp.json().get("response", "").strip()
                
                # estrai json se è in un blocco
                if "```json" in text:
                    text = text.split("```json")[1].split("```")[0].strip()
                elif "```" in text:
                    text = text.split("```")[1].split("```")[0].strip()
                    
                parsed = json.loads(text)
                if "d" in parsed and "opts" in parsed and isinstance(parsed["opts"], list):
                    q["d"] = parsed["d"]
                    q["opts"] = parsed["opts"]
                    q["gemma_fixed"] = True
                    print(f"[{index}] OK")
                    return q
            except Exception as e:
                print(f"[{index}] ERROR: {e}")
                
        print(f"[{index}] FAIL")
        return q

async def main():
    filename = "contenuti/quiz_suria.json"
    with open(filename, "r", encoding="utf-8") as f:
        data = json.load(f)
        
    quizzes = data.get("quiz", [])
    total = len(quizzes)
    
    print(f"Inizio elaborazione di {total} quiz...")
    
    # Processa in parallelo per fare prima, ma non troppi
    sem = asyncio.Semaphore(4)
    async with httpx.AsyncClient() as client:
        tasks = []
        for i, q in enumerate(quizzes):
            tasks.append(fix_quiz(client, sem, q, i))
            
        # per non intasare la RAM salviamo ogni 50
        for i in range(0, total, 50):
            chunk = tasks[i:i+50]
            await asyncio.gather(*chunk)
            
            # Save checkpoint
            with open(filename + ".tmp", "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            os.replace(filename + ".tmp", filename)
            print(f"--- Salvataggio completato ({min(i+50, total)}/{total}) ---")

if __name__ == "__main__":
    asyncio.run(main())
