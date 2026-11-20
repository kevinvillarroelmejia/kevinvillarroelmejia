"""Descarga el calendario de contribuciones del último año a data/contributions.json.

Usa la API GraphQL de GitHub con GITHUB_TOKEN (en la Action) y, si falla,
lee la página pública https://github.com/users/<usuario>/contributions.
Solo usa la librería estándar.
"""
import datetime as dt
import json
import os
import re
import urllib.request

USER = os.environ.get("GH_USER", "kevinvillarroelmejia")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "data", "contributions.json")
REPOS_OUT = os.path.join(ROOT, "data", "repos.json")
# Repos que salen en la tabla de procesos del panel htop (en este orden)
REPOS = [
    "job-market-analyzer",
    "ProyectoBootStrap_KevinStudio",
    "servicios_procesos",
    "ACCESO_DATOS",
    "MULTIMEDIA",
    "AMPLIACION_DE_ENTORNOS",
]

QUERY = """
query($login: String!) {
  user(login: $login) {
    contributionsCollection {
      contributionCalendar {
        totalContributions
        weeks { contributionDays { date contributionCount } }
      }
    }
  }
}
"""


def from_graphql(token):
    body = json.dumps({"query": QUERY, "variables": {"login": USER}}).encode()
    req = urllib.request.Request(
        "https://api.github.com/graphql",
        data=body,
        headers={"Authorization": f"bearer {token}", "User-Agent": "readme-cards"},
    )
    with urllib.request.urlopen(req, timeout=30) as r:
        data = json.load(r)
    cal = data["data"]["user"]["contributionsCollection"]["contributionCalendar"]
    days = []
    for week in cal["weeks"]:
        for d in week["contributionDays"]:
            days.append({"date": d["date"], "count": d["contributionCount"]})
    return days


def from_html():
    req = urllib.request.Request(
        f"https://github.com/users/{USER}/contributions",
        headers={"User-Agent": "readme-cards"},
    )
    with urllib.request.urlopen(req, timeout=30) as r:
        html = r.read().decode("utf-8", "replace")
    ids = dict(re.findall(r'data-date="(\d{4}-\d\d-\d\d)"[^>]*id="([^"]+)"', html))
    ids.update({d: i for i, d in re.findall(r'id="([^"]+)"[^>]*data-date="(\d{4}-\d\d-\d\d)"', html)})
    tips = {}
    for tid, text in re.findall(r'<tool-tip[^>]*for="([^"]+)"[^>]*>([^<]*)</tool-tip>', html):
        m = re.match(r"\s*(\d+)", text)
        tips[tid] = int(m.group(1)) if m else 0
    days = [{"date": d, "count": tips.get(i, 0)} for d, i in ids.items()]
    days.sort(key=lambda x: x["date"])
    return days


def fetch_repos(token):
    """Lenguaje, estrellas y último push de cada repo destacado (API REST)."""
    out = {}
    headers = {"User-Agent": "readme-cards", "Accept": "application/vnd.github+json"}
    if token:
        headers["Authorization"] = f"bearer {token}"
    for name in REPOS:
        req = urllib.request.Request(f"https://api.github.com/repos/{USER}/{name}", headers=headers)
        try:
            with urllib.request.urlopen(req, timeout=30) as r:
                d = json.load(r)
            out[name] = {
                "language": d.get("language"),
                "stars": d.get("stargazers_count", 0),
                "pushed_at": d.get("pushed_at"),
                "description": d.get("description"),
            }
        except Exception as e:  # noqa: BLE001
            print(f"No pude leer {name}:", e)
    with open(REPOS_OUT, "w", encoding="utf-8") as f:
        json.dump(out, f, indent=1)
    print(f"{REPOS_OUT}: {len(out)} repos")


def main():
    token = os.environ.get("GITHUB_TOKEN")
    days = []
    if token:
        try:
            days = from_graphql(token)
        except Exception as e:  # noqa: BLE001
            print("GraphQL falló, uso la página pública:", e)
    if not days:
        days = from_html()
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    payload = {
        "user": USER,
        "updated": dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "days": days,
    }
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=1)
    print(f"{OUT}: {len(days)} días, {sum(d['count'] for d in days)} contribuciones")
    fetch_repos(token)


if __name__ == "__main__":
    main()
