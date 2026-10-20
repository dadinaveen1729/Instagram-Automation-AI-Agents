#!/usr/bin/env python3
"""Render slides (PNG) and Reels (MP4) from text. Needs Pillow and ffmpeg. No paid services."""
import subprocess, tempfile
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

FONTS = ["/usr/share/fonts/opentype/inter/Inter-Bold.otf",
         "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
         "/usr/share/fonts/truetype/freefont/FreeSansBold.ttf"]


def font(size):
    for p in FONTS:
        if Path(p).exists():
            return ImageFont.truetype(p, size)
    return ImageFont.load_default()


def wrap(draw, text, fnt, width):
    lines, cur = [], ""
    for w in text.split():
        t = (cur + " " + w).strip()
        if draw.textlength(t, font=fnt) <= width:
            cur = t
        else:
            lines.append(cur)
            cur = w
    return lines + ([cur] if cur else [])


def card(headline, body, size, colors, tag="", footer="", progress=None):
    W, H = size
    img = Image.new("RGB", size, colors["bg"])
    d = ImageDraw.Draw(img)
    m = int(W * 0.09)
    d.rectangle([m, int(H * 0.08), m + 110, int(H * 0.08) + 10], fill=colors["accent"])
    hs = int(W * 0.075)
    hf, bf = font(hs), font(int(W * 0.04))
    # shrink headline until it fits in 5 lines
    while len(wrap(d, headline, hf, W - 2 * m)) > 5 and hs > 40:
        hs -= 4
        hf = font(hs)
    y = int(H * 0.2)
    for ln in wrap(d, headline, hf, W - 2 * m):
        d.text((m, y), ln, font=hf, fill=colors["fg"])
        y += int(hs * 1.2)
    y += int(H * 0.03)
    for ln in wrap(d, body or "", bf, W - 2 * m):
        d.text((m, y), ln, font=bf, fill=colors["fg"])
        y += int(W * 0.04 * 1.45)
    ff = font(int(W * 0.03))
    if footer:
        d.text((m, H - int(H * 0.08)), footer, font=ff, fill=colors["accent"])
    if tag:
        d.text((W - m - d.textlength(tag, font=ff), H - int(H * 0.08)), tag, font=ff, fill=colors["fg"])
    if progress is not None:
        d.rectangle([0, 0, int(W * progress), 12], fill=colors["accent"])
    return img


def render_slides(slides, outdir, colors, handle):
    outdir = Path(outdir); outdir.mkdir(parents=True, exist_ok=True)
    paths = []
    for i, s in enumerate(slides, 1):
        img = card(s["headline"], s.get("body", ""), (1080, 1350), colors,
                   tag=f"{i}/{len(slides)}", footer=handle)
        p = outdir / f"slide{i:02d}.png"
        img.save(p)
        paths.append(p)
    return paths


def render_reel(beats, out, colors, handle):
    """beats: [{text, seconds}]. 1080x1920, 30fps, h264 + silent AAC (valid for Instagram)."""
    out = Path(out); out.parent.mkdir(parents=True, exist_ok=True)
    total = sum(max(1.2, float(b.get("seconds", 3))) for b in beats)
    with tempfile.TemporaryDirectory() as td:
        lst, t = [], 0.0
        for i, b in enumerate(beats):
            dur = max(1.2, float(b.get("seconds", 3)))
            img = card(b["text"], "", (1080, 1920), colors, footer=handle, progress=(t + dur) / total)
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
