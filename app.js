// =============================================
//  PoliAnalisi - App Logic v3
//  PoliTost · github.com/SuperTost100
// =============================================
'use strict';

// ---- State ----
const S = {
  view: 'home',
  lezFilter: 'tutti',
  quizOrder: [],      // indici mescolati
  quizScore: 0,
  quizAnswered: {},   // { orderedIdx: chosenOpt }
  searchOpen: false,
  viewerPDF: null,
  viewerTitle: '',
  viewerAIHtml: '',   // cache AI content per il toggle tab
  _rendered: {},
};

function loadState() {
  try {
    const d = JSON.parse(localStorage.getItem('polianalisi_v3') || '{}');
    S.quizAnswered = d.qa || {};
    S.quizScore    = d.qs || 0;
    S.quizOrder    = d.qo || [];
    updateProgress();
    updateStats();
  } catch(e) {}
}

function saveState() {
  try {
    localStorage.setItem('polianalisi_v3', JSON.stringify({
      qa: S.quizAnswered, qs: S.quizScore, qo: S.quizOrder
    }));
  } catch(e) {}
}

// =============================================
//  NAVIGATION
// =============================================

const TITLES = {
  home:'Home', lezioni:'Lezioni',
  esercizi:'Esercizi', teoria:'Teoria & Formule',
  quiz:'Quiz', grafici:'Grafici Interattivi'
};

function nav(viewId, el) {
  document.querySelectorAll('.view').forEach(v => v.classList.remove('active'));
  document.querySelectorAll('.nav-item').forEach(n => n.classList.remove('active'));

  const v = document.getElementById('view-' + viewId);
  if (v) v.classList.add('active');
  if (el) el.classList.add('active');
  else document.querySelector(`[data-view="${viewId}"]`)?.classList.add('active');

  S.view = viewId;
  document.getElementById('tbTitle').textContent = TITLES[viewId] || viewId;

  if (!S._rendered[viewId]) {
    if (viewId === 'lezioni')  renderLezioni();
    if (viewId === 'esercizi') renderEsercizi();
    if (viewId === 'teoria')   renderTeoria();
    if (viewId === 'quiz')     renderQuiz();
    if (viewId === 'grafici')  setTimeout(() => plotGraph(), 80);
    S._rendered[viewId] = true;
  }

  document.querySelector('.main')?.scrollTo(0, 0);
  setTimeout(() => renderMathIn(v), 100);
}

// =============================================
//  HOME
// =============================================

function renderHome() {
  renderQuickGrid();
  renderArgList();
  updateProgress();
  updateStats();
  updateAIBadge();
}

function renderQuickGrid() {
  const g = document.getElementById('quickGrid');
  if (!g) return;
  const counts = {};
  DATA.lezioni.forEach(l => counts[l.arg] = (counts[l.arg]||0)+1);
  const args = DATA.argomenti.filter(a => a.id !== 'tutti');
  g.innerHTML = args.map(a => `
    <div class="qcard" style="--accent:${a.col}" onclick="goArg('${a.id}')">
      <span class="qcard-icon">${a.icon}</span>
      <div class="qcard-title">${a.label}</div>
      <div class="qcard-sub">${counts[a.id]||0} lezioni</div>
    </div>
  `).join('');
}

function renderArgList() {
  const el = document.getElementById('argList');
  if (!el) return;
  const counts = {};
  DATA.lezioni.forEach(l => counts[l.arg] = (counts[l.arg]||0)+1);
  const args = DATA.argomenti.filter(a => a.id !== 'tutti');
  el.innerHTML = args.map(a => `
    <div class="arg-item" onclick="goArg('${a.id}')">
      <div class="arg-dot" style="background:${a.col}"></div>
      <span class="arg-name">${a.icon} ${a.label}</span>
      <span class="arg-n">${counts[a.id]||0}</span>
    </div>
  `).join('');
}

function updateProgress() {
  const done  = Object.keys(S.quizAnswered).length;
  const total = DATA.quiz.length;
  const pct   = total ? Math.round(done / total * 100) : 0;
  const el = document.getElementById('progFill');
  const p  = document.getElementById('progPct');
  if (el) el.style.width = pct + '%';
  if (p)  p.textContent  = pct + '%';
}

function updateStats() {
  const done = Object.keys(S.quizAnswered).length;
  const qEl  = document.getElementById('statQuiz');
  const scEl = document.getElementById('statScore');
  if (qEl)  qEl.textContent  = done;
  if (scEl) scEl.textContent = S.quizScore;
}

function goArg(id) {
  S.lezFilter = id;
  S._rendered.lezioni = false;
  nav('lezioni', document.querySelector('[data-view=lezioni]'));
}

async function updateAIBadge() {
  const badge = document.getElementById('aiStatusBadge');
  if (!badge) return;
  try {
    const r = await fetch('contenuti/lezione_l1.json');
    if (r.ok) {
      const d = await r.json();
      if (!d.parse_error && d.concetti) {
        badge.innerHTML = '<span class="ai-badge">🤖 Spiegazioni AI disponibili</span>';
        return;
      }
    }
  } catch(e) {}
  badge.innerHTML = '<span class="ai-badge" style="color:var(--t3);border-color:var(--border)">📄 Contenuto AI in preparazione…</span>';
}

function showStats() {
  const done = Object.keys(S.quizAnswered).length;
  showToast(`Quiz: ${done}/${DATA.quiz.length} completati · ${S.quizScore} corrette`, 'cyan');
}

// =============================================
//  LEZIONI
// =============================================

const TAG_C = ['v','c','pk','am','gr'];

