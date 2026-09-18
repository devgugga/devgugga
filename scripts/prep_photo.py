"""
Prepare the portrait for ASCII conversion:
  1. remove the background (rembg) so only the subject is left
  2. crop tight to head + shoulders (a 60-column portrait can't afford margins)
  3. boost local contrast (CLAHE) so the face gets real highlights/shadows
  4. composite onto pure white (white -> spaces in the ascii ramp)

    python scripts/prep_photo.py [input] [output]
"""
import os
import sys

import cv2
import numpy as np
from PIL import Image
from rembg import remove

HERE = os.path.dirname(os.path.abspath(__file__))
INP = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "..", "source-photo.png")
OUT = sys.argv[2] if len(sys.argv) > 2 else os.path.join(HERE, "..", "source-prepped.png")

MAX_ASPECT = 1.25  # height / width of the final crop; trims the torso

cut = remove(Image.open(INP).convert("RGBA"))
rgb = np.array(cut.convert("RGB"))
alpha = np.array(cut.split()[-1])

# crop to the subject's bounding box, then cap the height
ys, xs = np.where(alpha > 32)
x0, x1, y0, y1 = xs.min(), xs.max(), ys.min(), ys.max()
pad = int((x1 - x0) * 0.04)
x0, y0 = max(0, x0 - pad), max(0, y0 - pad)
x1, y1 = min(rgb.shape[1], x1 + pad), min(rgb.shape[0], y1 + pad)
y1 = min(y1, y0 + int((x1 - x0) * MAX_ASPECT))
rgb, alpha = rgb[y0:y1, x0:x1], alpha[y0:y1, x0:x1]

gray = cv2.cvtColor(rgb, cv2.COLOR_RGB2GRAY)
gray = cv2.createCLAHE(clipLimit=2.6, tileGridSize=(8, 8)).apply(gray)
gray = cv2.convertScaleAbs(gray, alpha=1.05, beta=18)

mask = cv2.GaussianBlur(alpha.astype(np.float32) / 255.0, (0, 0), 1.0)
out = gray.astype(np.float32) * mask + 255.0 * (1.0 - mask)
out = np.clip(out, 0, 255).astype(np.uint8)

Image.fromarray(out, mode="L").save(OUT)
print("wrote", OUT, out.shape)
