#!/usr/bin/env python3
"""Regenerate Ahmad's profile stat cards from real GitHub data.
Runs daily via .github/workflows/refresh-profile.yml. Stdlib only."""
import json, os, re, sys, urllib.request
from datetime import date, timedelta

USER = "Ahmadraza970"
TOKEN = os.environ.get("GITHUB_TOKEN", "")
TITLE, TEXT, BG, BORDER, ACCENT = "E1461C", "333333", "FFFFFF", "D6D1C4", "E1461C"

def get(url, raw=False):
    req = urllib.request.Request(url, headers={"User-Agent": "profile-refresh"})
    if TOKEN and "api.github.com" in url:
        req.add_header("Authorization", f"Bearer {TOKEN}")
    with urllib.request.urlopen(req, timeout=60) as r:
        data = r.read().decode("utf-8")
    return data if raw else json.loads(data)

def stats_svg(u, stars, repos_n, contrib_total, today_n):
    rows = [("Total Stars Earned:", str(stars)),
            ("Total Commits (last year):", str(contrib_total)),
            ("Public Repositories:", str(repos_n)),
            ("Followers:", str(u["followers"])),
            ("Contributions Today:", str(today_n))]
    y, lines = 70, ""
    for label, val in rows:
        lines += (f'<text x="25" y="{y}" font-family="Segoe UI, Ubuntu, sans-serif" font-size="14" fill="#{TEXT}">{label}</text>'
                  f'<text x="330" y="{y}" font-family="Segoe UI, Ubuntu, sans-serif" font-size="14" font-weight="700" fill="#{TEXT}">{val}</text>')
        y += 25
    return (f'<svg width="495" height="195" viewBox="0 0 495 195" fill="none" xmlns="http://www.w3.org/2000/svg">'
            f'<rect x="0.5" y="0.5" width="494" height="194" rx="4.5" fill="#{BG}" stroke="#{BORDER}"/>'
            f'<text x="25" y="35" font-family="Segoe UI, Ubuntu, sans-serif" font-size="18" font-weight="600" fill="#{TITLE}">Ahmad\'s GitHub Stats</text>'
            f'{lines}'
            f'<circle cx="415" cy="110" r="40" fill="none" stroke="#{ACCENT}" stroke-width="6" opacity="0.25"/>'
            f'<circle cx="415" cy="110" r="40" fill="none" stroke="#{ACCENT}" stroke-width="6" stroke-dasharray="188 251" transform="rotate(-90 415 110)"/>'
            f'<text x="415" y="118" text-anchor="middle" font-family="Segoe UI, Ubuntu, sans-serif" font-size="20" font-weight="700" fill="#{ACCENT}">{contrib_total}</text></svg>')

LANG_COLORS = {"TypeScript": "#3178c6", "HTML": "#e34c26", "Python": "#3572A5", "CSS": "#663399",
               "JavaScript": "#f1e05a", "Dockerfile": "#384d54", "Batchfile": "#C1F12E"}

def langs_svg(langs):
    tot = sum(langs.values()) or 1
    top = sorted(langs.items(), key=lambda kv: -kv[1])[:5]
    shown = [(k, round(v / tot * 100, 1)) for k, v in top]
    rest = round(100 - sum(p for _, p in shown), 1)
    if rest > 0: shown.append(("Other", rest))
    bar, x = "", 25.0
    for name, pct in shown:
        w = 300 * pct / 100
        bar += f'<rect x="{x:.1f}" y="55" width="{w:.1f}" height="8" fill="{LANG_COLORS.get(name, "#ededed")}"/>'
        x += w
    legend, ly = "", 90
    for i, (name, pct) in enumerate(shown):
        lx, lyy = 25 + (i % 2) * 155, ly + (i // 2) * 22
        legend += (f'<circle cx="{lx+5}" cy="{lyy-4}" r="5" fill="{LANG_COLORS.get(name, "#ededed")}"/>'
                   f'<text x="{lx+16}" y="{lyy}" font-family="Segoe UI, Ubuntu, sans-serif" font-size="12" fill="#{TEXT}">{name} {pct}%</text>')
    return (f'<svg width="350" height="170" viewBox="0 0 350 170" fill="none" xmlns="http://www.w3.org/2000/svg">'
            f'<rect x="0.5" y="0.5" width="349" height="169" rx="4.5" fill="#{BG}" stroke="#{BORDER}"/>'
            f'<text x="25" y="35" font-family="Segoe UI, Ubuntu, sans-serif" font-size="18" font-weight="600" fill="#{TITLE}">Most Used Languages</text>{bar}{legend}</svg>')

def graph_svg():
    today = date.today()
    html = get(f"https://github.com/users/{USER}/contributions?from={today - timedelta(days=364)}&to={today}", raw=True)
    cells = re.findall(r'data-date="(\d{4}-\d{2}-\d{2})"\s+id="contribution-day-component-(\d+)-(\d+)"\s+data-level="(\d)"', html)
    tips = dict(re.findall(r'<tool-tip[^>]*for="([^"]+)"[^>]*>([^<]*)</tool-tip>', html))
    colors = ["#ebedf0", "#9be9a8", "#40c463", "#30a14e", "#216e39"]
    total, active, today_n, rects = 0, 0, 0, ""
    for d, col, row, level in cells:
        cid = f"contribution-day-component-{col}-{row}"
        m = re.match(r"(\d+) contribution", tips.get(cid, ""))
        c = int(m.group(1)) if m else 0
        total += c; active += c > 0
        if d == str(today): today_n = c
        x, y = 15 + int(col) * 13, 46 + int(row) * 13
        rects += f'<rect x="{x}" y="{y}" width="10" height="10" rx="2" fill="{colors[int(level)]}"><title>{c} contributions on {d}</title></rect>'
    cols = max(int(c[1]) for c in cells) + 1
    W = cols * 13 + 30
    svg = (f'<svg width="{W}" height="160" viewBox="0 0 {W} 160" fill="none" xmlns="http://www.w3.org/2000/svg">'
           f'<rect x="0.5" y="0.5" width="{W-1}" height="159" rx="4.5" fill="#{BG}" stroke="#{BORDER}"/>'
           f'<text x="15" y="24" font-family="Segoe UI, Ubuntu, sans-serif" font-size="14" font-weight="600" fill="#{TITLE}">{total} contributions in the last year</text>'
           f'<text x="15" y="40" font-family="Segoe UI, Ubuntu, sans-serif" font-size="11" fill="#57606a">{active} active days · auto-updated daily</text>{rects}</svg>')
    return svg, total, today_n

def main():
    u = get(f"https://api.github.com/users/{USER}")
    repos = get(f"https://api.github.com/users/{USER}/repos?per_page=100&type=owner")
    stars = sum(r["stargazers_count"] for r in repos)
    langs = {}
    for r in repos:
        if r["fork"]: continue
        for k, v in get(f"https://api.github.com/repos/{USER}/{r['name']}/languages").items():
            langs[k] = langs.get(k, 0) + v
    graph, total, today_n = graph_svg()
    os.makedirs("assets", exist_ok=True)
    open("assets/github-stats.svg", "w").write(stats_svg(u, stars, len(repos), total, today_n))
    open("assets/top-langs.svg", "w").write(langs_svg(langs))
    open("assets/contribution-graph.svg", "w").write(graph)
    print(f"refreshed: total={total} today={today_n} stars={stars} repos={len(repos)}")

if __name__ == "__main__":
    main()
