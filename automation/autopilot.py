#!/usr/bin/env python3
"""Hands-off publisher for Instagram, built on the official Content Publishing API.

Each queue/*.json item is humanized, linted and scored automatically. Items that
pass go out; items that fail are moved to failed/ with the reasons. No browser
automation, no logins, no auto-DMs or auto-comments (those break Instagram's Terms).

Item format (queue/anything.json):
  {"type": "IMAGE|REELS|CAROUSEL", "caption": "...",
   "media_url": "https://...", "media_urls": ["https://...", ...],   # carousel: 2-10
   "publish_at": "2026-10-21T14:00:00Z", "keywords": "term one,term two"}

Env: IG_USER_ID, IG_ACCESS_TOKEN (long-lived), IG_LIVE=1 to really post.
Default is a dry run. Create a file named PAUSE in automation/ to stop everything.
Optional: IG_MAX_PER_DAY (default 2).
"""
import json, os, subprocess, sys, tempfile, time, urllib.parse, urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SK = ROOT.parent / "skills"
API = "https://graph.facebook.com/v21.0"
LIVE = os.environ.get("IG_LIVE") == "1"
MAX_PER_DAY = int(os.environ.get("IG_MAX_PER_DAY", "2"))


def run(script, *args, text=None):
    p = subprocess.run([sys.executable, str(SK / script), *args], input=text,
                       capture_output=True, text=True)
    return p.returncode, p.stdout, p.stderr


def gate(item):
    """Humanize, then require caption lint READY and a human-score PASS."""
    rc, cleaned, err = run("ig-human/humanize.py", "-", text=item["caption"])
    if rc != 0 or not cleaned.strip():
        return None, ["humanizer failed: " + err.strip()[:200]]
    problems = []
    args = ["-", "--json"] + (["--keywords", item["keywords"]] if item.get("keywords") else [])
    rc, out, _ = run("ig-caption/caption.py", *args, text=cleaned)
    if rc != 0:
        try:
            checks = json.loads(out).get("checks", [])
            problems += [f'{c.get("check")}: {c.get("detail")}' for c in checks
                         if str(c.get("status", "")).upper() != "PASS"] or ["caption lint not READY"]
        except Exception:
            problems.append("caption lint not READY")
    rc, out, _ = run("ig-human/detect.py", "-", text=cleaned)
    if rc != 0:
        weak = [l.strip() for l in out.splitlines() if "Weakest" in l or "variation" in l or "contractions" in l]
        problems.append("human-score check flagged: " + " | ".join(weak))
    if "{{" in cleaned:
        problems.append("unfilled {{placeholder}} in caption")
    return cleaned.strip(), problems


def call(path, params, method="POST"):
    params = {**params, "access_token": os.environ["IG_ACCESS_TOKEN"]}
    data = urllib.parse.urlencode(params).encode()
    url = f"{API}/{path}" + ("" if method == "POST" else "?" + data.decode())
    req = urllib.request.Request(url, data=data if method == "POST" else None, method=method)
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.load(r)


def wait_ready(container):
    for _ in range(40):
        s = call(container, {"fields": "status_code"}, "GET").get("status_code")
        if s == "FINISHED":
            return
        if s in ("ERROR", "EXPIRED"):
            raise RuntimeError(f"container {container} status {s}")
        time.sleep(15)
    raise RuntimeError("timed out waiting for media processing")


def publish(item, caption):
    uid = os.environ["IG_USER_ID"]
    t = item["type"].upper()
    if t == "IMAGE":
        c = call(f"{uid}/media", {"image_url": item["media_url"], "caption": caption})["id"]
    elif t == "REELS":
        c = call(f"{uid}/media", {"media_type": "REELS", "video_url": item["media_url"],
                                  "caption": caption})["id"]
    elif t == "CAROUSEL":
        kids = []
        for u in item["media_urls"]:
            k = "video_url" if u.lower().split("?")[0].endswith((".mp4", ".mov")) else "image_url"
            p = {k: u, "is_carousel_item": "true"}
            if k == "video_url":
                p["media_type"] = "VIDEO"
            kid = call(f"{uid}/media", p)["id"]
            if k == "video_url":
                wait_ready(kid)
            kids.append(kid)
        c = call(f"{uid}/media", {"media_type": "CAROUSEL", "children": ",".join(kids),
                                  "caption": caption})["id"]
    else:
        raise ValueError(f"unknown type {t}")
    wait_ready(c)
    return call(f"{uid}/media_publish", {"creation_id": c})["id"]


def posted_today():
    d = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    return sum(1 for f in (ROOT / "posted").glob("*.json") if f.read_text().find(d) >= 0)


def move(f, folder, extra):
    dst = ROOT / folder
    dst.mkdir(exist_ok=True)
    data = json.loads(f.read_text())
    data.update(extra, at=datetime.now(timezone.utc).isoformat())
    (dst / f.name).write_text(json.dumps(data, indent=2))
    f.unlink()


def main():
    if (ROOT / "PAUSE").exists():
        print("PAUSE file present, doing nothing.")
        return 0
    print("MODE:", "LIVE" if LIVE else "DRY RUN (set IG_LIVE=1 to post)")
    now = datetime.now(timezone.utc)
    (ROOT / "posted").mkdir(exist_ok=True)
    budget = MAX_PER_DAY - posted_today()
    for f in sorted((ROOT / "queue").glob("*.json")):
        item = json.loads(f.read_text())
        when = item.get("publish_at")
        if when and datetime.fromisoformat(when.replace("Z", "+00:00")) > now:
            continue
        caption, problems = gate(item)
        if problems:
            print(f"FAIL {f.name}: {problems}")
            if LIVE:
                move(f, "failed", {"problems": problems})
            continue
        if budget <= 0:
            print("Daily cap reached.")
            break
        if not LIVE:
            print(f"DRY OK {f.name}: would publish {item['type']}\n---\n{caption}\n---")
            continue
        try:
            media_id = publish(item, caption)
        except Exception as e:
            print(f"ERROR {f.name}: {e}")
            move(f, "failed", {"problems": [str(e)]})
            continue
        move(f, "posted", {"media_id": media_id, "caption": caption})
        budget -= 1
        print(f"POSTED {f.name} -> {media_id}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
