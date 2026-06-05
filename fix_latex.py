import json, glob, re
from pathlib import Path

def fix_string(s):
    if not isinstance(s, str):
        return s
    
    # Fix swallowed escapes
    s = s.replace("\x0crac", "\\frac")
    s = s.replace("\x09ext{", "\\text{")
    s = s.replace("\x09o ", "\\to ")
    s = s.replace("\x09o_", "\\to_")
    s = s.replace("\x09o^", "\\to^")
    s = s.replace("\x09heta", "\\theta")
    s = s.replace("\x08inom", "\\binom")
    s = s.replace("\x08eta", "\\beta")
    s = s.replace("\nint", "\\nint") # wait, \n is a real newline. If it was \noindent, it would be \noindent.
    s = s.replace("\x0ce", "\\fe") # \f is formfeed
    
    # Fix missing braces or bad syntax we saw
    s = s.replace("∫ f(x) dx", "\\int f(x) \, dx")
    s = s.replace("∫(px/x²) dx = ∫p/x dx", "\\int \\frac{px}{x^2} \\, dx = \\int \\frac{p}{x} \\, dx")
    s = s.replace("√(x² + y²)", "\\sqrt{x^2 + y^2}")
    s = s.replace("lim n→∞", "\\lim_{n \\to \\infty}")
    s = s.replace("lim (n→∞)", "\\lim_{n \\to \\infty}")
    s = s.replace("lim_(x→∞)", "\\lim_{x \\to \\infty}")
    s = s.replace("lim (x->a)", "\\lim_{x \\to a}")
    s = s.replace("lim (x->+∞)", "\\lim_{x \\to +\\infty}")
    s = s.replace("lim_{h->0}", "\\lim_{h \\to 0}")
    s = s.replace("lim y→0", "\\lim_{y \\to 0}")
    s = s.replace("e^(-x)", "e^{-x}")
    s = s.replace("eˣ", "e^x")
    s = s.replace("O(x²)", "O(x^2)")
    
    return s

def traverse_and_fix(obj):
    if isinstance(obj, dict):
        for k, v in obj.items():
            if isinstance(v, str):
                obj[k] = fix_string(v)
            else:
                traverse_and_fix(v)
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            if isinstance(v, str):
                obj[i] = fix_string(v)
            else:
                traverse_and_fix(v)

for f in Path("contenuti").glob("*.json"):
    try:
        with open(f, "r", encoding="utf-8") as file:
            data = json.load(file)
        
        traverse_and_fix(data)
        
        with open(f, "w", encoding="utf-8") as file:
            json.dump(data, file, ensure_ascii=False, indent=2)
    except Exception as e:
        print("Error on", f, e)

print("Latex formats fixed!")
