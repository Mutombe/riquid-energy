"""Renders the Riquid 3D service objects as transparent WebP images.

Each object is a signed distance function (SDF). Rays are marched from a virtual
camera until they touch the surface; the hit points are then shaded with a fake
photo studio (sky, floor, softbox strips) and four lights. Everything is numpy,
rendered at 2x and downsampled with premultiplied alpha for clean edges.

Run:  python _src/tools/render3d.py            (all objects)
      python _src/tools/render3d.py panel ring (only some)
Output: assets/img/obj/obj-<name>.webp (520x520)
"""
import os, sys, time
import numpy as np
from PIL import Image

OUT = os.path.join(os.path.dirname(__file__), "..", "..", "assets", "img", "obj")
FINAL = 520           # output size in px
SS = 2                # supersampling factor
F32 = np.float32

# ---------------------------------------------------------------- vector helpers
def length(v): return np.sqrt((v * v).sum(-1))
def norm(v): return v / np.maximum(length(v), 1e-9)[..., None]
def dot(a, b): return (a * b).sum(-1)
def clamp01(x): return np.clip(x, 0, 1)

def rot(x, y, z):
    x, y, z = np.radians([x, y, z])
    Rx = np.array([[1, 0, 0], [0, np.cos(x), -np.sin(x)], [0, np.sin(x), np.cos(x)]])
    Ry = np.array([[np.cos(y), 0, np.sin(y)], [0, 1, 0], [-np.sin(y), 0, np.cos(y)]])
    Rz = np.array([[np.cos(z), -np.sin(z), 0], [np.sin(z), np.cos(z), 0], [0, 0, 1]])
    return (Rz @ Ry @ Rx).astype(F32)

# ---------------------------------------------------------------- SDF primitives
def sd_sphere(p, r): return length(p) - r

def sd_torus(p, R, r):
    q = np.stack([np.hypot(p[..., 0], p[..., 2]) - R, p[..., 1]], -1)
    return length(q) - r

def sd_round_box(p, b, r):
    q = np.abs(p) - (np.array(b, F32) - r)
    return length(np.maximum(q, 0)) + np.minimum(q.max(-1), 0) - r

def sd_round_cyl(p, ra, h, rb):
    """Vertical rounded cylinder: radius ra, half-height h, edge radius rb."""
    d = np.stack([np.hypot(p[..., 0], p[..., 2]) - ra + rb, np.abs(p[..., 1]) - h + rb], -1)
    return np.minimum(np.maximum(d[..., 0], d[..., 1]), 0) + length(np.maximum(d, 0)) - rb

def sd_round_cone(p, r1, r2, h):
    """Round cone along +y: sphere r1 at the origin blending into sphere r2 at height h."""
    b = (r1 - r2) / h
    a = np.sqrt(1 - b * b)
    q = np.stack([np.hypot(p[..., 0], p[..., 2]), p[..., 1]], -1)
    k = q[..., 0] * -b + q[..., 1] * a
    return np.where(k < 0, length(q) - r1,
           np.where(k > a * h, length(q - np.array([0, h], F32)) - r2,
                    q[..., 0] * a + q[..., 1] * b - r1))

def smin(a, b, k):
    h = clamp01(0.5 + 0.5 * (b - a) / k)
    return b * (1 - h) + a * h - k * h * (1 - h)

def polar(p, n):
    """Folds space into one of n angular sectors around y. Returns (folded p, sector angle)."""
    ang = np.arctan2(p[..., 2], p[..., 0])
    sector = 2 * np.pi / n
    a = (ang + sector / 2) % sector - sector / 2
    r = np.hypot(p[..., 0], p[..., 2])
    return np.stack([r * np.cos(a), p[..., 1], r * np.sin(a)], -1), ang - a

