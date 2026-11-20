"""Genera assets/portrait.txt (retrato ASCII) a partir del avatar de GitHub.

Se ejecuta una sola vez a mano (necesita Pillow):
    pip install pillow
    python scripts/make_portrait.py
"""
import io
import os
import sys
import urllib.request

from PIL import Image, ImageDraw, ImageEnhance, ImageOps

USER_ID = "116190636"
AVATAR = f"https://avatars.githubusercontent.com/u/{USER_ID}?s=400"
# Recorte (izq, arriba, der, abajo) sobre la imagen de 400x400: la cara
CROP = (55, 10, 355, 390)
COLS = 56
CELL_ASPECT = 1.85          # alto/ancho de una celda de texto
RAMP = " .:-=+*#%@"
BG_CUT = 0.86              # brillo a partir del cual es "fondo" (el círculo crema)
CIRCLE = (200, 200, 196)    # centro y radio del avatar redondo; fuera se deja vacío

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def main(path=None):
    if path:
        img = Image.open(path)
    else:
        with urllib.request.urlopen(AVATAR) as r:
            img = Image.open(io.BytesIO(r.read()))
    img = img.convert("L").resize((400, 400))
    # Las esquinas fuera del círculo pasan a blanco para que cuenten como fondo
    cx, cy, rad = CIRCLE
    circle = Image.new("L", img.size, 0)
    ImageDraw.Draw(circle).ellipse((cx - rad, cy - rad, cx + rad, cy + rad), fill=255)
    img = Image.composite(img, Image.new("L", img.size, 255), circle)
    img = img.crop(CROP)
    img = ImageOps.autocontrast(img, cutoff=2)
    img = ImageEnhance.Contrast(img).enhance(1.25)
    w, h = img.size
    rows = round(h / w * COLS / CELL_ASPECT)
    img = img.resize((COLS, rows), Image.LANCZOS)
    px = img.load()
    lines = []
    for y in range(rows):
        row = []
        for x in range(COLS):
            v = px[x, y] / 255
            # El fondo crema se deja vacío. Lo oscuro (pelo, contornos)
            # se dibuja denso, como un dibujo a tinta sobre la terminal.
            ch = " "
            if v < BG_CUT:
                t = 1 - v / BG_CUT
                ch = RAMP[min(len(RAMP) - 1, int(t * len(RAMP)))]
            row.append(ch)
        lines.append("".join(row).rstrip())
    out = os.path.join(ROOT, "assets", "portrait.txt")
    with open(out, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    print(f"{out}: {rows} filas x {COLS} columnas")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else None)
