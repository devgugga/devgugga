#!/usr/bin/env python3
"""
Render data/contributions.json as a terminal-framed contribution heatmap SVG:
53 weeks x 7 days of rounded cells in a teal ramp, revealed once with a
diagonal slide-down (CSS keyframes, no looping), plus a legend and stats.

Run by .github/workflows/update-profile-art.yml after fetch_contributions.py.
"""
import datetime
import json
import os

HERE = os.path.dirname(__file__)
IN_PATH = os.path.join(HERE, "..", "data", "contributions.json")
OUT_PATH = os.path.join(HERE, "..", "contrib-heatmap.svg")

# empty -> brightest, built around the profile accent #00bfbf
PALETTE = ["#161b22", "#0a3d3f", "#006b6d", "#009a9a", "#00bfbf", "#5ef2e8"]

CELL, GAP = 12, 3
STEP = CELL + GAP
PAD = 22
LEFT_LABEL_W = 30
TOP_LABEL_H = 20
TITLEBAR_H = 30
STATS_H = 88

BG, BG2 = "#0d1117", "#111722"
FRAME = "#30363d"
MUTED = "#7d8590"
ACCENT = "#00bfbf"
GOLD = "#f2cc60"

COL_T, ROW_T, CELL_DUR = 0.018, 0.045, 0.42


