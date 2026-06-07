#!/usr/bin/env python3
"""
analizza.py — PoliTo Analisi Studio
Estrae testo dai PDF del materiale didattico, chiama Ollama (gemma3:12b)
per generare spiegazioni strutturate, e salva JSON in contenuti/

Uso:
  python3 analizza.py [--model gemma3:12b] [--skip-existing]
"""

import os
import sys
import json
import time
import argparse
import hashlib
import textwrap
from pathlib import Path

try:
    import fitz  # pymupdf
except ImportError:
    print("Errore: pymupdf non installato. Esegui: pip3 install pymupdf --break-system-packages")
    sys.exit(1)

try:
    import httpx
except ImportError:
    print("Errore: httpx non installato. Esegui: pip3 install httpx --break-system-packages")
    sys.exit(1)

# =============================================
# CONFIGURAZIONE
# =============================================

BASE_DIR = Path(__file__).parent
MATERIALE = BASE_DIR / "materiale"
OUTPUT_DIR = BASE_DIR / "contenuti"
OLLAMA_URL = "http://localhost:11434"

LEZIONI_DIR = MATERIALE / "Lezioni"
ATTIVITA_DIR = MATERIALE / "Attivita' settimanali proposte"
RIASSUNTO = MATERIALE / "RiassuntoAnalisi1.pdf"
TEOREMI = MATERIALE / "Analisi Matematica 1 - TEOREMI.pdf"

OUTPUT_DIR.mkdir(exist_ok=True)

# =============================================
# ESTRAZIONE TESTO PDF
# =============================================

def estrai_testo_pdf(path: Path, max_chars: int = 12000) -> str:
    """Estrae testo da un PDF, limitando a max_chars caratteri."""
    try:
        doc = fitz.open(str(path))
        testo = ""
        for page in doc:
            testo += page.get_text()
        doc.close()
        testo = testo.strip()
        if len(testo) > max_chars:
            testo = testo[:max_chars] + "\n\n[...testo troncato per brevità...]"
        return testo
    except Exception as e:
        return f"[Errore estrazione PDF: {e}]"

# =============================================
# CHIAMATA OLLAMA
# =============================================

def chiama_ollama(prompt: str, model: str, timeout: int = 300) -> str:
    """Chiama l'API Ollama in streaming e restituisce la risposta completa."""
    try:
        with httpx.Client(timeout=timeout) as client:
            risposta = client.post(
                f"{OLLAMA_URL}/api/generate",
                json={
                    "model": model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.3,
                        "top_p": 0.9,
                        "num_predict": 2048,
                    }
                }
            )
            risposta.raise_for_status()
            data = risposta.json()
            return data.get("response", "").strip()
    except httpx.ConnectError:
        return "[ERRORE: Ollama non in esecuzione. Avvia con: ollama serve]"
    except Exception as e:
        return f"[ERRORE chiamata Ollama: {e}]"

def check_ollama() -> bool:
    """Verifica che Ollama sia in esecuzione."""
    try:
        r = httpx.get(f"{OLLAMA_URL}/api/tags", timeout=5)
        return r.status_code == 200
    except:
        return False

def check_model(model: str) -> bool:
    """Verifica che il modello sia disponibile."""
    try:
        r = httpx.get(f"{OLLAMA_URL}/api/tags", timeout=5)
        models = [m["name"] for m in r.json().get("models", [])]
        return any(m.startswith(model.split(":")[0]) for m in models)
    except:
        return False

# =============================================
# PROMPT TEMPLATES
# =============================================

