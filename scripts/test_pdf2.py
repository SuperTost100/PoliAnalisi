import fitz

doc = fitz.open("materiale/quiz Paola Suria.pdf")
print("--- ULTIME 5 PAGINE ---")
for i in range(len(doc)-5, len(doc)):
    print(f"Pag {i}:")
    print(doc[i].get_text()[:500])
    print("...")
