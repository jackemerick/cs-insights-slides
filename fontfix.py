"""Capa em DM Serif Display (mais legivel sobre foto). Idempotente."""
s = open("generate.py", encoding="utf-8").read()
if "DMSerifDisplay" not in s:
    OLD = '    return _font("BodoniModa-Italic.ttf" if italic else "BodoniModa.ttf", size, [wght, 30])'
    NEW = '    return _font_plain("DMSerifDisplay-Regular.ttf", size)'
    assert OLD in s
    s = s.replace(OLD, NEW, 1).replace("em_scale = 1.5", "em_scale = 1.25")
    open("generate.py", "w", encoding="utf-8").write(s)
    print("generate.py atualizado com DM Serif Display")
