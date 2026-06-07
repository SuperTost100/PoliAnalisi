import fitz
import sys

try:
    doc = fitz.open("materiale/quiz Paola Suria.pdf")
    print(f"Pagine: {len(doc)}")
    
    # Prendi testo delle prime 2 pagine
    text = ""
    for i in range(min(2, len(doc))):
        text += doc[i].get_text() + "\n"
        
    print("--- ESTRATTO (primi 2000 car) ---")
    print(text[:2000])
except Exception as e:
    print(e)
