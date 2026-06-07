import re

samples = [
    "f(x) = cos x `e soluzione dell’equazione differenziale:",
    "\\lim\\_{x→4}\\frac{5}{1 −cos(5x −4)} \\cdot \\frac{(x −4)}{5^2} =",
    "Quale `e la derivata prima della funzione f(x) = log(cos x):",
    "L’insieme A = \\left\\{\\-n/(n+5), n = 0, 1, 2, ...\\right\\} \\cup\\{-3} ha",
    "Sia data la funzione f : \\mathbb{R} →\\mathbb{R} tale che se x →+∞→f(x) ∼log x allora:",
    "Se l'integrale converge allora",
    "Il dominio della funzione è"
]

def smart_wrap(s):
    # Sostituiamo `e con è
    s = s.replace("`e", "è")
    
    # Split text blocks vs math blocks
    # Un blocco di testo è:
    # Inizia con limite di parola o spazio, contiene lettere italiane, apostrofi, virgole, punti, due punti, punti interrogativi.
    # NON contiene +, -, =, ^, _, \, /, {, }, [, ], (, ), numeri.
    # Ma "f(x)" o "cos x" contengono lettere. Se usiamo una regex che estrae solo parole:
    
    # regex per parola singola pura: non preceduta da \ e non parte di f(x)
    # È difficile.
    pass