function renderLezioni() {
  const bar = document.getElementById('lezFilter');
  if (bar) {
    bar.innerHTML = DATA.argomenti.map(a =>
      `<button class="filt${S.lezFilter===a.id?' active':''}" onclick="filterLez('${a.id}',this)">${a.icon} ${a.label}</button>`
    ).join('');
  }

  const grid = document.getElementById('lezGrid');
  if (!grid) return;

  const list = S.lezFilter === 'tutti'
    ? DATA.lezioni
    : DATA.lezioni.filter(l => l.arg === S.lezFilter);

  grid.innerHTML = list.map(l => {
    const argData = DATA.argomenti.find(a => a.id === l.arg);
    const col     = argData?.col || 'var(--v)';
    const tags    = l.concetti.slice(0,3).map((c,i) => `<span class="tag tag-${TAG_C[i%5]}">${c}</span>`).join('');

    return `
      <div class="lez-card" style="--arg-color:${col}"
           onclick="openContent('${esc(l.json)}','${esc(l.pdf)}','${esc(l.id+' - '+l.titolo)}','lezione','${esc(JSON.stringify(l))}')">
        <div class="lez-top">
          <span class="lez-id">${l.id}</span>
          <h3 class="lez-title">${l.titolo}</h3>
        </div>
        <div class="lez-body">
          <p class="lez-desc">${l.desc}</p>
          <div class="lez-tags">${tags}</div>
        </div>
        <div class="lez-foot">
          <span class="lez-meta"><span class="lez-meta-icon" style="color:${col}">${argData?.icon||'📄'}</span> ${l.argLabel} · ${l.durata}</span>
          <button class="btn-apri">📖 Apri</button>
        </div>
      </div>
    `;
  }).join('');

  if (!list.length) grid.innerHTML = '<div style="color:var(--t3);padding:20px">Nessuna lezione trovata.</div>';
}

function filterLez(id, btn) {
  S.lezFilter = id;
  document.querySelectorAll('#lezFilter .filt').forEach(b => b.classList.remove('active'));
  btn?.classList.add('active');
  renderLezioni();
}

// =============================================
//  ESERCIZI
// =============================================

function renderEsercizi() {
  const grid = document.getElementById('settGrid');
  if (!grid) return;

  // Raggruppa tutti gli esercizi per argomento (non per settimana)
  const gruppi = {};
  DATA.settimane.forEach(s => {
    const key = s.arg || 'altro';
    if (!gruppi[key]) gruppi[key] = { arg: s.arg, titolo: s.titolo, esercizi: [] };
    gruppi[key].esercizi.push(...s.esercizi);
  });

  // Aggiungi eventuali esercizi extra dalla cartella contenuti
  const extraIds = [
    'limiti_extra','derivate_extra','taylor_extra',
    'integrali_extra','continuita_extra','funzioni_extra'
  ];

  grid.innerHTML = Object.values(gruppi).map(g => {
    const argData = DATA.argomenti.find(a => a.id === g.arg);
    const col     = argData?.col || 'var(--v)';

    const esItems = g.esercizi.map(e => {
      const hasSol = e.sol !== null && e.sol !== undefined;
      return `
        <div class="es-item" onclick="openContent('${esc(e.json)}','${esc(e.pdf)}','${esc(e.nome)}','esercizio','')">
          <span class="tipo-badge tipo-${e.tipo}">${e.tipo}</span>
          <span class="es-nome">${e.nome}</span>
          <div class="es-acts">
            <button class="btn-es t" onclick="event.stopPropagation();openContent('${esc(e.json)}','${esc(e.pdf)}','${esc(e.nome)}','esercizio','')">📖 Guida AI</button>
            ${hasSol ? `<button class="btn-es s" onclick="event.stopPropagation();openPDFOnly('${esc(e.sol)}','Soluzione - ${esc(e.nome)}')">📄 Soluz.</button>` : ''}
          </div>
        </div>
      `;
    }).join('');

    return `
      <div class="sett-card">
        <div class="sett-head" style="border-left:3px solid ${col}">
          <span class="sett-badge" style="background:${col}20;color:${col}">${argData?.icon||'📝'} ${argData?.label||g.arg}</span>
          <h3 class="sett-title">${g.titolo}</h3>
        </div>
        <div class="sett-body">
          <div class="esercizi-list">${esItems}</div>
        </div>
      </div>
    `;
  }).join('');
}

// =============================================
//  CONTENT VIEWER (AI JSON + PDF fallback)
//  Fix: cache AI HTML per evitare bug sul re-switch tab
// =============================================

let _currentPDF  = null;
let _currentType = null;
let _currentMeta = null;

async function openContent(jsonPath, pdfPath, title, type, metaStr) {
  S.viewerTitle    = title;
  S.viewerPDF      = pdfPath;
  S.viewerAIHtml   = '';
  _currentPDF      = pdfPath;
  _currentType     = type;
  _currentMeta     = metaStr;

  const modal   = document.getElementById('viewerModal');
  const titleEl = document.getElementById('viewerTitle');
  const content = document.getElementById('viewerContent');
  const tabs    = document.getElementById('viewerTabs');

  titleEl.textContent = title;
  modal.classList.add('open');
  document.body.style.overflow = 'hidden';
  content.style.padding = '28px 32px';
  content.innerHTML = '<div class="pdf-loading"><div class="spinner"></div><span>Caricamento AI…</span></div>';
  tabs.innerHTML = '';

  // Try AI JSON
  let aiData = null;
  try {
    const r = await fetch(jsonPath + '?t=' + Date.now());
    if (r.ok) aiData = await r.json();
  } catch(e) {}

  const hasAI = aiData && !aiData.parse_error && (aiData.concetti || aiData.esercizi || aiData.teoremi);

  if (hasAI) {
    const aiHtml = type === 'lezione'
      ? renderLezioneAI(aiData, JSON.parse(metaStr || '{}'))
      : renderEsercizioAI(aiData);

    S.viewerAIHtml = aiHtml;

    tabs.innerHTML = `
      <div class="viewer-tab active" id="tabAI" onclick="switchViewerTab('ai',this)">🤖 Spiegazione AI</div>
      <div class="viewer-tab" id="tabPDF" onclick="switchViewerTab('pdf',this)">📄 PDF Originale</div>
    `;
    content.innerHTML = aiHtml;
    setTimeout(() => renderMathIn(content), 100);
  } else {
    tabs.innerHTML = `<div class="viewer-tab active">📄 PDF Originale</div>`;
    loadPDFInViewer(pdfPath);
  }
}

