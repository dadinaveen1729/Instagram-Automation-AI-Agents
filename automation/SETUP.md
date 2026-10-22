# Boost Oxygen Instagram automation: setup

Every Monday it drafts the week under the Brand Toolkit and Abi's copy rules, renders the images
and Reels, checks them, and opens a pull request. **Nothing publishes until the PR is merged
(approval).** After the merge, the publisher posts each approved item at its scheduled time.

## One-time setup
1. Instagram account is Business or Creator, linked to a Facebook Page, with a Meta Business account.
2. developers.facebook.com: create an app with "Instagram API with Facebook Login"
   (`instagram_basic`, `instagram_content_publish`). Get the Instagram user ID and a long-lived token
   (renew about every 60 days).
3. Anthropic API key (pay as you go).
4. GitHub repo: Secrets `IG_USER_ID`, `IG_ACCESS_TOKEN`, `ANTHROPIC_API_KEY`. Variable `IG_LIVE=1` only
   when ready to post for real (leave unset for dry runs). Repo must be public for Instagram to fetch media
   (or tell us and we change the hosting).
5. Add the approved assets (see `assets/README.md`): the approved logo files and approved photos.
   Without logos, every post is flagged "logo missing" and held for review.
6. Confirm the full product names (see `brand.json` -> `products.confirmed_full_names`).

## Approving
- `queue/` posts: clean. Merge the PR to approve.
- `review/` posts: flagged wording (see `REVIEW.md`). They never auto-publish. To approve one, edit its
  JSON (fix wording if needed), set `"reviewed_by": "Abi"`, and move it to `queue/`. To reject, delete it.
- Stop everything: add a file named `PAUSE` in `automation/`.

Rules enforced by `compliance.py` and `render.py` are listed in `docs/boost-oxygen-brand-rules.md`.
