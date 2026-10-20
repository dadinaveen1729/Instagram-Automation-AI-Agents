# Instagram autopilot: one-time setup

After this, it runs alone. Every Monday it writes the week, makes the images and Reels,
checks them, and either posts them on schedule (auto) or opens a pull request you merge
from your phone to approve.

**Requires a public GitHub repo** (Instagram must fetch media from a public link).

1. Instagram: switch to a Business or Creator account, link it to a Facebook Page.
2. developers.facebook.com: create an app, add "Instagram API with Facebook Login",
   permissions `instagram_basic` and `instagram_content_publish`. Get your Instagram user ID
   and a long-lived access token (renew about every 60 days).
3. console.anthropic.com: create an API key (pay as you go, roughly cents per week).
4. GitHub repo > Settings > Secrets and variables > Actions:
   - Secrets: `IG_USER_ID`, `IG_ACCESS_TOKEN`, `ANTHROPIC_API_KEY`
   - Variables: `AUTO_APPROVE` = `1` for fully hands-off (or leave unset to approve by merging a PR),
     `IG_LIVE` = `1` to really post (leave unset first to test)
5. Edit `automation/brand.json`: niche, audience, topics, search terms, posts per week.
6. Actions tab > run `instagram-generate` once, check the output, then set `IG_LIVE=1`.

Stop everything: add a file named `PAUSE` in `automation/`.
