import re

samples = [
    "f(x) = cos x `e soluzione dell’equazione differenziale:",
    "\\lim\\_{x→4}\\frac{5}{1 −cos(5x −4)} \\cdot \\frac{(x −4)}{5^2} =",
    "Quale `e la derivata prima della funzione f(x) = log(cos x):",
    "L’insieme A = \\left\\{\\-n/(n+5), n = 0, 1, 2, ...\\right\\} \\cup\\{-3} ha",
    "Sia data la funzione f : \\mathbb{R} →\\mathbb{R} tale che se x →+∞→f(x) ∼log x allora:",
    "L’integrale I = \\int_{0}^{1} \\frac{\\sin t}{t^{\\alpha}} dt = +∞ se: e x - ∞"
]

for s in samples:
    s_new = re.sub(r'(?<![\\a-zA-Z])([a-zA-Zàèéìòù\'’]{2,})(?![a-zA-Z])', r'\\text{\1}', s)
    print(f"$ {s_new} $")