PROMPT_LEZIONE = """Sei un tutor esperto di Analisi Matematica 1 per il Politecnico di Torino.
Ti viene fornito il testo di una lezione universitaria.
Il tuo compito è creare una spiegazione didattica eccellente in italiano.

TITOLO LEZIONE: {titolo}

TESTO ESTRATTO DAL PDF:
{testo}

Genera una spiegazione strutturata con questo formato JSON ESATTO (senza markdown esterno):
{{
  "titolo": "{titolo}",
  "introduzione": "Paragrafo introduttivo chiaro e motivante (2-3 frasi)",
  "concetti": [
    {{
      "nome": "Nome del concetto",
      "definizione": "Definizione precisa e formale",
      "spiegazione": "Spiegazione intuitiva con linguaggio accessibile (3-5 frasi)",
      "formula": "Formula LaTeX se applicabile (senza $$, solo il contenuto)",
      "esempio": "Esempio concreto e numerico se possibile"
    }}
  ],
  "punti_chiave": ["punto 1", "punto 2", "punto 3"],
  "errori_comuni": ["errore tipico 1", "errore tipico 2"],
  "connessioni": "Come questo argomento si collega agli altri del corso"
}}

Rispondi SOLO con il JSON valido, nessun altro testo."""

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

PROMPT_TEOREMA = """Sei un tutor esperto di Analisi Matematica 1 per il Politecnico di Torino.
Ti viene fornito il testo sui teoremi richiesti per il corso.

TESTO ESTRATTO:
{testo}

Genera una lista strutturata dei teoremi in JSON ESATTO:
{{
  "teoremi": [
    {{
      "nome": "Nome del teorema",
      "argomento": "categoria: limiti|continuita|derivate|integrali|edo",
      "ipotesi": "Le ipotesi necessarie",
      "tesi": "La conclusione del teorema",
      "enunciato_latex": "Enunciato formale con LaTeX (solo il contenuto, non i delimitatori)",
      "idea_dimostrazione": "Idea chiave della dimostrazione in 3-5 frasi",
      "applicazioni": "Quando e come si usa questo teorema",
      "importanza": "alta|media"
    }}
  ]
}}

Rispondi SOLO con il JSON valido, nessun altro testo."""

PROMPT_RIASSUNTO_SEZIONE = """Sei un tutor esperto di Analisi Matematica 1 per il Politecnico di Torino.
Ti viene fornito un estratto del riassunto del corso.

TESTO ESTRATTO (sezione {sezione}):
{testo}

Genera un riassunto strutturato in JSON ESATTO:
{{
  "sezione": "{sezione}",
  "argomenti_trattati": ["argomento 1", "argomento 2"],
  "definizioni": [
    {{
      "termine": "termine",
      "definizione": "definizione precisa",
      "formula": "formula LaTeX se applicabile"
    }}
  ],
  "risultati_principali": [
    {{
      "nome": "nome teorema/risultato",
      "enunciato": "enunciato in prosa",
      "formula": "formula LaTeX se applicabile"
    }}
  ],
  "note_studio": "Consigli pratici per studiare questa sezione"
}}

Rispondi SOLO con il JSON valido, nessun altro testo."""

# =============================================
# PARSING SICURO JSON
# =============================================

def parse_json_safe(testo: str, fallback_key: str = "contenuto") -> dict:
    """Prova a parsare JSON dalla risposta del modello."""
    testo = testo.strip()
    # Rimuovi eventuali code block markdown
    if testo.startswith("```"):
        lines = testo.split("\n")
        lines = [l for l in lines if not l.startswith("```")]
        testo = "\n".join(lines).strip()
    try:
        return json.loads(testo)
    except json.JSONDecodeError:
        # Fallback: prova a trovare il JSON dentro il testo
        start = testo.find('{')
        end = testo.rfind('}')
        if start != -1 and end != -1:
            try:
                return json.loads(testo[start:end+1])
            except:
                pass
    # Fallback finale
    return {fallback_key: testo, "parse_error": True}

# =============================================
# ANALISI LEZIONI
# =============================================