function openPDFOnly(pdfPath, title) {
  _currentPDF = pdfPath;
  const modal   = document.getElementById('viewerModal');
  const titleEl = document.getElementById('viewerTitle');
  const tabs    = document.getElementById('viewerTabs');

  titleEl.textContent = title;
  tabs.innerHTML = `<div class="viewer-tab active">📄 PDF</div>`;
  modal.classList.add('open');
  document.body.style.overflow = 'hidden';
  loadPDFInViewer(pdfPath);
}

function loadPDFInViewer(pdfPath) {
  const content = document.getElementById('viewerContent');
  if (!content) return;
  content.style.padding = '0';
  content.innerHTML = `
    <div class="pdf-loading" id="pdfLoading"><div class="spinner"></div><span>Caricamento PDF…</span></div>
    <iframe class="pdf-frame" id="pdfFrame" src=""
      onload="document.getElementById('pdfLoading').style.display='none'"></iframe>
  `;
  // Piccolo delay per evitare il flash
  requestAnimationFrame(() => {
    const frame = document.getElementById('pdfFrame');
    if (frame) frame.src = encodePath(pdfPath);
  });
}

function switchViewerTab(tab, btn) {
  document.querySelectorAll('.viewer-tab').forEach(t => t.classList.remove('active'));
  btn?.classList.add('active');

  const content = document.getElementById('viewerContent');

  if (tab === 'pdf') {
    loadPDFInViewer(_currentPDF);
  } else {
    // Ripristina HTML AI dalla cache - fix del bug "rimane il PDF"
    const frame = document.getElementById('pdfFrame');
    if (frame) frame.src = '';   // scarica l'iframe prima
    content.style.padding = '28px 32px';
    content.innerHTML = S.viewerAIHtml || '<div style="color:var(--t3);padding:20px">Contenuto AI non disponibile</div>';
    setTimeout(() => renderMathIn(content), 80);
  }
}

function closeViewer() {
  const modal = document.getElementById('viewerModal');
  const frame = document.getElementById('pdfFrame');
  if (modal) modal.classList.remove('open');
  if (frame) { frame.src = ''; }
  const content = document.getElementById('viewerContent');
  if (content) content.style.padding = '28px 32px';
  document.body.style.overflow = '';
}

function openExternalPDF() {
  if (_currentPDF) window.open(encodePath(_currentPDF), '_blank');
}

// =============================================
//  AI CONTENT RENDERERS
// =============================================

const REPO = 'https://github.com/SuperTost100/PoliAnalisi';

function reportBtn(title, jsonFile) {
  const issueTitle = encodeURIComponent(`[Contenuto] Segnalazione: ${title}`);
  const issueBody  = encodeURIComponent(
    `**File JSON:** \`${jsonFile}\`\n\n**Descrizione del problema o suggerimento:**\n\n<!-- Descrivi qui cosa non va o cosa vorresti migliorare -->`);
  const url = `${REPO}/issues/new?title=${issueTitle}&body=${issueBody}&labels=contenuto`;
  return `<a class="btn-report" href="${url}" target="_blank" rel="noopener" onclick="event.stopPropagation()">✏️ Segnala / Suggerisci modifica</a>`;
}

function renderLezioneAI(data, meta) {
  const intro    = data.introduzione || meta.desc || '';
  const concetti = Array.isArray(data.concetti)      ? data.concetti      : [];
  const punti    = Array.isArray(data.punti_chiave)  ? data.punti_chiave  : [];
  const errori   = Array.isArray(data.errori_comuni) ? data.errori_comuni : [];
  const conn     = data.connessioni || '';

  const cHtml = concetti.map(c => {
    // Se formula è null/vuota/N/A, non renderizzarla
    const hasFormula = c.formula && c.formula !== 'null' && !/^n\/a$/i.test(c.formula.trim());
    return `
      <div class="concetto-card">
        <div class="concetto-head">
          <div class="concetto-name">${processText(c.nome || '')}</div>
        </div>
        <div class="concetto-body">
          ${c.definizione ? `<div class="concetto-def">${processText(c.definizione)}</div>` : ''}
          ${c.spiegazione ? `<div class="concetto-spieg">${processText(c.spiegazione)}</div>` : ''}
          ${hasFormula   ? `<div class="math-block">\\[${c.formula}\\]</div>` : ''}
          ${c.esempio    ? `<div class="concetto-esempio"><strong style="color:var(--am);font-size:0.74rem">Esempio: </strong>${processText(c.esempio)}</div>` : ''}
        </div>
      </div>
    `;
  }).join('');

  const pkHtml = punti.filter(p => p && !/^n\/a$/i.test(p)).length ? `
    <div class="punti-chiave">
      <div class="pk-title">✓ Punti chiave</div>
      <ul class="pk-list">${punti.filter(p=>p&&!/^n\/a$/i.test(p)).map(p=>`<li>${processText(p)}</li>`).join('')}</ul>
    </div>` : '';

  const errHtml = errori.filter(e => e && !/^n\/a$/i.test(e)).length ? `
    <div class="errori">
      <div class="err-title">⚠ Errori comuni</div>
      <ul class="err-list">${errori.filter(e=>e&&!/^n\/a$/i.test(e)).map(e=>`<li>${processText(e)}</li>`).join('')}</ul>
    </div>` : '';

  const connHtml = conn && !/^n\/a$/i.test(conn) ? `<div class="conn-box">${processText(conn)}</div>` : '';

  return `<div class="ai-content">
    ${intro ? `<p class="intro">${processText(intro)}</p>` : ''}
    <div class="ai-concetti">${cHtml}</div>
    ${pkHtml}${errHtml}${connHtml}
    <div class="ai-footer">
      <span>🤖 Generato da gemma3:12b · <a href="${REPO}" target="_blank" style="color:var(--v-l)">PoliAnalisi</a></span>
      ${reportBtn(meta.titolo || meta.id, meta.json || '')}
    </div>
  </div>`;
}

