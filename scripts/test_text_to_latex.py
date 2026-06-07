import fitz
import httpx
import json

doc = fitz.open("materiale/quiz Paola Suria.pdf")
messy_text = doc[0].get_text()

prompt = """Sei un esperto di LaTeX e matematica.
Ecco il testo grezzo estratto da un PDF contenente esercizi di Analisi Matematica 1.
Il testo grezzo ha perso la formattazione (es. apici, pedici, frazioni appaiono come testo spezzettato).
Il tuo compito è ricostruire ESATTAMENTE le formule originali in LaTeX.
Rispondi con l'esercizio 1 formattato in Markdown:

TESTO GREZZO:
""" + messy_text[:1500]

payload = {
    "model": "gemma3:12b",
    "prompt": prompt,
    "stream": False,
    "options": {
        "temperature": 0.1
    }
}

print("Chiamata a Ollama (testo)...")
try:
    resp = httpx.post("http://localhost:11434/api/generate", json=payload, timeout=60)
    print("Status:", resp.status_code)
    print(resp.json().get("response", ""))
except Exception as e:
    print("Errore:", e)