# ---------------------------------------------------------------- objects
# Each object: sdf(p) -> distance, mat(p, n) -> material id per point (local space).
# Material ids: 0 red lacquer, 1 black lacquer, 2 pearl white, 3 chrome, 4 charcoal metal,
#               5 aluminium (brushed), 6 black glass with cell grid, 7 copper

def obj_ring():
    """Brand mark in 3D: a glossy red core inside a charcoal ring, orbited by a thin red band."""
    def parts(p):
        core = sd_sphere(p, 0.56)
        ring = sd_torus(p, 0.86, 0.12)
        # thin orbit, tilted 62deg about x
        c, s = np.cos(np.radians(62)), np.sin(np.radians(62))
        po = np.stack([p[..., 0], c * p[..., 1] - s * p[..., 2], s * p[..., 1] + c * p[..., 2]], -1)
        orbit = sd_torus(po, 1.18, 0.045)
        return core, ring, orbit
    def sdf(p):
        a, b, c = parts(p); return np.minimum(np.minimum(a, b), c)
    def mat(p, n):
        a, b, c = parts(p)
        return np.where(a <= np.minimum(b, c), 0, np.where(b <= c, 4, 0))
    return sdf, mat

def obj_panel():
    """A single monocrystalline solar module: black glass cells with silver busbars, aluminium frame."""
    B = (1.30, 0.055, 0.86)
    def sdf(p):
        body = sd_round_box(p, B, 0.035)
        recess = sd_round_box(p - np.array([0, 0.07, 0], F32), (1.22, 0.04, 0.78), 0.01)
        return np.maximum(body, -recess)
    def mat(p, n):
        x, y, z = p[..., 0], p[..., 1], p[..., 2]
        frame = (np.abs(x) > 1.215) | (np.abs(z) > 0.775) | (y < -0.02)
        return np.where(frame, np.where(y < -0.045, 2, 5), 6)
    return sdf, mat

def obj_battery():
    """Lithium battery cell: pearl body, red charge band, charcoal cap and chrome terminal."""
    def sdf(p):
        body = sd_round_cyl(p, 0.58, 1.0, 0.12)
        term = sd_round_cyl(p - np.array([0, 1.08, 0], F32), 0.2, 0.1, 0.04)
        return smin(body, term, 0.03)
    def mat(p, n):
        y = p[..., 1]
        m = np.full(y.shape, 2)
        m = np.where((y > -0.62) & (y < -0.05), 0, m)          # charge level band
        m = np.where(y > 0.78, 4, m)                            # cap
        m = np.where(y > 1.0, 3, m)                             # terminal
        return m
    return sdf, mat

def obj_drop():
    """Water droplet (solar borehole pumps): polished chrome with a pearl inner wash."""
    def sdf(p):
        return sd_round_cone(p + np.array([0, 0.4, 0], F32), 0.74, 0.07, 1.36)
    def mat(p, n):
        return np.full(p.shape[:-1], 3)
    return sdf, mat

def obj_ribbon():
    """Strip swept round a circle with one full twist: black on one face, white on the other.
    Reads as DC becoming AC: the hybrid inverter."""
    R, W, T = 0.95, 0.36, 0.05
    def local(p):
        ang = np.arctan2(p[..., 2], p[..., 0])
        q = np.stack([np.hypot(p[..., 0], p[..., 2]) - R, p[..., 1]], -1)
        tw = ang * 0.5 * 2  # one full turn per lap
        c, s = np.cos(tw), np.sin(tw)
        return np.stack([c * q[..., 0] - s * q[..., 1], s * q[..., 0] + c * q[..., 1]], -1)
    def sdf(p):
        q = local(p)
        d = np.abs(q) - np.array([W - 0.04, T - 0.04], F32)
        return (length(np.maximum(d, 0)) + np.minimum(d.max(-1), 0) - 0.04) * 0.55
    def mat(p, n):
        q = local(p)
        return np.where(q[..., 1] > 0, 1, 2)
    return sdf, mat

