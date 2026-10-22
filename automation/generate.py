#!/usr/bin/env python3
"""Weekly generator for Boost Oxygen: Claude drafts posts under the brand rules, render.py makes the
media, compliance + lint gates check them, and the result lands in a PR for Abi's approval.

Routing (nothing here posts anything):
  clean posts    -> queue/    (publish only after the PR is merged = approved)
  flagged posts  -> review/   (wording Abi must look at; never auto-published)
  blocked posts  -> repaired once by Claude, else dropped (listed in REVIEW.md)

Env: ANTHROPIC_API_KEY (or GEN_MOCK=path/to/posts.json to skip the API), MEDIA_BASE_URL.
"""
import json, os, sys, urllib.request, uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
import autopilot, render, compliance

MODEL = os.environ.get("GEN_MODEL", "claude-sonnet-5-5")
BRAND = json.loads((ROOT / "brand.json").read_text())

RULES = """HARD RULES from the Boost Oxygen social media manager (a linter enforces them; violations are discarded):
- Brand is always "Boost Oxygen". The product is a "canister", never "can". Say "aroma", never "flavor" (flavor only for OxyBurst, a drink mix).
- Never call the product "air" or "canned air". You may compare: "nearly 5X more oxygen than normal air" and "95% pure oxygen".
- NO medical claims, direct or implied: never say it treats, cures, diagnoses, prevents or heals anything. Do not name conditions. Avoid "relief", "recover", "support for breathing problems" style wording. If you are unsure about a phrase, still write it and list it in "reviewer_notes".
- Use ONLY the approved facts below. Never invent product details, statistics, testimonials, results, prices, discounts or dates. If something is missing, put it in "reviewer_notes" instead of guessing.
- Product names: use the full name incl. size and capacity, e.g. "SPORT Orange | Large (10L)". Only these full names are confirmed: {names}. Do not mention any other product line, aroma or size by name.
- "Made in USA" is the exact phrase for that message.
- Writing: friendly, natural, easy to understand, active verbs, a little light humor at most, never corny, exaggerated, hyped or salesy. No superlatives. Minimal emoji (0 or 1). Maximum 5 hashtags (use 2-3).
- Do not write promotions, sales or discounts unless the operator supplied one. (If one is supplied, the system appends the exact legal disclaimer; never write your own.)
- Do not describe or request AI-generated images of canisters or people. Never plan product visuals; visuals are text cards. Only reference photo ids from this approved list (may be empty): {photos}. Use at most one photo per slide.
- On-image text must follow the same rules as captions.
"""

PROMPT = """You write Instagram posts for {brand} ({handle}).
Voice: {voice}
Brand pillars: {pillars}. Need states: {needs}.
Approved facts (the ONLY facts you may use):
{facts}
Approved message headlines from the Brand Toolkit (use word-for-word or as inspiration; the ones marked REVIEW CLOSELY need extra care):
{messages}
Taglines (occasional sign-off only): {taglines}
Topics to rotate: {topics}
Search terms to work into captions naturally: {keywords}

{rules}
Write exactly this mix: {mix}.
Return ONLY a JSON array. Each item:
{{"type":"CAROUSEL|REELS|IMAGE","topic":"...","caption":"...","keywords":"one search term",
 "reviewer_notes":["anything questionable or missing, for the social media manager"],
 "slides":[{{"eyebrow":"short label","headline":"short, sentence case, will be set in caps","sub":"optional","body":"optional","photo":"approved photo id or omit","circles":false}}],   // CAROUSEL 5-7 slides, slide 1 is the hook; IMAGE 1 slide
 "beats":[{{"text":"short line","seconds":3}}]}}   // REELS 5-7 beats, 15-30s total, beat 1 is the hook

Caption rules: first line under 120 characters and stands alone; one call to action; 2-3 hashtags at the end after a blank line; work in one search term; no em dashes.
Write like a person talks: mix short sentences (2-4 words) with longer ones (15-25 words), use contractions, say "I", "we" and "you".
{extra}"""


def ask_claude(prompt):
    body = json.dumps({"model": MODEL, "max_tokens": 10000,
                       "messages": [{"role": "user", "content": prompt}]}).encode()
    req = urllib.request.Request("https://api.anthropic.com/v1/messages", data=body, headers={
        "x-api-key": os.environ["ANTHROPIC_API_KEY"], "anthropic-version": "2023-06-01",
        "content-type": "application/json"})
    with urllib.request.urlopen(req, timeout=300) as r:
        text = json.load(r)["content"][0]["text"]
    s, e = text.find("["), text.rfind("]")
    return json.loads(text[s:e + 1])