function renderEsercizioAI(data) {
  const intro    = data.introduzione || '';
  const esercizi = Array.isArray(data.esercizi) ? data.esercizi : [];
  const riepilogo = data.riepilogo || '';
  const diff     = data.difficolta || 'medio';
  const argomenti = Array.isArray(data.argomenti) ? data.argomenti : [];
  const isExtra  = data.ufficiale === false;
  const avviso   = data.avviso || '';

  const esHtml = esercizi.map((e, i) => {
    const formule = (e.formule_usate || []).filter(f => f && !/^n\/a$/i.test(f) && f.trim().length > 2);
    return `
      <div class="concetto-card es-card" id="escard-${i}">
        <div class="concetto-head">
          <div class="concetto-name">Esercizio ${e.numero || i+1}
            ${e.difficolta ? `<span class="diff-badge diff-${e.difficolta}" style="margin-left:8px">${e.difficolta}</span>` : ''}
          </div>
          ${e.nota && !/^n\/a$/i.test(e.nota) ? `<span class="tag tag-am" style="margin-left:auto">${escHTML(e.nota)}</span>` : ''}
        </div>
        <div class="concetto-body">
          ${e.testo ? `<div class="concetto-def">${processText(e.testo)}</div>` : ''}
          ${formule.length ? `<div class="formule-usate">${formule.map(f=>`<div class="math-block">\\[${f}\\]</div>`).join('')}</div>` : ''}

          <!-- Hint/Soluzione collassabili -->
          ${e.strategia && !/^n\/a$/i.test(e.strategia) ? `
            <details class="es-details" onclick="setTimeout(()=>renderMathIn(this),60)">
              <summary class="es-summary">💡 Vedi strategia</summary>
              <div class="es-hint">${processText(e.strategia)}</div>
            </details>` : ''}
          ${e.soluzione && !/^n\/a$/i.test(e.soluzione) ? `
            <details class="es-details" onclick="setTimeout(()=>renderMathIn(this),60)">
              <summary class="es-summary sol-summary">✓ Vedi soluzione completa</summary>
              <div class="es-solution">${processText(e.soluzione)}</div>
            </details>` : ''}
        </div>
      </div>
    `;
  }).join('');

  const tagHtml  = argomenti.map(a => `<span class="tag tag-v">${escHTML(a)}</span>`).join(' ');
  const diffClass = {'base':'tag-gr','medio':'tag-am','avanzato':'tag-pk'}[diff] || 'tag-am';

  return `<div class="ai-content">
    ${isExtra ? `<div class="extra-banner">📚 ${escHTML(avviso || 'Esercizi extra non ufficiali - utili per prepararsi all\'esame.')}</div>` : ''}
    <div style="display:flex;gap:8px;align-items:center;margin-bottom:16px;flex-wrap:wrap">
      <span class="tag ${diffClass}">${diff}</span>
      ${tagHtml}
    </div>
    ${intro ? `<p class="intro">${processText(intro)}</p>` : ''}
    ${esHtml}
    ${riepilogo && !/^n\/a$/i.test(riepilogo) ? `
      <div class="punti-chiave"><div class="pk-title">📝 Cosa imparare</div>
      <p style="font-size:0.83rem;color:var(--t2)">${processText(riepilogo)}</p></div>` : ''}
    <div class="ai-footer">
      <span>🤖 Generato da gemma3:12b · <a href="${REPO}" target="_blank" style="color:var(--v-l)">PoliAnalisi</a></span>
      ${reportBtn(data.nome || '', data._meta?.id || '')}
    </div>
  </div>`;
}

// =============================================
//  TEORIA
// =============================================

function renderTeoria() {
  renderFormule();
  renderTeoremi();
  renderMcLaurin();
}

function renderFormule() {
  const g = document.getElementById('formGrid');
  if (!g || g.children.length > 0) return;
  g.innerHTML = DATA.formule.map(f => `
    <div class="form-card">
      <div class="form-cat">${f.cat}</div>
      <div class="form-title">${f.titolo}</div>
      <div class="form-math">\\[${f.f}\\]</div>
      <div class="form-nota">${f.nota}</div>
    </div>
  `).join('');
}

