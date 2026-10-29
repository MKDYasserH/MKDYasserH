"""Draw the profile stats card (light and dark) from the GitHub GraphQL API.

Usage: GITHUB_TOKEN=... PROFILE_USER=... python3 stats.py <output dir>
Standard library only, so the workflow needs no setup step.
"""
import datetime as dt
import json
import os
import sys
import urllib.request
from pathlib import Path

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

THEMES = {
    "dark": dict(bg="#0b0c0a", rule="#2a2d27", ink="#f3f3ef", quiet="#9a9d93", accent="#c5f82a", spot="#c5f82a"),
    "light": dict(bg="#f5f5ef", rule="#d6d6cc", ink="#12140f", quiet="#5c5f56", accent="#4d6b00", spot="#c5f82a"),
}
MONO = "ui-monospace, SFMono-Regular, Menlo, Consolas, 'Liberation Mono', monospace"


def fetch(login, token):
    body = json.dumps({"query": QUERY, "variables": {"login": login}}).encode()
    req = urllib.request.Request(
        "https://api.github.com/graphql",
        data=body,
        headers={"Authorization": f"bearer {token}", "Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=30) as res:
        data = json.load(res)
    if "errors" in data:
        raise SystemExit(f"GraphQL error: {data['errors']}")
    return data["data"]["user"]


def busiest_month(days):
    totals = {}
    for date, count in days:
        totals[date[:7]] = totals.get(date[:7], 0) + count
    month = max(totals, key=totals.get)
    return dt.date.fromisoformat(month + "-01").strftime("%b %Y")


def card(stats, t):
    w, h = 1280, 220
    cols = [(64 + i * 400) for i in range(3)]
    cells = []
    for x, (value, label) in zip(cols, stats):
        cells.append(
            f'<text x="{x}" y="118" font-size="56" font-weight="700" fill="{t["ink"]}" letter-spacing="-1">{value}</text>'
            f'<text x="{x}" y="156" font-size="20" fill="{t["quiet"]}">{label}</text>'
        )
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" role="img" aria-label="{'; '.join(f'{v} {l}' for v, l in stats)}">
  <rect width="{w}" height="{h}" rx="16" fill="{t['bg']}"/>
  <rect x="0.5" y="0.5" width="{w - 1}" height="{h - 1}" rx="16" fill="none" stroke="{t['rule']}"/>
  <g font-family="{MONO}">
    <text x="64" y="52" font-size="18" fill="{t['quiet']}">$ git log --since="1 year ago" <tspan fill="{t['accent']}">--stat</tspan></text>
    {''.join(cells)}
  </g>
  <rect x="424" y="72" width="1" height="96" fill="{t['rule']}"/>
  <rect x="824" y="72" width="1" height="96" fill="{t['rule']}"/>
  <rect x="64" y="186" width="64" height="6" fill="{t['spot']}"/>
</svg>
"""


def main():
    out = Path(sys.argv[1])
    out.mkdir(parents=True, exist_ok=True)
    user = fetch(os.environ["PROFILE_USER"], os.environ["GITHUB_TOKEN"])
    cal = user["contributionsCollection"]["contributionCalendar"]
    days = [(d["date"], d["contributionCount"]) for w in cal["weeks"] for d in w["contributionDays"]]
    stats = [
        (f"{cal['totalContributions']:,}", "contributions, past year"),
        (f"{sum(1 for _, c in days if c)}", "active days"),
        (busiest_month(days), "busiest month"),
    ]
    for name, theme in THEMES.items():
        (out / f"stats-{name}.svg").write_text(card(stats, theme))
    print(dt.date.today(), stats)


if __name__ == "__main__":
    main()
