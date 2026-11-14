"""Renderizador do carrossel educativo (visual Mare Profunda).
Uso: python carousel/render.py carousel_specs/AAAA-MM-DD-nome.json
Gera out/carousel/<id>/slide_01.jpg ... slide_09.jpg (1080x1350).
Marcacao nos textos: [[texto]] = sublinhado.
"""
import math, os, sys, json, re, html
SAND="#EFE9DD"; TEAL="#2EC4B6"; NAVYH="#0B2A3C"; NAVY="11,42,60"; INDIGO="#5A4FA3"
W=1080; N=9; TW=W*N; H=1350
TEALZ=[]
def hx(c): c=c.lstrip('#'); return [int(c[i:i+2],16) for i in (0,2,4)]
def mix(a,b,t):
    A,B=hx(a),hx(b); return '#%02x%02x%02x'%tuple(round(A[k]+(B[k]-A[k])*t) for k in range(3))
def sm(t): t=max(0,min(1,t)); return t*t*(3-2*t)
def f(x):
    v=0
    for k in TEALZ:
        a=(k-1)*W; b=k*W
        l=sm((x-(a-80))/160)
        r=1 if k==N else 1-sm((x-(b-80))/160)
        v=max(v,l*r)
    return v
NAVSTOPS=[(0,"#0B2A3C"),(0.25,"#103A53"),(0.5,"#0B2A3C"),(0.75,"#123F5C"),(1,"#0B2A3C")]
def navy_at(x):
    t=x/TW
    for (t0,c0),(t1,c1) in zip(NAVSTOPS,NAVSTOPS[1:]):
        if t<=t1: return mix(c0,c1,(t-t0)/(t1-t0))
    return NAVSTOPS[-1][1]
def wave(base,amp,lam,ph,step=30):
    pts=[];x=0
    while x<=TW:
        y=base+amp*math.sin(2*math.pi*x/lam+ph)+amp*0.35*math.sin(2*math.pi*x/(lam*0.43)+ph*1.7)
        pts.append(f"{x},{y:.1f}"); x+=step
    return "M"+" L".join(pts)
def lg(idn,colfn,step=40):
    st="".join(f'<stop offset="{x/TW:.4f}" stop-color="{colfn(x)}"></stop>' for x in range(0,TW+1,step))
    return f'<linearGradient id="{idn}" gradientUnits="userSpaceOnUse" x1="0" y1="0" x2="{TW}" y2="0">{st}</linearGradient>'
def waves_svg(i):
    off=-(i-1)*W
    spec=[(wave(420,90,3600,0.4),TEAL,0.40,3),(wave(520,120,4400,2.1),"#1B6A8F",0.55,7),(wave(900,110,3900,4.0),SAND,0.14,2),(wave(980,80,5200,1.0),TEAL,0.30,3)]
    defs="".join(lg(f"wa{k}",lambda x,c=c:mix(c,'#1B6A8F',f(x)),60) for k,(d,c,o,w) in enumerate(spec))
    body="".join(f'<path d="{d}" fill="none" stroke="url(#wa{k})" stroke-opacity="{o}" stroke-width="{w}" stroke-linecap="round"></path>' for k,(d,c,o,w) in enumerate(spec))
    return f'<svg aria-hidden="true" width="{TW}" height="{H}" viewBox="0 0 {TW} {H}" style="position: absolute; left: {off}px; top: 0"><defs>{defs}</defs>{body}</svg>'
blobs=[(2700,1100,"i",380),(3240,300,"t",420),(4320,1040,"o",520),(5400,280,"i",480),(7900,300,"o",420),(8300,1100,"t",380),
       (1500,260,"w",380),(1900,1150,"w",420),(1750,700,"d",300),(6800,1150,"w",400),(7250,250,"w",380),(7000,700,"d",300),(9100,260,"w",380),(9450,1120,"w",400),(9300,700,"d",300)]
def base_svg(i):
    off=-(i-1)*W
    rg=lambda n,c,o:f'<radialGradient id="{n}"><stop offset="0" stop-color="{c}" stop-opacity="{o}"></stop><stop offset="1" stop-color="{c}" stop-opacity="0"></stop></radialGradient>'
    defs=('<defs>'+lg("bg",lambda x:mix(navy_at(x),SAND,f(x)))+rg("o","#1B6A8F",0.75)+rg("i","#5A4FA3",0.65)+rg("t",TEAL,0.38)+rg("w",TEAL,0.26)+rg("d","#1B6A8F",0.18)+'</defs>')
    bl="".join(f'<circle cx="{x}" cy="{y}" r="{r}" fill="url(#{c})"></circle>' for x,y,c,r in blobs)
    return f'<svg aria-hidden="true" width="{TW}" height="{H}" viewBox="0 0 {TW} {H}" style="position: absolute; left: {off}px; top: 0">{defs}<rect x="0" y="0" width="{TW}" height="{H}" fill="url(#bg)"></rect>{bl}</svg>'