function renderTeoremi() {
  const el = document.getElementById('teorList');
  if (!el || el.children.length > 0) return;
  el.innerHTML = DATA.teoremi.map((t, i) => `
    <div class="teorema-card" id="tc-${i}">
      <div class="teorema-head" onclick="toggleTeorema(${i})">
        <div class="teorema-icon">T</div>
        <div>
          <div class="teorema-name">${t.nome}</div>
          <div style="font-size:0.7rem;color:var(--t3);margin-top:1px">${t.arg}</div>
        </div>
        <span class="teorema-chev">▶</span>
      </div>
      <div class="teorema-body">
        <p style="margin-bottom:8px"><strong style="color:var(--v-l);font-size:0.78rem">IPOTESI</strong><br>${t.ipotesi}</p>
        <p style="margin-bottom:10px"><strong style="color:var(--c-l);font-size:0.78rem">TESI</strong><br>${t.tesi}</p>
        <p style="margin-bottom:10px"><strong style="color:var(--am);font-size:0.78rem">IDEA DIMOSTRAZIONE</strong><br>${t.idea}</p>
        <p style="font-size:0.8rem;color:var(--t3)"><strong style="font-size:0.73rem">USO PRATICO:</strong> ${t.uso}</p>
      </div>
    </div>
  `).join('');
}

function toggleTeorema(i) {
  const el = document.getElementById('tc-' + i);
  if (!el) return;
  el.classList.toggle('open');
  setTimeout(() => renderMathIn(el), 50);
}

function renderMcLaurin() {
  const el = document.getElementById('mclGrid');
  if (!el || el.children.length > 0) return;
  el.innerHTML = DATA.mclaurin.map(m => `
    <div class="mcl-row">
      <div class="mcl-fn">\\(${m.fn}\\)</div>
      <div class="mcl-eq">=</div>
      <div>\\[${m.f}\\]<div style="font-size:0.7rem;color:var(--t3);text-align:right;margin-top:4px">${m.dom}</div></div>
    </div>
  `).join('');
}

function switchTab(id, btn) {
  document.querySelectorAll('.vtab').forEach(t => t.classList.remove('active'));
  document.querySelectorAll('[id^="tab-"]').forEach(t => t.classList.add('hidden'));
  btn?.classList.add('active');
  const target = document.getElementById('tab-' + id);
  if (target) {
    target.classList.remove('hidden');
    setTimeout(() => renderMathIn(target), 80);
  }
}

// =============================================
//  QUIZ - con randomizzazione
// =============================================

const _selOpt = {};

// Costruisce l'ordine mescolato dei quiz (base + extra se disponibili)
function buildQuizOrder() {
  let allQ = [...DATA.quiz];
  // Aggiunge quiz extra se presenti (caricati dinamicamente)
  if (window._extraQuiz) allQ = allQ.concat(window._extraQuiz);

  // Fisher-Yates shuffle
  for (let i = allQ.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1));
    [allQ[i], allQ[j]] = [allQ[j], allQ[i]];
  }
  S.quizScore = 0;
  return allQ;
}

let _quizData = [];  // ordine attuale

async function renderQuiz() {
  // Tenta di caricare quiz extra generati da gemma
  if (!window._extraQuiz) {
    try {
      const r = await fetch('contenuti/quiz_extra.json?t=' + Date.now());
      if (r.ok) {
        const d = await r.json();
        window._extraQuiz = d.quiz || [];
      }
    } catch(e) {}
  }

  // Se non c'è ancora un ordine, creane uno
  if (_quizData.length === 0) {
    _quizData = buildQuizOrder();
  }

  const container = document.getElementById('quizContainer');
  if (!container) return;

  const total = _quizData.length;
  document.getElementById('qTot').textContent = total;

  container.innerHTML = _quizData.map((q, qi) => {
    const answeredOpt = S.quizAnswered[qi];
    const answered    = answeredOpt !== undefined;
    const opts = q.opts.map((o, oi) => {
      let cls = 'q-opt';
      if (answered) {
        cls += ' answered';
        if (oi === q.ok)          cls += ' correct';
        else if (oi === answeredOpt) cls += ' wrong';
      }
      return `<div class="${cls}" id="qo-${qi}-${oi}" onclick="selOpt(${qi},${oi})">
        <div class="opt-ltr">${String.fromCharCode(65 + oi)}</div>
        <div class="opt-txt">${o}</div>
      </div>`;
    }).join('');

    const diffCls  = 'diff-' + (q.dif || 'medio');
    const expShow  = answered ? 'show' : '';

    return `
      <div class="quiz-card" id="qcard-${qi}">
        <div class="q-num">
          Domanda ${qi+1} di ${total}
          <span class="diff-badge ${diffCls}">${q.dif || 'medio'}</span>
          <span style="font-size:0.66rem;color:var(--t3)">${q.arg || ''}</span>
        </div>
        <div class="q-domanda">${q.d}</div>
        <div class="q-opts">${opts}</div>
        <div class="q-exp ${expShow}" id="qexp-${qi}">💡 <strong>Spiegazione:</strong> ${q.spieg}</div>
        <div class="q-acts" id="qact-${qi}">
          ${!answered ? `<button class="btn-q btn-qc" id="qconf-${qi}" onclick="confirmOpt(${qi})" disabled>Conferma</button>` : ''}
          ${qi < total-1 ? `<button class="btn-q btn-qn" onclick="scrollToQ(${qi+1})">Prossima →</button>` : ''}
        </div>
      </div>
    `;
  }).join('');

  updateQuizUI();
  setTimeout(() => renderMathIn(container), 120);
}

function selOpt(qi, oi) {
  if (S.quizAnswered[qi] !== undefined) return;
  document.querySelectorAll(`[id^="qo-${qi}-"]`).forEach(el => el.classList.remove('selected'));
  document.getElementById(`qo-${qi}-${oi}`)?.classList.add('selected');
  _selOpt[qi] = oi;
  const btn = document.getElementById(`qconf-${qi}`);
  if (btn) btn.disabled = false;
}