def obj_impeller():
    """Pump impeller (AC pumps): charcoal shroud, swept blades, red hub."""
    def parts(p):
        hub = sd_round_cyl(p - np.array([0, 0.12, 0], F32), 0.26, 0.2, 0.08)
        disc = sd_round_cyl(p + np.array([0, 0.12, 0], F32), 1.0, 0.06, 0.04)
        # sweep the blades: rotate by radius before folding
        r = np.hypot(p[..., 0], p[..., 2])
        sw = r * 0.9
        c, s = np.cos(sw), np.sin(sw)
        ps = np.stack([c * p[..., 0] - s * p[..., 2], p[..., 1], s * p[..., 0] + c * p[..., 2]], -1)
        pf, _ = polar(ps, 7)
        blade = sd_round_box(pf - np.array([0.6, 0.06, 0], F32), (0.36, 0.14, 0.035), 0.025)
        return hub, disc, blade
    def sdf(p):
        hub, disc, blade = parts(p)
        return smin(np.minimum(disc, hub), blade, 0.04)
    def mat(p, n):
        hub, disc, blade = parts(p)
        return np.where(hub < np.minimum(disc, blade) + 0.01, 0, np.where(disc < blade, 4, 3))
    return sdf, mat

def obj_gear():
    """Gear (maintenance & reconfiguration): chrome teeth, charcoal centre plate."""
    def sdf(p):
        body = sd_round_cyl(p, 0.82, 0.16, 0.05)
        pf, _ = polar(p, 12)
        tooth = sd_round_box(pf - np.array([0.9, 0, 0], F32), (0.16, 0.16, 0.11), 0.04)
        g = np.minimum(body, tooth)
        hole = sd_round_cyl(p, 0.3, 0.4, 0.02)
        return np.maximum(g, -hole)
    def mat(p, n):
        r = np.hypot(p[..., 0], p[..., 2])
        return np.where((r < 0.62) & (np.abs(n[..., 1]) > 0.6), 4, 3)
    return sdf, mat

def obj_sun():
    """Glossy red sphere wrapped by a chrome ring of 'rays' (pricing, CTAs)."""
    def parts(p):
        core = sd_sphere(p, 0.62)
        pf, _ = polar(p, 16)
        ray = sd_round_box(pf - np.array([0.98, 0, 0], F32), (0.16, 0.035, 0.035), 0.03)
        return core, ray
    def sdf(p):
        a, b = parts(p); return np.minimum(a, b)
    def mat(p, n):
        a, b = parts(p); return np.where(a < b, 0, 3)
    return sdf, mat

OBJECTS = {
    # name: (factory, pose xyz degrees, scale)
    "ring": (obj_ring, (64, 10, -22), 1.0),
    "panel": (obj_panel, (38, -32, -14), 1.0),
    "battery": (obj_battery, (16, -20, -18), 0.92),
    "drop": (obj_drop, (14, 0, -14), 1.0),
    "ribbon": (obj_ribbon, (58, 16, -28), 1.05),
    "impeller": (obj_impeller, (52, 0, -18), 1.0),
    "gear": (obj_gear, (58, 12, -26), 1.0),
    "sun": (obj_sun, (60, 0, -20), 1.0),
}

# ---------------------------------------------------------------- studio
LIGHTS = [  # direction, sharpness, strength, colour
    (norm(np.array([-0.55, 0.75, 0.65], F32)), 22, 4.0, np.array([1.0, 0.97, 0.93], F32)),   # warm key
    (norm(np.array([0.85, 0.25, -0.45], F32)), 10, 1.5, np.array([0.92, 0.95, 1.0], F32)),   # neutral rim
    (norm(np.array([0.0, 1.0, 0.1], F32)), 6, 0.6, np.array([1.0, 1.0, 1.0], F32)),           # top
    (norm(np.array([0.6, -0.4, 0.7], F32)), 9, 0.5, np.array([1.0, 0.72, 0.66], F32)),       # warm red-ish fill
]

