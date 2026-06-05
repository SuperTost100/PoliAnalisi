#!/usr/bin/env python3
"""
rigenera.py — PoliAnalisi 1 (PoliTost)
Tre pipeline per gemma3:12b:
  FASE 1: revisione qualità su tutti i JSON esistenti
  FASE 2: generazione nuovi esercizi pratici (non ufficiali)
  FASE 3: generazione nuovi quiz e aggiornamento data.js

Uso:
  python3 rigenera.py --fase 1      # solo revisione
  python3 rigenera.py --fase 2      # solo nuovi esercizi
  python3 rigenera.py --fase 3      # solo nuovi quiz
  python3 rigenera.py               # tutte le fasi in sequenza
"""
import os, sys, json, time, argparse, re
from pathlib import Path

try:
    import httpx
except ImportError:
    print("Errore: pip3 install httpx --break-system-packages")
    sys.exit(1)

BASE_DIR   = Path(__file__).parent
OUTPUT_DIR = BASE_DIR / "contenuti"
OLLAMA_URL = "http://localhost:11434"
MODEL      = "gemma3:12b"

# ─────────────────────────────────────────────
# UTILS
# ─────────────────────────────────────────────

def chiama_ollama(prompt: str, timeout: int = 360) -> str:
    try:
        with httpx.Client(timeout=timeout) as c:
            r = c.post(f"{OLLAMA_URL}/api/generate", json={
                "model": MODEL,
                "prompt": prompt,
                "stream": False,
                "options": {"temperature": 0.2, "top_p": 0.9, "num_predict": 3000}
            })
            r.raise_for_status()
            return r.json().get("response", "").strip()
    except Exception as e:
        return f"[ERRORE: {e}]"

def parse_json_safe(text: str) -> dict | None:
    text = text.strip()
    if text.startswith("```"):
        text = "\n".join(l for l in text.split("\n") if not l.startswith("```")).strip()
    try:
        return json.loads(text)
    except:
        s, e = text.find('{'), text.rfind('}')
        if s != -1 and e != -1:
            try: return json.loads(text[s:e+1])
            except: pass
    return None

def check_ollama():
    try:
        r = httpx.get(f"{OLLAMA_URL}/api/tags", timeout=5)
        return r.status_code == 200
    except:
        return False

def save(path: Path, data: dict):
    data.setdefault("_revisione", {})["timestamp"] = time.strftime("%Y-%m-%dT%H:%M:%S")
    data["_revisione"]["model"] = MODEL
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2))

# ─────────────────────────────────────────────
# FASE 1: REVISIONE QUALITÀ
# ─────────────────────────────────────────────

PROMPT_REVISIONE_LEZIONE = """Sei un docente esperto di Analisi Matematica 1.
Hai generato questo JSON con la spiegazione di una lezione universitaria.
Devi revisionarlo accuratamente e restituire una versione MIGLIORATA.

REGOLE FONDAMENTALI:
1. Le formule LaTeX vanno nei campi "formula" — MAI testo normale in un campo formula. Se non c'è formula reale, usa null.
2. "N/A", "Non applicabile", "non presente", "nessuna" → sostituisci con null o rimuovi.
3. La "definizione" deve essere formale e precisa (non colloquiale).
4. La "spiegazione" deve essere intuitiva, 3-5 frasi, leggibile.
5. Le formule LaTeX devono essere matematicamente corrette (controlla segni, indici, notazioni).
6. I "punti_chiave" devono essere frasi complete e utili allo studio.
7. Gli "errori_comuni" devono essere errori reali tipici degli studenti.
8. La "connessioni" deve essere una frase che collega al resto del corso.
9. Nei testi ricchi di formule: struttura in modo che ogni concetto matematico abbia la sua formula separata, non mischiare testo e LaTeX nello stesso campo.
10. Grammatica italiana corretta.

JSON DA REVISIONARE:
{json_input}

Restituisci SOLO il JSON revisionato e migliorato, senza markdown esterno, senza commenti."""

