"""Gerador de slides do carrossel (Instagram) - Jack Emerick Insights.
Uso: python generate.py [--all]   (renderiza specs/*.json que ainda nao tem pasta em out/)

Design: editorial escuro. Titulos em Bodoni Moda (palavra de destaque em italico laranja),
textos em Archivo. Foto de fundo SOMENTE no slide 1.

Spec: {"set": "...", "brand": "...", "slides": [ ... ]}
Tipos de slide (campo "type", se faltar: tem chart -> chart, tem cta -> cta, senao content; slide 1 e sempre capa):
  cover    kicker (ignorado), title, body (subtitulo), photo, photo_fx, photo_fy
  content  title, body                              (o tipo principal: texto)
  stat     title, stat ("5,3%"), body, note
  chart    title, body (subtitulo), chart {...}, insight (frase de fechamento)
  cta      title, body, cta (texto da chamada: UMA unica acao)
Slide 1: Bodoni/Archivo. Slides 2+: Bebas (titulo laranja) e Inter. Sem tags nem paginacao; marca d'agua discreta.
Destaques: em titulos use *palavra* (italico laranja); em textos use **trecho** (negrito laranja).
Graficos (chart.type): bar (colunas) | hbar (ranking horizontal) | line | donut
  bar/hbar: labels[], values[], unit, hi (indice destacado), max (opcional, so hbar)
  line:     labels[] (eixo x) e values[] OR series[{name, values[]}] (ate 3), unit
  donut:    values[] (primeira fatia em laranja), big ("3"), big_sub (" de 10"), small ("VOLTAM")
  todos:    note (rodape pequeno, ex.: "EXEMPLO ILUSTRATIVO" ou "FONTE: X")
"""
import os, re, sys, json, glob
from PIL import Image, ImageDraw, ImageFont, ImageOps, ImageChops

W, H, M = 1080, 1350, 72
NAVY, ORANGE, WHITE, SOFT = (16, 30, 50), (192, 123, 68), (255, 255, 255), (201, 209, 219)
PANEL, BAR, TEXT = (27, 47, 76), (84, 110, 150), (228, 233, 239)
FD = os.environ.get("FONT_DIR", "fonts")
BRAND_DEFAULT = "Jack Emerick Insights"

_fc = {}


def _font(file, size, axes):
    k = (file, size, tuple(axes))
    if k not in _fc:
        f = ImageFont.truetype(os.path.join(FD, file), int(size))
        f.set_variation_by_axes(list(axes))
        _fc[k] = f
    return _fc[k]


def bebas(size):
    return _font_plain("BebasNeue-Regular.ttf", size)


def inter(weight, size):
    return _font_plain(f"Inter-{weight}.otf", size)


def _font_plain(file, size):
    k = (file, int(size))
    if k not in _fc:
        _fc[k] = ImageFont.truetype(os.path.join(FD, file), int(size))
    return _fc[k]


def bodoni(size, italic=False, wght=500):
    return _font("BodoniModa-Italic.ttf" if italic else "BodoniModa.ttf", size, [wght, 30])


def archivo(size, wght=500):
    return _font("Archivo.ttf", size, [wght, 100])


# ---------- texto rico ----------
def parse_rich(text):
    """'a *b* c' ou 'a **b** c' -> lista de (char, estilo) com estilo 'r' ou 'e'."""
    out, em = [], False
    i = 0
    while i < len(text):
        if text.startswith("**", i):
            em = not em; i += 2; continue
        if text[i] == "*":
            em = not em; i += 1; continue
        out.append((text[i], "e" if em else "r")); i += 1
    return out


def strip_rich(text):
    return "".join(c for c, _ in parse_rich(text))


def split_words(chars):
    words, cur = [], []
    for c, st in chars:
        if c in " \n":
            if cur: words.append(cur); cur = []
            if c == "\n": words.append("BR")
        else:
            cur.append((c, st))
    if cur: words.append(cur)
    return words


def runs(word):
    rs = []
    for c, st in word:
        if rs and rs[-1][1] == st: rs[-1][0] += c
        else: rs.append([c, st])
    return rs


