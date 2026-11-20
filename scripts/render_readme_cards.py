"""Dibuja las tarjetas SVG animadas del README (estilo terminal "Kevin OS").

Lee data/contributions.json y data/repos.json (los genera fetch_contributions.py)
y escribe en cards/:
    hero.svg            log de arranque + retrato ASCII + nombre
    graph.svg           gráfica de contribuciones del último año
    htop.svg            panel tipo htop: meses, racha como "uptime" y repos
    key-f1..f4.svg      barra de teclas F1-F4 con enlaces

Solo CSS dentro del SVG, SMIL y fuentes embebidas en base64 (GitHub no deja
JavaScript ni fuentes externas). Todo se apaga con prefers-reduced-motion.

    python scripts/render_readme_cards.py           # animado
    STATIC=1 python scripts/render_readme_cards.py  # estado final, para revisar
"""
import base64
import datetime as dt
import json
import os
from xml.sax.saxutils import escape

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CARDS = os.path.join(ROOT, "cards")
STATIC = os.environ.get("STATIC") == "1"
W = 880

# ---------------------------------------------------------------- contenido
# Datos sacados del README anterior del perfil (nada inventado).
PROFILE = {
    "name": "Kevin Villarroel",
    "role": "Desarrollador junior · Java · Python · SQL",
    "boot": [
        ("OK", "Montando /home/kevin", "Madrid, España"),
        ("OK", "Restaurando sesión", "SMR + 12 meses de soporte técnico"),
        ("OK", "Cargando módulos", "java python kotlin sql"),
        ("OK", "Iniciando job-market-analyzer.service", "selenium + flask"),
        ("OK", "Configurando idiomas", "español nativo · inglés B1"),
        ("OK", "Compilando 2º de DAM", "acceso a datos · PSP · android"),
        ("WAIT", "Buscando primer puesto junior", "prácticas o junior en Madrid"),
    ],
}

# Tabla de procesos del panel htop. El lenguaje y el último push se
# actualizan desde la API (data/repos.json); esto es el valor por defecto.
REPOS = [
    ("job-market-analyzer", "Python", "scraper de ofertas tech + dashboard"),
    ("ProyectoBootStrap_KevinStudio", "JavaScript", "e-commerce KevStudio (Bootstrap 5)"),
    ("servicios_procesos", "Java", "hilos, procesos y sincronización"),
    ("ACCESO_DATOS", "Java", "ficheros, JDBC y persistencia"),
    ("MULTIMEDIA", "Kotlin", "apps Android: Dice Roller, Tip Time…"),
    ("AMPLIACION_DE_ENTORNOS", "Java", "testing y entornos de desarrollo"),
]

KEYS = [
    ("F1", "LinkedIn", "key-f1.svg"),
    ("F2", "Email", "key-f2.svg"),
    ("F3", "Proyecto", "key-f3.svg"),
    ("F4", "Repos", "key-f4.svg"),
]

MESES = ["ene", "feb", "mar", "abr", "may", "jun", "jul", "ago", "sep", "oct", "nov", "dic"]
DIAS = ["lun", "mar", "mié", "jue", "vie", "sáb", "dom"]

# ---------------------------------------------------------------- estilo
C = {
    "bg": "#0b0f14",
    "bar": "#111821",
    "line": "#1e2a36",
    "fg": "#c9d1d9",
    "dim": "#6e7b88",
    "green": "#3fb950",
    "cyan": "#39c5cf",
    "amber": "#e3b341",
    "red": "#ff7b72",
    "violet": "#bc8cff",
    "blue": "#58a6ff",
}
LANG = {"Python": C["blue"], "Java": C["red"], "JavaScript": C["amber"],
        "Kotlin": C["violet"], "HTML": C["red"], "CSS": C["violet"]}
LEVELS = ["#161b22", "#0e4429", "#006d32", "#26a641", "#39d353"]


def font_b64(name):
    with open(os.path.join(ROOT, "assets", "fonts", name), "rb") as f:
        return base64.b64encode(f.read()).decode()


