"""Splits the Harare skyline photo into a background plate and a skyline foreground with alpha,
so the giant RIQUID wordmark can sit in the sky *behind* the buildings.

Run: python _src/tools/hero_cutout.py <path-to-skyline.jpg>
"""
import os, sys
import numpy as np
from PIL import Image, ImageFilter

src = sys.argv[1]
OUT = os.path.join(os.path.dirname(__file__), "..", "..", "assets", "img")
W = 2400
im = Image.open(src).convert("RGB")
im = im.resize((W, round(im.height * W / im.width)), Image.LANCZOS)
H = im.height
a = np.asarray(im).astype(np.float32) / 255
lum = a @ np.array([.299, .587, .114], np.float32)
# sky is bright, low-saturation and smooth; anything else counts as "ground"
blur = np.asarray(Image.fromarray((lum * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(1.2))).astype(np.float32) / 255
gy, gx = np.gradient(blur)
grad = np.hypot(gx, gy)
sat = a.max(2) - a.min(2)
sky_ref = np.median(a[: H // 5], axis=(0, 1))
dist = np.abs(a - sky_ref).sum(2)
row_ref = np.median(a, axis=1)  # vertical sky gradient per row
dist_row = np.abs(a - row_ref[:, None, :]).sum(2)
ground = grad > .010
# per column: first y (below 25% height) where ground persists for 6px
top = np.full(W, H, np.int32)
start = int(H * .25)
g = ground[start:]
run = np.zeros_like(g, np.int32)
for y in range(g.shape[0] - 1, -1, -1):
    run[y] = np.where(g[y], (run[y + 1] + 1) if y + 1 < g.shape[0] else 1, 0)
for x in range(W):
    ys = np.nonzero(run[:, x] >= 10)[0]
    if len(ys): top[x] = start + ys[0]
# tidy: remove single-column spikes, keep tower edges sharp
from scipy.ndimage import median_filter  # noqa
top = median_filter(top, size=5, mode="nearest")
from scipy.ndimage import grey_opening, grey_closing
h = grey_closing(H - top, size=35, mode="nearest")  # fill smooth facades read as sky
top = H - grey_opening(h, size=11, mode="nearest")  # drop spikes narrower than 11px
yy = np.arange(H)[:, None]
alpha = np.clip((yy - top[None, :] + 1.0) / 2.0, 0, 1)  # ~2px feather
fg = np.dstack([np.asarray(im), (alpha * 255).astype(np.uint8)])
Image.fromarray(fg, "RGBA").save(os.path.join(OUT, "hero-fg.webp"), "WEBP", quality=80, method=6)
im.save(os.path.join(OUT, "hero-bg.webp"), "WEBP", quality=80, method=6)
prev = Image.fromarray(fg, "RGBA").resize((W // 3, H // 3))
bg = Image.new("RGBA", prev.size, (255, 0, 80, 255)); bg.alpha_composite(prev)
bg.convert("RGB").save(os.path.join(os.environ.get("PREVIEW_DIR", OUT), "hero-cutout-preview.jpg"))
print("skyline top range", top.min(), top.max(), "of", H)
