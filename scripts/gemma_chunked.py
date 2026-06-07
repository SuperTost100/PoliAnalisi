import json
import httpx
import asyncio
import os
import sys

PROMPT_TEMPLATE = """Sei un correttore esperto di matematica e testo italiano.
Riceverai una lista di {num} quiz. Ogni quiz ha difetti di OCR da PDF:
- Parole incollate senza spazi (es: "Lasuccessione" -> "La successione").
- Andate a capo '\\n' errate a metà frase.
- Sintassi matematica non formattata in KaTeX.

REGOLE:
1. Correggi TUTTI gli spazi mancanti.
2. Avvolgi TUTTA e SOLO la matematica nei dollari `$ ... $`. NON avvolgere frasi intere.
3. Restituisci ESATTAMENTE ED ESCLUSIVAMENTE un ARRAY JSON VALIDO contenente {num} oggetti. Nessuna spiegazione o testo extra.
Formato richiesto:
[
  {{
    "d": "testo domanda 1",
    "opts": ["opz 1", "opz 2", "opz 3", "opz 4", "opz 5"]
  }},
  ...
]

QUIZ DA CORREGGERE:
{quizzes_json}
"""

async def fix_chunk(client, sem, chunk, start_idx):
    async with sem:
        # Controlla se il chunk è già stato fixato
        if all(q.get("gemma_fixed") for q in chunk):
            return chunk
            
        input_json = json.dumps([{"d": q["d"], "opts": q["opts"]} for q in chunk], ensure_ascii=False, indent=2)
        prompt = PROMPT_TEMPLATE.replace("{num}", str(len(chunk))).replace("{quizzes_json}", input_json)
        
        for attempt in range(3):
            try:
                resp = await client.post("http://localhost:11434/api/generate", json={
                    "model": "gemma3:12b",
                    "prompt": prompt,
                    "stream": False
                }, timeout=300.0)
                
                resp.raise_for_status()
                text = resp.json().get("response", "").strip()
                
                if "```json" in text:
                    text = text.split("```json")[1].split("```")[0].strip()
                elif "```" in text:
                    text = text.split("```")[1].split("```")[0].strip()
                import re
                def replacer(m):
                    if m.group(1): return m.group(1)
                    if m.group(2): return '\\\\' + m.group(2)
                    return m.group(0)
                text = re.sub(r'(\\\\)|\\([^"\\/bfnrtu])', replacer, text)
                parsed = json.loads(text)
                if isinstance(parsed, list) and len(parsed) == len(chunk):
                    valid = True
                    for i, res in enumerate(parsed):
                        if "d" not in res or "opts" not in res:
                            valid = False
                            break
                    if valid:
                        for i, res in enumerate(parsed):
                            chunk[i]["d"] = res["d"]
                            chunk[i]["opts"] = res["opts"]
                            chunk[i]["gemma_fixed"] = True
                        print(f"[{start_idx}-{start_idx+len(chunk)-1}] OK")
                        return chunk
            except Exception as e:
                print(f"[{start_idx}-{start_idx+len(chunk)-1}] ERROR: {e}")
                
        print(f"[{start_idx}-{start_idx+len(chunk)-1}] FAIL")
        return chunk

async def main():
    filename = "contenuti/quiz_suria.json"
    with open(filename, "r", encoding="utf-8") as f:
        data = json.load(f)
        
    quizzes = data.get("quiz", [])
    total = len(quizzes)
    
    print(f"Inizio elaborazione di {total} quiz in blocchi...")
    
    # 1 in parallelo per non soffocare Ollama ma massimizzare l'uso
    sem = asyncio.Semaphore(1)
    chunk_size = 5
    
    async with httpx.AsyncClient() as client:
        tasks = []
        chunks = []
        for i in range(0, total, chunk_size):
            chunk = quizzes[i:i+chunk_size]
            chunks.append((chunk, i))
            
        for chunk, idx in chunks:
            tasks.append(fix_chunk(client, sem, chunk, idx))
            
        for i in range(0, len(tasks), 5):
            await asyncio.gather(*tasks[i:i+5])
            
            with open(filename + ".tmp", "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            os.replace(filename + ".tmp", filename)
            print(f"--- Salvataggio completato ({min((i+5)*chunk_size, total)}/{total}) ---")

if __name__ == "__main__":
    asyncio.run(main())
