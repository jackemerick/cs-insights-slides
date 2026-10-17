"""Gerador de slides do carrossel (Instagram) - Jack Emerick Insights.
Uso: python generate.py [--all]   (renderiza specs/*.json que ainda nao tem pasta em out/)

Campos do spec (por slide):
  kicker, title, body, foot            textos (titulo sem ponto final: o gerador remove)
  photo, photo_fx, photo_fy            so no slide 1: foto de fundo (arquivo em photos/) e foco (0 a 1)
  box_pos                              slide 1: "bottom" (padrao) ou "top"
  chart {type bar|line, title, labels[], values[], unit, hi, note}   grafico no slide
  cta, cta_sub                         botao de chamada para acao (ultimo slide)
Topo do spec: linkedin_image {kicker,title,chart,foot} gera out/<set>/linkedin.jpg (1080x1350)
"""
import os, sys, json, glob
from PIL import Image, ImageDraw, ImageFont, ImageOps

W, H, M = 1080, 1350, 96
# Paleta (um unico lugar para trocar as cores)
NAVY, ORANGE, WHITE, SOFT = (16, 30, 50), (192, 123, 68), (255, 255, 255), (201, 209, 219)
PANEL, BAR = (27, 47, 76), (84, 110, 150)
FD = os.environ.get("FONT_DIR", "fonts")
BRAND_DEFAULT = "Jack Emerick Insights"


def inter(weight, size):
    return ImageFont.truetype(os.path.join(FD, f"Inter-{weight}.otf"), size)


def bebas(size):
    return ImageFont.truetype(os.path.join(FD, "BebasNeue-Regular.ttf"), size)


def wrap(d, text, fnt, max_w):
    lines = []
    for para in text.split("\n"):
        cur = ""
        for w in para.split(" "):
            t = (cur + " " + w).strip()
            if d.textlength(t, font=fnt) <= max_w:
                cur = t
            else:
                if cur:
                    lines.append(cur)
                cur = w
        lines.append(cur)
    return lines


def draw_lines(d, lines, fnt, x, y, fill, lh):
    for ln in lines:
        d.text((x, y), ln, font=fnt, fill=fill)
        y += lh
    return y


def spaced(d, xy, text, fnt, fill, ls):
    x, y = xy
    for ch in text:
        d.text((x, y), ch, font=fnt, fill=fill)
        x += d.textlength(ch, font=fnt) + ls
    return x


def spaced_w(d, text, fnt, ls):
    return sum(d.textlength(c, font=fnt) + ls for c in text) - ls


def clean_title(t):
    return t.strip().rstrip(". ").strip()


def fit_text(d, text, make_font, w, max_h, start, minimum, lh, step=2, max_lines=None):
    size = start
    while True:
        f = make_font(size)
        lines = wrap(d, text, f, w)
        h = len(lines) * int(size * lh)
        ok = h <= max_h and (max_lines is None or len(lines) <= max_lines)
        if ok or size <= minimum:
            return f, lines, int(size * lh), size
        size -= step


# ---------- elementos ----------
def vtag(img, brand):
    f = inter("SemiBold", 19)
    tmp = Image.new("RGBA", (900, 34), (0, 0, 0, 0))
    td = ImageDraw.Draw(tmp, "RGBA")
    tw = spaced_w(td, brand.upper(), f, 4)
    spaced(td, (0, 4), brand.upper(), f, SOFT + (175,), 4)
    tmp = tmp.crop((0, 0, int(tw) + 4, 34)).rotate(90, expand=True)
    x, y = 26, H - 56 - tmp.height
    img.alpha_composite(tmp, (x, y))
    ImageDraw.Draw(img, "RGBA").rectangle([x + 12, y - 46, x + 14, y - 10], fill=ORANGE + (230,))


def fmt(v, unit):
    s = f"{v:g}".replace(".", ",")
    return s + unit