PROMPT_REVISIONE_ESERCIZIO = """Sei un docente esperto di Analisi Matematica 1.
Hai generato questo JSON con la guida a un esercizio universitario.
Devi revisionarlo accuratamente e restituire una versione MIGLIORATA.

REGOLE FONDAMENTALI:
1. Le "formule_usate" devono contenere SOLO LaTeX puro (es: "\\\\int_a^b f(x)\\,dx"). MAI testo normale lì.
2. "N/A", "Non applicabile", "nessuna" → rimuovi dall'array o metti [].
3. Il "testo" dell'esercizio deve essere chiaro e completo.
4. La "strategia" deve essere un metodo step-by-step utile, non generico.
5. La "soluzione" deve avere i passaggi intermedi con formule LaTeX inline \\(...\\).
6. "nota" deve essere un trucco reale, non ovvio.
7. Se un campo è vuoto o inutile, rimuovilo o metti null.
8. Grammatica italiana corretta.
9. Le aree ricche di formule devono essere strutturate con una formula per riga/campo.

JSON DA REVISIONARE:
{json_input}

Restituisci SOLO il JSON revisionato, senza markdown esterno."""

def fase1_revisione():
    print("\n" + "="*60)
    print("🔍 FASE 1: REVISIONE QUALITÀ JSON")
    print("="*60)

    json_files = sorted(OUTPUT_DIR.glob("*.json"))
    print(f"  Trovati {len(json_files)} file da revisionare\n")

    for f in json_files:
        if f.name in ("quiz_extra.json",):
            continue  # saltare file speciali

        print(f"  📋 {f.name}...", end="", flush=True)
        try:
            data = json.loads(f.read_text())
        except:
            print(" ⚠️  JSON non valido, skip")
            continue

        # Determina tipo
        is_lezione = f.name.startswith("lezione_")
        is_esercizio = f.name.startswith("esercizio_")

        if not (is_lezione or is_esercizio):
            print(" ⏭  (teoremi/riassunto, skip)")
            continue

        # Salta se già revisionato di recente (entro 24h)
        ts = data.get("_revisione", {}).get("timestamp", "")
        if ts:
            try:
                import datetime
                rev_time = datetime.datetime.fromisoformat(ts)
                if (datetime.datetime.now() - rev_time).total_seconds() < 3600 * 2:
                    print(" ✓ già revisionato")
                    continue
            except: pass

        json_str = json.dumps(data, ensure_ascii=False, indent=2)[:6000]

        if is_lezione:
            prompt = PROMPT_REVISIONE_LEZIONE.format(json_input=json_str)
        else:
            prompt = PROMPT_REVISIONE_ESERCIZIO.format(json_input=json_str)

        t0 = time.time()
        risposta = chiama_ollama(prompt)
        dt = time.time() - t0

        parsed = parse_json_safe(risposta)
        if parsed and isinstance(parsed, dict) and len(parsed) > 2:
            # Preserva _meta originale
            parsed["_meta"] = data.get("_meta", {})
            save(f, parsed)
            print(f" ✅ ({dt:.0f}s)")
        else:
            print(f" ⚠️  parse fallito ({dt:.0f}s), mantenuto originale")

# ─────────────────────────────────────────────
# FASE 2: NUOVI ESERCIZI PRATICI
# ─────────────────────────────────────────────

ARGOMENTI_NUOVI_ES = [
    ("limiti_extra",     "Limiti — esercizi extra",       "limiti",     ["limiti", "forme indeterminate", "limiti notevoli"]),
    ("derivate_extra",   "Derivate — esercizi extra",     "derivate",   ["derivate", "regola della catena", "derivate composte"]),
    ("taylor_extra",     "Taylor — esercizi extra",       "taylor",     ["sviluppi di Taylor", "McLaurin", "limiti con Taylor"]),
    ("integrali_extra",  "Integrali — esercizi extra",    "integrali",  ["integrali per sostituzione", "per parti", "integrali definiti"]),
    ("continuita_extra", "Continuità — esercizi extra",   "continuita", ["continuità", "teorema di Bolzano", "punti di discontinuità"]),
    ("funzioni_extra",   "Funzioni — esercizi extra",     "funzioni",   ["funzioni", "dominio", "iniettività", "funzione inversa"]),
]