def analizza_lezioni(model: str, skip_existing: bool):
    print("\n" + "="*60)
    print("📚 ANALISI LEZIONI")
    print("="*60)

    lezioni_meta = [
        ("L1", "Introduzione al corso, predicati logici"),
        ("L2", "Quantificatori, insiemi numerici"),
        ("L3", "Sup, inf, max, min, funzioni"),
        ("L4", "Funzioni iniettive, suriettive, inversa"),
        ("L5", "Funzioni limitate, massimi e minimi, funzioni monotone"),
        ("L6", "Introduzione ai limiti"),
        ("L7", "Limiti e continuità"),
        ("L8", "Limiti con dominio o immagine illimitati"),
        ("L9", "Teoremi sui limiti"),
        ("L10", "Teorema limite funzione composta"),
        ("L11", "Teorema funzione composta e limiti notevoli"),
        ("L12", "Successioni"),
        ("L13", "Successione geometrica, primi teoremi per funzioni continue"),
        ("L14", "Teorema di esistenza degli zeri"),
        ("L15", "Teorema valori intermedi, simboli di Landau"),
        ("L16", "Parte principale"),
        ("L17", "Derivate"),
        ("L18", "Punti di non derivabilità"),
        ("L19", "Teoremi di derivazione"),
        ("L20", "Sviluppi di Taylor"),
        ("L21", "Sviluppi di McLaurin, concavità, convessità, flessi"),
        ("L22", "Convessità con Taylor"),
        ("L23", "Integrali indefiniti"),
        ("L24", "Integrale definito"),
        ("L25", "Teorema Fondamentale del Calcolo Integrale (TFCI)"),
        ("L26", "Integrali impropri"),
    ]

    pdf_files = list(LEZIONI_DIR.glob("L*.pdf"))
    pdf_map = {}
    for pf in pdf_files:
        for lid, _ in lezioni_meta:
            if pf.name.startswith(lid + " ") or pf.name.startswith(lid + "_"):
                pdf_map[lid] = pf
                break

    # Anche EDO
    edo_file = LEZIONI_DIR / "EDO.pdf"
    if edo_file.exists():
        lezioni_meta.append(("EDO", "Equazioni Differenziali Ordinarie"))
        pdf_map["EDO"] = edo_file

    for lid, titolo in lezioni_meta:
        out_file = OUTPUT_DIR / f"lezione_{lid.lower()}.json"

        if skip_existing and out_file.exists():
            print(f"  ⏭  {lid} — già presente, skip")
            continue

        pdf = pdf_map.get(lid)
        if not pdf:
            # Cerca file con nome contenente l'id
            matches = list(LEZIONI_DIR.glob(f"{lid}*.pdf"))
            if matches:
                pdf = matches[0]

        if not pdf or not pdf.exists():
            print(f"  ⚠️  {lid} — PDF non trovato, genero placeholder")
            testo = f"Lezione {lid}: {titolo}"
        else:
            print(f"  📄 {lid} — Estraggo testo da {pdf.name}")
            testo = estrai_testo_pdf(pdf)
            if not testo or len(testo) < 50:
                print(f"       ⚠️  Testo scarso (scan-based PDF?), uso titolo")
                testo = titolo

        print(f"       🤖 Chiamo {model}...", end="", flush=True)
        t0 = time.time()
        prompt = PROMPT_LEZIONE.format(titolo=titolo, testo=testo)
        risposta = chiama_ollama(prompt, model)
        dt = time.time() - t0
        print(f" fatto in {dt:.1f}s")

        parsed = parse_json_safe(risposta)
        parsed["_meta"] = {
            "id": lid,
            "titolo": titolo,
            "pdf": pdf.name if pdf else None,
            "model": model,
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S")
        }

        out_file.write_text(json.dumps(parsed, ensure_ascii=False, indent=2))
        print(f"       ✅ Salvato in {out_file.name}")

# =============================================
# ANALISI ESERCIZI
# =============================================