def approved_photo_ids():
    p = ROOT / "assets" / "approved" / "catalog.json"
    return [e["id"] for e in json.loads(p.read_text())] if p.exists() else []


def get_posts(extra="", mix_override=None):
    if os.environ.get("GEN_MOCK"):
        return json.loads(Path(os.environ["GEN_MOCK"]).read_text())
    mix = mix_override or ", ".join(f"{n} {t}" for t, n in BRAND["posts_per_week"].items())
    msgs = "\n".join(f"- {k}: " + " | ".join(v) for k, v in BRAND["core_messages"].items())
    rules = RULES.format(names=", ".join(BRAND["products"]["confirmed_full_names"]),
                         photos=", ".join(approved_photo_ids()) or "none")
    return ask_claude(PROMPT.format(
        brand=BRAND["brand_name"], handle=BRAND["handle"], voice=BRAND["voice"],
        pillars=", ".join(BRAND["pillars"]), needs=", ".join(BRAND["need_states"]),
        facts="\n".join("- " + f for f in BRAND["approved_facts"]), messages=msgs,
        taglines=", ".join(BRAND["taglines"]), topics="; ".join(BRAND["topics"]),
        keywords=", ".join(BRAND["keywords"]), rules=rules, mix=mix, extra=extra))


def evaluate(p):
    final, problems, flags = autopilot.gate(p)
    return final, problems, flags


def main():
    base = os.environ.get("MEDIA_BASE_URL", "https://example.com/media").rstrip("/")
    posts = get_posts()
    results = [(p, *evaluate(p)) for p in posts]
    # one repair round for blocked posts, fed with the exact violations
    bad = [(p, pr) for p, _, pr, _ in results if pr]
    if bad and not os.environ.get("GEN_MOCK"):
        fb = "; ".join(sorted({x for _, pr in bad for x in pr}))[:1500]
        fixed = get_posts(extra=f"The previous attempt was rejected for: {fb}. Fix exactly that.",
                          mix_override=", ".join(f"1 {p['type']}" for p, _ in bad))
        results = [r for r in results if not r[2]] + [(p, *evaluate(p)) for p in fixed]

    start = datetime.now(timezone.utc).replace(hour=14, minute=0, second=0, microsecond=0)
    review_lines, made, slot = [], 0, 0
    for p, final, problems, flags in results:
        title = f'{p.get("type")} "{p.get("topic")}"'
        if problems:
            review_lines.append(f"### DROPPED {title}\n" + "\n".join(f"- BLOCK: {x}" for x in problems) + "\n")
            continue
        pid = f"{datetime.now(timezone.utc):%Y%m%d}-{uuid.uuid4().hex[:6]}"
        media, warnings, t = ROOT / "media" / pid, [], p["type"].upper()
        item = {"type": t, "caption": final, "keywords": p.get("keywords", "")}
        if t == "REELS":
            render.render_reel(p["beats"], media / "reel.mp4", warnings)
            item["media_url"] = f"{base}/{pid}/reel.mp4"
        else:
            files = render.render_slides(p["slides"], media, warnings)
            urls = [f"{base}/{pid}/{f.name}" for f in files]
            if t == "CAROUSEL" and len(urls) >= 2:
                item["media_urls"] = urls
            else:
                item["type"], item["media_url"] = "IMAGE", urls[0]
        slot += 1
        item["publish_at"] = (start + timedelta(days=1 + (slot - 1) * 7 // max(len(results), 1))).isoformat().replace("+00:00", "Z")
        notes = [f"NOTE: {n}" for n in p.get("reviewer_notes", [])]
        allflags = flags + sorted(set(warnings))
        dest = "review" if allflags else "queue"
        item["flags"] = allflags
        (ROOT / dest).mkdir(exist_ok=True)
        (ROOT / dest / f"{pid}.json").write_text(json.dumps(item, indent=2))
        made += 1
        review_lines.append(f"### {'NEEDS REVIEW' if allflags else 'CLEAN'}: {pid} {item['type']} {item['publish_at']}\n"
                            + f"Topic: {p.get('topic')}\n\nCaption:\n\n> " + final.replace("\n", "\n> ")[:900] + "\n\n"
                            + "\n".join(f"- FLAG: {x}" for x in allflags) + ("\n" if allflags else "")
                            + "\n".join(f"- {x}" for x in notes) + "\n")
    (ROOT / "REVIEW.md").write_text("# Weekly review\n\nClean posts are in queue/. Flagged posts are in review/ and will NOT "
                                    "publish until reviewed.\n\n" + "\n".join(review_lines))
    print(f"{made}/{len(results)} posts created; see automation/REVIEW.md")


if __name__ == "__main__":
    main()