def draw_chart(img, c, box):
    x0, y0, x1, y1 = box
    d = ImageDraw.Draw(img, "RGBA")
    d.rectangle([x0, y0, x1, y1], fill=PANEL + (255,))
    d.rectangle([x0, y0, x0 + 6, y1], fill=ORANGE + (255,))
    pad = 34
    ft = inter("SemiBold", 26)
    title = c.get("title", "")
    d.text((x0 + pad, y0 + 24), title, font=ft, fill=SOFT)
    if c.get("note"):
        fn = inter("Medium", 20)
        nw = d.textlength(c["note"], font=fn)
        if x0 + pad + d.textlength(title, font=ft) + nw + 30 < x1 - pad:
            d.text((x1 - pad - nw, y0 + 28), c["note"], font=fn, fill=ORANGE)
        else:
            d.text((x0 + pad, y0 + 60), c["note"], font=fn, fill=ORANGE)
    labels, vals, unit = c["labels"], c["values"], c.get("unit", "")
    n = len(vals)
    hi = c.get("hi", n - 1)
    top, bottom = y0 + 130, y1 - 62
    left, right = x0 + pad + 8, x1 - pad - 8
    vmax = max(vals) if max(vals) > 0 else 1
    fv, fl = bebas(52), inter("Medium", 23)
    slot = (right - left) / n
    pts = []
    for i, v in enumerate(vals):
        cx = left + slot * (i + 0.5)
        hgt = (bottom - top) * (v / vmax) if c.get("type", "bar") == "bar" else (bottom - top) * (0.15 + 0.85 * (v / vmax))
        yv = bottom - hgt
        col = ORANGE if i == hi else BAR
        if c.get("type", "bar") == "bar":
            bw = min(slot * 0.58, 150)
            d.rectangle([cx - bw / 2, yv, cx + bw / 2, bottom], fill=col + (255,))
        else:
            pts.append((cx, yv))
        txt = fmt(v, unit)
        tw = d.textlength(txt, font=fv)
        d.text((cx - tw / 2, yv - 62), txt, font=fv, fill=WHITE if i == hi else SOFT)
        lab = labels[i]
        lw = d.textlength(lab, font=fl)
        while lw > slot - 8 and len(lab) > 3:
            lab = lab[:-2]
            lw = d.textlength(lab + ".", font=fl)
        if lab != labels[i]:
            lab += "."
        lw = d.textlength(lab, font=fl)
        d.text((cx - lw / 2, bottom + 16), lab, font=fl, fill=SOFT)
    if pts:
        d.line(pts, fill=BAR + (255,), width=6, joint="curve")
        for i, (px, py) in enumerate(pts):
            r = 11 if i == hi else 8
            d.ellipse([px - r, py - r, px + r, py + r], fill=(ORANGE if i == hi else BAR) + (255,))
    d.line([left - 6, bottom, right + 6, bottom], fill=SOFT + (110,), width=2)


def cover_photo(path, fx, fy):
    p = ImageOps.exif_transpose(Image.open(path)).convert("RGB")
    s = max(W / p.width, H / p.height)
    p = p.resize((int(p.width * s) + 1, int(p.height * s) + 1), Image.LANCZOS)
    cx, cy = fx * p.width, fy * p.height
    l = int(max(0, min(p.width - W, cx - W / 2)))
    t = int(max(0, min(p.height - H, cy - H * 0.38)))
    return p.crop((l, t, l + W, t + H))