def analizza_esercizi(model: str, skip_existing: bool):
    print("\n" + "="*60)
    print("📝 ANALISI ESERCIZI SETTIMANALI")
    print("="*60)

    for settimana_dir in sorted(ATTIVITA_DIR.iterdir()):
        if not settimana_dir.is_dir() or settimana_dir.name.startswith('.'):
            continue

        num = settimana_dir.name.split()[-1]
        print(f"\n  📅 {settimana_dir.name}")

        pdf_files = [f for f in settimana_dir.glob("*.pdf")
                     if "svolgimento" not in f.name.lower()
                     and "risposta" not in f.name.lower()
                     and "risposte" not in f.name.lower()]

        for pdf in sorted(pdf_files):
            safe_name = pdf.stem.replace(" ", "_").replace("/", "_")[:50]
            out_file = OUTPUT_DIR / f"esercizio_s{num}_{safe_name}.json"

            if skip_existing and out_file.exists():
                print(f"    ⏭  {pdf.name[:45]} — già presente")
                continue

            # Cerca il file soluzione corrispondente
            soluzione_candidates = [
                settimana_dir / (pdf.stem + "_svolgimento" + pdf.suffix),
                settimana_dir / (pdf.stem + "_risposta" + pdf.suffix),
                settimana_dir / (pdf.stem + "_risposte" + pdf.suffix),
            ]
            # Cerca per pattern
            sol_file = None
            for c in soluzione_candidates:
                if c.exists():
                    sol_file = c
                    break
            if not sol_file:
                # Cerca con pattern globbing
                base = pdf.stem.split("_")[0] if "_" in pdf.stem else pdf.stem[:20]
                matches = list(settimana_dir.glob(f"*svolgimento*"))
                if matches:
                    sol_file = matches[0]

            print(f"    📄 {pdf.name[:45]}...", end="", flush=True)
            testo = estrai_testo_pdf(pdf)

            if sol_file:
                testo_sol = estrai_testo_pdf(sol_file, max_chars=8000)
                testo += f"\n\n---SOLUZIONE---\n{testo_sol}"

            t0 = time.time()
            prompt = PROMPT_ESERCIZIO.format(
                nome=pdf.stem,
                settimana=settimana_dir.name,
                testo=testo
            )
            risposta = chiama_ollama(prompt, model)
            dt = time.time() - t0
            print(f" {dt:.1f}s")

            parsed = parse_json_safe(risposta)
            parsed["_meta"] = {
                "settimana": num,
                "nome": pdf.stem,
                "pdf": pdf.name,
                "soluzione_pdf": sol_file.name if sol_file else None,
                "model": model,
                "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S")
            }

            out_file.write_text(json.dumps(parsed, ensure_ascii=False, indent=2))
            print(f"       ✅ {out_file.name}")

# =============================================
# ANALISI TEOREMI
# =============================================

def analizza_teoremi(model: str, skip_existing: bool):
    print("\n" + "="*60)
    print("📜 ANALISI TEOREMI")
    print("="*60)

    out_file = OUTPUT_DIR / "teoremi.json"
    if skip_existing and out_file.exists():
        print("  ⏭  teoremi.json — già presente")
        return

    if not TEOREMI.exists():
        print(f"  ⚠️  File teoremi non trovato: {TEOREMI}")
        return

    print(f"  📄 Estraggo testo da {TEOREMI.name}")
    testo = estrai_testo_pdf(TEOREMI, max_chars=15000)

    print(f"  🤖 Chiamo {model}...", end="", flush=True)
    t0 = time.time()
    prompt = PROMPT_TEOREMA.format(testo=testo)
    risposta = chiama_ollama(prompt, model)
    dt = time.time() - t0
    print(f" fatto in {dt:.1f}s")

    parsed = parse_json_safe(risposta)
    parsed["_meta"] = {
        "model": model,
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S")
    }

    out_file.write_text(json.dumps(parsed, ensure_ascii=False, indent=2))
    print(f"  ✅ Salvato in {out_file.name}")

# =============================================
# ANALISI RIASSUNTO
# =============================================

