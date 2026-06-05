import os, sys, json, time, re
import fitz
import httpx
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

def gen_json(pdf_name, json_name, nome):
    out = Path("contenuti") / json_name
    if out.exists():
        print(f"Skipping {json_name}, already exists")
        return
    pdf_path = Path("materiale/Attivita' settimanali proposte/Settimana 10") / pdf_name
    try:
        doc = fitz.open(pdf_path)
        text = "\n".join([page.get_text() for page in doc])
        prompt = PROMPT_ESERCIZIO.format(nome=nome, settimana=10, testo=text[:6000])
        print(f"Generating {json_name}...")
        with httpx.Client(timeout=300) as c:
            r = c.post(f"{OLLAMA_URL}/api/generate", json={"model": MODEL, "prompt": prompt, "stream": False, "options": {"temperature": 0.2}})
            res = r.json().get("response", "").strip()
            if res.startswith("```json"): res = res[7:]
            if res.startswith("```"): res = res[3:]
            if res.endswith("```"): res = res[:-3]
            res = res.strip()
            res = re.sub(r"\\([^\"\\/bfnrt])", r"\\\\\1", res)
            data = json.loads(res)
            data["_meta"] = {"id": json_name, "pdf": pdf_name, "model": MODEL}
            with open(out, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            print(f"✅ Generated {json_name}")
    except Exception as e:
        print(f"❌ Error on {json_name}:", e)

# 1. Generate missing files
gen_json("Esercitazione finale testo_e_svolgimento.pdf", "esercizio_s10_Esercitazione_finale_testo_e_svolgimento.json", "Esercitazione finale")
gen_json("Funzione integrale_testo_e_svolgimento.pdf", "esercizio_s10_Funzione_integrale_testo_e_svolgimento.json", "Funzione integrale")
gen_json("Itinere3-23-24-testo-e-svolgimento.pdf", "esercizio_s10_Itinere3-23-24-testo-e-svolgimento.json", "Itinere 3 2023-24")

# 2. Fix N/A and dump all formulas
def is_bad(s):
    if not isinstance(s, str): return False
    u = s.upper()
    return "N/A" in u or "NESSUN" in u or "NON APPLICABILE" in u

md_lines = ["# Tutte le formule nei JSON\n"]
for f in sorted(Path("contenuti").glob("*.json")):
    try:
        with open(f, "r", encoding="utf-8") as file:
            data = json.load(file)
        
        changed = False
        md_lines.append(f"## {f.name}\n")
        
        if "concetti" in data:
            for i, c in enumerate(data["concetti"]):
                form = c.get("formula")
                if is_bad(form):
                    c["formula"] = ""
                    changed = True
                    form = ""
                if form:
                    md_lines.append(f"**Concetto {i} ({c.get('nome','')}):**\n```latex\n{form}\n```\n")
                    
        if "esercizi" in data:
            for i, e in enumerate(data["esercizi"]):
                fu = e.get("formule_usate")
                if isinstance(fu, list):
                    new_fu = []
                    for fx in fu:
                        if not is_bad(fx):
                            new_fu.append(fx)
                        else:
                            changed = True
                    e["formule_usate"] = new_fu
                    if new_fu:
                        md_lines.append(f"**Esercizio {i} (formule_usate):**\n```latex\n" + "\n".join(new_fu) + "\n```\n")
                elif is_bad(fu):
                    e["formule_usate"] = []
                    changed = True
                    
        if changed:
            with open(f, "w", encoding="utf-8") as file:
                json.dump(data, file, ensure_ascii=False, indent=2)
            print(f"Fixed N/A in {f.name}")
    except Exception as e:
        print("Error on", f, e)

with open("formulas_review.md", "w", encoding="utf-8") as f:
    f.write("\n".join(md_lines))
print("Dumped all formulas to formulas_review.md")