PROMPT_NUOVI_ESERCIZI = """Sei un docente esperto di Analisi Matematica 1 al Politecnico di Torino.
Crea {n} esercizi ORIGINALI sull'argomento: {argomento}.
Gli esercizi devono essere propedeutici allo studio della materia ma NON sono esercizi ufficiali del corso.

TEMI DA COPRIRE: {temi}

LIVELLI: crea esercizi di difficoltà mista (base, medio, avanzato).

IMPORTANTISSIMO — REGOLE FORMATTAZIONE:
- Le formule LaTeX inline nel testo usano la notazione \\(formula\\)
- I campi "formule_usate" contengono SOLO LaTeX puro, un array di stringhe LaTeX
- MAI testo normale in un campo formula. MAI "N/A" o "nessuna".
- La "strategia" è dettagliata step-by-step con formule inline
- La "soluzione" ha tutti i passaggi intermedi con formule inline
- Ogni esercizio deve essere completo e risolvibile
- Grammatica italiana impeccabile
- Aree ricche di formule: una formula per concetto, ben separate

Formato JSON ESATTO:
{{
  "nome": "Titolo descrittivo",
  "tipo_contenuto": "extra",
  "ufficiale": false,
  "avviso": "Questi esercizi non sono ufficiali del corso PoliTo ma sono utili per la preparazione all'esame.",
  "difficolta": "base|medio|avanzato",
  "argomenti": {argomenti_json},
  "introduzione": "Breve presentazione degli esercizi",
  "esercizi": [
    {{
      "numero": 1,
      "difficolta": "base|medio|avanzato",
      "testo": "Testo completo dell'esercizio con formule \\(f(x)\\) inline",
      "strategia": "Metodo di risoluzione step-by-step",
      "soluzione": "Soluzione completa con passaggi",
      "formule_usate": ["formula LaTeX 1", "formula LaTeX 2"],
      "nota": "Trucco o osservazione utile"
    }}
  ],
  "riepilogo": "Cosa si impara da questi esercizi"
}}

Crea esattamente {n} esercizi. Rispondi SOLO con il JSON valido."""

def fase2_nuovi_esercizi():
    print("\n" + "="*60)
    print("✨ FASE 2: GENERAZIONE NUOVI ESERCIZI PRATICI")
    print("="*60)

    for file_id, nome, arg, temi in ARGOMENTI_NUOVI_ES:
        out = OUTPUT_DIR / f"esercizio_extra_{file_id}.json"
        if out.exists():
            print(f"  ⏭  {file_id} — già presente, skip")
            continue

        print(f"\n  📝 Genero: {nome}...")
        n_esercizi = 5 if arg in ("limiti", "derivate", "taylor") else 4
        prompt = PROMPT_NUOVI_ESERCIZI.format(
            n=n_esercizi,
            argomento=nome,
            temi=", ".join(temi),
            argomenti_json=json.dumps(temi, ensure_ascii=False)
        )

        t0 = time.time()
        risposta = chiama_ollama(prompt, timeout=420)
        dt = time.time() - t0

        parsed = parse_json_safe(risposta)
        if parsed and isinstance(parsed, dict) and "esercizi" in parsed:
            parsed["_meta"] = {
                "model": MODEL,
                "file_id": file_id,
                "argomento": arg,
                "ufficiale": False,
                "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S")
            }
            out.write_text(json.dumps(parsed, ensure_ascii=False, indent=2))
            n = len(parsed.get("esercizi", []))
            print(f"  ✅ {out.name} — {n} esercizi ({dt:.0f}s)")
        else:
            print(f"  ⚠️  parse fallito ({dt:.0f}s). Risposta:\n{risposta[:200]}")

    # Revisiona subito i nuovi esercizi extra
    print("\n  🔍 Revisiono i nuovi esercizi extra...")
    for file_id, _, _, _ in ARGOMENTI_NUOVI_ES:
        f = OUTPUT_DIR / f"esercizio_extra_{file_id}.json"
        if not f.exists():
            continue
        data = json.loads(f.read_text())
        # Salta se già revisionato (appena creato)
        json_str = json.dumps(data, ensure_ascii=False, indent=2)[:6000]
        prompt = PROMPT_REVISIONE_ESERCIZIO.format(json_input=json_str)
        print(f"    📋 {f.name}...", end="", flush=True)
        t0 = time.time()
        risposta = chiama_ollama(prompt)
        dt = time.time() - t0
        parsed = parse_json_safe(risposta)
        if parsed and isinstance(parsed, dict) and "esercizi" in parsed:
            parsed["_meta"] = data.get("_meta", {})
            save(f, parsed)
            print(f" ✅ ({dt:.0f}s)")
        else:
            print(f" ⚠️  ({dt:.0f}s)")

