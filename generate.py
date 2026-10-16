import os, sys, json, glob
from PIL import Image, ImageDraw, ImageFont

W, H, M = 1080, 1350, 90
NAVY, ORANGE, WHITE, SOFT = "#101E32", "#C07B44", "#FFFFFF", "#C9D1DB"
FD = os.environ.get("FONT_DIR", "fonts")

def inter(weight, size):
    return ImageFont.truetype(os.path.join(FD, f"Inter-{weight}.otf"), size)

def bebas(size):
    return ImageFont.truetype(os.path.join(FD, "BebasNeue-Regular.ttf"), size)

def wrap(draw, text, fnt, max_w):
    lines = []
    for para in text.split("\n"):
        cur = ""
        for w in para.split(" "):
            t = (cur + " " + w).strip()
            if draw.textlength(t, font=fnt) <= max_w:
                cur = t
            else:
                if cur: lines.append(cur)
                cur = w
        lines.append(cur)
    return lines

def block(draw, text, fnt, x, y, max_w, fill, gap):
    lh = int(fnt.size * gap)
    for ln in wrap(draw, text, fnt, max_w):
        draw.text((x, y), ln, font=fnt, fill=fill)
        y += lh
    return y

def render(spec_path):
    spec = json.load(open(spec_path, encoding="utf-8"))
    name = spec["set"]
    brand = spec.get("brand", "Jack Emerick Insights")
    out = os.path.join("out", name)
    os.makedirs(out, exist_ok=True)
    slides = spec["slides"]
    n = len(slides)
    for i, s in enumerate(slides, 1):
        img = Image.new("RGB", (W, H), NAVY)
        d = ImageDraw.Draw(img)
        top = 0
        photo = s.get("photo")
        if photo and os.path.exists(os.path.join("photos", photo)):
            p = Image.open(os.path.join("photos", photo)).convert("RGB")
            ph = 520
            r = max(W / p.width, ph / p.height)
            p = p.resize((int(p.width * r) + 1, int(p.height * r) + 1))
            l, t = (p.width - W) // 2, (p.height - ph) // 2
            img.paste(p.crop((l, t, l + W, t + ph)), (0, 0))
            top = ph - 190
        d.rectangle([M, 130 + top, M + 90, 136 + top], fill=ORANGE)
        d.text((M, 160 + top), s.get("kicker", "").upper(), font=inter("SemiBold", 28), fill=SOFT)
        big = s.get("big")
        size = 210 if big else 150
        bsz = 46 if big else 42
        y0 = 300 + top if big else 250 + top
        limit = H - (230 if s.get("foot") else 160)
        while True:
            tf = bebas(size)
            nt = len(wrap(d, s["title"].upper(), tf, W - 2 * M))
            nb = len(wrap(d, s.get("body", ""), inter("Regular", bsz), W - 2 * M))
            if y0 + nt * int(size * 1.0) + 40 + nb * int(bsz * 1.38) <= limit or size <= 70:
                break
            size -= 6
        y = block(d, s["title"].upper(), tf, M, y0, W - 2 * M, ORANGE, 1.0) + 40
        block(d, s.get("body", ""), inter("Regular", bsz), M, y, W - 2 * M, WHITE, 1.38)
        if s.get("foot"):
            d.text((M, H - 190), s["foot"], font=inter("Medium", 28), fill=SOFT)
        d.line([M, H - 120, W - M, H - 120], fill=ORANGE, width=2)
        d.text((M, H - 95), brand, font=inter("Medium", 28), fill=SOFT)
        num = f"{i}/{n}"
        tw = d.textlength(num, font=inter("SemiBold", 28))
        d.text((W - M - tw, H - 95), num, font=inter("SemiBold", 28), fill=ORANGE)
        img.save(os.path.join(out, f"slide_{i:02d}.jpg"), "JPEG", quality=90, optimize=True)
        print("ok", name, i)

for p in sorted(glob.glob("specs/*.json")):
    name = json.load(open(p, encoding="utf-8"))["set"]
    if not os.path.isdir(os.path.join("out", name)) or "--all" in sys.argv:
        render(p)