function confirmOpt(qi) {
  const oi = _selOpt[qi];
  if (oi === undefined) return;
  const q = _quizData[qi];
  S.quizAnswered[qi] = oi;
  const correct = oi === q.ok;
  if (correct) S.quizScore++;

  document.querySelectorAll(`[id^="qo-${qi}-"]`).forEach((el, idx) => {
    el.classList.add('answered');
    if (idx === q.ok)          el.classList.add('correct');
    else if (idx === oi)       el.classList.add('wrong');
  });

  document.getElementById(`qexp-${qi}`)?.classList.add('show');

  const acts = document.getElementById(`qact-${qi}`);
  const total = _quizData.length;
  if (acts) {
    acts.innerHTML = `
      <div style="font-size:0.82rem;padding:5px 12px;border-radius:7px;
        ${correct
          ? 'background:var(--gr-d);color:var(--gr);border:1px solid rgba(16,185,129,0.28)'
          : 'background:var(--rd-d);color:var(--rd);border:1px solid rgba(239,68,68,0.28)'}">
        ${correct ? '✓ Corretto!' : `✗ Sbagliato - Corretta: ${String.fromCharCode(65+q.ok)}`}
      </div>
      ${qi < total-1
        ? `<button class="btn-q btn-qn" onclick="scrollToQ(${qi+1})">Prossima →</button>`
        : '<div style="font-size:0.83rem;color:var(--v-l);font-weight:600">Quiz completato! 🎉</div>'}
    `;
  }

  const expEl = document.getElementById(`qexp-${qi}`);
  if (expEl) setTimeout(() => renderMathIn(expEl), 50);

  updateQuizUI();
  saveState();
  updateStats();
  updateProgress();
  showToast(correct ? '✓ Risposta corretta!' : '✗ Sbagliata', correct ? 'green' : 'red');
}

function scrollToQ(qi) {
  document.getElementById(`qcard-${qi}`)?.scrollIntoView({ behavior: 'smooth', block: 'start' });
}

function updateQuizUI() {
  const done  = Object.keys(S.quizAnswered).length;
  const total = _quizData.length;
  const pct   = total ? done / total * 100 : 0;
  const bar   = document.getElementById('qProgBar');
  const lbl   = document.getElementById('qProgLbl');
  const score = document.getElementById('qScore');
  if (bar)   bar.style.width = pct + '%';
  if (lbl)   lbl.innerHTML   = `${done} / <span id="qTot">${total}</span>`;
  if (score) score.textContent = S.quizScore;
}

function shuffleAndReset() {
  S.quizAnswered = {};
  S.quizScore    = 0;
  _quizData      = buildQuizOrder();
  Object.keys(_selOpt).forEach(k => delete _selOpt[k]);
  saveState();
  S._rendered.quiz = false;
  document.getElementById('quizContainer').innerHTML = '';
  renderQuiz();
  showToast('🔀 Quiz mescolato!', 'violet');
}

function resetQuiz() {
  S.quizAnswered = {};
  S.quizScore    = 0;
  Object.keys(_selOpt).forEach(k => delete _selOpt[k]);
  saveState();
  S._rendered.quiz = false;
  document.getElementById('quizContainer').innerHTML = '';
  renderQuiz();
  showToast('↺ Quiz reimpostato', 'violet');
}

// =============================================
//  GRAFICI - Plotly.js
// =============================================

const GFN = {
  sin:       x => Math.sin(x),
  cos:       x => Math.cos(x),
  tan:       x => { const t = Math.tan(x); return Math.abs(t) > 30 ? NaN : t; },
  exp:       x => Math.exp(Math.min(x, 10)),
  ln:        x => x > 0 ? Math.log(x) : NaN,
  x2:        x => x * x,
  x3:        x => x * x * x,
  sinx_x:    x => Math.abs(x) < 1e-10 ? 1 : Math.sin(x) / x,
  abs:       x => Math.abs(x),
  sqrt:      x => x >= 0 ? Math.sqrt(x) : NaN,
  '1_x':     x => Math.abs(x) < 1e-10 ? NaN : 1 / x,
  sigmoid:   x => 1 / (1 + Math.exp(-x)),
  x2_minus1: x => x * x - 1,
  x3_minus_x:x => x * x * x - x,
};

const GDFN = {
  sin:        x => Math.cos(x),
  cos:        x => -Math.sin(x),
  tan:        x => 1 / Math.pow(Math.cos(x), 2),
  exp:        x => Math.exp(Math.min(x, 10)),
  ln:         x => x > 0 ? 1 / x : NaN,
  x2:         x => 2 * x,
  x3:         x => 3 * x * x,
  sinx_x:     x => Math.abs(x) < 1e-10 ? 0 : (x * Math.cos(x) - Math.sin(x)) / (x * x),
  abs:        x => x < 0 ? -1 : x > 0 ? 1 : NaN,
  sqrt:       x => x > 0 ? 0.5 / Math.sqrt(x) : NaN,
  '1_x':      x => Math.abs(x) < 1e-10 ? NaN : -1 / (x * x),
  sigmoid:    x => { const s = 1 / (1 + Math.exp(-x)); return s * (1 - s); },
  x2_minus1:  x => 2 * x,
  x3_minus_x: x => 3 * x * x - 1,
};

function linspace(a, b, n) {
  const arr = [];
  for (let i = 0; i < n; i++) arr.push(a + (b - a) * i / (n - 1));
  return arr;
}