class Rich:
    """Texto com dois estilos. kind 'title' (Bodoni) ou 'body' (Archivo)."""
    def __init__(self, kind, size, ls=0.0, em_scale=1.0, color=WHITE):
        self.kind, self.size, self.ls, self.em_scale, self.color = kind, size, ls, em_scale, color

    def font(self, st):
        if self.kind == "bt":
            return bebas(self.size)
        if self.kind == "bb":
            return inter("ExtraBold" if st == "e" else "Regular", self.size)
        if self.kind == "title":
            return bodoni(self.size * (self.em_scale if st == "e" else 1), st == "e", 700 if st == "e" else 500)
        return archivo(self.size, 700 if st == "e" else 500)

    def col(self, st):
        return ORANGE if (st == "e" or self.kind == "bt") else self.color

    def adv(self, d, f, prev, ch):
        if prev:
            return d.textlength(prev + ch, font=f) - d.textlength(prev, font=f)
        return d.textlength(ch, font=f)

    def run_w(self, d, txt, st):
        f = self.font(st)
        return sum(self.adv(d, f, txt[i - 1] if i else "", c) for i, c in enumerate(txt)) + self.ls * self.size * len(txt)

    def word_w(self, d, word):
        return sum(self.run_w(d, t, st) for t, st in runs(word))

    def layout(self, d, text, max_w, lh):
        words = split_words(parse_rich(text))
        sp = d.textlength(" ", font=self.font("r")) + self.ls * self.size
        lines, cur, cw = [], [], 0
        for w in words:
            if w == "BR":
                lines.append(cur); cur, cw = [], 0; continue
            ww = self.word_w(d, w)
            if cur and cw + sp + ww > max_w:
                lines.append(cur); cur, cw = [], 0
            cw = cw + (sp if cur else 0) + ww
            cur.append((w, ww))
        lines.append(cur)
        res = []
        for ln in lines:
            big = max([self.em_scale if any(s == "e" for _, s in w) else 1 for w, _ in ln] or [1])
            res.append((ln, self.size * big * lh, self.size * big))
        self._sp = sp
        return res

    def height(self, lines):
        return sum(h for _, h, _ in lines)

    def draw(self, d, lines, x, y, align="left", box_w=None):
        for ln, h, s in lines:
            base = y + s * 0.82 * (h / (s * 1.0) if False else 1)
            base = y + h - (h - s) * 0.5 - s * 0.2
            tw = sum(w for _, w in ln) + self._sp * max(0, len(ln) - 1)
            cx = x if align == "left" else x + (box_w - tw) / 2
            for word, ww in ln:
                for t, st in runs(word):
                    f = self.font(st)
                    prev = ""
                    for ch in t:
                        cx += self.adv(d, f, prev, ch) - d.textlength(ch, font=f) if prev else 0
                        d.text((cx, base), ch, font=f, fill=self.col(st), anchor="ls")
                        cx += d.textlength(ch, font=f) + self.ls * self.size
                        prev = ch
                cx += self._sp
            y += h
        return y


def fit_rich(d, kind, text, max_w, max_h, start, minimum, lh, ls=0.0, em_scale=1.0, color=WHITE, step=4, max_lines=None):
    size = start
    while True:
        r = Rich(kind, size, ls, em_scale, color)
        lines = r.layout(d, text, max_w, lh)
        ok = r.height(lines) <= max_h and (max_lines is None or len(lines) <= max_lines)
        if ok or size <= minimum:
            return r, lines
        size -= step


def spaced(d, xy, text, fnt, fill, ls):
    x, y = xy
    for ch in text:
        d.text((x, y), ch, font=fnt, fill=fill)
        x += d.textlength(ch, font=fnt) + ls
    return x


def spaced_w(d, text, fnt, ls):
    return sum(d.textlength(c, font=fnt) + ls for c in text) - ls


def clean_title(t):
    t = t.strip()
    return re.sub(r"[. ]+$", "", t) if not t.endswith("*") else re.sub(r"\.(\*+)$", r"\1", t)


# ---------- elementos comuns ----------
def background():
    sw, sh = 108, 135
    small = Image.new("RGB", (sw, sh))
    px = small.load()
    for y in range(sh):
        for x in range(sw):
            dx = (x / sw - 0.5) / 1.2
            dy = (y / sh) / 0.8
            t = min(1.0, (dx * dx + dy * dy) ** 0.5 / 0.6)
            px[x, y] = tuple(int(PANEL[i] + (NAVY[i] - PANEL[i]) * t) for i in range(3))
    return small.resize((W, H), Image.BICUBIC).convert("RGBA")


