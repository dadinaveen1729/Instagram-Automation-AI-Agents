#!/usr/bin/env python3
"""Render Boost Oxygen slides (PNG) and Reels (MP4) from text. Needs Pillow and ffmpeg.

Brand rules from the toolkit, enforced here:
- Headlines Oswald SemiBold, ALL CAPS. Eyebrow Open Sans Bold caps. Subhead Open Sans SemiBold.
  Body Open Sans Regular. (Oswald/Open Sans are bundled in assets/fonts, OFL licence.)
- Palette: Dark Green, Mid-Green, Light Green, Light Gray, White only. Secondary circles only in the
  five use-case colors, in order, locked under a headline, width no more than the logo, never on a
  photo slide (the primary graphic is not used here).
- Logo: ONLY the approved files in assets/logo/, scaled uniformly, never recolored or redrawn.
  If a file is missing, no logo is drawn and a warning is returned for the reviewer.
- Product canisters: NEVER generated. Only approved photos from assets/approved/, placed whole
  (uniform scale, no crop, no overlay, no filters).
Not implemented: the toolkit's -10 letter-tracking on headlines (Pillow has no tracking control).
"""
import json, subprocess, tempfile
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent
FONTS = ROOT / "assets" / "fonts"
LOGOS = ROOT / "assets" / "logo"
APPROVED = ROOT / "assets" / "approved"
BRAND = json.loads((ROOT / "brand.json").read_text())
C = BRAND["colors"]
OSWALD, SEMI, BOLD, REG = ("Oswald_600SemiBold.ttf", "OpenSans_600SemiBold.ttf",
                           "OpenSans_700Bold.ttf", "OpenSans_400Regular.ttf")
THEMES = {  # bg, headline, eyebrow, body, logo file
    "dark": (C["dark_green"], C["white"], C["light_green"], C["white"], "logo-reverse.png"),
    "light": (C["light_gray"], C["dark_green"], C["mid_green"], C["black"], "logo-fullcolor.png"),
    "white": (C["white"], C["dark_green"], C["mid_green"], C["black"], "logo-fullcolor.png"),
}
LOGO_W = 300


def font(name, size):
    return ImageFont.truetype(str(FONTS / name), size)


def wrap(d, text, fnt, width):
    lines, cur = [], ""
    for w in text.split():
        t = (cur + " " + w).strip()
        if d.textlength(t, font=fnt) <= width:
            cur = t
        else:
            lines.append(cur)
            cur = w
    return lines + ([cur] if cur else [])


def catalog():
    p = APPROVED / "catalog.json"
    return {e["id"]: e for e in json.loads(p.read_text())} if p.exists() else {}


