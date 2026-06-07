import re

samples = [
    "f(x) = cos x `e soluzione dell’equazione differenziale:",
    "\\lim\\_{x→4}\\frac{5}{1 −cos(5x −4)} \\cdot \\frac{(x −4)}{5^2} =",
    "Quale `e la derivata prima della funzione f(x) = log(cos x):",
    "L’insieme A = \\left\\{\\-n/(n+5), n = 0, 1, 2, ...\\right\\} \\cup\\{-3} ha",
    "Sia data la funzione f : \\mathbb{R} →\\mathbb{R} tale che se x →+∞→f(x) ∼log x allora:",
    "L’integrale I = \\int_{0}^{1} \\frac{\\sin t}{t^{\\alpha}} dt = +∞ se: e x - ∞",
    "Il dominio della funzione f(x) è D = [0, 1]"
]

def smart_wrap(s):
    s = s.replace("`e", "è").replace("`", "'")
    
    # 1. Troviamo tutte le sequenze di parole testuali.
    # Una "parola testuale" è una sequenza di lettere. 
    # Vogliamo ignorare: f, x, y, z, n, t, dt, dx, dy, i (come numero immaginario) se sono da sole.
    # Ma vogliamo prendere: è, e, a, o, i, il, la se sono dentro una frase.
    
    # Invece di regex complessa, facciamo un replace delle funzioni note per proteggerle:
    s = s.replace("cos", "\\cos").replace("sin", "\\sin").replace("tan", "\\tan").replace("log", "\\log").replace("ln", "\\ln")
    # fix double backslashes
    s = s.replace("\\\\cos", "\\cos").replace("\\\\sin", "\\sin")
    
    # Ora la regex per il testo:
    # Matchiamo sequenze di lettere che NON sono f,x,y,z isolate.
    # E' più facile: prendiamo sequenze di 2+ lettere, o 1 lettera accentata (è, à).
    # E le parole di 1 lettera non accentate le prendiamo solo se adiacenti a spazi.
    
    # Usiamo una regex semplice: prendiamo tutto ciò che è composto da lettere [a-zA-Zàèéìòù\'’]
    # lunghe almeno 2, e "è".
    
    s_new = re.sub(r'(?<![\\a-zA-Z])([a-zA-Zàèéìòù\'’]{2,}|è)(?![a-zA-Z])', r'\\text{\1}', s)
    
    # Sistemiamo gli spazi tra blocchi \text{}
    s_new = re.sub(r'\} \{', '} \\text{ } \\text{', s_new)
    # Oppure molto meglio, facciamo il join
    s_new = re.sub(r'\}\s+\\text\{', ' ', s_new)
    
    return f"$ {s_new} $"

for s in samples:
    print(smart_wrap(s))