function plotGraph() {
  const div = document.getElementById('plotlyGraph');
  if (!div || typeof Plotly === 'undefined') return;

  const fnId   = document.getElementById('graphFn')?.value || 'sin';
  const showDf = document.getElementById('showDerivative')?.checked;
  const showTg = document.getElementById('showTangent')?.checked;
  const x0Lbl = document.getElementById('x0Label');
  if (x0Lbl) x0Lbl.style.display = showTg ? 'flex' : 'none';

  const fn  = GFN[fnId];
  const dfn = GDFN[fnId];

  // Range automatico smart
  let xMin = -8, xMax = 8;
  if (fnId === 'ln' || fnId === 'sqrt') { xMin = 0.01; xMax = 10; }
  if (fnId === 'sigmoid') { xMin = -6; xMax = 6; }

  const xs = linspace(xMin, xMax, 1200);
  const ys = xs.map(x => { const y = fn(x); return Math.abs(y) > 500 ? NaN : y; });

  const traces = [];

  // Funzione principale
  traces.push({
    x: xs, y: ys,
    mode: 'lines',
    name: `f(x)`,
    line: { color: '#7c3aed', width: 2.5, shape: 'spline' },
    hovertemplate: 'x=%{x:.3f}<br>f(x)=%{y:.4f}<extra></extra>',
  });

  // Derivata
  if (showDf) {
    const dys = xs.map(x => { const y = dfn(x); return Math.abs(y) > 500 ? NaN : y; });
    traces.push({
      x: xs, y: dys,
      mode: 'lines',
      name: `f'(x)`,
      line: { color: '#06b6d4', width: 2, dash: 'dot', shape: 'spline' },
      hovertemplate: "x=%{x:.3f}<br>f'(x)=%{y:.4f}<extra></extra>",
    });
  }

  // Tangente
  if (showTg) {
    const x0Raw = parseInt(document.getElementById('x0Slider')?.value || '0');
    const x0    = x0Raw / 10;
    document.getElementById('x0Val').textContent = x0.toFixed(1);
    const y0  = fn(x0);
    const dy0 = dfn(x0);

    if (isFinite(y0) && isFinite(dy0)) {
      const tYs = xs.map(x => dy0 * (x - x0) + y0);
      traces.push({
        x: xs, y: tYs,
        mode: 'lines',
        name: `Tangente x₀=${x0.toFixed(1)}`,
        line: { color: '#f59e0b', width: 1.8, dash: 'dash' },
      });
      traces.push({
        x: [x0], y: [y0],
        mode: 'markers',
        name: `P(${x0.toFixed(1)}, ${y0.toFixed(3)})`,
        marker: { color: '#f59e0b', size: 10, symbol: 'circle',
          line: { color: '#fff', width: 2 } },
        hovertemplate: `x=${x0.toFixed(3)}<br>f(x)=${y0.toFixed(4)}<extra></extra>`,
      });

      const info = document.getElementById('graphInfo');
      if (info) info.innerHTML = `
        Tangente in x₀ = ${x0.toFixed(2)}: &nbsp;
        <strong style="color:var(--am)">y = ${dy0.toFixed(3)}(x &minus; ${x0.toFixed(1)}) + ${y0.toFixed(3)}</strong>
        &nbsp;&nbsp;|&nbsp;&nbsp; f'(x₀) = ${dy0.toFixed(4)}
      `;
    }
  } else {
    const info = document.getElementById('graphInfo');
    if (info) info.textContent = '';
  }

  const layout = {
    paper_bgcolor: '#0d0e17',
    plot_bgcolor:  '#0d0e17',
    font: { family: 'Inter, sans-serif', color: 'rgba(255,255,255,0.65)', size: 12 },
    xaxis: {
      gridcolor: 'rgba(255,255,255,0.07)',
      zerolinecolor: 'rgba(255,255,255,0.2)',
      zerolinewidth: 1.5,
      tickcolor: 'rgba(255,255,255,0.2)',
      range: [xMin, xMax],
    },
    yaxis: {
      gridcolor: 'rgba(255,255,255,0.07)',
      zerolinecolor: 'rgba(255,255,255,0.2)',
      zerolinewidth: 1.5,
      tickcolor: 'rgba(255,255,255,0.2)',
      autorange: true,
    },
    legend: {
      bgcolor: 'rgba(13,14,23,0.8)',
      bordercolor: 'rgba(255,255,255,0.12)',
      borderwidth: 1,
      font: { size: 11 },
    },
    margin: { l: 50, r: 20, t: 20, b: 50 },
    hovermode: 'closest',
    dragmode: 'pan',
    shapes: [
      // Zero crossing highlight
      { type: 'line', x0: xMin, x1: xMax, y0: 0, y1: 0,
        line: { color: 'rgba(255,255,255,0.15)', width: 1 } },
    ],
  };

  const config = {
    responsive: true,
    displayModeBar: true,
    displaylogo: false,
    modeBarButtons: [['pan2d', 'zoom2d', 'autoScale2d', 'resetScale2d', 'toImage']],
    scrollZoom: true,
  };

  if (div._hasPlot) {
    Plotly.react(div, traces, layout, config);
  } else {
    Plotly.newPlot(div, traces, layout, config);
    div._hasPlot = true;
  }
}

function updateX0() {
  plotGraph();
}

// =============================================
//  SEARCH
// =============================================

let _searchResults = [];

function openSearch() {
  const ov = document.getElementById('searchOverlay');
  if (ov) { ov.classList.add('open'); S.searchOpen = true; }
  const inp = document.getElementById('searchInput');
  if (inp) { inp.value = ''; inp.focus(); inp.oninput = () => renderSearch(inp.value); renderSearch(''); }
}