# ─────────────────────────────────────────────
# FASE 3: NUOVI QUIZ + AGGIORNAMENTO data.js
# ─────────────────────────────────────────────

PROMPT_NUOVI_QUIZ = """Sei un docente esperto di Analisi Matematica 1.
Crea {n} domande di quiz a risposta multipla (4 opzioni) sull'argomento: {argomento}.

REGOLE:
- Le domande devono essere specifiche, non banali, utili per prepararsi all'esame
- Difficoltà mista: base, medio, avanzato
- 4 opzioni per domanda (una sola corretta)
- Le formule LaTeX usano \\(...\\) per inline e \\[...\\] per display
- La spiegazione deve essere dettagliata e didattica
- Le risposte sbagliate devono essere plausibili (errori tipici degli studenti)
- MAI domande duplicate di quelle già presenti
- Grammatica italiana impeccabile

ARGOMENTO: {argomento}
SOTTOTEMI: {sottotemi}

Formato JSON ESATTO (array di oggetti):
[
  {{
    "arg": "{arg_id}",
    "dif": "base|medio|avanzato",
    "d": "Testo della domanda con eventuali formule \\(f(x)\\)",
    "opts": ["Opzione A", "Opzione B", "Opzione C", "Opzione D"],
    "ok": 0,
    "spieg": "Spiegazione dettagliata della risposta corretta con formule"
  }}
]

Il campo "ok" è l'indice (0-3) dell'opzione corretta.
Crea esattamente {n} domande. Rispondi SOLO con il JSON array."""

ARGOMENTI_QUIZ = [
    ("fondamenti",  "Fondamenti e Logica",         ["quantificatori", "sup inf max min", "insiemi numerici"]),
    ("funzioni",    "Funzioni",                    ["iniettività", "suriettività", "funzione inversa", "monotonia"]),
    ("limiti",      "Limiti e Continuità",         ["forme indeterminate", "limiti notevoli", "tipi di discontinuità"]),
    ("successioni", "Successioni",                 ["convergenza", "successione geometrica", "teorema monotonia"]),
    ("continuita",  "Teoremi di Continuità",       ["Bolzano", "Weierstrass", "valori intermedi", "Landau"]),
    ("derivate",    "Derivate",                    ["regole derivazione", "punti non derivabilità", "Rolle", "Lagrange", "De l'Hôpital"]),
    ("taylor",      "Taylor e McLaurin",           ["sviluppi di McLaurin", "resto di Peano", "convessità"]),
    ("integrali",   "Integrali",                   ["integrali indefiniti", "per parti", "sostituzione", "impropri", "TFCI"]),
    ("edo",         "EDO",                         ["EDO separabili", "EDO lineari I ordine", "problema di Cauchy"]),
]

