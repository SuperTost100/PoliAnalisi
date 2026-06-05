import fitz
import httpx
import json
import re
from pathlib import Path

MODEL = "gemma3:12b"
OLLAMA_URL = "http://localhost:11434"
PROMPT_ESERCIZIO = """Sei un tutor esperto di Analisi Matematica 1 per il Politecnico di Torino.
Ti viene fornito il testo di un esercizio o una prova d'esame.
Il tuo compito è creare una guida alla risoluzione chiara e dettagliata.

NOME ESERCIZIO: {nome}
SETTIMANA: {settimana}

TESTO ESTRATTO DAL PDF:
{testo}

Genera una guida strutturata in JSON ESATTO:
{{
  "nome": "{nome}",
  "difficolta": "base|medio|avanzato",
  "argomenti": ["arg1", "arg2"],
  "introduzione": "Di cosa tratta questo esercizio e quali competenze richiede",
  "esercizi": [
    {{
      "numero": 1,
      "testo": "Testo dell'esercizio come estratto",
      "strategia": "Come approcciare questo esercizio (step by step)",
      "soluzione": "Soluzione guidata con passaggi intermedi",
      "formule_usate": ["formula LaTeX 1", "formula LaTeX 2"],
      "nota": "Osservazione o trucco utile"
    }}
  ],
  "riepilogo": "Cosa imparare da questo esercizio"
}}

Rispondi SOLO con il JSON valido, nessun altro testo."""

pdf_path = Path("materiale/Attivita' settimanali proposte/Settimana 10/Esercitazione finale testo_e_svolgimento.pdf")
out_path = Path("contenuti/esercizio_s10_Esercitazione_finale_testo_e_svolgimento.json")

doc = fitz.open(pdf_path)
text = "\n".join([page.get_text() for page in doc])
prompt = PROMPT_ESERCIZIO.format(nome="Esercitazione finale", settimana=10, testo=text[:6000])

with httpx.Client(timeout=300) as c:
    r = c.post(f"{OLLAMA_URL}/api/generate", json={"model": MODEL, "prompt": prompt, "stream": False, "options": {"temperature": 0.2}})
    res = r.json().get("response", "").strip()
    
    if res.startswith("```json"): res = res[7:]
    if res.startswith("```"): res = res[3:]
    if res.endswith("```"): res = res[:-3]
    res = res.strip()
    
    # Very robust escaping:
    # 1. Escape all backslashes that are NOT already escaped
    res = re.sub(r'\\(?!["\\/bfnrt])', r'\\\\', res)
    # 2. Fix the ones that look like \frac but are treated as form-feed
    res = res.replace('\\f', '\\\\f')
    res = res.replace('\\t', '\\\\t')
    res = res.replace('\\v', '\\\\v')
    res = res.replace('\\a', '\\\\a')
    res = res.replace('\\b', '\\\\b')

    try:
        data = json.loads(res)
        data["_meta"] = {"id": out_path.name, "pdf": pdf_path.name, "model": MODEL}
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print("✅ Generated", out_path.name)
    except Exception as e:
        print("❌ Still failed to parse JSON:", e)
        # Fallback dump
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(res)