function handleSearchOverlayClick(e) {
  if (e.target === document.getElementById('searchOverlay')) closeSearch();
}

function closeSearch() {
  document.getElementById('searchOverlay')?.classList.remove('open');
  S.searchOpen = false;
}

function renderSearch(q) {
  const res = document.getElementById('searchResults');
  if (!res) return;
  const qn = q.toLowerCase().trim();
  if (!qn) { res.innerHTML = '<div class="sr-empty">Inizia a digitare per cercare…</div>'; return; }
  _searchResults = [];

  DATA.lezioni.forEach(l => {
    if (l.titolo.toLowerCase().includes(qn) || l.desc.toLowerCase().includes(qn) ||
        l.concetti.some(c => c.toLowerCase().includes(qn))) {
      _searchResults.push({
        icon: '📚', title: l.id + ' - ' + l.titolo, sub: l.argLabel,
        action: () => openContent(l.json, l.pdf, l.id + ' - ' + l.titolo, 'lezione', JSON.stringify(l))
      });
    }
  });

  DATA.settimane.forEach(s => {
    s.esercizi.forEach(e => {
      if (e.nome.toLowerCase().includes(qn)) {
        _searchResults.push({
          icon: '📝', title: e.nome, sub: s.titolo,
          action: () => openContent(e.json, e.pdf, e.nome, 'esercizio', '')
        });
      }
    });
  });

  DATA.argomenti.filter(a => a.id !== 'tutti').forEach(a => {
    if (a.label.toLowerCase().includes(qn)) {
      _searchResults.push({
        icon: a.icon, title: a.label, sub: 'Argomento',
        action: () => goArg(a.id)
      });
    }
  });

  if (!_searchResults.length) {
    res.innerHTML = `<div class="sr-empty">Nessun risultato per "<strong>${escHTML(qn)}</strong>"</div>`;
    return;
  }

  res.innerHTML = _searchResults.slice(0, 10).map((r, i) => `
    <div class="sr-item" onclick="clickSearch(${i})">
      <span class="sr-icon">${r.icon}</span>
      <div><div class="sr-title">${escHTML(r.title)}</div><div class="sr-sub">${escHTML(r.sub)}</div></div>
    </div>
  `).join('');
}

function clickSearch(i) {
  closeSearch();
  setTimeout(() => _searchResults[i]?.action(), 80);
}

// =============================================
//  TOAST
// =============================================

let _toastTO;

function showToast(msg, col = 'violet') {
  const t = document.getElementById('toast');
  const m = document.getElementById('toastMsg');
  if (!t || !m) return;
  clearTimeout(_toastTO);
  m.textContent = msg;
  const cols = {
    violet: 'var(--border-a)', green: 'rgba(16,185,129,0.4)',
    red: 'rgba(239,68,68,0.4)', cyan: 'rgba(6,182,212,0.4)', amber: 'rgba(245,158,11,0.4)'
  };
  t.style.borderColor = cols[col] || cols.violet;
  t.classList.add('show');
  _toastTO = setTimeout(() => t.classList.remove('show'), 3200);
}

// =============================================
//  UTILS
// =============================================

function escHTML(s) {
  return String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
}

/**
 * processText - converte testo misto LaTeX in HTML sicuro.
 * Preserva gli spazi attorno alle formule \(...\).
 */
function processText(s) {
  if (!s) return '';
  s = String(s);
  const parts = [];
  const re = /(\\\\?\[[^\]]*?\\\\?\]|\\\\?\([^\)]*?\\\\?\))/g;
  // Più robusto: dividi su \[...\] e \(...\)
  const re2 = /(\\\[[^\]]{0,500}?\\\]|\\\([^\)]{0,300}?\\\))/g;
  let last = 0, m;
  while ((m = re2.exec(s)) !== null) {
    if (m.index > last) parts.push({ type: 'text', val: s.slice(last, m.index) });
    const isDisplay = m[0].startsWith('\\[');
    parts.push({ type: isDisplay ? 'display' : 'inline', val: m[0] });
    last = m.index + m[0].length;
  }
  if (last < s.length) parts.push({ type: 'text', val: s.slice(last) });

  return parts.map(p => {
    if (p.type === 'text') return escHTML(p.val);
    if (p.type === 'display') return `<span class="math-display-wrap">${p.val}</span>`;
    const inner = p.val.slice(2, -2).trim();
    return `<span class="math-iw">\\(${inner}\\)</span>`;
  }).join('');
}

function esc(s) {
  return String(s).replace(/'/g, "\\'").replace(/"/g, '&quot;').replace(/\n/g, ' ');
}

function encodePath(p) {
  return p.split('/').map(encodeURIComponent).join('/');
}

// =============================================
//  KEYBOARD
// =============================================

document.addEventListener('keydown', e => {
  if (e.key === 'Escape') {
    if (document.getElementById('viewerModal')?.classList.contains('open')) closeViewer();
    else if (S.searchOpen) closeSearch();
  }
  if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
    e.preventDefault();
    openSearch();
  }
});

// =============================================
//  RESIZE
// =============================================

const ro = new ResizeObserver(() => {
  if (S.view === 'grafici' && typeof Plotly !== 'undefined') {
    const div = document.getElementById('plotlyGraph');
    if (div && div._hasPlot) Plotly.relayout(div, {});
  }
});

// =============================================
//  INIT
// =============================================

document.addEventListener('DOMContentLoaded', () => {
  loadState();
  renderHome();
  ro.observe(document.querySelector('.main') || document.body);
  setTimeout(() => updateAIBadge(), 600);
});
