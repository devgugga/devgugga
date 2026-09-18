#!/usr/bin/env python3
"""
Render a neofetch-style info card SVG. Each line fades and slides in with a
staggered delay (CSS keyframes, plays once). STATIC=1 emits the final frame.
Edit INFO below to change the content.

    python scripts/make_info_card.py
"""
import html
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "..", "info-card.svg")
PORTRAIT = os.path.join(HERE, "..", "portrait-ascii.svg")

USER = "gustavo@devgugga"
# (key, value); an empty key continues the previous row, None is a blank line
INFO = [
    ("Name", "Gustavo Gomes"),
    ("Location", "Goias, Brazil"),
    ("Role", "Software Developer"),
    ("OS", "Arch Linux (Omarchy) + Hyprland"),
    None,
    ("Languages", "TypeScript, Python, Go, Rust, C#, Java"),
    ("Backend", ".NET, Spring, Django, FastAPI"),
    ("Frontend", "Vue, Nuxt, React"),
    ("Databases", "Postgres, MongoDB, MariaDB, Redis"),
    ("Cloud", "AWS, Azure, GCP, Vercel, OVH"),
    None,
    ("Building", "Grafite: engineering provenance (Rust)"),
    ("", "agent-sandbox: rootless AI agent sandboxes"),
    None,
    ("Learning", "DICOM, PACS, MWL-RS, DCM4CHEE, Quarkus"),
    ("", "Keycloak/OIDC, observability, Podman"),
    ("", "zero-trust for coding agents, SSH runtimes"),
    ("", "worktree isolation, deterministic identities"),
    None,
    ("Web", "gustavgomes.com.br"),
    ("Instagram", "@devguga"),
]

W = 700
PAD = 24
TITLEBAR_H = 30
LINE_H = 22
KEY_W = 118

BG, BG2 = "#0d1117", "#111722"
FRAME = "#30363d"
MUTED = "#7d8590"
TEXT = "#c9d1d9"
ACCENT = "#00bfbf"
SWATCHES = ["#ff5f56", "#ffbd2e", "#27c93f", "#00bfbf", "#1f6feb", "#a371f7", "#f778ba", "#c9d1d9"]

STAGGER, DUR = 0.09, 0.4


def match_portrait_height():
    """Keep the card the same rendered height as the portrait next to it
    (README shows the portrait at 370px wide and this card at 490px)."""
    try:
        with open(PORTRAIT) as f:
            m = re.search(r'width="(\d+)" height="(\d+)"', f.read(500))
        pw, ph = int(m.group(1)), int(m.group(2))
        return round(ph * 370 / pw * W / 490)
    except (OSError, AttributeError):
        return 620


H = match_portrait_height()
css = (f"@keyframes in{{0%{{opacity:0;transform:translateX(-8px)}}100%{{opacity:1;transform:translateX(0)}}}}"
       f".l{{animation:in {DUR}s ease-out both}}"
       f"@keyframes blink{{0%,50%{{opacity:1}}51%,100%{{opacity:0}}}}.cur{{animation:blink 1s step-end infinite}}")
if os.environ.get("STATIC"):
    css = ".l{opacity:1}"

p = [
    f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" '
    f'font-family="ui-monospace, SFMono-Regular, Menlo, Consolas, monospace" font-size="14">',
    f"<style>{css}</style>",
    f'<defs><linearGradient id="cbg" x1="0" y1="0" x2="0" y2="1">'
    f'<stop offset="0" stop-color="{BG2}"/><stop offset="1" stop-color="{BG}"/></linearGradient></defs>',
    f'<rect width="{W}" height="{H}" rx="12" fill="url(#cbg)"/>',
    f'<rect x="0.5" y="0.5" width="{W-1}" height="{H-1}" rx="12" fill="none" stroke="{FRAME}"/>',
    f'<line x1="0" y1="{TITLEBAR_H}" x2="{W}" y2="{TITLEBAR_H}" stroke="{FRAME}"/>',
]
for i, c in enumerate(["#ff5f56", "#ffbd2e", "#27c93f"]):
    p.append(f'<circle cx="{PAD + i*16}" cy="{TITLEBAR_H/2}" r="5" fill="{c}"/>')
p.append(f'<text x="{W/2}" y="{TITLEBAR_H/2 + 4}" fill="{MUTED}" font-size="12" '
         f'text-anchor="middle">gustavo@github: ~$ neofetch</text>')

n = 0  # animated line index, drives the stagger


def line(y, inner):
    global n
    p.append(f'<g class="l" style="animation-delay:{0.3 + n*STAGGER:.2f}s">{inner}</g>')
    n += 1


y = TITLEBAR_H + 36
line(y, f'<text x="{PAD}" y="{y}" fill="{ACCENT}" font-weight="700" font-size="16">{USER}</text>')
y += 12
line(y, f'<line x1="{PAD}" y1="{y}" x2="{PAD + len(USER)*9.6:.0f}" y2="{y}" stroke="{MUTED}" stroke-dasharray="4 3"/>')
y += 28

for row in INFO:
    if row is None:
        y += LINE_H // 2
        continue
    key, val = row
    k = f'<text x="{PAD}" y="{y}" fill="{ACCENT}" font-weight="700">{html.escape(key)}</text>' if key else ""
    line(y, k + f'<text x="{PAD + KEY_W}" y="{y}" fill="{TEXT}">{html.escape(val)}</text>')
    y += LINE_H

y += 10
sw = "".join(f'<rect x="{PAD + i*30}" y="{y}" width="26" height="14" rx="3" fill="{c}"/>'
             for i, c in enumerate(SWATCHES))
line(y, sw)

prompt_y = H - 22
line(prompt_y, f'<text x="{PAD}" y="{prompt_y}" fill="{MUTED}">gustavo@github:~$ </text>'
               f'<rect class="cur" x="{PAD + 18*8.4 + 2:.0f}" y="{prompt_y - 12}" width="8" height="15" fill="{TEXT}"/>')

p.append("</svg>")
svg = "".join(p)
with open(OUT, "w") as f:
    f.write(svg)
print(f"wrote {OUT} ({len(svg)} bytes; {W}x{H}; content ends at y={y + 14})")
