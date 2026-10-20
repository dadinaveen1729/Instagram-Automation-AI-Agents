#!/usr/bin/env python3
"""Weekly generator: Claude writes the posts, render.py makes the media, gate checks them,
and the results land in queue/ for autopilot.py to publish.

Env: ANTHROPIC_API_KEY (or GEN_MOCK=path/to/posts.json to skip the API), MEDIA_BASE_URL
(public URL prefix where automation/media/ will be served, e.g.
https://raw.githubusercontent.com/OWNER/REPO/main/automation/media).
"""
import json, os, sys, urllib.request, uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import autopilot, render

ROOT = Path(__file__).resolve().parent
MODEL = os.environ.get("GEN_MODEL", "claude-sonnet-5-5")
BRAND = json.loads((ROOT / "brand.json").read_text())

PROMPT = """You write Instagram posts for {handle}.
Niche: {niche}
Audience: {audience}
Voice: {voice}
Never say: {never}
Topics to rotate: {topics}
Search terms to work into captions: {keywords}

Write exactly this mix: {mix}.
Return ONLY a JSON array. Each item:
{{"type":"CAROUSEL|REELS|IMAGE","topic":"...","caption":"...","keywords":"one term",
 "slides":[{{"headline":"...","body":"..."}}],      // CAROUSEL: 6-8 slides, slide 1 is the hook. IMAGE: 1 slide.
 "beats":[{{"text":"...","seconds":3}}]}}           // REELS: 5-7 beats, 15-30s total, beat 1 is the hook, last beat echoes a word from beat 1.

Caption rules (enforced by a linter, failures are discarded):
- First line is under 120 characters, concrete, and stands alone.
- One call to action only. 2-3 hashtags, placed at the end after a blank line.
- Work in one search term naturally. No em dashes. No emoji.
- Never invent statistics, clients, results or quotes. Teach real, general knowledge only.
- Write like a person talks: mix very short sentences (2-4 words) with long ones (15-25 words), use contractions (I'm, it's, don't), and say "I" and "you".
- No placeholders or {{{{ }}}} anywhere.
{extra}"""


def ask_claude(prompt):
    body = json.dumps({"model": MODEL, "max_tokens": 8000,
                       "messages": [{"role": "user", "content": prompt}]}).encode()
    req = urllib.request.Request("https://api.anthropic.com/v1/messages", data=body, headers={
        "x-api-key": os.environ["ANTHROPIC_API_KEY"], "anthropic-version": "2023-06-01",
        "content-type": "application/json"})
    with urllib.request.urlopen(req, timeout=300) as r:
        text = json.load(r)["content"][0]["text"]
    s, e = text.find("["), text.rfind("]")
    return json.loads(text[s:e + 1])


def get_posts(extra="", mix_override=None):
    if os.environ.get("GEN_MOCK"):
        return json.loads(Path(os.environ["GEN_MOCK"]).read_text())
    mix = mix_override or ", ".join(f"{n} {t}" for t, n in BRAND["posts_per_week"].items())
    return ask_claude(PROMPT.format(
        handle=BRAND["handle"], niche=BRAND["niche"], audience=BRAND["audience"],
        voice=BRAND["voice"], never=", ".join(BRAND["never_say"]),
        topics=", ".join(BRAND["topics"]), keywords=", ".join(BRAND["keywords"]),
        mix=mix, extra=extra))


def main():
    if "FILL IN" in json.dumps(BRAND):
        sys.exit("Edit automation/brand.json first (niche, audience, topics).")
    base = os.environ.get("MEDIA_BASE_URL", "https://example.com/media").rstrip("/")
    posts = get_posts()
    # one repair round: re-ask for the posts the gate rejected, with its feedback
    bad = [(p, autopilot.gate(p)[1]) for p in posts]
    if any(pr for _, pr in bad) and not os.environ.get("GEN_MOCK"):
        redo = [p for p, pr in bad if pr]
        fb = "; ".join(sorted({x for _, pr in bad for x in pr}))
        fixed = get_posts(extra=f"Previous attempt was rejected for: {fb}. Fix that.",
                          mix_override=", ".join(f"1 {p['type']}" for p in redo))
        posts = [p for p, pr in bad if not pr] + fixed
    start = datetime.now(timezone.utc).replace(hour=14, minute=0, second=0, microsecond=0)
    slot, made = 0, 0
    for p in posts:
        pid = f"{datetime.now(timezone.utc):%Y%m%d}-{uuid.uuid4().hex[:6]}"
        caption, problems = autopilot.gate(p)
        if problems:
            print(f"DROP {p.get('topic')}: {problems}")
            continue
        media = ROOT / "media" / pid
        t = p["type"].upper()
        item = {"type": t, "caption": p["caption"], "keywords": p.get("keywords", "")}
        if t == "REELS":
            render.render_reel(p["beats"], media / "reel.mp4", BRAND["colors"], BRAND["handle"])
            item["media_url"] = f"{base}/{pid}/reel.mp4"
        else:
            files = render.render_slides(p["slides"], media, BRAND["colors"], BRAND["handle"])
            urls = [f"{base}/{pid}/{f.name}" for f in files]
            if t == "CAROUSEL" and len(urls) >= 2:
                item["media_urls"] = urls
            else:
                item["type"], item["media_url"] = "IMAGE", urls[0]
        slot += 1
        day = start + timedelta(days=1 + (slot - 1) * 7 // max(len(posts), 1))
        item["publish_at"] = day.isoformat().replace("+00:00", "Z")
        (ROOT / "queue").mkdir(exist_ok=True)
        (ROOT / "queue" / f"{pid}.json").write_text(json.dumps(item, indent=2))
        made += 1
        print(f"QUEUED {pid} {item['type']} {item['publish_at']}")
    print(f"{made}/{len(posts)} posts queued")


if __name__ == "__main__":
    main()
