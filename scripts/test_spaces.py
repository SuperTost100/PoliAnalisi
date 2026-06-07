import re

samples = [
    "f(x) = $ cos x $ è soluzione",
    "$ (y')^2 - y^2 = 1 $",
    "L'integrale $ \\int_0^1 x dx $ e poi $f(x)$",
    "Opzione $ y = 1 $"
]

for s in samples:
    # Matchiamo un blocco $ ... $ e rimuoviamo gli spazi adiacenti ai dollari all'interno
    # \$ = $ letterale
    # \s* = spazi opzionali
    # (.*?) = contenuto
    # \s* = spazi opzionali
    # \$ = $ letterale
    # Se il contenuto NON ha dollari al suo interno
    s_new = re.sub(r'\$\s*([^\$]*?)\s*\$', r'$\1$', s)
    print(s_new)