FONTS = (
    "@font-face{font-family:'GM';font-weight:400;"
    f"src:url(data:font/woff2;base64,{font_b64('geistmono-400.woff2')}) format('woff2')}}"
    "@font-face{font-family:'GM';font-weight:700;"
    f"src:url(data:font/woff2;base64,{font_b64('geistmono-700.woff2')}) format('woff2')}}"
)

BASE_CSS = f"""
text{{font-family:'GM',ui-monospace,SFMono-Regular,Menlo,Consolas,monospace;fill:{C['fg']};white-space:pre}}
.dim{{fill:{C['dim']}}} .g{{fill:{C['green']}}} .c{{fill:{C['cyan']}}} .a{{fill:{C['amber']}}}
.r{{fill:{C['red']}}} .v{{fill:{C['violet']}}} .b{{font-weight:700}}
.in{{animation:fadeUp .5s cubic-bezier(.2,.7,.2,1) both}}
.type{{animation:type .45s steps(28,end) both}}
.pop{{transform-box:fill-box;transform-origin:center;animation:pop .35s cubic-bezier(.3,1.6,.5,1) both}}
.grow{{transform-box:fill-box;transform-origin:left center;animation:grow .7s cubic-bezier(.2,.8,.2,1) both}}
.blink{{animation:blink 1s steps(1,end) infinite}}
.pulse{{transform-box:fill-box;transform-origin:center;animation:pulse 1.6s ease-in-out infinite}}
.nudge{{animation:nudge 1.8s ease-in-out infinite}}
@keyframes fadeUp{{from{{opacity:0;transform:translateY(6px)}}to{{opacity:1;transform:none}}}}
@keyframes type{{from{{clip-path:inset(0 100% 0 0)}}to{{clip-path:inset(0 0 0 0)}}}}
@keyframes pop{{from{{opacity:0;transform:scale(.2)}}to{{opacity:1;transform:none}}}}
@keyframes grow{{from{{transform:scaleX(0)}}to{{transform:none}}}}
@keyframes blink{{50%{{opacity:0}}}}
@keyframes pulse{{0%,100%{{opacity:1;transform:none}}50%{{opacity:.35;transform:scale(.7)}}}}
@keyframes nudge{{0%,60%,100%{{transform:none}}30%{{transform:translate(2px,-2px)}}}}
@media (prefers-reduced-motion:reduce){{*{{animation:none!important}}}}
"""
if STATIC:
    BASE_CSS += "*{animation:none!important}"


def d(sec):
    """style con retraso de animación."""
    return f' style="animation-delay:{sec:.2f}s"'


def t(x, y, s, cls="", size=13, extra=""):
    c = f' class="{cls}"' if cls else ""
    return f'<text x="{x}" y="{y}" font-size="{size}"{c}{extra}>{escape(s)}</text>'


def svg(h, body, title, defs="", w=W):
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" '
        f'viewBox="0 0 {w} {h}" role="img" aria-label="{escape(title)}">'
        f"<title>{escape(title)}</title>"
        f"<style>{FONTS}{BASE_CSS}</style>{defs}{body}</svg>"
    )


def window(h, title, w=W):
    """Marco de ventana de terminal."""
    return (
        f'<rect x="1" y="1" width="{w-2}" height="{h-2}" rx="10" fill="{C["bg"]}" stroke="{C["line"]}"/>'
        f'<path d="M1 11a10 10 0 0 1 10-10h{w-22}a10 10 0 0 1 10 10v21H1z" fill="{C["bar"]}"/>'
        f'<line x1="1" y1="32" x2="{w-1}" y2="32" stroke="{C["line"]}"/>'
        f'<circle cx="20" cy="17" r="5.5" fill="#ff5f57"/>'
        f'<circle cx="38" cy="17" r="5.5" fill="#febc2e"/>'
        f'<circle cx="56" cy="17" r="5.5" fill="#28c840"/>'
        + t(w / 2, 21, title, "dim", 12, ' text-anchor="middle"')
    )


