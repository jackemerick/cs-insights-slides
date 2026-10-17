"""Uso: python make_photo.py entrada.jpg saida.jpg FACE_Y
Gera a faixa 1080x520 (JPEG q72) centrada no rosto (FACE_Y = fração da altura, ex 0.2)
e escurece levemente se a parte de baixo ficar muito clara (contraste com o texto)."""
import sys
from PIL import Image, ImageEnhance
src, dst, fy = sys.argv[1], sys.argv[2], float(sys.argv[3])
im = Image.open(src).convert("RGB")
w, h = im.size
ch = min(h, int(w * 520 / 1080))
cy = int(fy * h + 0.06 * h)
y0 = max(0, min(h - ch, cy - ch // 2))
c = im.crop((0, y0, w, y0 + ch)).resize((1080, 520), Image.LANCZOS)
lum = sum(c.crop((0, 400, 1080, 520)).convert("L").getdata()) / (1080 * 120)
if lum > 150:
    c = ImageEnhance.Brightness(c).enhance(0.85)
c.save(dst, quality=72)
print("ok", dst, round(lum))
