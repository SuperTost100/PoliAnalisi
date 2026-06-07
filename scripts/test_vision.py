import fitz
import httpx
import base64

# 1. Convert page 0 to image
doc = fitz.open("materiale/quiz Paola Suria.pdf")
page = doc[0]
pix = page.get_pixmap(dpi=150)
img_bytes = pix.tobytes("png")
b64_img = base64.b64encode(img_bytes).decode('utf-8')

# 2. Call Ollama with Gemma 3
prompt = """Estrai il testo matematico da questa immagine, preservando tutte le formule in formato LaTeX (usa i delimitatori \\[ per le formule in display e \\( per quelle inline). Formatta il testo come markdown pulito."""

payload = {
    "model": "gemma3:12b",
    "prompt": prompt,
    "images": [b64_img],
    "stream": False,
    "options": {
        "temperature": 0.1
    }
}

print("Chiamata a Ollama gemma3:12b con immagine...")
try:
    resp = httpx.post("http://localhost:11434/api/generate", json=payload, timeout=60)
    print("Status:", resp.status_code)
    print(resp.json().get("response", ""))
except Exception as e:
    print("Errore:", e)
