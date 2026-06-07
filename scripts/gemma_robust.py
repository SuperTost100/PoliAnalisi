import json
import httpx
import asyncio
import os
import sys
import re

PROMPT_TEMPLATE = """Sei un correttore esperto di matematica e testo italiano.
Riceverai un quiz con difetti di OCR da PDF:
- Parole incollate senza spazi (es: "Lasuccessione" -> "La successione").
- Andate a capo '\\n' errate a metà frase.
- Sintassi matematica non formattata in KaTeX.

REGOLE:
1. Correggi TUTTI gli spazi mancanti.
2. Avvolgi TUTTA e SOLO la matematica nei dollari `$ ... $`. NON avvolgere frasi intere.
3. Restituisci ESATTAMENTE ED ESCLUSIVAMENTE un JSON VALIDO. Nessuna spiegazione.
Formato richiesto:
{{
  "d": "testo domanda",
  "opts": ["opz 1", "opz 2", "opz 3", "opz 4", "opz 5"]
}}

QUIZ DA CORREGGERE:
{quiz_json}
"""

async def fix_single(client, sem, q, idx):
    async with sem:
        if q.get("gemma_fixed"):
            return q
            
        input_json = json.dumps({"d": q["d"], "opts": q["opts"]}, ensure_ascii=False, indent=2)
        prompt = PROMPT_TEMPLATE.replace("{quiz_json}", input_json)
        
        for attempt in range(3):
            try:
                # Usa un timeout ferreo di 40 secondi
                timeout = httpx.Timeout(40.0)
                resp = await client.post("http://localhost:11434/api/generate", json={
                    "model": "gemma3:12b",
                    "prompt": prompt,
                    "stream": False
                }, timeout=timeout)
                
                resp.raise_for_status()
                text = resp.json().get("response", "").strip()
                
                if "```json" in text:
                    text = text.split("```json")[1].split("```")[0].strip()
                elif "```" in text:
                    text = text.split("```")[1].split("```")[0].strip()
                    
                def replacer(m):
                    if m.group(1): return m.group(1)
                    if m.group(2): return '\\\\' + m.group(2)
                    return m.group(0)
                text = re.sub(r'(\\\\)|\\([^"\\/bfnrtu])', replacer, text)
                
                parsed = json.loads(text)
                if isinstance(parsed, dict) and "d" in parsed and "opts" in parsed:
                    q["d"] = parsed["d"]
                    q["opts"] = parsed["opts"]
                    q["gemma_fixed"] = True
                    print(f"[{idx}] OK")
                    return q
            except Exception as e:
                print(f"[{idx}] ERROR: {type(e).__name__} {e}")
                
        print(f"[{idx}] FAIL - SKIP")
        return q

async def main():
    filename = "contenuti/quiz_suria.json"
    with open(filename, "r", encoding="utf-8") as f:
        data = json.load(f)
        
    quizzes = data.get("quiz", [])
    total = len(quizzes)
    
    print(f"Inizio elaborazione robusta di {total} quiz...")
    
    # Processa 1 alla volta
    sem = asyncio.Semaphore(1)
    
    async with httpx.AsyncClient() as client:
        tasks = []
        for i, q in enumerate(quizzes):
            tasks.append(fix_single(client, sem, q, i))
            
        for i in range(0, len(tasks), 5):
            await asyncio.gather(*tasks[i:i+5])
            
            with open(filename + ".tmp", "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            os.replace(filename + ".tmp", filename)
            print(f"--- Salvataggio completato ({min(i+5, total)}/{total}) ---")

if __name__ == "__main__":
    asyncio.run(main())
