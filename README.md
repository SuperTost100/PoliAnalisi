# PoliAnalisi — Analisi Matematica 1

![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)
[![PoliTost](https://img.shields.io/badge/Project-PoliTost-7c3aed.svg)](https://politost.it)
[![Open Source](https://img.shields.io/badge/Open%20Source-%E2%9D%A4%EF%B8%8F-06b6d4.svg)](https://github.com/SuperTost100/PoliAnalisi)

> Piattaforma open source per studiare Analisi Matematica 1 al Politecnico di Torino in modo intelligente, interattivo ed efficace.

**[→ Apri il sito: politost.it/analisi](https://politost.it/analisi)**

---

## ✨ Funzionalità

| Feature | Descrizione |
|---|---|
| 🤖 **Spiegazioni AI** | Teoria ed esercizi spiegati da un modello AI (gemma3:12b via Ollama), pre-generati e inclusi nel repo |
| 📚 **28 Lezioni** | Copertura completa del programma, da logica e insiemi fino a EDO e integrali impropri |
| 📝 **Esercizi guidati** | 37+ esercizi con strategia di risoluzione, soluzione completa e formule usate |
| 🎯 **Quiz interattivi** | Autovalutazione con randomizzazione, feedback immediato e punteggio |
| 📊 **Grafici interattivi** | Visualizza funzioni, derivate e tangenti tramite Plotly.js (offline) |
| 🧮 **Teoria & Formule** | Formulario completo, sviluppi di McLaurin, teoremi con dimostrazione |
| 🔍 **Ricerca rapida** | Cerca lezioni, esercizi e argomenti con `⌘K` |
| ✏️ **Segnala errori** | Ogni lezione ed esercizio ha un tasto per aprire una GitHub Issue direttamente |
| 🔒 **Privacy first** | 100% client-side, nessun dato inviato a server esterni |

## 🚀 Utilizzo

Il sito è disponibile online, pronto all'uso, senza installazioni:

**[https://politost.it/analisi](https://politost.it/analisi)**

## 🛠️ Sviluppo locale

```bash
# Clona il progetto
git clone https://github.com/SuperTost100/PoliAnalisi.git
cd PoliAnalisi

# Avvia un server locale
python3 -m http.server 8080
# oppure: npx serve .
```

Visita `http://localhost:8080`.

## 🤖 Generazione / aggiornamento contenuti AI (opzionale)

I contenuti JSON in `/contenuti` sono già pre-generati e inclusi nel repo. Gli utenti finali non hanno bisogno di nulla in locale.

Per rigenerare o espandere i contenuti:

1. Installa [Ollama](https://ollama.com/) e avvialo
2. Scarica il modello: `ollama pull gemma3:12b`
3. Esegui lo script: `python3 rigenera.py`

> **Nota:** `analizza.py` estrae i contenuti dai PDF originali in `materiale/`. I file `fix_formulas.py` e `fix_latex.py` sono script di pulizia del LaTeX generato.

## 📁 Struttura del progetto

```
PoliAnalisi/
├── index.html          # App shell (struttura HTML)
├── style.css           # Design system (glassmorphism, dark mode, CSS variables)
├── app.js              # Logica app (navigazione, rendering AI, quiz, grafici)
├── data.js             # Catalogo dati (lezioni, esercizi, quiz, formule)
│
├── contenuti/          # JSON pre-generati dall'AI
│   ├── lezione_l*.json         # Spiegazioni lezioni (L1-L26, EDO, EsFin)
│   ├── esercizio_s*.json       # Guide esercizi per settimana
│   ├── riassunto.json          # Riassunto corso
│   ├── teoremi.json            # Elenco teoremi
│   └── quiz_extra.json         # Quiz aggiuntivi
│
├── materiale/          # PDF originali (non tracciati da git)
│   ├── Lezioni/                # Slide lezioni
│   └── Attivita' settimanali proposte/
│
├── rigenera.py         # Script per rigenerare i contenuti AI
├── analizza.py         # Script per estrarre contenuto dai PDF
├── fix_formulas.py     # Pulizia formule LaTeX generate
├── fix_latex.py        # Fix aggiuntivi sintassi LaTeX
│
├── favicon.svg         # Icona progetto
└── manifest.json       # PWA manifest
```

## 🤝 Come contribuire

Ogni contributo è benvenuto!

- **Segnala un errore nei contenuti:** usa il tasto **✏️ Segnala / Suggerisci modifica** presente in ogni lezione ed esercizio, oppure [apri una Issue](https://github.com/SuperTost100/PoliAnalisi/issues/new)
- **Migliora il codice:** fork → branch → PR
- **Aggiungi contenuti:** modifica i JSON in `contenuti/` o usa `rigenera.py`

### Flusso PR

```bash
git checkout -b feature/nome-miglioramento
# ... modifica ...
git commit -m "feat: descrizione"
git push origin feature/nome-miglioramento
# Apri PR su GitHub
```

## 📜 Licenza

Distribuito sotto licenza **[Apache 2.0](LICENSE)**.  
Creato e mantenuto da [SuperTost100](https://github.com/SuperTost100) per [PoliTost](https://politost.it).

## 🌐 Ecosistema PoliTost

- [politost.it/analisi](https://politost.it/analisi) — PoliAnalisi (questo progetto)
- [politost.it/chimiquiz](https://politost.it/chimiquiz) — ChimiQuiz, quiz di Chimica
