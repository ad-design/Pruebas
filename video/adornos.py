"""Genera las capas decorativas de estilo mexicano (1080x1920, RGBA).

Salida en DIR:
  loop/0000.png ... : bucle sin cortes de LOOP_S segundos (papel picado que se mece,
                      pétalos de cempasúchil cayendo, guirnalda de flores y velas)
  titulo.png, final.png : rótulos de entrada y salida
Uso: python adornos.py DIR FUENTE_TITULO FUENTE_SUBTITULO
"""
import math
import os
import sys
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

W, H, FPS, LOOP_S = 1080, 1920, 30, 8
N = FPS * LOOP_S
OUT, F_TIT, F_SUB = sys.argv[1], sys.argv[2], sys.argv[3]
rng = np.random.default_rng(11)

COLORES = [(230, 0, 126), (255, 122, 0), (0, 166, 166), (255, 200, 0),
           (123, 44, 191), (46, 204, 113)]
NARANJA = [(255, 140, 0), (255, 165, 0), (255, 120, 10), (255, 190, 30), (240, 100, 0)]


# ---------- papel picado ----------
def bandera(color, motivo, w=160, h=200):
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, w, h - 18], fill=color + (235,))
    for x in range(0, w, 20):  # flecos inferiores
        d.polygon([(x, h - 18), (x + 20, h - 18), (x + 10, h)], fill=color + (235,))
    m = Image.new("L", (w, h), 0)
    md = ImageDraw.Draw(m)
    for x in range(10, w - 5, 20):  # festón superior
        md.ellipse([x - 4, 10, x + 4, 18], fill=255)
    for x in range(14, w - 10, 22):  # rombos del borde inferior
        md.polygon([(x, h - 40), (x + 7, h - 32), (x, h - 24), (x - 7, h - 32)], fill=255)
    cx, cy = w // 2, (h - 18) // 2 + 6
    if motivo == 0:  # flor
        for k in range(8):
            a = k * math.pi / 4
            px, py = cx + 34 * math.cos(a), cy + 34 * math.sin(a)
            md.ellipse([px - 13, py - 13, px + 13, py + 13], fill=255)
        md.ellipse([cx - 14, cy - 14, cx + 14, cy + 14], fill=255)
        img_c = Image.new("L", (w, h), 0)
        ImageDraw.Draw(img_c).ellipse([cx - 7, cy - 7, cx + 7, cy + 7], fill=255)
        m = Image.fromarray(np.where(np.array(img_c) > 0, 0, np.array(m)).astype(np.uint8))
        md = ImageDraw.Draw(m)
    elif motivo == 1:  # rombos concéntricos (ojo de Dios)
        for r, val in [(50, 255), (36, 0), (24, 255), (11, 0)]:
            md.polygon([(cx, cy - r), (cx + r, cy), (cx, cy + r), (cx - r, cy)], fill=val)
        for dx, dy in [(-44, -44), (44, -44), (-44, 44), (44, 44)]:
            md.ellipse([cx + dx - 7, cy + dy - 7, cx + dx + 7, cy + dy + 7], fill=255)
    elif motivo == 2:  # corazón
        md.ellipse([cx - 40, cy - 34, cx + 2, cy + 6], fill=255)
        md.ellipse([cx - 2, cy - 34, cx + 40, cy + 6], fill=255)
        md.polygon([(cx - 38, cy - 6), (cx + 38, cy - 6), (cx, cy + 44)], fill=255)
    else:  # estrella / sol
        pts = []
        for k in range(16):
            r = 46 if k % 2 == 0 else 20
            a = k * math.pi / 8 - math.pi / 2
            pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))
        md.polygon(pts, fill=255)
    for x, y in [(18, 34), (w - 18, 34), (18, h - 60), (w - 18, h - 60)]:
        md.ellipse([x - 6, y - 6, x + 6, y + 6], fill=255)
    a = np.array(img)
    a[..., 3] = np.where(np.array(m) > 0, 0, a[..., 3])
    out = Image.fromarray(a)
    # leve sombreado para dar textura de papel
    sh = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    ImageDraw.Draw(sh).rectangle([0, 0, w, 8], fill=(0, 0, 0, 40))
    return Image.alpha_composite(out, sh)