def env(d):
    """What shiny surfaces reflect: bright sky, grey horizon, dark floor, two softboxes."""
    y = d[..., 1]
    sky = np.array([0.97, 0.97, 0.98], F32)
    hor = np.array([0.30, 0.31, 0.33], F32)
    flo = np.array([0.08, 0.07, 0.07], F32)
    up = clamp01(y / 0.6)[..., None] ** 0.7
    dn = clamp01(-y / 0.3)[..., None]
    c = hor * (1 - up) + sky * up
    c = c * (1 - dn) + flo * dn
    c = c * (0.55 + 0.45 * clamp01(d[..., 2:3] + 0.6))  # darker behind
    c = c * (0.8 + 0.2 * clamp01(d[..., 0:1] + 0.8))    # darker on the left
    strip_h = np.exp(-((y - 0.18) / 0.06) ** 2) * 1.6
    strip_v = np.exp(-((d[..., 0] - 0.75) / 0.08) ** 2) * 1.1 * clamp01(y + 0.4)
    return c + (strip_h + strip_v)[..., None] * np.array([1, 0.99, 0.97], F32)

def fresnel(f0, ndv):
    return f0 + (1 - f0) * ((1 - ndv) ** 5)[..., None]

def lights(n, v, power, strength=1.0):
    dif = np.zeros(n.shape, F32); spe = np.zeros(n.shape, F32)
    for L, sharp, s, col in LIGHTS:
        ndl = clamp01(dot(n, L))
        h = norm(L + v)
        dif += (ndl * s * 0.25)[..., None] * col
        spe += (clamp01(dot(n, h)) ** power * s * 0.55 * strength)[..., None] * col
    return dif, spe

def shade(p, n, v, m, lp, ao):
    ndv = clamp01(dot(n, v))
    r = norm(2 * dot(n, v)[..., None] * n - v)
    E = env(r)
    out = np.zeros(p.shape, F32)
    a = ao[..., None]

    def lacquer(base, cc=0.8, power=110, rim=None):
        dif, spe = lights(n, v, power, 1.3)
        col = base * (0.18 + dif) * a + E * fresnel(np.array([0.04] * 3, F32), ndv) * cc + spe
        if rim is not None:
            col += rim * ((1 - ndv) ** 3)[..., None] * 0.35
        return col

    def metal(f0, rough=0.0, power=140):
        e = E if rough == 0 else E * (1 - rough) + env(n) * rough
        dif, spe = lights(n, v, power, 1.6)
        return e * fresnel(f0, ndv) * 0.95 * a + 0.08 * dif * f0 + spe * f0

    red = np.array([0.78, 0.015, 0.025], F32)
    sel = [
        (0, lambda: lacquer(red, 0.85, 120, np.array([1.0, 0.25, 0.2], F32))),
        (1, lambda: lacquer(np.array([0.012, 0.012, 0.014], F32), 0.95, 140)),
        (2, lambda: lacquer(np.array([0.82, 0.82, 0.83], F32), 0.6, 60)),
        (3, lambda: metal(np.array([0.93, 0.93, 0.95], F32))),
        (4, lambda: metal(np.array([0.26, 0.28, 0.31], F32), 0.25, 90)),
        (5, lambda: metal(np.array([0.80, 0.81, 0.83], F32), 0.45, 60)),
        (7, lambda: metal(np.array([0.95, 0.62, 0.45], F32), 0.1)),
    ]
    for mid, fn in sel:
        k = m == mid
        if k.any():
            out[k] = fn()[k]
    k = m == 6  # black glass with cell grid
    if k.any():
        x, z = lp[..., 0], lp[..., 2]
        cw, ch = 2.44 / 10, 1.56 / 6                     # 10 x 6 cells
        gx = np.abs(((x + 1.22) / cw) % 1 - 0.5) * cw
        gz = np.abs(((z + 0.78) / ch) % 1 - 0.5) * ch
        line = (np.minimum(cw / 2 - gx, ch / 2 - gz) < 0.012)
        bus = (np.abs(((x + 1.22) / cw * 3) % 1 - 0.5) * cw / 3 > cw / 6 - 0.004)
        cell = lacquer(np.array([0.010, 0.014, 0.030], F32), 1.0, 220)
        silver = metal(np.array([0.85, 0.86, 0.88], F32), 0.3)
        g = np.where((line | bus)[..., None], silver * 0.7 + cell * 0.3, cell)
        out[k] = g[k]
    return out