def fase3_nuovi_quiz():
    print("\n" + "="*60)
    print("🎯 FASE 3: NUOVI QUIZ")
    print("="*60)

    out_file = OUTPUT_DIR / "quiz_extra.json"
    tutti_quiz = []

    for arg_id, nome, sottotemi in ARGOMENTI_QUIZ:
        n = 4  # 4 domande per argomento = 36 nuove domande totali
        print(f"\n  📝 Genero {n} quiz su: {nome}...")
        prompt = PROMPT_NUOVI_QUIZ.format(
            n=n,
            argomento=nome,
            arg_id=arg_id,
            sottotemi=", ".join(sottotemi)
        )
        t0 = time.time()
        risposta = chiama_ollama(prompt, timeout=300)
        dt = time.time() - t0

        parsed = parse_json_safe(risposta)
        if isinstance(parsed, list) and len(parsed) > 0:
            for q in parsed:
                if isinstance(q, dict) and "d" in q and "opts" in q and "ok" in q:
                    tutti_quiz.append(q)
            print(f"  ✅ {len(parsed)} domande ({dt:.0f}s)")
        else:
            print(f"  ⚠️  parse fallito ({dt:.0f}s)")

    # Salva quiz extra
    out_file.write_text(json.dumps({
        "quiz": tutti_quiz,
        "_meta": {
            "model": MODEL,
            "n_domande": len(tutti_quiz),
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S")
        }
    }, ensure_ascii=False, indent=2))

    print(f"\n  ✅ Totale: {len(tutti_quiz)} nuove domande → {out_file.name}")

    # Revisiona i quiz generati
    print("\n  🔍 Revisiono qualità dei quiz...")
    PROMPT_REVISIONE_QUIZ = """Sei un docente esperto di Analisi Matematica 1.
Revisiona questo array di domande quiz e restituisci una versione MIGLIORATA.

CONTROLLA:
1. Le formule LaTeX siano matematicamente corrette
2. La domanda sia chiara e non ambigua
3. Il campo "ok" punti all'opzione corretta (verifica matematicamente!)
4. La spiegazione sia accurata e didattica
5. MAI "N/A" o testo generico nelle formule
6. Grammatica italiana corretta

QUIZ DA REVISIONARE:
{quiz_json}

Restituisci SOLO il JSON array revisionato."""

    data = json.loads(out_file.read_text())
    quiz_str = json.dumps(data["quiz"][:20], ensure_ascii=False, indent=2)
    prompt = PROMPT_REVISIONE_QUIZ.format(quiz_json=quiz_str)
    t0 = time.time()
    risposta = chiama_ollama(prompt, timeout=300)
    dt = time.time() - t0
    parsed = parse_json_safe(risposta)
    if isinstance(parsed, list) and len(parsed) > 5:
        data["quiz"][:len(parsed)] = parsed
        out_file.write_text(json.dumps(data, ensure_ascii=False, indent=2))
        print(f"  ✅ Prima metà revisionata ({dt:.0f}s)")

    # Revisiona seconda metà
    quiz_str2 = json.dumps(data["quiz"][20:], ensure_ascii=False, indent=2)
    if quiz_str2 and quiz_str2 != "[]":
        prompt2 = PROMPT_REVISIONE_QUIZ.format(quiz_json=quiz_str2)
        risposta2 = chiama_ollama(prompt2, timeout=300)
        parsed2 = parse_json_safe(risposta2)
        if isinstance(parsed2, list) and len(parsed2) > 2:
            data["quiz"][20:20+len(parsed2)] = parsed2
            out_file.write_text(json.dumps(data, ensure_ascii=False, indent=2))
            print(f"  ✅ Seconda metà revisionata")

# ─────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--fase", type=int, choices=[1,2,3], help="Esegui solo la fase specificata")
    args = parser.parse_args()

    print("\n" + "🔬 "*20)
    print("  PoliAnalisi — Rigenerazione AI Locale")
    print("🔬 "*20)

    if not check_ollama():
        print("❌ Ollama non in esecuzione!")
        sys.exit(1)
    print(f"✅ Ollama OK · Modello: {MODEL}\n")

    t_start = time.time()

    if args.fase in (None, 1):
        fase1_revisione()

    if args.fase in (None, 2):
        fase2_nuovi_esercizi()

    if args.fase in (None, 3):
        fase3_nuovi_quiz()

    dt = (time.time() - t_start) / 60
    print(f"\n{'='*60}")
    print(f"✅ COMPLETATO in {dt:.1f} minuti")
    print(f"{'='*60}\n")

if __name__ == "__main__":
    main()