# ---------- slides ----------
def render_cover(s, brand):
    photo = s.get("photo")
    ppath = os.path.join("photos", photo) if photo else None
    if ppath and os.path.exists(ppath):
        bg = cover_photo(ppath, float(s.get("photo_fx", 0.5)), float(s.get("photo_fy", 0.3))).convert("RGBA")
    else:
        bg = Image.new("RGBA", (W, H), NAVY + (255,))
    img = bg
    # escurece levemente a foto toda e reforca topo e base (leitura)
    shade = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    sd = ImageDraw.Draw(shade)
    for y in range(H):
        a = 40
        if y < 330:
            a += int(120 * (1 - y / 330))
        if y > H - 520:
            a += int(110 * (y - (H - 520)) / 520)
        sd.line([(0, y), (W, y)], fill=NAVY + (min(a, 220),))
    img.alpha_composite(shade)
    d = ImageDraw.Draw(img, "RGBA")
    # masthead de revista
    fm = bebas(112)
    mt = brand.upper()
    ls = 10
    mw = spaced_w(d, mt, fm, ls)
    while mw > W - 2 * 60 and fm.size > 60:
        fm = bebas(fm.size - 4)
        mw = spaced_w(d, mt, fm, ls)
    spaced(d, ((W - mw) / 2, 58), mt, fm, WHITE + (245,), ls)
    d.rectangle([60, 58 + int(fm.size * 1.02) + 14, W - 60, 58 + int(fm.size * 1.02) + 17], fill=ORANGE + (255,))
    fs = inter("SemiBold", 21)
    sub = "CUSTOMER SUCCESS  ·  MERCADO  ·  CLIENTES"
    sw = spaced_w(d, sub, fs, 5)
    d.text(((W - sw) / 2, 58 + int(fm.size * 1.02) + 32), "", font=fs, fill=SOFT)
    spaced(d, ((W - sw) / 2, 58 + int(fm.size * 1.02) + 32), sub, fs, SOFT + (235,), 5)
    # caixa de texto (canto reto, fundo translucido)
    bx0, bx1 = 60, W - 60
    pad = 50
    inner = bx1 - bx0 - 2 * pad
    title = clean_title(s["title"]).upper()
    body = s.get("body", "")
    kick = s.get("kicker", "").upper()
    max_box_h = 800
    size = 168
    while True:
        ft = bebas(size)
        tl = wrap(d, title, ft, inner)
        fb = inter("Regular", 38)
        bl = wrap(d, body, fb, inner)
        th = len(tl) * int(size * 0.98)
        bh = len(bl) * int(38 * 1.38)
        total = 40 + 34 + 26 + th + 22 + bh + 34 + 44
        if (total <= max_box_h and len(tl) <= 5) or size <= 84:
            break
        size -= 6
    box_h = total
    if s.get("box_pos", "bottom") == "top":
        by0 = 340
    else:
        by0 = H - 70 - box_h
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ld = ImageDraw.Draw(layer)
    ld.rectangle([bx0, by0, bx1, by0 + box_h], fill=NAVY + (178,))
    ld.rectangle([bx0, by0, bx1, by0 + 7], fill=ORANGE + (255,))
    img.alpha_composite(layer)
    d = ImageDraw.Draw(img, "RGBA")
    y = by0 + 40
    spaced(d, (bx0 + pad, y), kick, inter("SemiBold", 26), ORANGE, 3)
    y += 34 + 26
    y = draw_lines(d, tl, ft, bx0 + pad, y, WHITE, int(size * 0.98)) + 22
    y = draw_lines(d, bl, fb, bx0 + pad, y, SOFT, int(38 * 1.38))
    fa = inter("SemiBold", 24)
    at = "ARRASTE PARA O LADO  ›"
    d.text((bx1 - pad - d.textlength(at, font=fa), by0 + box_h - 50), at, font=fa, fill=ORANGE)
    return img.convert("RGB")