ICON={
"userx":'<path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2"></path><circle cx="9" cy="7" r="4"></circle><line x1="17" y1="8" x2="22" y2="13"></line><line x1="22" y1="8" x2="17" y2="13"></line>',
"target":'<circle cx="12" cy="12" r="10"></circle><circle cx="12" cy="12" r="6"></circle><circle cx="12" cy="12" r="2"></circle>',
"cal":'<rect x="3" y="4" width="18" height="18" rx="2"></rect><line x1="16" y1="2" x2="16" y2="6"></line><line x1="8" y1="2" x2="8" y2="6"></line><line x1="3" y1="10" x2="21" y2="10"></line><path d="m9 16 2 2 4-4"></path>',
"msg":'<path d="M7.9 20A9 9 0 1 0 4 16.1L2 22Z"></path>',
"send":'<line x1="22" y1="2" x2="11" y2="13"></line><polygon points="22 2 15 22 11 13 2 9 22 2"></polygon>',
"trend":'<polyline points="22 7 13.5 15.5 8.5 10.5 2 17"></polyline><polyline points="16 7 22 7 22 13"></polyline>',
"zap":'<polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"></polygon>',
"check":'<path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"></path><polyline points="22 4 12 14.01 9 11.01"></polyline>',
"users":'<path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"></path><circle cx="9" cy="7" r="4"></circle><path d="M23 21v-2a4 4 0 0 0-3-3.87"></path><path d="M16 3.13a4 4 0 0 1 0 7.75"></path>',
"search":'<circle cx="11" cy="11" r="8"></circle><line x1="21" y1="21" x2="16.65" y2="16.65"></line>',
"heart":'<path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z"></path>',
"book":'<path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20"></path><path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z"></path>',
"clock":'<circle cx="12" cy="12" r="10"></circle><polyline points="12 6 12 12 16 14"></polyline>',
"chart":'<line x1="18" y1="20" x2="18" y2="10"></line><line x1="12" y1="20" x2="12" y2="4"></line><line x1="6" y1="20" x2="6" y2="14"></line>',
}
class Th:
    def __init__(s,hot):
        s.hot=hot; s.fg=NAVYH if hot else SAND; s.acc=INDIGO if hot else TEAL
    def u(s,t,big=False):
        th,off=(8,12) if big else (4,7)
        return f'<span style="text-decoration: underline; text-decoration-color: {s.acc}; text-decoration-thickness: {th}px; text-underline-offset: {off}px; text-decoration-skip-ink: none">{t}</span>'
    def mk(s,txt,big=False):
        txt=html.escape(txt,quote=False)
        return re.sub(r"\[\[(.+?)\]\]",lambda m:s.u(m.group(1),big),txt)
    def icon(s,k):
        bg,br,st=(NAVYH,NAVYH,TEAL) if s.hot else ("rgba(239,233,221,0.10)","rgba(239,233,221,0.28)",TEAL)
        return f'<div style="width: 148px; height: 148px; border-radius: 74px; background: {bg}; border: 1px solid {br}; display: flex; align-items: center; justify-content: center"><svg aria-hidden="true" width="76" height="76" viewBox="0 0 24 24" fill="none" stroke="{st}" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round">{ICON[k]}</svg></div>'
    def h1(s,txt,size=96): return f'<h1 style="margin: 0; font-family: \'Oswald\', sans-serif; font-weight: 700; font-size: {size}px; line-height: 1.12; color: {s.fg}">{s.mk(txt,True)}</h1>'
    def p(s,txt,size=44,w=500): return f'<p style="margin: 0; font-size: {size}px; line-height: 1.38; font-weight: {w}; color: {s.fg}">{s.mk(txt)}</p>'
    def hl(s,txt,size=42): return f'<p style="margin: 0; font-size: {size}px; line-height: 1.5; font-weight: 800; color: {s.fg}">{s.u(html.escape(txt,quote=False))}</p>'
    def card(s,txt,size=42,w=600):
        box=("background: rgba(11,42,60,0.06); border: 2px solid rgba(11,42,60,0.30)" if s.hot else "background: rgba(239,233,221,0.10); border: 1px solid rgba(239,233,221,0.28)")
        return f'<div style="{box}; border-radius: 28px; padding: 36px 44px"><span style="font-size: {size}px; line-height: 1.38; font-weight: {w}; color: {s.fg}">{s.mk(txt)}</span></div>'
    def bullets(s,items):
        row=lambda t:f'<div style="display: flex; gap: 20px; align-items: flex-start"><div style="flex: none; width: 16px; height: 16px; margin-top: 16px; background: {NAVYH if s.hot else TEAL}; border-radius: 4px"></div><span style="font-size: 40px; line-height: 1.35; font-weight: 600; color: {s.fg}">{s.mk(t)}</span></div>'
        return '<div style="display: flex; flex-direction: column; gap: 18px">'+"".join(row(t) for t in items)+'</div>'
    def lines(s,items):
        return '<div style="display: flex; flex-direction: column; gap: 10px">'+"".join(s.p(t,46,800) for t in items)+'</div>'
    def block(s,b):
        k=b["type"]
        if k=="h1": return s.h1(b["text"],b.get("size",96))
        if k=="p": return s.p(b["text"],b.get("size",44),b.get("weight",500))
        if k=="hl": return s.hl(b["text"],b.get("size",42))
        if k=="card": return s.card(b["text"],b.get("size",42),b.get("weight",600))
        if k=="bullets": return s.bullets(b["items"])
        if k=="lines": return s.lines(b["items"])
        raise ValueError(k)

