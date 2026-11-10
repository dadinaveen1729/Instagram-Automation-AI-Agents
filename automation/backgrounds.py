#!/usr/bin/env python3
"""Animated, story-related backgrounds for kinetic.py. Brand palette only (greens, gray, white;
the use-case circles stay under headlines). Procedural: numpy + Pillow, no stock footage, no AI.

A scene carries "art": {"kind": ..., plus optional "morph": [a, b], "fill": [a, b], "two": true}.
kinds: chart (jagged market line, can morph into a mountain ridge), network (nodes and links),
trail (parallax mountains, pines, rising sun), pie (pie chart filling up), route (path with
runner dot(s)), bokeh (soft rising circles, for end cards).
These are illustrations, not from the toolkit: Abi should approve the look.
"""
import math
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

HEX = lambda h: tuple(int(h[i:i + 2], 16) for i in (1, 3, 5))
DG, MG, LG, GRAY, WHITE = HEX("#004E3B"), HEX("#017543"), HEX("#82D17E"), HEX("#EBEBEB"), HEX("#FFFFFF")
lerp = lambda a, b, t: tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))
_cache = {}


def tone_of(bg):
    return {"dark": "dark", "mid": "mid", "light": "light", "white": "light"}[bg]


PAL = {  # base, sky top, sky horizon, far, mid, near, line, line alpha
    "dark": dict(base=DG, top=DG, hor=lerp(DG, MG, .45), far=lerp(DG, MG, .35), mid=lerp(DG, MG, .65), near=MG,
                 line=LG, la=200, soft=WHITE),
    "mid": dict(base=MG, top=lerp(MG, DG, .3), hor=lerp(MG, LG, .35), far=lerp(MG, LG, .25), mid=lerp(MG, DG, .35),
                near=DG, line=WHITE, la=190, soft=WHITE),
    "light": dict(base=GRAY, top=GRAY, hor=WHITE, far=lerp(GRAY, LG, .35), mid=lerp(GRAY, LG, .7),
                  near=lerp(LG, MG, .55), line=MG, la=210, soft=MG),
}


def gradient(size, top, bottom):
    W, H = size
    y = np.linspace(0, 1, H)[:, None, None]
    a = np.array(top, float)[None, None, :]
    b = np.array(bottom, float)[None, None, :]
    return Image.fromarray(((a + (b - a) * y) * np.ones((1, W, 1))).astype(np.uint8), "RGB")


def _overlay(size):
    return Image.new("RGBA", size, (0, 0, 0, 0))


def _blend(base, overlay):
    base = base.convert("RGBA")
    base.alpha_composite(overlay)
    return base.convert("RGB")


# ----------------------------------------------------------------- trail
def _ridge(W, seed, base, amp, ks):
    rng = np.random.default_rng(seed)
    x = np.arange(2 * W)
    h = np.zeros(2 * W)
    for k, a in ks:
        h += a * np.sin(2 * np.pi * k * x / W + rng.uniform(0, 6.28))
    return base + amp * h