def thresholds(days):
    """Split non-zero days into len(PALETTE)-1 buckets by quantile, like GitHub."""
    counts = sorted(d["count"] for d in days if d["count"] > 0)
    n = len(PALETTE) - 1
    if not counts:
        return [1] * n
    return [counts[min(len(counts) - 1, (len(counts) * i) // n)] for i in range(1, n)]


def level_for(count, cuts):
    if count == 0:
        return 0
    return 1 + sum(count > c for c in cuts)


def build_grid(days, cuts):
    first = datetime.date.fromisoformat(days[0]["date"])
    grid, col = [], [None] * ((first.weekday() + 1) % 7)  # sunday = row 0
    for d in days:
        col.append((d["date"], d["count"], level_for(d["count"], cuts)))
        if len(col) == 7:
            grid.append(col)
            col = []
    if col:
        grid.append(col + [None] * (7 - len(col)))
    return grid


def render(data):
    days = data["days"]
    grid = build_grid(days, thresholds(days))
    art_w, art_h = len(grid) * STEP, 7 * STEP
    W = PAD + LEFT_LABEL_W + art_w + PAD
    H = TITLEBAR_H + TOP_LABEL_H + art_h + STATS_H + PAD

    css = (f"@keyframes cell{{0%{{opacity:0;transform:translateY(-6px)}}100%{{opacity:1;transform:translateY(0)}}}}"
           f".c{{animation:cell {CELL_DUR}s cubic-bezier(.2,.8,.2,1) both}}")
    if os.environ.get("STATIC"):
        css = ".c{opacity:1}"

    p = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" '
        f'font-family="ui-monospace, SFMono-Regular, Menlo, Consolas, monospace">',
        f"<style>{css}</style>",
        f'<defs><linearGradient id="hbg" x1="0" y1="0" x2="0" y2="1">'
        f'<stop offset="0" stop-color="{BG2}"/><stop offset="1" stop-color="{BG}"/></linearGradient></defs>',
        f'<rect width="{W}" height="{H}" rx="12" fill="url(#hbg)"/>',
        f'<rect x="0.5" y="0.5" width="{W-1}" height="{H-1}" rx="12" fill="none" stroke="{FRAME}"/>',
        f'<line x1="0" y1="{TITLEBAR_H}" x2="{W}" y2="{TITLEBAR_H}" stroke="{FRAME}"/>',
    ]
    for i, c in enumerate(["#ff5f56", "#ffbd2e", "#27c93f"]):
        p.append(f'<circle cx="{PAD + i*16}" cy="{TITLEBAR_H/2}" r="5" fill="{c}"/>')
    p.append(f'<text x="{W/2}" y="{TITLEBAR_H/2 + 4}" fill="{MUTED}" font-size="12" '
             f'text-anchor="middle">gustavo@github: ~/contributions --graph</text>')

    grid_top = TITLEBAR_H + TOP_LABEL_H
    grid_left = PAD + LEFT_LABEL_W

    seen = set()
    for ci, column in enumerate(grid):
        cell = next(c for c in column if c)
        date = datetime.date.fromisoformat(cell[0])
        if (date.year, date.month) not in seen and date.day <= 7 and ci < len(grid) - 2:
            seen.add((date.year, date.month))
            p.append(f'<text x="{grid_left + ci*STEP}" y="{TITLEBAR_H + 14}" fill="{MUTED}" '
                     f'font-size="10">{date.strftime("%b")}</text>')
    for wi, name in [(1, "Mon"), (3, "Wed"), (5, "Fri")]:
        p.append(f'<text x="{PAD}" y="{grid_top + wi*STEP + CELL*0.78:.1f}" fill="{MUTED}" font-size="9">{name}</text>')

    for ci, column in enumerate(grid):
        for ri, cell in enumerate(column):
            if cell is None:
                continue
            date_s, count, lvl = cell
            p.append(f'<rect class="c" x="{grid_left + ci*STEP}" y="{grid_top + ri*STEP}" width="{CELL}" '
                     f'height="{CELL}" rx="2.5" fill="{PALETTE[lvl]}" '
                     f'style="animation-delay:{ci*COL_T + ri*ROW_T:.3f}s">'
                     f'<title>{date_s}: {count} contribution{"s" if count != 1 else ""}</title></rect>')

    leg_y = grid_top + art_h + 6
    leg_x = W - PAD - (len(PALETTE) * CELL + 40)
    p.append(f'<text x="{leg_x}" y="{leg_y + CELL*0.8:.1f}" fill="{MUTED}" font-size="10" text-anchor="end">Less</text>')
    lx = leg_x + 8
    for color in PALETTE:
        p.append(f'<rect x="{lx}" y="{leg_y}" width="{CELL-1}" height="{CELL-1}" rx="2.2" fill="{color}"/>')
        lx += CELL
    p.append(f'<text x="{lx + 4}" y="{leg_y + CELL*0.8:.1f}" fill="{MUTED}" font-size="10">More</text>')

    sep_y = leg_y + CELL + 14
    p.append(f'<line x1="0" y1="{sep_y}" x2="{W}" y2="{sep_y}" stroke="{FRAME}"/>')

    best, rng = data["best_day"], data["range"]
    ly = sep_y + 24
    p.append(f'<text x="{PAD}" y="{ly}" font-size="13" fill="{ACCENT}">'
             f'<tspan font-weight="700">{data["total_contributions"]:,}</tspan>'
             f'<tspan fill="{MUTED}"> contributions in the last year</tspan></text>')
    p.append(f'<text x="{W - PAD}" y="{ly}" font-size="12" fill="{MUTED}" text-anchor="end">'
             f'{rng["start"]} &#8594; {rng["end"]}</text>')
    ly += 24
    p.append(f'<text x="{PAD}" y="{ly}" font-size="13" fill="{MUTED}">current streak '
             f'<tspan fill="{ACCENT}" font-weight="700">{data["current_streak"]} days</tspan>'
             f'   &#183;   longest <tspan fill="{ACCENT}" font-weight="700">{data["longest_streak"]} days</tspan></text>')
    p.append(f'<text x="{W - PAD}" y="{ly}" font-size="12" fill="{MUTED}" text-anchor="end">'
             f'best day <tspan fill="{GOLD}" font-weight="700">{best["count"]}</tspan> on {best["date"]}</text>')
    p.append("</svg>")
    return "".join(p)


if __name__ == "__main__":
    with open(IN_PATH) as f:
        svg = render(json.load(f))
    with open(OUT_PATH, "w") as f:
        f.write(svg)
    print(f"wrote {OUT_PATH} ({len(svg)} bytes)")