def fila_banderas(y, n, escala, fase):
    w = int(160 * escala)
    paso = W / n
    flags = []
    for i in range(n):
        b = bandera(COLORES[(i + fase) % len(COLORES)], (i + fase) % 4)
        b = b.resize((w, int(200 * escala)), Image.LANCZOS)
        flags.append((b, paso * i + (paso - w) / 2, rng.uniform(0, 2 * math.pi)))
    return y, flags


FILAS = [fila_banderas(-6, 6, 1.0, 0), fila_banderas(150, 7, 0.72, 3)]


def dibuja_papel_picado(lienzo, t):
    d = ImageDraw.Draw(lienzo)
    for y, flags in FILAS:
        d.line([(0, y + 6), (W, y + 6)], fill=(250, 240, 220, 220), width=3)
        for b, x, ph in flags:
            ang = 4.0 * math.sin(2 * math.pi * t / LOOP_S + ph)
            r = b.rotate(ang, resample=Image.BICUBIC, expand=True,
                         center=(b.width / 2, 0))
            lienzo.alpha_composite(r, (int(x - (r.width - b.width) / 2), int(y + 4)))


# ---------- pétalos ----------
NP = 46
PETALOS = []
for _ in range(NP):
    vueltas = int(rng.integers(1, 3))  # vueltas completas por bucle -> bucle sin corte
    PETALOS.append(dict(x=rng.uniform(0, W), y0=rng.uniform(0, H + 200), v=vueltas * (H + 200) / LOOP_S,
                        amp=rng.uniform(15, 60), ph=rng.uniform(0, 2 * math.pi),
                        tam=rng.uniform(10, 22), col=NARANJA[int(rng.integers(0, 5))],
                        giro=int(rng.integers(-2, 3)) or 1, a0=rng.uniform(0, 360)))