def _strip(size, tone, layer, seed):
    key = ("strip", size, tone, layer)
    if key in _cache:
        return _cache[key]
    W, H = size
    p = PAL[tone]
    cfg = {"far": (H * 0.60, H * 0.07, [(2, 1), (3, .6), (5, .3)], p["far"]),
           "mid": (H * 0.69, H * 0.06, [(3, 1), (5, .5), (8, .25)], p["mid"]),
           "near": (H * 0.80, H * 0.05, [(2, 1), (4, .7), (7, .35)], p["near"])}[layer]
    base, amp, ks, col = cfg
    hgt = _ridge(W, seed, base, amp, ks)
    img = Image.new("RGBA", (2 * W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    pts = [(x, hgt[x]) for x in range(0, 2 * W, 4)]
    d.polygon(pts + [(2 * W, H), (0, H)], fill=col + (255,))
    if layer == "near":  # pines along the near ridge, periodic in W
        rng = np.random.default_rng(seed + 9)
        xs = sorted(rng.uniform(0, W, 11))
        for rep in (0, W):
            for x0 in xs:
                x = x0 + rep
                y = hgt[int(x) % (2 * W)]
                s = rng.uniform(0.7, 1.4) * W * 0.045
                for j in range(3):
                    yy = y - j * s * 0.75
                    d.polygon([(x, yy - s * 1.3), (x - s * (0.9 - j * .12), yy + s * .35), (x + s * (0.9 - j * .12), yy + s * .35)],
                              fill=lerp(col, DG, .35) + (255,))
    _cache[key] = (img, hgt)
    return _cache[key]


def trail(size, tone, t, u):
    W, H = size
    p = PAL[tone]
    key = ("sky", size, tone)
    if key not in _cache:
        _cache[key] = gradient(size, p["top"], p["hor"])
    img = _cache[key].copy()
    ov = _overlay(size)
    d = ImageDraw.Draw(ov)
    sx, sy, r = W * 0.72, H * (0.64 - 0.07 * u), W * 0.10
    for k, a in ((2.2, 22), (1.6, 40), (1.0, 120)):
        d.ellipse([sx - r * k, sy - r * k, sx + r * k, sy + r * k], fill=p["soft"] + (a,))
    img = _blend(img, ov).convert("RGBA")
    for layer, seed, speed in (("far", 3, 14), ("mid", 5, 30), ("near", 8, 58)):
        strip, _ = _strip(size, tone, layer, seed)
        off = int(t * speed) % W
        img.alpha_composite(strip.crop((off, 0, off + W, H)))
    return img.convert("RGB")


# ----------------------------------------------------------------- chart
def chart(size, tone, t, u, morph=(0.0, 0.0)):
    W, H = size
    p = PAL[tone]
    m = morph[0] + (morph[1] - morph[0]) * u
    img = gradient(size, p["top"], lerp(p["base"], p["hor"], .5))
    key = ("series",)
    if key not in _cache:
        rng = np.random.default_rng(11)
        i = np.arange(400)
        s = 0.5 + 0.26 * np.sin(i * 1.3) + 0.17 * np.sin(i * 0.37 + 1) + 0.10 * rng.normal(0, 1, 400)
        s = np.clip(s, 0.02, 0.98)
        _cache[key] = s
    s = _cache[key]
    ov = _overlay(size)
    d = ImageDraw.Draw(ov)
    for i in range(1, 6):  # faint grid
        d.line([(0, H * i / 6), (W, H * i / 6)], fill=p["line"] + (28,), width=2)
    n, speed = 16, 2.4
    pos = t * speed + m * 0
    i0 = int(pos)
    frac = pos - i0
    pts = []
    for j in range(-1, n + 2):
        v = s[(i0 + j) % len(s)]
        x = (j - frac) * W / (n - 1)
        y_jag = H * (0.86 - 0.32 * v)
        # ridge: smooth rolling mountains the line settles into
        y_ridge = H * (0.66 + 0.04 * math.sin(x / W * 5.0 + 1.0) + 0.05 * math.sin(x / W * 9.0))
        pts.append((x, (1 - m) * y_jag + m * y_ridge))
    d.polygon(pts + [(W + 40, H), (-40, H)], fill=p["line"] + (36 + int(30 * m),))
    d.line(pts, fill=p["line"] + (255,), width=int(W * 0.016), joint="curve")
    px, py = pts[n // 2]
    d.ellipse([px - 26, py - 26, px + 26, py + 26], fill=p["line"] + (255,))
    d.ellipse([px - 46, py - 46, px + 46, py + 46], outline=p["line"] + (140,), width=5)
    return _blend(img, ov)


# ----------------------------------------------------------------- network
def network(size, tone, t, u):
    W, H = size
    p = PAL[tone]
    img = gradient(size, p["top"], lerp(p["base"], p["hor"], .4))
    rng = np.random.default_rng(21)
    N = 42
    base = rng.uniform(0, 1, (N, 2))
    ph = rng.uniform(0, 6.28, (N, 2))
    pts = np.stack([(base[:, 0] + 0.04 * np.sin(t * 0.8 + ph[:, 0])) * W,
                    (base[:, 1] + 0.03 * np.cos(t * 0.7 + ph[:, 1])) * H], axis=1)
    ov = _overlay(size)
    d = ImageDraw.Draw(ov)
    lim = min(W, H) * 0.24
    for i in range(N):
        for j in range(i + 1, N):
            dist = math.dist(pts[i], pts[j])
            if dist < lim:
                a = int(120 * (1 - dist / lim) * (0.7 + 0.3 * math.sin(t * 3 + i)))
                d.line([tuple(pts[i]), tuple(pts[j])], fill=p["line"] + (a,), width=2)
    for i, (x, y) in enumerate(pts):
        r = 5 + 3 * (0.5 + 0.5 * math.sin(t * 2.5 + i))
        d.ellipse([x - r, y - r, x + r, y + r], fill=p["line"] + (190,))
    return _blend(img, ov)


# ----------------------------------------------------------------- pie
def pie(size, tone, t, u, fill=(0.0, 1.0)):
    W, H = size
    p = PAL[tone]
    f = fill[0] + (fill[1] - fill[0]) * u
    img = gradient(size, p["top"], lerp(p["base"], p["hor"], .5))
    ov = _overlay(size)
    d = ImageDraw.Draw(ov)
    cx, cy, R = W / 2, H * 0.52, W * 0.62
    box = [cx - R, cy - R, cx + R, cy + R]
    rot = -90 + t * 6
    slices = 8
    for k in range(slices):
        a0, a1 = rot + k * 360 / slices, rot + (k + 1) * 360 / slices
        part = min(max(f * slices - k, 0), 1)
        if part > 0:
            d.pieslice(box, a0, a0 + (a1 - a0) * part, fill=p["line"] + (46,))
        d.pieslice(box, a0, a1, outline=p["line"] + (110,), width=3)
    d.ellipse([cx - R * 1.04, cy - R * 1.04, cx + R * 1.04, cy + R * 1.04], outline=p["line"] + (150,), width=8)
    return _blend(img, ov)


# ----------------------------------------------------------------- route
def route(size, tone, t, u, two=False):
    W, H = size
    p = PAL[tone]
    img = gradient(size, p["top"], lerp(p["base"], p["hor"], .5))
    ov = _overlay(size)
    d = ImageDraw.Draw(ov)
    xs = np.linspace(W * 0.06, W * 0.94, 120)
    ys = H * (0.74 + 0.07 * np.sin(xs / W * 6.0) + 0.03 * np.sin(xs / W * 14.0))
    path = list(zip(xs, ys))
    for i in range(0, len(path) - 1, 4):  # dashed trail
        d.line([path[i], path[min(i + 2, len(path) - 1)]], fill=p["line"] + (210,), width=int(W * 0.013))
    for (x, y) in (path[0], path[-1]):
        d.ellipse([x - 30, y - 30, x + 30, y + 30], outline=p["line"] + (240,), width=9)
    pos = (t * 0.07 + u * 0.55) % 1.0
    for k, off in enumerate((0.0, 0.035) if two else (0.0,)):
        idx = min(len(path) - 1, int(((pos - off) % 1.0) * (len(path) - 1)))
        x, y = path[idx]
        for tr in range(1, 9):  # trailing dots
            ti = max(0, idx - tr * 2)
            tx, ty = path[ti]
            d.ellipse([tx - 11, ty - 11, tx + 11, ty + 11], fill=p["line"] + (max(0, 160 - tr * 17),))
        r = 30
        d.ellipse([x - r, y - r, x + r, y + r], fill=p["line"] + (255,))
    return _blend(img, ov)


# ----------------------------------------------------------------- bokeh
def bokeh(size, tone, t, u):
    W, H = size
    p = PAL[tone]
    img = gradient(size, p["top"], lerp(p["base"], p["hor"], .8))
    rng = np.random.default_rng(5)
    ov = _overlay(size)
    d = ImageDraw.Draw(ov)
    for i in range(22):
        r = rng.uniform(0.02, 0.09) * W
        x = rng.uniform(0, 1) * W + 20 * math.sin(t + i)
        y = (rng.uniform(0, 1) * H - t * rng.uniform(25, 70)) % (H + 2 * r) - r
        d.ellipse([x - r, y - r, x + r, y + r], fill=(p["soft"] if i % 3 else LG) + (int(rng.uniform(18, 50)),))
    return _blend(img, ov.filter(ImageFilter.GaussianBlur(5)))


def frame(art, bg, size, t, scene_len):
    """Return the RGB background for a scene at time t (seconds into the scene)."""
    tone = tone_of(bg)
    u = min(max(t / max(scene_len, 1e-6), 0.0), 1.0)
    kind = art["kind"]
    if kind == "trail":
        return trail(size, tone, t, u)
    if kind == "chart":
        return chart(size, tone, t, u, tuple(art.get("morph", (0, 0))))
    if kind == "network":
        return network(size, tone, t, u)
    if kind == "pie":
        return pie(size, tone, t, u, tuple(art.get("fill", (0, 1))))
    if kind == "route":
        return route(size, tone, t, u, bool(art.get("two")))
    return bokeh(size, tone, t, u)