def render_content(s, brand, last):
    img = Image.new("RGBA", (W, H), NAVY + (255,))
    d = ImageDraw.Draw(img, "RGBA")
    d.rectangle([M, 96, M + 90, 102], fill=ORANGE)
    d.text((M, 122), s.get("kicker", "").upper(), font=inter("SemiBold", 28), fill=SOFT)
    title = clean_title(s["title"]).upper()
    body = s.get("body", "")
    has_chart = bool(s.get("chart"))
    cta = s.get("cta")
    foot = s.get("foot")
    inner = W - M - 70
    ft, tl, tlh, tsize = fit_text(d, title, bebas, inner, 3 * 140, 124, 72, 1.0, step=6, max_lines=3)
    y = 190
    y = draw_lines(d, tl, ft, M, y, ORANGE, tlh) + 30
    # limites inferiores
    foot_gap = 40 if foot else 0
    cta_block = (cta_h_ := 130) + (70 if s.get("cta_sub") else 30) if cta else 0
    free_total = H - 120 - foot_gap - cta_block - y
    if has_chart and not body.strip():
        chart_h = min(760, free_total - 10)
        fb, bl, blh, bsize = inter("Regular", 40), [], 0, 40
    elif has_chart:
        for chart_h in (500, 450, 400, 350, 310):
            avail = free_total - chart_h - 34
            fb, bl, blh, bsize = fit_text(d, body, lambda z: inter("Regular", z), inner, avail, 48, 30, 1.38)
            if bsize >= 38 or chart_h == 310:
                break
    else:
        chart_h = 0
        fb, bl, blh, bsize = fit_text(d, body, lambda z: inter("Regular", z), inner, free_total, 62, 30, 1.38)
    cta_h = 130
    y = draw_lines(d, bl, fb, M, y, WHITE, blh)
    if has_chart:
        cy1 = H - 120 - (40 if foot else 0) - ((cta_h + (70 if s.get("cta_sub") else 30)) if cta else 0)
        draw_chart(img, s["chart"], (M, cy1 - chart_h, W - 70, cy1))
    if cta:
        by1 = H - 120 - (40 if foot else 0) - (70 if s.get("cta_sub") else 30) + 0
        by0 = by1 - cta_h
        d = ImageDraw.Draw(img, "RGBA")
        d.rectangle([M, by0, W - 70, by1], fill=ORANGE + (255,))
        fc, cl, clh, _ = fit_text(d, cta.upper(), bebas, W - 70 - M - 60, cta_h - 24, 78, 44, 1.0, step=4, max_lines=1)
        cw = d.textlength(cl[0], font=fc)
        d.text((M + (W - 70 - M - cw) / 2, by0 + (cta_h - fc.size * 1.0) / 2 - 2), cl[0], font=fc, fill=NAVY)
        if s.get("cta_sub"):
            fs = inter("Medium", 27)
            sw = d.textlength(s["cta_sub"], font=fs)
            d.text((M + (W - 70 - M - sw) / 2, by1 + 20), s["cta_sub"], font=fs, fill=SOFT)
    d = ImageDraw.Draw(img, "RGBA")
    if foot:
        d.text((M, H - 100), foot, font=inter("Medium", 25), fill=SOFT)
    vtag(img, brand)
    return img.convert("RGB")


def render(spec_path):
    spec = json.load(open(spec_path, encoding="utf-8"))
    name = spec["set"]
    brand = spec.get("brand", BRAND_DEFAULT)
    out = os.path.join("out", name)
    os.makedirs(out, exist_ok=True)
    slides = spec["slides"]
    for i, s in enumerate(slides, 1):
        im = render_cover(s, brand) if i == 1 else render_content(s, brand, i == len(slides))
        im.save(os.path.join(out, f"slide_{i:02d}.jpg"), "JPEG", quality=90, optimize=True)
        print("ok", name, i)
    li = spec.get("linkedin_image")
    if li:
        im = render_content(dict(li), brand, False)
        im.save(os.path.join(out, "linkedin.jpg"), "JPEG", quality=92, optimize=True)
        print("ok", name, "linkedin")


if __name__ == "__main__":
    for p in sorted(glob.glob("specs/*.json")):
        nm = json.load(open(p, encoding="utf-8"))["set"]
        if not os.path.isdir(os.path.join("out", nm)) or "--all" in sys.argv:
            render(p)
