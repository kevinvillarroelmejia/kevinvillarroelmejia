"""Genera assets/portrait.txt (retrato ASCII) a partir del avatar de GitHub.

Se ejecuta una sola vez a mano (necesita Pillow):
    pip install pillow
    python scripts/make_portrait.py
"""
import io
import os
import sys
import urllib.request

from PIL import Image, ImageOps, ImageEnhance

USER_ID = "116190636"
AVATAR = f"https://avatars.githubusercontent.com/u/{USER_ID}?s=400"
# Recorte (izq, arriba, der, abajo) sobre la imagen de 400x400: la cara
CROP = (246, 6, 398, 196)
COLS = 56
CELL_ASPECT = 1.85          # alto/ancho de una celda de texto
RAMP = " .:-=+*#%@"
BG_CUT = 0.66              # brillo a partir del cual es "fondo"

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def main(path=None):
    if path:
        img = Image.open(path)
    else:
        with urllib.request.urlopen(AVATAR) as r:
            img = Image.open(io.BytesIO(r.read()))
    img = img.convert("L").crop(CROP)
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
            # La pared del fondo es casi blanca: se deja vacía.
            # El resto se estira y lo claro se dibuja denso (terminal oscura).
            ch = " "
            if v < BG_CUT:
                t = v / BG_CUT
                ch = RAMP[min(len(RAMP) - 1, int(t * len(RAMP)))]
            row.append(ch)
        lines.append("".join(row).rstrip())
    out = os.path.join(ROOT, "assets", "portrait.txt")
    with open(out, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    print(f"{out}: {rows} filas x {COLS} columnas")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else None)