def page(layers,content,extra_css=""):
    return f"""<!doctype html><html lang="pt-BR"><head><meta charset="utf-8">
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Oswald:wght@500;600;700&family=Manrope:wght@400;500;600;700;800&display=swap">
<style>html,body{{margin:0;background:#0B2A3C}}{extra_css}</style></head><body>
<div id="s" style="width: 1080px; height: 1350px; box-sizing: border-box; background: #0B2A3C; font-family: 'Manrope', sans-serif; position: relative; overflow: hidden">{layers}{content}</div></body></html>"""

def inner(th,key,body,gap=30):
    return f'<div style="position: absolute; left: 88px; right: 88px; top: 96px; bottom: 96px; display: flex; flex-direction: column; justify-content: center; gap: {gap}px">{th.icon(key)}{body}</div>'

def build(spec,root):
    global TEALZ
    TEALZ=spec["destaques"]   # numeros dos slides em areia clara
    d=Th(False); pages={}
    foto=os.path.abspath(os.path.join(root,spec["foto"]))
    fy=spec.get("face_y",0.2)
    c=spec["capa"]
    layers=(f'<div class="foto" style="position: absolute; left: 0; top: 0; width: 1080px; height: 1350px"></div>'
     f'<div style="position: absolute; inset: 0; background: linear-gradient(155deg, rgba(27,106,143,0.42) 0%, rgba({NAVY},0) 52%, rgba(90,79,163,0.30) 100%)"></div>'
     f'<div style="position: absolute; inset: 0; background: linear-gradient(to bottom, rgba({NAVY},0.55) 0%, rgba({NAVY},0) 24%)"></div>'
     f'<div style="position: absolute; inset: 0; background: linear-gradient(to top, rgba({NAVY},0.97) 0%, rgba({NAVY},0.92) 32%, rgba({NAVY},0.55) 55%, rgba({NAVY},0) 80%)"></div>'
     f'<div style="position: absolute; inset: 0; background: linear-gradient(to left, rgba(239,233,221,0.55) 0px, rgba(239,233,221,0) 90px)"></div>')
    body=(f'<div style="position: absolute; left: 88px; right: 88px; bottom: 96px; display: flex; flex-direction: column; gap: 26px"><div style="width: 84px; height: 8px; border-radius: 4px; background: {TEAL}"></div>'
     +d.h1(c["titulo"],c.get("size",128))+d.p(c["subtitulo"],60,700)+f'<p style="margin: 0; font-size: 32px; font-weight: 700; color: {TEAL}">{html.escape(c.get("chamada","Arraste para o lado →"))}</p></div>')
    pages[1]=page(layers,body,f".foto{{background-image: url('file://{foto}'); background-size: cover; background-position: center {fy*100:.0f}%}}")
    for i,s in enumerate(spec["slides"],start=2):
        t=Th(i in TEALZ)
        b="".join(t.block(x) for x in s["blocos"])
        pages[i]=page(base_svg(i)+waves_svg(i),inner(t,s["icone"],b))
    return pages

def main():
    from playwright.sync_api import sync_playwright
    specp=sys.argv[1]; root=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    spec=json.load(open(specp))
    assert len(spec["slides"])==8, "o carrossel tem capa + 8 slides"
    pages=build(spec,root)
    out=os.path.join(root,"out","carousel",spec["id"]); os.makedirs(out,exist_ok=True)
    tmp=os.path.join(root,"_tmp_render"); os.makedirs(tmp,exist_ok=True)
    with sync_playwright() as p:
        kw={"args":["--allow-file-access-from-files"]}
        if os.environ.get("CHROME_PATH"): kw["executable_path"]=os.environ["CHROME_PATH"]
        br=p.chromium.launch(**kw)
        pg=br.new_page(viewport={"width":1080,"height":1350})
        for i,h in pages.items():
            hp=os.path.join(tmp,f"s{i}.html"); open(hp,"w").write(h)
            pg.goto("file://"+hp,wait_until="networkidle"); pg.evaluate("document.fonts.ready")
            pg.locator("#s").screenshot(path=os.path.join(out,f"slide_{i:02d}.jpg"),type="jpeg",quality=90)
        br.close()
    import shutil; shutil.rmtree(tmp)
    print("ok",out)
if __name__=="__main__": main()
