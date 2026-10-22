#!/usr/bin/env python3
"""Boost Oxygen brand and compliance checks, from Abi Todd's rules and the Brand Toolkit.

BLOCK = the post must not go out as written (generator rewrites or drops it).
FLAG  = a human must review the wording before it can publish.

    python3 compliance.py caption.txt        # prints BLOCK / FLAG lines, exit 1 on any BLOCK
"""
import json, re, sys
from pathlib import Path

BRAND = json.loads((Path(__file__).resolve().parent / "brand.json").read_text())
DISC = BRAND["disclaimer"]

# --- hard rules -------------------------------------------------------------------------
BLOCK_RULES = [
    (r"\b(canned|bottled|bagged) air\b|\bair in a (can|bottle|canister)\b",
     'Never describe the product as "air" or "canned air".'),
    (r"\b(treats?|treated|treating|treatment|cures?|cured|curing|diagnos\w*|heals?|healing|prevents?|preventing|therap\w+)\b",
     "Medical claim wording (treat/cure/diagnose/heal/prevent/therapy)."),
    (r"\b(copd|asthma|emphysema|bronchitis|pneumonia|mesothelioma|cancer|covid|altitude sickness|hypoxi\w*|apnea|disease|disorder)\b",
     "Names a medical condition."),
    (r"\bclinically (proven|tested)\b|\bscientifically proven\b|\bdoctor[- ]recommended\b|\bfda[- ](approved|cleared)\b",
     "Unsupported proof or endorsement claim."),
    (r"\b(testimonial|customers? (say|love|report)|rated \d|\d+ ?stars?|#1\b|best[- ]selling)\b",
     "Testimonial, rating or ranking claim that is not in the toolkit."),
    (r"[“\"][^”\"]{15,}[”\"]\s*[-—–]\s*\w+",
     "Quoted testimonial with attribution."),
]
# "can/cans" as the noun (the product container); modal "can" is left alone.
CAN_NOUN = re.compile(r"\b(a|an|the|this|that|each|every|one|your|our|their|lightweight|portable|small|new|spray|oxygen|boost)\s+cans?\b|\bcans\b|\bcanned\b|\bcan of\b", re.I)

FLAG_RULES = [
    (r"\b(relief|relieve[sd]?|relieving|ease[sd]?|easing|soothe[sd]?|soothing|alleviat\w+|fight\w*|combat\w*|improve[sd]?|reduc\w+)\b",
     "Could read as a medical or health-outcome claim. Abi to review."),
    (r"\b(shortness of breath|breathless\w*|breathing (issues?|problems?|conditions?|challenges?|difficult\w*)|lung|respiratory|symptom\w*|condition\w*|fatigue|dizz\w*|headache)\b",
     "Health or condition wording. Abi to review."),
    (r"\b(recover\w*|recharge[sd]?|energi[sz]\w+|stamina|endurance|blood flow|immune|cellular)\b",
     "Performance or physiological wording. Abi to review against the no-medical-claims rule."),
    (r"\b(acclimat\w+|altitude)\b", "Altitude wording. Confirm it does not imply treating altitude illness."),
    (r"\b(best|ultimate|incredible|amazing|revolutionary|miracle|life[- ]changing|game[- ]chang\w+|unbeatable|perfect|guaranteed|proven|superior)\b",
     "Hyperbole or superlative. The toolkit says avoid it."),
    (r"\b(buy now|limited time|act now|hurry|don't miss|last chance|must[- ]have)\b",
     "Overly salesy wording."),
    (r"\b(made in america|american[- ]made|made in the usa)\b",
     'Use the exact brand message "Made in USA".'),
]
PROMO = re.compile(r"\b(sale|discount|coupon|promo(tion)?|% ?off|\d+% off|free shipping|use code|offer|deal)\b", re.I)
NUM = re.compile(r"(?<![#\w])\d[\d,\.]*\+?\s?(?:%|X|x|L|million)?")


def split_disclaimer(text):
    if DISC in text:
        body, _, tail = text.partition(DISC)
        return body.rstrip(), True, tail.strip()
    return text.strip(), False, ""


def autofix(text):
    """Deterministic fixes only: brand message wording. Returns (text, changes)."""
    out, changes = text, []
    out2 = re.sub(r"\b(?:made in america|american[- ]made|made in (?:the )?(?:usa|u\.s\.a))\b", "Made in USA", out, flags=re.I)
    if out2 != out:
        changes.append('normalized to "Made in USA"')
        out = out2
    # brand name casing in running text (not handles or hashtags)
    out2 = re.sub(r"(?<![@#\w])boost\s?oxygen\b(?!\.com)", "Boost Oxygen", out, flags=re.I)
    if out2 != out:
        changes.append('normalized brand name to "Boost Oxygen"')
        out = out2
    return out, changes