def countup(x, y, value, cls, size, begin, dur=1.0, frames=18, suffix=""):
    """Número que cuenta desde 0 con fotogramas SMIL <set> (CSS no cambia texto)."""
    if STATIC or value == 0:
        return t(x, y, f"{value}{suffix}", cls, size)
    vals = []
    for i in range(1, frames + 1):
        v = round(value * i / frames)
        if not vals or vals[-1] != v:
            vals.append(v)
    step = dur / len(vals)
    out = []
    for i, v in enumerate(vals):
        start = begin + i * step
        last = i == len(vals) - 1
        end = "" if last else f' end="{start + step:.3f}s"'
        out.append(
            f'<text x="{x}" y="{y}" font-size="{size}" class="{cls}" visibility="hidden">'
            f'{v}{escape(suffix)}<set attributeName="visibility" to="visible" '
            f'begin="{start:.3f}s"{end} fill="{"freeze" if last else "remove"}"/></text>'
        )
    return "".join(out)


# ---------------------------------------------------------------- datos
def load_json(name, default):
    path = os.path.join(ROOT, "data", name)
    result = default
    if os.path.exists(path):
        with open(path, encoding="utf-8") as f:
            result = json.load(f)
    return result


def stats(days):
    today = dt.date.today()
    if days:
        today = dt.date.fromisoformat(days[-1]["date"])
    counts = {dt.date.fromisoformat(x["date"]): x["count"] for x in days}
    total = sum(counts.values())
    active = sum(1 for v in counts.values() if v > 0)

    # Racha actual: si hoy aún no hay nada, se empieza a contar desde ayer
    cur = 0
    day = today if counts.get(today, 0) > 0 else today - dt.timedelta(days=1)
    while counts.get(day, 0) > 0:
        cur += 1
        day -= dt.timedelta(days=1)

    best = run = 0
    for k in sorted(counts):
        run = run + 1 if counts[k] > 0 else 0
        best = max(best, run)

    busiest = max(counts.items(), key=lambda kv: kv[1], default=(today, 0))

    months = []
    y, m = today.year, today.month
    for _ in range(12):
        months.append((y, m))
        m -= 1
        if m == 0:
            y, m = y - 1, 12
    months.reverse()
    per_month = [(f"{MESES[mm-1]}", sum(v for k, v in counts.items() if (k.year, k.month) == (yy, mm)))
                 for yy, mm in months]

    by_wd = [0] * 7
    for k, v in counts.items():
        by_wd[k.weekday()] += v
    return {
        "total": total, "active": active, "streak": cur, "best": best,
        "busiest": busiest, "months": per_month, "today": today,
        "weekday": DIAS[by_wd.index(max(by_wd))] if total else "-",
        "counts": counts,
    }


def dias(n):
    return f"{n} día" if n == 1 else f"{n} días"


def ago(iso, today):
    result = "—"
    if iso:
        delta = (today - dt.date.fromisoformat(iso[:10])).days
        if delta <= 0:
            result = "hoy"
        elif delta < 30:
            result = f"{delta}d"
        elif delta < 365:
            result = f"{delta // 30}mes"
        else:
            result = f"{delta // 365}a"
    return result