def analizza_riassunto(model: str, skip_existing: bool):
    print("\n" + "="*60)
    print("📖 ANALISI RIASSUNTO")
    print("="*60)

    out_file = OUTPUT_DIR / "riassunto.json"
    if skip_existing and out_file.exists():
        print("  ⏭  riassunto.json — già presente")
        return

    if not RIASSUNTO.exists():
        print(f"  ⚠️  File riassunto non trovato: {RIASSUNTO}")
        return

    print(f"  📄 Estraggo testo da {RIASSUNTO.name}")

    # Il riassunto può essere lungo, lo dividiamo in sezioni
    try:
        doc = fitz.open(str(RIASSUNTO))
        n_pages = len(doc)
        doc.close()
    except:
        n_pages = 1

    # Prendi il testo completo diviso in 3 sezioni
    sezioni = []
    chunk_size = max(1, n_pages // 3)

    for i, start_page in enumerate(range(0, n_pages, chunk_size)):
        if i >= 3:
            break
        try:
            doc = fitz.open(str(RIASSUNTO))
            testo = ""
            end_page = min(start_page + chunk_size, n_pages)
            for p in range(start_page, end_page):
                testo += doc[p].get_text()
            doc.close()
            testo = testo.strip()[:10000]
            sezioni.append((f"Sezione {i+1} (pag. {start_page+1}-{end_page})", testo))
        except Exception as e:
            sezioni.append((f"Sezione {i+1}", f"Errore: {e}"))

    risultati = []
    for nome_sezione, testo in sezioni:
        print(f"  🤖 {nome_sezione}...", end="", flush=True)
        t0 = time.time()
        prompt = PROMPT_RIASSUNTO_SEZIONE.format(sezione=nome_sezione, testo=testo)
        risposta = chiama_ollama(prompt, model)
        dt = time.time() - t0
        print(f" {dt:.1f}s")
        parsed = parse_json_safe(risposta)
        risultati.append(parsed)

    output = {
        "sezioni": risultati,
        "_meta": {
            "model": model,
            "n_pagine": n_pages,
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S")
        }
    }
    out_file.write_text(json.dumps(output, ensure_ascii=False, indent=2))
    print(f"  ✅ Salvato in {out_file.name}")

# =============================================
# MAIN
# =============================================

def main():
    parser = argparse.ArgumentParser(description="Analizza materiale Analisi con AI locale")
    parser.add_argument("--model", default="gemma3:12b", help="Modello Ollama da usare")
    parser.add_argument("--skip-existing", action="store_true", help="Salta file già generati")
    parser.add_argument("--only", choices=["lezioni","esercizi","teoremi","riassunto"],
                        help="Analizza solo una categoria")
    args = parser.parse_args()

    print("\n" + "🧮 "*20)
    print("  PoliTo Analisi Studio — Analisi AI Locale")
    print("🧮 "*20)
    print(f"\n  Modello: {args.model}")
    print(f"  Output:  {OUTPUT_DIR}")
    print(f"  Skip:    {args.skip_existing}")

    # Verifica Ollama
    print("\n  🔍 Verifico Ollama...")
    if not check_ollama():
        print("  ❌ Ollama non in esecuzione!")
        print("  ➡️  Avvia con: ollama serve")
        sys.exit(1)
    print("  ✅ Ollama OK")

    if not check_model(args.model):
        print(f"  ⚠️  Modello {args.model} non trovato.")
        print(f"  ➡️  Scarica con: ollama pull {args.model}")
        sys.exit(1)
    print(f"  ✅ Modello {args.model} disponibile")

    t_start = time.time()

    if args.only == "lezioni" or args.only is None:
        analizza_lezioni(args.model, args.skip_existing)

    if args.only == "esercizi" or args.only is None:
        analizza_esercizi(args.model, args.skip_existing)

    if args.only == "teoremi" or args.only is None:
        analizza_teoremi(args.model, args.skip_existing)

    if args.only == "riassunto" or args.only is None:
        analizza_riassunto(args.model, args.skip_existing)

    dt = time.time() - t_start
    print(f"\n{'='*60}")
    print(f"✅ COMPLETATO in {dt/60:.1f} minuti")
    print(f"   Output in: {OUTPUT_DIR}")
    print(f"   File generati: {len(list(OUTPUT_DIR.glob('*.json')))}")
    print(f"{'='*60}\n")

if __name__ == "__main__":
    main()