def ensure_disclaimer(text):
    body, has, _ = split_disclaimer(text)
    if PROMO.search(body) and not has:
        return body + "\n\n" + DISC, True
    return text, False


def check(text, visible_text=""):
    """text = caption. visible_text = on-image text (slides/beats). Returns (blocks, flags)."""
    blocks, flags = [], []
    body, has_disc, _ = split_disclaimer(text)
    scan = body + "\n" + visible_text
    low = scan.lower()

    for rx, msg in BLOCK_RULES:
        if re.search(rx, low, re.I):
            blocks.append(msg + f' Found: "{re.search(rx, low, re.I).group(0)}".')
    if CAN_NOUN.search(scan):
        blocks.append(f'Say "canister", not "can". Found: "{CAN_NOUN.search(scan).group(0)}".')
    if re.search(r"\bflavou?r(s|ed)?\b", low) and "oxyburst" not in low:
        blocks.append('Say "aroma", not "flavor", for oxygen products (flavor is only OK for OxyBurst).')
    tags = re.findall(r"(?<!\w)#\w+", body)
    if len(tags) > BRAND["max_hashtags"]:
        blocks.append(f'{len(tags)} hashtags; the maximum is {BRAND["max_hashtags"]}.')
    if PROMO.search(body) and not has_disc:
        blocks.append("Promotion wording without the exact supplied disclaimer.")
    if has_disc and DISC not in text:
        blocks.append("Disclaimer is not exactly as written.")
    if re.search(r"\b(boost oxygen)\b", scan) and not re.search(r"Boost Oxygen", scan):
        blocks.append('Brand must be written "Boost Oxygen".')
    if len(body) + (len(DISC) + 2 if has_disc else 0) > 2200:
        blocks.append("Caption over 2,200 characters.")

    for rx, msg in FLAG_RULES:
        for m in re.finditer(rx, low, re.I):
            flags.append(f'{msg} Wording: "{m.group(0)}".')
            break
    # "air": only allowed as a comparison or "air quality"
    for m in re.finditer(r"\bair\b", low):
        ctx = low[max(0, m.start() - 14):m.end() + 9]
        if not re.search(r"than (normal )?air|air quality", ctx):
            flags.append(f'"air" used outside an allowed comparison ("5X more oxygen than normal air"). Context: "...{ctx.strip()}..."')
            break
    # emoji
    emoji = re.findall(r"[\U0001F300-\U0001FAFF☀-➿]", scan)
    if len(emoji) > BRAND["max_emoji"]:
        flags.append(f'{len(emoji)} emoji; the brief says minimal (max {BRAND["max_emoji"]}).')
    # numbers must come from the approved facts
    allowed = [a.lower().replace(" ", "") for a in BRAND["allowed_numbers"]]
    for m in NUM.finditer(scan):
        tok = m.group(0).strip().rstrip(".,").lower().replace(" ", "")
        if tok and not any(tok == a or a.startswith(tok) for a in allowed):
            flags.append(f'Number not in the approved facts (possible invented detail): "{m.group(0).strip()}".')
    # products need the full approved name
    names = BRAND["products"]["confirmed_full_names"]
    mentions = [w for w in BRAND["products"]["aroma_words"] if re.search(rf"\b{w}\b", low)]
    mentions += [l for l in BRAND["products"]["lines"] if re.search(rf"\b{l}\b", scan)]
    if mentions and not any(n in scan for n in names):
        flags.append("Product line or aroma mentioned without a full approved name "
                     f'(format: {BRAND["products"]["name_format"]}). Mentions: {sorted(set(mentions))}.')
    if re.search(r"\b(sport|natural|revive|balance|breathe|calm|focus|outdoors)\s+(small|medium|large|pocket)\b", low) and not any(n in scan for n in names):
        flags.append("Size mentioned without the full name including capacity.")
    return blocks, flags


if __name__ == "__main__":
    t = sys.stdin.read() if len(sys.argv) < 2 or sys.argv[1] == "-" else Path(sys.argv[1]).read_text()
    t, ch = autofix(t)
    b, f = check(t)
    for c in ch: print("FIXED", c)
    for x in b: print("BLOCK", x)
    for x in f: print("FLAG ", x)
    if not b and not f: print("CLEAN")
    sys.exit(1 if b else 0)
