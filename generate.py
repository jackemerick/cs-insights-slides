import os, sys, json, glob
from PIL import Image, ImageDraw, ImageFont

W, H, M = 1080, 1350, 90
NIGHT, OCEAN, TURQ, INDIGO = "#0B2A3C", "#1B6A8F", "#2EC4B6", "#5A4FA3"
SAND, GRAPHITE = "#EFE9DD", "#1F2933"
ACC = {"turq": TURQ, "ocean": OCEAN, "indigo": INDIGO}
FD = os.environ.get("FONT_DIR", "fonts")

def font(weight, size):
    return ImageFont.truetype(os.path.join(FD, f"Inter-{weight}.otf"), size)

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

def block(draw, text, fnt, x, y, max_w, fill, gap=1.28):
    lh = int(fnt.size * gap)
    for ln in wrap(draw, text, fnt, max_w):
        draw.text((x, y), ln, font=fnt, fill=fill)
        y += lh
    return y

def render(spec_path):
    spec = json.load(open(spec_path, encoding="utf-8"))
    name = spec["set"]
    brand = spec.get("brand", "Customer Success Insights")
    out = os.path.join("out", name)
    os.makedirs(out, exist_ok=True)
    slides = spec["slides"]
    n = len(slides)
    for i, s in enumerate(slides, 1):
        dark = s.get("dark", i % 2 == 1)
        acc = ACC.get(s.get("accent", "turq"), TURQ)
        bg = NIGHT if dark else SAND
        title_c = SAND if dark else NIGHT
        body_c = "#D6DEE3" if dark else GRAPHITE
        img = Image.new("RGB", (W, H), bg)
        d = ImageDraw.Draw(img)
        d.rectangle([0, 0, W, 18], fill=acc)
        d.rectangle([M, 130, M + 90, 138], fill=acc)
        d.text((M, 160), s.get("kicker", ""), font=font("SemiBold", 30), fill=acc)
        big = s.get("big")
        tf = font("ExtraBold", 108 if big else 82)
        y = 330 if big else 260
        y = block(d, s["title"], tf, M, y, W - 2 * M, title_c, gap=1.14) + 50
        block(d, s.get("body", ""), font("Regular", 44 if big else 40), M, y, W - 2 * M, body_c, gap=1.4)
        if s.get("foot"):
            d.text((M, H - 190), s["foot"], font=font("Medium", 28), fill=acc)
        d.line([M, H - 120, W - M, H - 120], fill=acc, width=2)
        d.text((M, H - 95), brand, font=font("Medium", 28), fill=body_c)
        num = f"{i}/{n}"
        tw = d.textlength(num, font=font("SemiBold", 28))
        d.text((W - M - tw, H - 95), num, font=font("SemiBold", 28), fill=acc)
        img.save(os.path.join(out, f"slide_{i:02d}.jpg"), "JPEG", quality=88, optimize=True)
        print("ok", name, i)

for p in sorted(glob.glob("specs/*.json")):
    name = json.load(open(p, encoding="utf-8"))["set"]
    if not os.path.isdir(os.path.join("out", name)) or "--all" in sys.argv:
        render(p)
