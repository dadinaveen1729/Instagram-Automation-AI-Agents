# Trend-based posts for Boost Oxygen (drafts, nothing posted)

Five concepts. Each has a 30-second vertical video with sound (1080x1920), a hook image (1080x1350
for Instagram, Facebook, LinkedIn), a wide hook image (1600x900 for X), and a caption per platform
(Instagram, Facebook, LinkedIn, X under 280 characters).

| # | Trend / format | Hook |
| --- | --- | --- |
| 01 | Market jitters, stock news | "Checking the market. Again." |
| 02 | Nonstop AI news | "AI can write your email." ... "Skills AI does not have:" |
| 03 | Thanksgiving week, turkey trots | "Thanksgiving math: pie is earned." |
| 04 | "Major cheat code in life" tip format | "Go outside first. Emails will wait." |
| 05 | "Life never handed me lemons" humor format | "It handed me a to-do list and too many tabs." |

Trends 04 and 05 come from a trending-topics list supplied by the account owner (an AI answer citing
newengen.com, sociable.how and socialbee.com). It is unverified, so check the formats on Instagram
before posting.

## What's inside each video
- Story-related animated backgrounds in the brand palette: a jagged market line that turns into a
  mountain ridge (01, 05), a network that gives way to a forest trail (02), a pie chart that fills and
  becomes a route with runners (03), a route and trail (04). Built by `automation/backgrounds.py`.
- Kinetic text (Oswald caps, Open Sans) popping in on the beat, scene flashes and shakes.
- An original synthesized 120 BPM soundtrack with word-hit sounds (`automation/kinetic.py`). It is
  royalty free. It is NOT a trending sound.

## Trending audio: add it in the app
The trends list names two audio-based formats ("It's Time" by Mariah Carey and "Housewife" by Tate
McRae). Those songs are licensed to the platforms, so they must be added inside Instagram or TikTok
(Add audio, then pick from Trending), then set the video's own sound to zero. Business accounts may
only see a commercially licensed subset. Do not embed them in the video file (copyright).

## Before posting
- **Abi approves first.** Nothing here has been posted.
- **No logo, no product photo** (approved files not supplied yet). Product canisters only come from
  approved photos. The "Add to Cart" product-showcase trend needs approved product photos, so it is not built.
- **Backgrounds are new illustrations**, not from the Brand Toolkit. Abi should approve the look. They use
  toolkit colors only.
- **Tone:** dry humor aimed at situations, never at people or health. All text passes
  `automation/compliance.py` (canister/aroma wording, Made in USA, no medical claims, only "5X" as a number).
- Real viral Reels usually show a face or the product in hand. Film that and these scripts become the
  on-screen text and voiceover.