# ---------------------------------------------------------------- render
def render(name):
    factory, pose, scale = OBJECTS[name]
    sdf_l, mat_l = factory()
    R = rot(*pose)
    def sdf(pw):  # world -> local
        return sdf_l((pw / scale) @ R) * scale
    N = FINAL * SS
    fl = 0.30
    u = (np.arange(N, dtype=F32) + 0.5) / N * 2 - 1
    U, V = np.meshgrid(u, -u)
    rd = norm(np.stack([U * fl, V * fl, -np.ones_like(U)], -1)).reshape(-1, 3)
    ro = np.array([0, 0, 5], F32)
    t = np.full(len(rd), 2.5, F32)
    hit = np.zeros(len(rd), bool)
    alive = np.arange(len(rd))
    for i in range(260):
        p = ro + rd[alive] * t[alive, None]
        d = sdf(p)
        h = d < 0.0008
        hit[alive[h]] = True
        t[alive] += d * 0.9
        alive = alive[~h & (t[alive] < 7.5)]
        if len(alive) == 0:
            break
    idx = np.nonzero(hit)[0]
    p = ro + rd[idx] * t[idx, None]
    e = 0.0015
    ks = np.array([[1, -1, -1], [-1, -1, 1], [-1, 1, -1], [1, 1, 1]], F32)
    n = norm(sum(k * sdf(p + k * e)[:, None] for k in ks))
    ao = np.ones(len(idx), F32)
    occ = np.zeros(len(idx), F32)
    for j in range(1, 6):
        hgt = 0.06 * j
        occ += (hgt - sdf(p + n * hgt)) * (0.5 ** j)
    ao = clamp01(1 - 2.4 * occ) * 0.75 + 0.25
    lp = (p / scale) @ R
    ln = n @ R
    m = mat_l(lp, ln)
    col = shade(p, n, -rd[idx], m, lp, ao)
    col = 1 - np.exp(-1.75 * np.maximum(col, 0))                # tone map
    col = col ** (1 / 1.12)                                     # gentle lift
    img = np.zeros((N * N, 4), F32)
    img[idx, :3] = col
    img[idx, 3] = 1
    img = img.reshape(N, N, 4)
    # premultiplied downsample
    img = img.reshape(FINAL, SS, FINAL, SS, 4).mean((1, 3))
    a = img[..., 3:4]
    rgb = np.where(a > 0, img[..., :3] / np.maximum(a, 1e-6), 0)
    out = np.concatenate([rgb, a], -1)
    im = Image.fromarray((clamp01(out) * 255).astype(np.uint8), "RGBA")
    bb = im.getbbox()
    im = im.crop(bb)
    side = max(im.size) + 32
    sq = Image.new("RGBA", (side, side), (0, 0, 0, 0))
    sq.paste(im, ((side - im.width) // 2, (side - im.height) // 2))
    sq = sq.resize((FINAL, FINAL), Image.LANCZOS)
    os.makedirs(OUT, exist_ok=True)
    sq.save(os.path.join(OUT, f"obj-{name}.webp"), "WEBP", quality=88, method=6)

if __name__ == "__main__":
    names = sys.argv[1:] or list(OBJECTS)
    for nm in names:
        t0 = time.time()
        render(nm)
        print(f"{nm}: {time.time() - t0:.1f}s", flush=True)
