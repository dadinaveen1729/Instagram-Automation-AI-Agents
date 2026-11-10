#!/usr/bin/env python3
"""Kinetic-text skit videos with a synthesized beat-synced soundtrack. Pillow + numpy + ffmpeg only.

A script is a list of scenes: {"text": "...", "beats": 4, "bg": "dark|mid|light|white", "eyebrow": "...",
"sub": "...", "circles": false, "punch": false}. 120 BPM, so one beat is 0.5s and 60 beats is 30s.
*word* marks an emphasized word (brand light green on dark, mid green on light).
Words pop in on the beat (overshoot ease), the background flips between brand colors, punch scenes
flash and shake, and every word hit has a tick sound. The music (kick, clap, hats, bass, arp) is
synthesized here, so it is original and royalty free. It is NOT a trending sound: add that in-app.
Brand rules still apply: Oswald/Open Sans, toolkit palette only, no logo or product drawn.
"""
import json, math, subprocess, sys, wave
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import backgrounds

ROOT = Path(__file__).resolve().parent
FONTS = ROOT / "assets" / "fonts"
BRAND = json.loads((ROOT / "brand.json").read_text())
C = BRAND["colors"]
BG = {"dark": (C["dark_green"], C["white"], C["light_green"]),
      "mid": (C["mid_green"], C["white"], C["white"]),
      "light": (C["light_gray"], C["dark_green"], C["mid_green"]),
      "white": (C["white"], C["dark_green"], C["mid_green"])}
BPM, FPS, SR = 120, 30, 44100
BEAT = 60.0 / BPM
_fc = {}


def font(name, size):
    k = (name, size)
    if k not in _fc:
        _fc[k] = ImageFont.truetype(str(FONTS / name), size)
    return _fc[k]


def ease_out_back(u):
    u = min(max(u, 0.0), 1.0)
    c1 = 1.70158
    c3 = c1 + 1
    return 1 + c3 * (u - 1) ** 3 + c1 * (u - 1) ** 2


def layout(scene, size):
    """Word positions at final scale: list of (word, emphasized, cx, cy), font size, block box."""
    W, H = size
    d = ImageDraw.Draw(Image.new("RGB", (4, 4)))
    # multi-word emphasis spans like "*Go anyway.*"
    em_on, out = False, []
    for raw in scene["text"].split():
        if raw.startswith("*"):
            em_on = True
        out.append((raw.strip("*"), em_on))
        if raw.endswith("*"):
            em_on = False
    words = out
    base = min(W, H * 0.78)
    hs = int(base * 0.15)
    while hs > 40:
        f = font("Oswald_600SemiBold.ttf", hs)
        lines, cur = [], []
        for w, em in words:
            trial = " ".join(x[0].upper() for x in cur + [(w, em)])
            if d.textlength(trial, font=f) <= W * 0.84 or not cur:
                cur.append((w, em))
            else:
                lines.append(cur)
                cur = [(w, em)]
        lines.append(cur)
        if len(lines) <= 5 and all(d.textlength(" ".join(x[0].upper() for x in l), font=f) <= W * 0.9 for l in lines):
            break
        hs -= 4
    f = font("Oswald_600SemiBold.ttf", hs)
    lh = int(hs * 1.12)
    total_h = lh * len(lines)
    ty = 0.36 if scene.get("art", {}).get("kind") in ("chart", "trail", "route") else 0.48
    y0 = H * ty - total_h / 2
    pos = []
    for li, line in enumerate(lines):
        widths = [d.textlength(w.upper(), font=f) for w, _ in line]
        sp = d.textlength(" ", font=f)
        lw = sum(widths) + sp * (len(line) - 1)
        x = (W - lw) / 2
        for (w, em), ww in zip(line, widths):
            pos.append((w.upper(), em, x + ww / 2, y0 + li * lh + lh / 2))
            x += ww + sp
    return pos, hs, (y0, y0 + total_h)


