"""Aplica no generate.py a foto automatica de reserva (idempotente)."""
s = open("generate.py", encoding="utf-8").read()
if "def auto_photo" not in s:
    OLD = 'def render_cover(s, brand, n, total):\n    photo = s.get("photo")\n    ppath = os.path.join("photos", photo) if photo else None\n    if ppath and os.path.exists(ppath):\n        img = cover_photo(ppath, float(s.get("photo_fx", 0.5)), float(s.get("photo_fy", 0.3))).convert("RGBA")\n    else:\n        img = background()\n'
    NEW = 'def auto_photo(key):\n    """Escolhe uma foto do catalogo de forma estavel pelo nome do set."""\n    try:\n        cat = json.load(open("photos_catalog.json", encoding="utf-8"))["photos"]\n        cat = [c for c in cat if os.path.exists(os.path.join("photos", "%02d.jpg" % c["n"]))]\n        c = cat[sum(ord(ch) * (i + 1) for i, ch in enumerate(key)) % len(cat)]\n        return os.path.join("photos", "%02d.jpg" % c["n"]), c.get("face_y", 0.3)\n    except Exception as e:\n        print("AVISO auto_photo:", e)\n        return None, 0.3\n\n\ndef render_cover(s, brand, n, total):\n    photo = s.get("photo")\n    ppath = os.path.join("photos", str(photo)) if photo else None\n    fx, fy = float(s.get("photo_fx", 0.5)), s.get("photo_fy")\n    if not (ppath and os.path.exists(ppath)):\n        ppath, auto_fy = auto_photo(s.get("_set", ""))\n        if fy is None:\n            fy = auto_fy\n        print("AVISO: foto ausente no spec, usando automatica", ppath)\n    if fy is None:\n        fy = 0.3\n    if ppath and os.path.exists(ppath):\n        img = cover_photo(ppath, fx, float(fy)).convert("RGBA")\n    else:\n        print("AVISO: sem nenhuma foto disponivel, capa em gradiente")\n        img = background()\n'
    assert OLD in s
    s = s.replace(OLD, NEW, 1)
    s = s.replace('        im = fn(s, brand, i, total)', '        s["_set"] = name\n        im = fn(s, brand, i, total)')
    open("generate.py", "w", encoding="utf-8").write(s)
    print("generate.py atualizado com auto_photo")