def dibuja_petalos(lienzo, t):
    for p in PETALOS:
        y = (p["y0"] + p["v"] * t) % (H + 200) - 100
        x = p["x"] + p["amp"] * math.sin(2 * math.pi * t / LOOP_S * 2 + p["ph"])
        s = int(p["tam"])
        pet = Image.new("RGBA", (s * 2, s * 2), (0, 0, 0, 0))
        pd = ImageDraw.Draw(pet)
        pd.ellipse([s // 2, 0, s * 3 // 2, s * 2], fill=p["col"] + (225,))
        pd.line([(s, 3), (s, s * 2 - 3)], fill=(200, 80, 0, 160), width=1)
        ang = p["a0"] + p["giro"] * 360 * t / LOOP_S
        pet = pet.rotate(ang, resample=Image.BICUBIC, expand=True)
        lienzo.alpha_composite(pet, (int(x - pet.width / 2), int(y - pet.height / 2)))


# ---------- guirnalda de cempasúchil y velas (estática + llamas) ----------
def flor(r, base):
    img = Image.new("RGBA", (r * 2 + 4, r * 2 + 4), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    c = r + 2
    for capa, (rr, n) in enumerate([(r, 18), (r * 0.78, 14), (r * 0.55, 10), (r * 0.32, 7)]):
        col = tuple(min(255, int(v * (0.82 + 0.08 * capa))) for v in base)
        for k in range(n):
            a = 2 * math.pi * k / n + capa * 0.4
            px, py = c + rr * 0.62 * math.cos(a), c + rr * 0.62 * math.sin(a)
            pr = rr * 0.42
            d.ellipse([px - pr, py - pr, px + pr, py + pr], fill=col + (255,),
                      outline=(170, 70, 0, 255))
    return img


def base_estatica():
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    # sombra cálida bajo la guirnalda
    sh = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ImageDraw.Draw(sh).rectangle([0, H - 210, W, H], fill=(40, 10, 30, 170))
    img.alpha_composite(sh.filter(ImageFilter.GaussianBlur(40)))
    for vx in VELAS:  # cuerpo de las velas
        d = ImageDraw.Draw(img)
        d.rounded_rectangle([vx - 26, H - 330, vx + 26, H - 150], 10, fill=(250, 238, 210, 255))
        d.rectangle([vx - 26, H - 300, vx + 26, H - 280], fill=(230, 0, 126, 255))
        d.line([(vx, H - 330), (vx, H - 344)], fill=(40, 30, 30, 255), width=3)
    hojas = ImageDraw.Draw(img)
    for _ in range(60):
        x, y = rng.uniform(0, W), H - rng.uniform(40, 150)
        a = rng.uniform(0, math.pi)
        hojas.polygon([(x, y), (x + 40 * math.cos(a), y - 18 * math.sin(a) - 10),
                       (x + 50 * math.cos(a), y + 5)], fill=(40, 120, 50, 255))
    flores = []
    for _ in range(70):
        flores.append((rng.uniform(-20, W + 20), H - rng.uniform(20, 140) ** 1.0,
                       int(rng.uniform(34, 62)), NARANJA[int(rng.integers(0, 5))]))
    for x, y, r, col in sorted(flores, key=lambda f: f[1]):
        f = flor(r, col)
        img.alpha_composite(f, (int(x - f.width / 2), int(y - f.height / 2)))
    return img


VELAS = [110, W - 110]


def dibuja_llamas(lienzo, t):
    for i, vx in enumerate(VELAS):
        fl = 1 + 0.12 * math.sin(2 * math.pi * t * 3 + i) + 0.06 * math.sin(2 * math.pi * t * 7.25 + 2 * i)
        glow = Image.new("RGBA", (420, 420), (0, 0, 0, 0))
        ImageDraw.Draw(glow).ellipse([60, 60, 360, 360], fill=(255, 170, 60, int(90 * fl)))
        glow = glow.filter(ImageFilter.GaussianBlur(50))
        lienzo.alpha_composite(glow, (vx - 210, H - 344 - 30 - 210))
        h = 52 * fl
        d = ImageDraw.Draw(lienzo)
        sway = 3 * math.sin(2 * math.pi * t * 2 + i)
        d.ellipse([vx - 13 + sway, H - 344 - h, vx + 13 + sway, H - 336], fill=(255, 150, 20, 240))
        d.ellipse([vx - 7 + sway, H - 344 - h * 0.6, vx + 7 + sway, H - 338], fill=(255, 240, 160, 255))


def texto(lineas, nombre):
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    velo = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ImageDraw.Draw(velo).rounded_rectangle([90, 640, W - 90, 1120], 60, fill=(30, 5, 35, 150))
    img.alpha_composite(velo.filter(ImageFilter.GaussianBlur(25)))
    d = ImageDraw.Draw(img)
    y = 700
    for txt, fuente, tam, col in lineas:
        f = ImageFont.truetype(fuente, tam)
        bx = d.textbbox((0, 0), txt, font=f)
        x = (W - (bx[2] - bx[0])) / 2 - bx[0]
        d.text((x, y), txt, font=f, fill=col, stroke_width=max(3, tam // 18),
               stroke_fill=(60, 10, 40))
        y += int(tam * 1.25)
    img.save(os.path.join(OUT, nombre))


if __name__ == "__main__":
    os.makedirs(os.path.join(OUT, "loop"), exist_ok=True)
    base = base_estatica()
    for i in range(N):
        t = i / FPS
        c = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        dibuja_petalos(c, t)
        c.alpha_composite(base)
        dibuja_llamas(c, t)
        dibuja_papel_picado(c, t)
        c.save(os.path.join(OUT, "loop", f"{i:04d}.png"), compress_level=1)
    texto([("Cuarteto", F_TIT, 150, (255, 140, 0)), ("de cuerda", F_TIT, 150, (255, 140, 0)),
           ("¡a la mexicana!", F_SUB, 84, (255, 230, 120))], "titulo.png")
    texto([("¡Que viva", F_TIT, 120, (255, 140, 0)), ("la música!", F_TIT, 120, (255, 140, 0))],
          "final.png")