# ---------------------------------------------------------------- tarjetas
def hero():
    with open(os.path.join(ROOT, "assets", "portrait.txt"), encoding="utf-8") as f:
        rows = f.read().rstrip("\n").split("\n")
    H = 404
    fs, lh = 7.0, 7.6
    body = [window(H, "kevin@dam: ~ — tty1")]

    # Retrato ASCII: se imprime fila a fila
    py0 = 58
    for i, row in enumerate(rows):
        body.append(
            f'<text x="22" y="{py0 + i * lh:.1f}" font-size="{fs}" class="in" fill="#8b98a5" style="fill:#8b98a5;animation-delay:{0.15 + i * 0.03:.2f}s">'
            f"{escape(row)}</text>"
        )
    body.append(f'<rect x="20" y="{py0 + len(rows) * lh - 2:.0f}" width="240" height="1" fill="{C["line"]}"/>')

    x0 = 290
    body.append(t(x0, 60, "KevinOS 2.0 (DAM) — arranque", "dim in", 12, d(0.1)))
    y = 86
    for i, (status, what, detail) in enumerate(PROFILE["boot"]):
        delay = 0.35 + i * 0.32
        ok = status == "OK"
        tag_cls = "g" if ok else "a"
        tag = "[  OK  ]" if ok else "[ WAIT ]"
        dots = "." * max(2, 40 - len(what))
        body.append(
            f'<g class="type"{d(delay)}>'
            f'<text x="{x0}" y="{y}" font-size="12.5"><tspan class="{tag_cls} b">{tag}</tspan> '
            f'{escape(what)} <tspan class="dim">{dots}</tspan></text>'
            f'<text x="{x0 + 28}" y="{y + 15}" font-size="11" class="dim">↳ {escape(detail)}</text></g>'
        )
        if not ok:
            body.append(f'<circle cx="{W - 32}" cy="{y - 4}" r="4" fill="{C["amber"]}" class="pulse"/>')
        y += 30

    name_y = y + 26
    body.append(
        f'<text x="{x0}" y="{name_y}" font-size="34" font-weight="700" fill="url(#shine)" '
        f'class="in"{d(2.7)}>{escape(PROFILE["name"])}</text>'
    )
    body.append(t(x0, name_y + 24, PROFILE["role"], "c in", 13, d(2.95)))
    body.append(
        f'<g class="in"{d(3.2)}><text x="{x0}" y="{name_y + 52}" font-size="13">'
        f'<tspan class="g b">kevin@dam</tspan><tspan class="dim">:</tspan>'
        f'<tspan class="c">~</tspan><tspan class="dim">$ </tspan></text>'
        f'<rect x="{x0 + 7.8 * 14}" y="{name_y + 41}" width="8" height="14" fill="{C["green"]}" class="blink"/></g>'
    )

    anim = "" if STATIC else (
        '<animateTransform attributeName="gradientTransform" type="translate" '
        'values="-1 0;-1 0;1.2 0" keyTimes="0;.55;1" dur="5s" begin="3s" repeatCount="indefinite"/>'
    )
    defs = (
        f'<defs><linearGradient id="shine" x1="0" x2="1" y1="0" y2="0">'
        f'<stop offset="0" stop-color="{C["fg"]}"/><stop offset=".42" stop-color="{C["fg"]}"/>'
        f'<stop offset=".5" stop-color="{C["cyan"]}"/><stop offset=".58" stop-color="{C["fg"]}"/>'
        f'<stop offset="1" stop-color="{C["fg"]}"/>{anim}</linearGradient></defs>'
    )
    if STATIC:
        defs = defs.replace(f'stop-color="{C["cyan"]}"', f'stop-color="{C["fg"]}"')
    return svg(H, "".join(body), f"{PROFILE['name']} — {PROFILE['role']}", defs)


def graph(s):
    H = 214
    cell, gap = 12, 2.5
    step = cell + gap
    x0, y0 = 58, 74
    today = s["today"]
    # Semanas de lunes a domingo; la última columna es la semana de hoy
    start = today - dt.timedelta(days=today.weekday()) - dt.timedelta(weeks=52)
    body = [window(H, "git log --graph --since='1 year'")]
    body.append(
        f'<text x="22" y="52" font-size="12.5" class="in"{d(0.05)}><tspan class="g b">$</tspan> '
        f'git log --author=kevin --since="1 year" | wc -l</text>'
    )
    body.append(f'<g class="in"{d(0.3)}>' + t(W - 22, 52, "", "", 12.5, ' text-anchor="end"')[:-7]
                + f'<tspan class="c b">{s["total"]}</tspan><tspan class="dim"> contribuciones</tspan></text></g>')
    last_month = None
    for wk in range(53):
        col_day = start + dt.timedelta(weeks=wk)
        if col_day.month != last_month:
            if wk < 51:
                body.append(t(x0 + wk * step, y0 - 7, MESES[col_day.month - 1], "dim", 10))
            last_month = col_day.month
        for wd in range(7):
            day = col_day + dt.timedelta(days=wd)
            if day > today:
                continue
            v = s["counts"].get(day, 0)
            lvl = 0 if v == 0 else 1 if v < 3 else 2 if v < 6 else 3 if v < 10 else 4
            body.append(
                f'<rect x="{x0 + wk * step:.1f}" y="{y0 + wd * step:.1f}" width="{cell}" height="{cell}" '
                f'rx="2.5" fill="{LEVELS[lvl]}" class="pop"{d(0.4 + wk * 0.022 + wd * 0.01)}/>'
            )
    for wd, lab in ((0, "lun"), (2, "mié"), (4, "vie")):
        body.append(t(22, y0 + wd * step + 10, lab, "dim", 10))
    lx = W - 22 - 5 * step - 72
    body.append(t(lx, H - 8, "menos", "dim", 10))
    for i, col in enumerate(LEVELS):
        body.append(f'<rect x="{lx + 40 + i * step:.1f}" y="{H - 18}" width="10" height="10" rx="2" fill="{col}"/>')
    body.append(t(lx + 40 + 5 * step + 4, H - 8, "más", "dim", 10))
    return svg(H, "".join(body), f"{s['total']} contribuciones en el último año")


