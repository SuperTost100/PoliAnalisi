import httpx
import json

prompt = """Aggiungi i delimitatori $ ... $ ESCLUSIVAMENTE attorno alle formule matematiche o simboli all'interno delle seguenti stringhe.
Non alterare o tradurre il testo italiano.
Restituisci SOLO un array JSON di stringhe formattate, nessun altro testo.

Stringhe originali:
[
  "f(x) = cos x `e soluzione dell’equazione differenziale:",
  "\\lim\\_{x→4}\\frac{5}{1 −cos(5x −4)} \\cdot \\frac{(x −4)}{5^2} =",
  "Quale `e la derivata prima della funzione f(x) = log(cos x):",
  "L’insieme A = \\left\\{\\-n/(n+5), n = 0, 1, 2, ...\\right\\} \\cup\\{-3} ha",
  "Sia data la funzione f : \\mathbb{R} →\\mathbb{R} tale che se x →+∞→f(x) ∼log x allora:"
]
"""

payload = {
    "model": "gemma3:12b",
    "prompt": prompt,
    "stream": False,
    "options": {
        "temperature": 0.0
    }
}

try:
    resp = httpx.post("http://localhost:11434/api/generate", json=payload, timeout=60)
    print(resp.json().get("response", ""))
except Exception as e:
    print("Error:", e)