def draw_frame(scene, size, t, scene_len, nxt_bg=None, progress=0.0, final=False):
    """Render one frame. t = seconds since scene start (None with final=True renders the finished state)."""
    W, H = size
    bg, fg, hi = BG[scene.get("bg", "dark")]
    if scene.get("art"):
        img = backgrounds.frame(scene["art"], scene.get("bg", "dark"), size, 1.2 if final else t, scene_len if not final else 2.4)
    else:
        img = Image.new("RGB", size, bg)
    d = ImageDraw.Draw(img)
    pos, hs, (top, bot) = layout(scene, size)
    n = len(pos)
    active = scene_len * 0.62
    step = active / max(n, 1)
    sx = sy = 0
    if scene.get("punch") and not final and 0 <= t < 0.3:
        sx = int(math.sin(t * 90) * W * 0.012 * (1 - t / 0.3))
        sy = int(math.cos(t * 70) * W * 0.008 * (1 - t / 0.3))
    # slow push-in plus a pulse on every beat
    zoom = 1.0 if final else 1.0 + 0.03 * (t / scene_len) + 0.035 * math.exp(-((t % BEAT) / BEAT) * 7)
    for i, (w, em, cx, cy) in enumerate(pos):
        s = 1.0 if final else ease_out_back((t + 0.09 - i * step) / 0.22)
        if s < 0.04:
            continue
        sz = max(8, int(hs * s * zoom))
        f = font("Oswald_600SemiBold.ttf", sz)
        col = hi if em else fg
        px = (cx - W / 2) * zoom + W / 2 + sx
        py = (cy - H / 2) * zoom + H / 2 + sy
        d.text((px, py), w, font=f, fill=col, anchor="mm")
    if scene.get("eyebrow"):
        a = 1.0 if final else min(1.0, t / 0.25)
        if a > 0:
            ef = font("OpenSans_700Bold.ttf", int(min(W, H * 0.78) * 0.04))
            ecol = tuple(int(bg_c + (hi_c - bg_c) * a) for bg_c, hi_c in zip(Image.new("RGB", (1, 1), bg).getpixel((0, 0)), Image.new("RGB", (1, 1), hi).getpixel((0, 0))))
            d.text((W / 2 + sx, max(H * 0.07, top - hs * 0.9)), scene["eyebrow"].upper(), font=ef, fill=ecol, anchor="mm")
    if scene.get("sub") and (final or t > scene_len * 0.55):
        sf = font("OpenSans_600SemiBold.ttf", int(min(W, H * 0.78) * 0.042))
        d.text((W / 2, bot + hs * 0.55), scene["sub"], font=sf, fill=fg, anchor="mm")
    if scene.get("circles") and (final or t > scene_len * 0.4):
        dia = int(min(W, H) * 0.045)
        gap = dia // 5
        total = 5 * dia + 4 * gap
        x0 = (W - total) // 2
        yy = int(bot + hs * 0.5)
        for i, col in enumerate(BRAND["circle_colors_in_order"]):
            k = 1.0 if final else ease_out_back((t - scene_len * 0.4 - i * 0.07) / 0.2)
            if k < 0.04:
                continue
            r = dia * k / 2
            cxx = x0 + i * (dia + gap) + dia / 2
            d.ellipse([cxx - r, yy - r, cxx + r, yy + r], fill=col)
    if not final:
        d.rectangle([0, 0, int(W * progress), max(6, int(H * 0.005))], fill=C["light_green"])
        if scene.get("punch") and 0 <= t < 0.1:  # white flash on the punch hit
            ov = Image.new("RGB", size, C["white"])
            img = Image.blend(img, ov, 0.45 * (1 - t / 0.1))
    return img


# ------------------------------------------------------------------ audio
def _env(n, decay):
    return np.exp(-np.arange(n) / (SR * decay))