def htop(s, repos_api):
    H = 384
    body = [window(H, "htop — kevin@dam")]
    months = s["months"]
    mx = max((v for _, v in months), default=0) or 1
    best_i = max(range(12), key=lambda i: months[i][1]) if s["total"] else -1
    nbar = 16
    for i, (lab, v) in enumerate(months):
        col, row = divmod(i, 6)
        x = 22 + col * 222
        y = 60 + row * 19
        n = round(v / mx * nbar)
        cls = "c b" if i == best_i else "g"
        delay = 0.2 + i * 0.07
        body.append(t(x, y, f"{lab}", "c" if i == best_i else "dim", 12))
        body.append(t(x + 32, y, "[", "", 12))
        body.append(t(x + 32 + 7.2 * (nbar + 1), y, "]", "", 12))
        if n:
            body.append(
                f'<text x="{x + 39.2:.1f}" y="{y}" font-size="12" class="{cls} grow"{d(delay)}>{"|" * n}</text>'
            )
        body.append(t(x + 32 + 7.2 * (nbar + 2) + 4, y, f"{v:>4}", "c b" if i == best_i else "", 12))
        if i == best_i:
            body.append(t(x + 32 + 7.2 * (nbar + 7) + 2, y, "▲", "c pop", 11, d(delay + 0.6)))

    # Columna derecha: el resumen de htop
    rx = 482
    by, bd = s["busiest"]
    best_lab = months[best_i][0] if best_i >= 0 else "-"
    best_val = months[best_i][1] if best_i >= 0 else 0
    lines = [
        (60, "Tasks: ", f"{len(REPOS)} repos destacados, ", "1 running"),
        (79, "Load average: ", f"{dias(s['active'])} activos", ""),
        (117, "Mejor racha: ", dias(s["best"]), ""),
        (136, "Día más activo: ", f"{by.day} {MESES[by.month-1]} ({bd})" if bd else "-", f" · {s['weekday']}"),
        (155, "Mejor mes: ", f"{best_lab} ({best_val})", ""),
    ]
    for i, (y, k, v, extra) in enumerate(lines):
        body.append(
            f'<text x="{rx}" y="{y}" font-size="12" class="in"{d(0.3 + i * 0.12)}>'
            f'<tspan class="c b">{escape(k)}</tspan>{escape(v)}<tspan class="g b">{escape(extra)}</tspan></text>'
        )
    body.append(f'<g class="in"{d(0.4)}>' + t(rx, 98, "Uptime: ", "c b", 12) + "</g>")
    unit = " día" if s["streak"] == 1 else " días"
    body.append(countup(rx + 7.2 * 8, 98, s["streak"], "b g", 12, 0.6, suffix=unit))
    body.append(t(rx + 7.2 * (9 + len(dias(s["streak"]))), 98, "(racha actual)", "dim in", 12, d(0.6)))

    # Tabla de procesos
    ty = 188
    body.append(f'<rect x="12" y="{ty}" width="{W - 24}" height="20" fill="{C["green"]}"/>')
    hdr = f"{'PID':>5}  {'USER':<6} {'LANG':<11} {'★':>2} {'TIME+':>6}  COMMAND"
    body.append(t(18, ty + 14.5, hdr, "b", 12, f' fill="{C["bg"]}" style="fill:{C["bg"]}"'))
    rows_y = ty + 22
    rh = 22
    if not STATIC:
        ys = ";".join(f"{rows_y + i * rh}" for i in range(len(REPOS))) + f";{rows_y}"
        n = len(REPOS)
        kt = ";".join(f"{i / n:.3f}" for i in range(n)) + ";1"
        body.append(
            f'<rect x="12" y="{rows_y}" width="{W - 24}" height="{rh}" fill="{C["cyan"]}" opacity=".16">'
            f'<animate attributeName="y" values="{ys}" keyTimes="{kt}" dur="{n * 1.4}s" '
            f'begin="1.6s" calcMode="discrete" repeatCount="indefinite"/></rect>'
        )
    else:
        body.append(f'<rect x="12" y="{rows_y}" width="{W - 24}" height="{rh}" fill="{C["cyan"]}" opacity=".16"/>')
    for i, (name, lang, desc) in enumerate(REPOS):
        api = repos_api.get(name, {})
        lang = api.get("language") or lang
        stars = api.get("stars", 0)
        when = ago(api.get("pushed_at"), s["today"])
        y = rows_y + i * rh + 15
        pid = 1000 + i * 137
        body.append(
            f'<text x="18" y="{y}" font-size="12" class="in"{d(1.0 + i * 0.1)}>'
            f'<tspan class="dim">{pid:>5}  </tspan><tspan class="g">{"kevin":<6} </tspan>'
            f'<tspan fill="{LANG.get(lang, C["fg"])}" style="fill:{LANG.get(lang, C["fg"])}">{escape(f"{lang:<11}")}</tspan>'
            f'<tspan class="a"> {stars:>2}</tspan><tspan class="dim"> {when:>6}  </tspan>'
            f'<tspan class="b">{escape(name)}</tspan><tspan class="dim"> — {escape(desc)}</tspan></text>'
        )
    upd = s["today"].isoformat()
    body.append(t(W - 22, H - 12, f"actualizado {upd} · se redibuja cada día", "dim", 10, ' text-anchor="end"'))
    return svg(H, "".join(body), f"Racha actual {dias(s['streak'])} · {dias(s['active'])} activos · repos destacados")