def place_photo(img, photo_id, area, bg, warnings):
    """Whole approved photo, uniform scale, centered in area. No crop, no overlay, no filter."""
    e = catalog().get(photo_id)
    if not e or not (APPROVED / e["file"]).exists():
        warnings.append(f'Approved photo "{photo_id}" not found in assets/approved/catalog.json; slide has no photo.')
        return False
    ph = Image.open(APPROVED / e["file"]).convert("RGB")
    x0, y0, x1, y1 = area
    s = min((x1 - x0) / ph.width, (y1 - y0) / ph.height)
    ph = ph.resize((int(ph.width * s), int(ph.height * s)), Image.LANCZOS)
    img.paste(ph, (x0 + (x1 - x0 - ph.width) // 2, y0 + (y1 - y0 - ph.height) // 2))
    return True


def paste_logo(img, theme, warnings, m):
    f = LOGOS / THEMES[theme][4]
    if not f.exists():
        warnings.append(f"Approved logo file assets/logo/{f.name} is missing; no logo placed on this card.")
        return
    lg = Image.open(f).convert("RGBA")
    lg = lg.resize((LOGO_W, int(lg.height * LOGO_W / lg.width)), Image.LANCZOS)  # uniform scale only
    img.paste(lg, (m, img.height - m - lg.height), lg)


def circles(d, x, y):
    """Secondary graphic: five circles, order fixed, gap = 1/5 diameter, locked under a headline."""
    dia = 46
    gap = dia // 5
    assert 5 * dia + 4 * gap <= LOGO_W  # never wider than the logo
    for i, col in enumerate(BRAND["circle_colors_in_order"]):
        d.ellipse([x + i * (dia + gap), y, x + i * (dia + gap) + dia, y + dia], fill=col)
    return y + dia


def card(size, eyebrow="", headline="", sub="", body="", theme="dark", photo=None,
         use_circles=False, tag="", progress=None, warnings=None):
    warnings = warnings if warnings is not None else []
    W, H = size
    bg, hc, ec, bc, _ = THEMES[theme]
    img = Image.new("RGB", size, bg)
    d = ImageDraw.Draw(img)
    m = int(W * 0.08)
    top = int(H * 0.07)
    if photo:
        ph_h = int(H * 0.52)
        if place_photo(img, photo, (0, 0, W, ph_h), bg, warnings):
            top = ph_h + int(H * 0.03)
        use_circles = False  # circles never share an asset with a photo
    hs = int(W * 0.105) if not photo else int(W * 0.07)
    hf = font(OSWALD, hs)
    H_TXT = headline.upper()
    max_lines = 5 if not photo else 3
    while len(wrap(d, H_TXT, hf, W - 2 * m)) > max_lines and hs > 40:
        hs -= 4
        hf = font(OSWALD, hs)
    y = top
    if eyebrow:
        ef = font(BOLD, max(26, int(hs * 0.4)))
        d.text((m, y), eyebrow.upper(), font=ef, fill=ec)
        y += int(ef.size * 1.8)
    for ln in wrap(d, H_TXT, hf, W - 2 * m):
        d.text((m, y), ln, font=hf, fill=hc)
        y += int(hs * 1.08)
    y += int(hs * (0.45 if use_circles else 0.25))
    if use_circles:
        y = circles(d, m, y) + int(hs * 0.3)
    if sub:
        sf = font(SEMI, max(34, int(hs * 0.5)))
        for ln in wrap(d, sub, sf, W - 2 * m):
            d.text((m, y), ln, font=sf, fill=bc)
            y += int(sf.size * 1.4)
        y += int(sf.size * 0.4)
    if body:
        if not sub:
            y += int(hs * 0.3)
        bf = font(REG, max(30, int(hs * 0.33)))
        for ln in wrap(d, body, bf, W - 2 * m):
            d.text((m, y), ln, font=bf, fill=bc)
            y += int(bf.size * 1.4)
    paste_logo(img, theme, warnings, m)
    if tag:
        tf = font(BOLD, 28)
        d.text((W - m - d.textlength(tag, font=tf), H - m - 28), tag, font=tf, fill=ec)
    if progress is not None:
        d.rectangle([0, 0, int(W * progress), 12], fill=C["light_green"])
    return img


def render_slides(slides, outdir, warnings):
    outdir = Path(outdir); outdir.mkdir(parents=True, exist_ok=True)
    paths = []
    for i, s in enumerate(slides, 1):
        img = card((1080, 1350), s.get("eyebrow", ""), s["headline"], s.get("sub", ""), s.get("body", ""),
                   theme=s.get("theme", "dark"), photo=s.get("photo"),
                   use_circles=bool(s.get("circles")) and i == 1,
                   tag=f"{i}/{len(slides)}", warnings=warnings)
        p = outdir / f"slide{i:02d}.png"
        img.save(p)
        paths.append(p)
    return paths


def render_reel(beats, out, warnings):
    """beats: [{text, seconds, eyebrow?, photo?}]. 1080x1920, 30fps, H.264 + silent AAC."""
    out = Path(out); out.parent.mkdir(parents=True, exist_ok=True)
    total = sum(max(1.2, float(b.get("seconds", 3))) for b in beats)
    with tempfile.TemporaryDirectory() as td:
        lst, t, fp = [], 0.0, None
        for i, b in enumerate(beats):
            dur = max(1.2, float(b.get("seconds", 3)))
            img = card((1080, 1920), b.get("eyebrow", ""), b["text"], theme=b.get("theme", "dark"),
                       photo=b.get("photo"), progress=(t + dur) / total, warnings=warnings)
            fp = Path(td) / f"b{i}.png"; img.save(fp)
            lst += [f"file '{fp}'", f"duration {dur}"]
            t += dur
        lst.append(f"file '{fp}'")
        (Path(td) / "list.txt").write_text("\n".join(lst))
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0",
                        "-i", str(Path(td) / "list.txt"), "-f", "lavfi", "-i",
                        "anullsrc=r=44100:cl=stereo", "-shortest", "-r", "30",
                        "-c:v", "libx264", "-pix_fmt", "yuv420p", "-c:a", "aac",
                        "-movflags", "+faststart", str(out)], check=True)
    return out