def synth(scenes, total_s):
    n = int(total_s * SR)
    out = np.zeros(n, dtype=np.float64)
    rng = np.random.default_rng(7)

    def add(buf, start_s, gain=1.0):
        i = int(start_s * SR)
        if i >= n:
            return
        j = min(n, i + len(buf))
        out[i:j] += buf[: j - i] * gain

    # drums
    kt = np.arange(int(0.3 * SR)) / SR
    kick = np.sin(2 * np.pi * (45 * kt + 75 * (1 - np.exp(-kt * 28)) / 28)) * _env(len(kt), 0.09)
    hat = rng.standard_normal(int(0.05 * SR)) * _env(int(0.05 * SR), 0.012)
    hat = np.diff(hat, prepend=0)
    clap = rng.standard_normal(int(0.16 * SR)) * _env(int(0.16 * SR), 0.04)
    clap = np.convolve(clap, np.ones(6) / 6, mode="same")
    nbeats = int(total_s / BEAT)
    for b in range(nbeats):
        t0 = b * BEAT
        add(kick, t0, 0.85)
        add(hat, t0 + BEAT / 2, 0.22)
        if b % 2 == 1:
            add(clap, t0, 0.35)
    # bass (A minor): A1 A1 C2 E1 per bar
    notes = [55.0, 55.0, 65.41, 41.2]
    for b in range(nbeats):
        f0 = notes[b % 4]
        bt = np.arange(int(BEAT * 0.9 * SR)) / SR
        wave_ = np.sin(2 * np.pi * f0 * bt) + 0.35 * np.sin(2 * np.pi * 2 * f0 * bt)
        add(wave_ * _env(len(bt), 0.25), b * BEAT + BEAT / 2 * (b % 2), 0.38)
    # arp (A minor pentatonic) on 8ths, starts after the first 2 bars to build
    arp = [440.0, 523.25, 659.25, 783.99, 659.25, 523.25, 587.33, 523.25]
    for k in range(int(total_s / (BEAT / 2))):
        if k < 8:
            continue
        f0 = arp[k % len(arp)]
        at = np.arange(int(0.18 * SR)) / SR
        tone = (np.sin(2 * np.pi * f0 * at) + 0.3 * np.sin(2 * np.pi * 2 * f0 * at)) * _env(len(at), 0.07)
        add(tone, k * BEAT / 2, 0.09)
    # word ticks + whoosh at scene changes + riser into the end card
    t = 0.0
    for sc in scenes:
        length = sc["beats"] * BEAT
        words = len(sc["text"].split())
        step = length * 0.62 / max(words, 1)
        for i in range(words):
            tt = np.arange(int(0.05 * SR)) / SR
            add(np.sin(2 * np.pi * (1100 + 90 * (i % 4)) * tt) * _env(len(tt), 0.012), t + i * step, 0.16)
        wn = int(0.28 * SR)
        sweep = rng.standard_normal(wn) * np.linspace(0, 1, wn) ** 2 * _env(wn, 0.4)
        add(np.diff(sweep, prepend=0), max(0, t - 0.18), 0.22)
        if sc.get("punch"):
            dt = np.arange(int(0.4 * SR)) / SR
            add(np.sin(2 * np.pi * 60 * dt) * _env(len(dt), 0.15), t, 0.5)
        t += length
    # end ding
    dt = np.arange(int(1.2 * SR)) / SR
    add((np.sin(2 * np.pi * 1318.5 * dt) + 0.5 * np.sin(2 * np.pi * 1975.5 * dt)) * _env(len(dt), 0.5), total_s - 2.0, 0.25)
    fade = np.ones(n)
    fi, fo = int(0.05 * SR), int(0.8 * SR)
    fade[:fi] = np.linspace(0, 1, fi)
    fade[-fo:] = np.linspace(1, 0, fo)
    out *= fade
    out = np.tanh(out * 1.1)  # soft limiter
    out /= max(1e-9, np.abs(out).max()) / 0.9
    return out


def write_wav(path, x):
    pcm = (x * 32767).astype(np.int16)
    with wave.open(str(path), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(pcm.tobytes())


# ------------------------------------------------------------------ video
def render_video(scenes, out_mp4, size=(1080, 1920)):
    out_mp4 = Path(out_mp4)
    out_mp4.parent.mkdir(parents=True, exist_ok=True)
    total_beats = sum(s["beats"] for s in scenes)
    total_s = total_beats * BEAT
    wav = out_mp4.with_suffix(".wav")
    write_wav(wav, synth(scenes, total_s))
    p = subprocess.Popen(
        ["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{size[0]}x{size[1]}",
         "-r", str(FPS), "-i", "-", "-i", str(wav), "-c:v", "libx264", "-preset", "veryfast", "-pix_fmt", "yuv420p",
         "-c:a", "aac", "-b:a", "160k", "-t", f"{total_s:.2f}", "-movflags", "+faststart", str(out_mp4)],
        stdin=subprocess.PIPE)
    nframes = int(round(total_s * FPS))
    starts, acc = [], 0.0
    for s in scenes:
        starts.append(acc)
        acc += s["beats"] * BEAT
    for fidx in range(nframes):
        tt = fidx / FPS
        si = max(i for i, st in enumerate(starts) if st <= tt + 1e-9)
        sc = scenes[si]
        img = draw_frame(sc, size, tt - starts[si], sc["beats"] * BEAT, progress=tt / total_s)
        p.stdin.write(img.tobytes())
    p.stdin.close()
    p.wait()
    wav.unlink(missing_ok=True)
    return out_mp4


def render_still(scene, out_png, size):
    draw_frame(scene, size, 0, 1, final=True).save(out_png)