def watermark(img, brand):
    f = inter("SemiBold", 24)
    t = brand.upper()
    tmp = Image.new("RGBA", (W, 40), (0, 0, 0, 0))
    td = ImageDraw.Draw(tmp, "RGBA")
    tw = spaced_w(td, t, f, 7)
    spaced(td, ((W - tw) / 2, 4), t, f, WHITE + (70,), 7)
    img.alpha_composite(tmp, (0, H - 74))


def chrome(img, d, tag, n, total, brand, page=True):
    watermark(img, brand)


def rule(d, x, y):
    d.rectangle([x, y, x + 90, y + 4], fill=ORANGE)


def fmt(v, unit=""):
    s = f"{v:g}".replace(".", ",")
    return s + unit


def ss_layer(w, h, k=3):
    return Image.new("RGBA", (int(w) * k, int(h) * k), (0, 0, 0, 0)), k


def paste_ss(img, layer, k, x, y):
    small = layer.resize((layer.width // k, layer.height // k), Image.LANCZOS)
    img.alpha_composite(small, (int(x), int(y)))


def wrap_plain(d, text, fnt, max_w, max_lines=2):
    words, lines, cur = text.split(" "), [], ""
    for w in words:
        t = (cur + " " + w).strip()
        if d.textlength(t, font=fnt) <= max_w or not cur:
            cur = t
        else:
            lines.append(cur); cur = w
    lines.append(cur)
    return lines[:max_lines]


# ---------- graficos ----------
def chart_bar(img, d, c, box):
    x0, y0, x1, y1 = box
    labels, vals, unit = c["labels"], c["values"], c.get("unit", "")
    n, hi = len(vals), c.get("hi", len(vals) - 1)
    fl = inter("SemiBold", 25)
    slot = (x1 - x0) / n
    lab_h = 70
    base = y1 - lab_h
    vmax = max(vals) or 1
    top = y0 + 80
    for i, v in enumerate(vals):
        cx = x0 + slot * (i + .5)
        bw = min(slot * 0.62, 190)
        hh = max(8, (base - top) * v / vmax)
        col = ORANGE if i == hi else BAR
        d.rectangle([cx - bw / 2, base - hh, cx + bw / 2, base], fill=col + (255,))
        f = bebas(int((60)*1.3))
        t = fmt(v, unit)
        tw = d.textlength(t, font=f)
        d.text((cx - tw / 2, base - hh - 14), t, font=f, fill=ORANGE if i == hi else SOFT, anchor="ls")
        for j, ln in enumerate(wrap_plain(d, labels[i], fl, slot - 10)):
            lw = d.textlength(ln, font=fl)
            d.text((cx - lw / 2, base + 18 + j * 30), ln, font=fl, fill=WHITE if i == hi else SOFT)
    d.line([x0, base, x1, base], fill=SOFT + (110,), width=2)


def chart_hbar(img, d, c, box):
    x0, y0, x1, y1 = box
    labels, vals, unit = c["labels"], c["values"], c.get("unit", "")
    n, hi = len(vals), c.get("hi", 0)
    vmax = c.get("max") or max(vals) or 1
    row = min(150, (y1 - y0) / n)
    fl, fv = inter("SemiBold", 32), bebas(int(min(78, row * .56)))
    for i, v in enumerate(vals):
        y = y0 + i * row
        col = ORANGE if i == hi else BAR
        d.text((x0, y + row * .36), labels[i], font=fl, fill=WHITE if i == hi else SOFT, anchor="ls")
        t = fmt(v, unit)
        d.text((x1, y + row * .40), t, font=fv, fill=ORANGE if i == hi else SOFT, anchor="rs")
        by = y + row * .52
        bh = max(16, row * .18)
        d.rectangle([x0, by, x1, by + bh], fill=BAR + (90,))
        d.rectangle([x0, by, x0 + (x1 - x0) * min(1, v / vmax), by + bh], fill=col + (255,))


def chart_line(img, d, c, box):
    x0, y0, x1, y1 = box
    labels, unit = c["labels"], c.get("unit", "")
    series = c.get("series") or [{"name": "", "values": c["values"]}]
    cols = [ORANGE, BAR, SOFT]
    allv = [v for s in series for v in s["values"]]
    vmin, vmax = min(allv), max(allv)
    if vmin == vmax: vmin, vmax = vmin - 1, vmax + 1
    pad = (vmax - vmin) * 0.12
    vmin, vmax = vmin - pad, vmax + pad
    n = len(labels)
    px0, px1 = x0 + 50, x1 - 70
    top, bot = y0 + 70, y1 - 60
    fl = inter("SemiBold", 25)
    for g in range(4):
        gy = top + (bot - top) * g / 3
        d.line([x0, gy, x1, gy], fill=SOFT + (28,), width=2)
    layer, k = ss_layer(x1 - x0, y1 - y0)
    ld = ImageDraw.Draw(layer)
    pts_all = []
    for si, s in enumerate(series):
        pts = []
        for i, v in enumerate(s["values"]):
            x = px0 + (px1 - px0) * (i / max(1, n - 1))
            y = bot - (bot - top) * (v - vmin) / (vmax - vmin)
            pts.append((x, y))
        pts_all.append(pts)
        col = cols[si % 3]
        ld.line([((p[0] - x0) * k, (p[1] - y0) * k) for p in pts], fill=col + (255,), width=9 * k, joint="curve")
        for j, p in enumerate(pts):
            r = (13 if j == len(pts) - 1 else 8) * k
            ld.ellipse([(p[0] - x0) * k - r, (p[1] - y0) * k - r, (p[0] - x0) * k + r, (p[1] - y0) * k + r], fill=col + (255,))
    paste_ss(img, layer, k, x0, y0)
    d = ImageDraw.Draw(img, "RGBA")
    fv = bebas(int((58)*1.3))
    for si, (s, pts) in enumerate(zip(series, pts_all)):
        col = cols[si % 3]
        for j in ((0, len(pts) - 1) if si == 0 else (len(pts) - 1,)):
            p = pts[j]
            t = fmt(s["values"][j], unit)
            tw = d.textlength(t, font=fv)
            ty = p[1] - 26
            tx = min(max(p[0] - tw / 2, x0), x1 - tw)
            d.text((tx, ty), t, font=fv, fill=col if si == 0 else SOFT, anchor="ls")
    for i, lab in enumerate(labels):
        x = px0 + (px1 - px0) * (i / max(1, n - 1))
        lw = d.textlength(lab, font=fl)
        tx = min(max(x - lw / 2, x0), x1 - lw)
        d.text((tx, bot + 24), lab, font=fl, fill=SOFT)
    if len(series) > 1:
        lx = x0
        for si, s in enumerate(series):
            d.rectangle([lx, y0 + 12, lx + 22, y0 + 22], fill=cols[si % 3] + (255,))
            d.text((lx + 34, y0 + 20), s["name"], font=inter("SemiBold", 24), fill=WHITE, anchor="ls")
            lx += 34 + d.textlength(s["name"], font=inter("SemiBold", 24)) + 40


def chart_donut(img, d, c, box):
    x0, y0, x1, y1 = box
    vals = c["values"]
    tot = sum(vals) or 1
    size = int(min(x1 - x0, y1 - y0, 620))
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    k = 3
    S = size * k
    layer = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    ld = ImageDraw.Draw(layer)
    cols = [ORANGE, BAR, SOFT, (60, 85, 125)]
    a = -90.0
    for i, v in enumerate(vals):
        sweep = 360.0 * v / tot
        ld.pieslice([0, 0, S - 1, S - 1], a, a + sweep, fill=cols[i % 4] + (255,))
        a += sweep
    ring = int(size * 0.115) * k
    mask = Image.new("L", (S, S), 0)
    md = ImageDraw.Draw(mask)
    md.ellipse([0, 0, S - 1, S - 1], fill=255)
    md.ellipse([ring, ring, S - 1 - ring, S - 1 - ring], fill=0)
    layer.putalpha(ImageChops.multiply(layer.getchannel("A"), mask))
    paste_ss(img, layer, k, cx - size / 2, cy - size / 2)
    d = ImageDraw.Draw(img, "RGBA")
    big = c.get("big") or f"{round(100 * vals[0] / tot)}%"
    sub = c.get("big_sub", "")
    fb, fs = bebas(int((int(size * .34))*1.3)), bebas(int((int(size * .16))*1.3))
    wb = d.textlength(big, font=fb)
    ws = d.textlength(sub, font=fs) if sub else 0
    sx = cx - (wb + ws) / 2
    by = cy + size * .10
    d.text((sx, by), big, font=fb, fill=WHITE, anchor="ls")
    if sub:
        d.text((sx + wb, by), sub, font=fs, fill=SOFT, anchor="ls")
    if c.get("small"):
        fsm = inter("SemiBold", 24)
        t = c["small"].upper()
        tw = spaced_w(d, t, fsm, 5)
        spaced(d, (cx - tw / 2, by + 34), t, fsm, ORANGE, 5)


CHARTS = {"bar": chart_bar, "hbar": chart_hbar, "line": chart_line, "donut": chart_donut}


# ---------- slides ----------
def cover_photo(path, fx, fy):
    p = ImageOps.exif_transpose(Image.open(path)).convert("RGB")
    s = max(W / p.width, H / p.height)
    p = p.resize((int(p.width * s) + 1, int(p.height * s) + 1), Image.LANCZOS)
    cx, cy = fx * p.width, fy * p.height
    l = int(max(0, min(p.width - W, cx - W / 2)))
    t = int(max(0, min(p.height - H, cy - H * 0.38)))
    return p.crop((l, t, l + W, t + H))


def render_cover(s, brand, n, total):
    photo = s.get("photo")
    ppath = os.path.join("photos", photo) if photo else None
    if ppath and os.path.exists(ppath):
        img = cover_photo(ppath, float(s.get("photo_fx", 0.5)), float(s.get("photo_fy", 0.3))).convert("RGBA")
    else:
        img = background()
    shade = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    sd = ImageDraw.Draw(shade)
    for y in range(H):
        t = y / H
        a = 55 + int(190 * max(0, (t - 0.28) / 0.72) ** 1.2)
        sd.line([(0, y), (W, y)], fill=NAVY + (min(a, 242),))
    img.alpha_composite(shade)
    d = ImageDraw.Draw(img, "RGBA")
    watermark(img, brand)
    inner = W - 2 * M
    body = s.get("body", "")
    fb = archivo(32, 500)
    r_b = Rich("body", 32, 0, 1, TEXT)
    bl = r_b.layout(d, body, 800, 1.4)
    bh = r_b.height(bl)
    foot_y = H - 135
    bottom = foot_y - 40 - bh - 30
    em_scale = 1.0
    plain = [c for c, st in parse_rich(clean_title(s["title"])) if st == "e"]
    if 0 < len(plain) <= 9: em_scale = 1.5
    tr, tl = fit_rich(d, "title", clean_title(s["title"]), inner, 760, 118, 70, 0.92, ls=-0.045, em_scale=em_scale, step=4)
    th = tr.height(tl)
    y = bottom - th
    tr.draw(d, tl, M, y)
    y = bottom + 10
    rule(d, M, y)
    r_b.draw(d, bl, M, y + 28)
    at = "ARRASTE PARA O LADO"
    fa = archivo(22, 600)
    tw = spaced_w(d, at, fa, 4.4)
    spaced(d, (W - M - tw - 50, foot_y), at, fa, ORANGE, 4.4)
    ax = W - M - 36
    d.line([ax, foot_y + 12, ax + 30, foot_y + 12], fill=ORANGE, width=4)
    d.line([ax + 20, foot_y + 2, ax + 31, foot_y + 12, ax + 20, foot_y + 22], fill=ORANGE, width=4)
    return img.convert("RGB")


def btitle(d, s, max_h, start=132, minimum=76, max_lines=4, width=None):
    t = clean_title(s["title"]).replace("*", "").upper()
    return fit_rich(d, "bt", t, width or (W - 2 * M), max_h, start, minimum, 1.0, ls=0.0, step=4, max_lines=max_lines)


def bbody(d, text, size, max_w=W - 2 * M - 20):
    rb = Rich("bb", size, 0, 1, WHITE)
    return rb, rb.layout(d, text, max_w, 1.4)


def fit_body(d, text, max_h, start=46, minimum=30):
    size = start
    while True:
        rb, bl = bbody(d, text, size)
        if rb.height(bl) <= max_h or size <= minimum:
            return rb, bl
        size -= 2


def render_content(s, brand, n, total):
    img = background()
    d = ImageDraw.Draw(img, "RGBA")
    watermark(img, brand)
    d.rectangle([M, 96, M + 90, 102], fill=ORANGE)
    tr, tl = btitle(d, s, 480)
    y = tr.draw(d, tl, M, 140) + 34
    rb, bl = fit_body(d, s.get("body", ""), H - 150 - y)
    rb.draw(d, bl, M, y)
    return img.convert("RGB")


def render_stat(s, brand, n, total):
    img = background()
    d = ImageDraw.Draw(img, "RGBA")
    watermark(img, brand)
    d.rectangle([M, 96, M + 90, 102], fill=ORANGE)
    tr, tl = btitle(d, s, 300, start=104, minimum=64, max_lines=3)
    y = tr.draw(d, tl, M, 140)
    stat = s["stat"]
    size = 560
    while size > 140 and d.textlength(stat, font=bebas(size)) > W - 2 * M:
        size -= 10
    f = bebas(size)
    base = max(y + size * 0.85 + 20, 640)
    d.text((M, base), stat, font=f, fill=ORANGE, anchor="ls")
    y = base + 75
    rb, bl = fit_body(d, s.get("body", ""), H - 170 - y, start=44)
    rb.draw(d, bl, M, y)
    if s.get("note"):
        d.text((M, H - 118), s["note"].upper(), font=inter("SemiBold", 20), fill=ORANGE)
    return img.convert("RGB")


def render_chart(s, brand, n, total):
    img = background()
    d = ImageDraw.Draw(img, "RGBA")
    watermark(img, brand)
    d.rectangle([M, 96, M + 90, 102], fill=ORANGE)
    c = s["chart"]
    tr, tl = btitle(d, s, 300, start=104, minimum=64, max_lines=3)
    y = tr.draw(d, tl, M, 140)
    if s.get("body"):
        rb, bl = bbody(d, s["body"], 32)
        y = rb.draw(d, bl, M, y + 20)
    ins = s.get("insight", "")
    ri, il = bbody(d, ins, 34) if ins else (None, [])
    note = (c.get("note") or "").upper()
    bottom = H - 120
    block = (ri.height(il) if il else 0) + (36 if note else 0)
    btop = bottom - block
    chart_top = y + 40
    chart_bot = btop - 40
    CHARTS[c.get("type", "bar")](img, d, c, (M, chart_top, W - M, chart_bot))
    d = ImageDraw.Draw(img, "RGBA")
    if il:
        ri.draw(d, il, M, btop)
    if note:
        d.text((M, bottom), note, font=inter("SemiBold", 20), fill=ORANGE, anchor="ls")
    return img.convert("RGB")


def render_cta(s, brand, n, total):
    img = background()
    d = ImageDraw.Draw(img, "RGBA")
    watermark(img, brand)
    d.rectangle([M, 96, M + 90, 102], fill=ORANGE)
    tr, tl = btitle(d, s, 480, start=120)
    y = tr.draw(d, tl, M, 140) + 34
    rb, bl = fit_body(d, s.get("body", ""), 380, start=42)
    y = rb.draw(d, bl, M, y)
    cta = fix_cta(s.get("cta", "SIGA ESTE PERFIL")).upper()
    size = 96
    while size > 48 and d.textlength(cta, font=bebas(size)) > W - 2 * M - 90:
        size -= 4
    f = bebas(size)
    cy = H - 250
    d.rectangle([M, cy - size - 36, M + W - 2 * M, cy - size - 34], fill=ORANGE + (120,))
    d.text((M, cy), cta, font=f, fill=ORANGE, anchor="ls")
    ax = M + d.textlength(cta, font=f) + 26
    ay = cy - size * 0.35
    d.line([ax, ay, ax + 56, ay], fill=ORANGE, width=6)
    d.line([ax + 42, ay - 14, ax + 57, ay, ax + 42, ay + 14], fill=ORANGE, width=6)
    return img.convert("RGB")


def fix_cta(t):
    """CTA sem @: troca por 'este perfil' (uma unica acao por post)."""
    return re.sub(r"@\w[\w.]*", "este perfil", t or "")


def render(spec_path):
    spec = json.load(open(spec_path, encoding="utf-8"))
    name = spec["set"]
    brand = spec.get("brand", BRAND_DEFAULT)
    out = os.path.join("out", name)
    os.makedirs(out, exist_ok=True)
    slides = spec["slides"]
    total = len(slides)
    for i, s in enumerate(slides, 1):
        typ = "cover" if i == 1 else s.get("type") or ("chart" if s.get("chart") else "cta" if s.get("cta") else "content")
        fn = {"cover": render_cover, "content": render_content, "stat": render_stat, "chart": render_chart, "cta": render_cta}[typ]
        im = fn(s, brand, i, total)
        im.save(os.path.join(out, f"slide_{i:02d}.jpg"), "JPEG", quality=90, optimize=True)
        print("ok", name, i, typ)


if __name__ == "__main__":
    for p in sorted(glob.glob("specs/*.json")):
        nm = json.load(open(p, encoding="utf-8"))["set"]
        if not os.path.isdir(os.path.join("out", nm)) or "--all" in sys.argv:
            render(p)
