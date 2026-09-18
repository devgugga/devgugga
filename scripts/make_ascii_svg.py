"""
Turn source-prepped.png (see prep_photo.py) into a monochrome ASCII portrait
SVG that "types" itself in row by row, then holds.

GitHub renders SVGs embedded via <img> and runs their SMIL animations (no JS).
Each row is revealed with a left-to-right clip wipe and a block cursor riding
the wipe edge. STATIC=1 emits the final frame only (handy for previews).

    python scripts/make_ascii_svg.py [input] [output]
"""
import html
import os
import sys

from PIL import Image, ImageEnhance

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "..", "source-prepped.png")
OUT = sys.argv[2] if len(sys.argv) > 2 else os.path.join(HERE, "..", "portrait-ascii.svg")
STATIC = bool(os.environ.get("STATIC"))

COLS = 64
CELL_W = 8
CELL_H = 15
RAMP = " .`:-=+*cs#%@"  # bright (sparse) -> dark (dense)

CONTRAST = 1.05
GAMMA = 1.15        # >1 brightens mids so the face lands in sparser chars
WHITE_FLOOR = 0.82  # luminance above this becomes a space

PAD = 20
TITLEBAR_H = 30
STATUS_H = 34

BG, BG2 = "#0d1117", "#111722"
FRAME = "#30363d"
MUTED = "#7d8590"
INK = "#c9d1d9"
ACCENT = "#00bfbf"

ROW_DUR = 0.11
STAGGER = 0.11  # == ROW_DUR -> one cursor sweeping down

im = Image.open(SRC).convert("L")
ROWS = round(COLS * im.height / im.width * CELL_W / CELL_H)
im = ImageEnhance.Contrast(im).enhance(CONTRAST).resize((COLS, ROWS), Image.LANCZOS)
px = im.load()

rows_txt = []
for y in range(ROWS):
    line = []
    for x in range(COLS):
        lum = (px[x, y] / 255.0) ** GAMMA
        if lum >= WHITE_FLOOR:
            line.append(" ")
        else:
            line.append(RAMP[min(len(RAMP) - 1, int((1.0 - lum) * (len(RAMP) - 1) + 0.5))])
    rows_txt.append("".join(line))

ART_W, ART_H = COLS * CELL_W, ROWS * CELL_H
W = ART_W + PAD * 2
H = TITLEBAR_H + PAD // 2 + ART_H + PAD // 2 + STATUS_H

p = [
    f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" '
    f'font-family="ui-monospace, SFMono-Regular, Menlo, Consolas, monospace" style="font-variant-ligatures:none">',
    f'<defs><linearGradient id="bg" x1="0" y1="0" x2="0" y2="1">'
    f'<stop offset="0" stop-color="{BG2}"/><stop offset="1" stop-color="{BG}"/></linearGradient></defs>',
    f'<rect width="{W}" height="{H}" rx="12" fill="url(#bg)"/>',
    f'<rect x="0.5" y="0.5" width="{W-1}" height="{H-1}" rx="12" fill="none" stroke="{FRAME}"/>',
    f'<line x1="0" y1="{TITLEBAR_H}" x2="{W}" y2="{TITLEBAR_H}" stroke="{FRAME}"/>',
]
for i, c in enumerate(["#ff5f56", "#ffbd2e", "#27c93f"]):
    p.append(f'<circle cx="{PAD + i*16}" cy="{TITLEBAR_H/2}" r="5" fill="{c}"/>')
p.append(f'<text x="{W/2}" y="{TITLEBAR_H/2 + 4}" fill="{MUTED}" font-size="12" '
         f'text-anchor="middle">gustavo@github: ~$ ./portrait.sh</text>')

art_top = TITLEBAR_H + PAD // 2
font_size = CELL_H * 0.86
for ry, line in enumerate(rows_txt):
    row_y = art_top + ry * CELL_H
    delay = ry * STAGGER
    text = (f'<text xml:space="preserve" x="{PAD}" y="{row_y + CELL_H*0.74:.1f}" fill="{INK}" '
            f'font-size="{font_size:.1f}" textLength="{ART_W}" lengthAdjust="spacing">{html.escape(line)}</text>')
    if STATIC:
        p.append(text)
        continue
    p.append(f'<clipPath id="r{ry}"><rect x="{PAD}" y="{row_y}" height="{CELL_H}" width="0">'
             f'<animate attributeName="width" from="0" to="{ART_W}" begin="{delay:.2f}s" '
             f'dur="{ROW_DUR}s" fill="freeze"/></rect></clipPath>')
    p.append(f'<g clip-path="url(#r{ry})">{text}</g>')
    p.append(f'<rect y="{row_y+1}" width="{CELL_W}" height="{CELL_H-2}" fill="{ACCENT}" opacity="0">'
             f'<animate attributeName="x" from="{PAD}" to="{PAD+ART_W}" begin="{delay:.2f}s" '
             f'dur="{ROW_DUR}s" fill="freeze"/>'
             f'<set attributeName="opacity" to="0.9" begin="{delay:.2f}s"/>'
             f'<set attributeName="opacity" to="0" begin="{delay+ROW_DUR:.2f}s"/></rect>')

status_line_y = art_top + ART_H + PAD // 2
status_y = status_line_y + 22
p.append(f'<line x1="0" y1="{status_line_y}" x2="{W}" y2="{status_line_y}" stroke="{FRAME}"/>')
p.append(f'<text x="{PAD}" y="{status_y}" fill="{MUTED}" font-size="13">'
         f'gustavo@github:~$ whoami <tspan fill="{ACCENT}">Gustavo Gomes</tspan></text>')
# 13px monospace ~ 7.8px/char; 38 chars before the cursor
p.append(f'<rect x="{PAD + 38*7.8 + 4:.0f}" y="{status_y-11}" width="8" height="14" fill="{INK}">'
         f'<animate attributeName="opacity" values="1;1;0;0" keyTimes="0;0.5;0.51;1" '
         f'dur="1s" repeatCount="indefinite"/></rect>')
p.append("</svg>")

svg = "".join(p)
with open(OUT, "w") as f:
    f.write(svg)
print("wrote", OUT, f"{len(svg)} bytes; {W}x{H}; {COLS}x{ROWS} chars")
print("\n".join(rows_txt))