def key(k, label, i):
    w, h = 210, 50
    delay = 0.2 + i * 0.12
    body = (
        f'<rect x="1" y="1" width="{w-2}" height="{h-2}" rx="8" fill="{C["bg"]}" stroke="{C["line"]}"/>'
        f'<g class="pop"{d(delay)}><rect x="12" y="12" width="40" height="26" rx="5" fill="{C["cyan"]}"/>'
        f'<text x="32" y="30" font-size="14" font-weight="700" text-anchor="middle" '
        f'style="fill:{C["bg"]}">{k}</text></g>'
        + t(64, 30, label, "b in", 15, d(delay + 0.1))
        + f'<g class="nudge"{d(delay + 0.4)}>' + t(w - 30, 30, "↗", "g", 15) + "</g>"
    )
    return svg(h, body, f"{k} {label}", w=w)


def main():
    data = load_json("contributions.json", {"days": []})
    repos_api = load_json("repos.json", {})
    s = stats(data.get("days", []))
    os.makedirs(CARDS, exist_ok=True)
    out = {
        "hero.svg": hero(),
        "graph.svg": graph(s),
        "htop.svg": htop(s, repos_api),
    }
    for i, (k, label, fname) in enumerate(KEYS):
        out[fname] = key(k, label, i)
    for name, content in out.items():
        with open(os.path.join(CARDS, name), "w", encoding="utf-8") as f:
            f.write(content)
        print(f"cards/{name}: {len(content) // 1024} KB")


if __name__ == "__main__":
    main()
