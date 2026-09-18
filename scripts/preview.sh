#!/usr/bin/env bash
# Screenshot the README layout with every SVG in its final (STATIC) frame,
# then regenerate the animated SVGs. Usage: scripts/preview.sh [out.png]
set -euo pipefail
cd "$(dirname "$0")/.."
PY=.venv/bin/python
OUT=${1:-/tmp/profile-preview.png}
DIR=$(mktemp -d)

# the portrait needs the git-ignored source-prepped.png; without it the
# committed (animated) portrait would screenshot blank, so say so
if [[ -f source-prepped.png ]]; then
  STATIC=1 $PY scripts/make_ascii_svg.py source-prepped.png "$DIR/portrait.svg" >/dev/null
else
  echo "warning: source-prepped.png missing; run scripts/prep_photo.py (portrait will be blank)" >&2
  cp portrait-ascii.svg "$DIR/portrait.svg"
fi
STATIC=1 $PY scripts/make_info_card.py >/dev/null && cp info-card.svg "$DIR/card.svg"
[[ -f data/contributions.json ]] && STATIC=1 $PY scripts/render_heatmap_svg.py >/dev/null && cp contrib-heatmap.svg "$DIR/heat.svg"

cat > "$DIR/index.html" <<'HTML'
<!doctype html><body style="background:#0d1117;color:#e6edf3;font-family:monospace;text-align:center">
<h3><code>gustavo@github ~ $ whoami</code></h3>
<table style="margin:auto"><tr><td valign="top"><img src="portrait.svg" width="370"></td>
<td valign="top"><img src="card.svg" width="490"></td></tr></table>
<h3><code>gustavo@github ~ $ ./contributions.sh</code></h3><img src="heat.svg" width="860"></body>
HTML
chromium --headless --disable-gpu --window-size=1000,1100 --screenshot="$OUT" "file://$DIR/index.html" 2>/dev/null

# restore the animated versions that get committed
$PY scripts/make_info_card.py >/dev/null
[[ -f data/contributions.json ]] && $PY scripts/render_heatmap_svg.py >/dev/null
echo "preview: $OUT"
