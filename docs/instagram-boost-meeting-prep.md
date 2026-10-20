# Boosting our Instagram account: meeting prep

For the meeting with the Instagram marketing manager team. Built around the 13 `/ig-*` skills in this repo.

## 1. The pitch in 30 seconds

These skills do the writing and the thinking: Reel scripts, captions, carousels, stories, comments, DMs, the weekly plan, and an audit of what already worked. **A person still posts everything.** Nothing is auto-posted, because automating posting or DMs on Instagram breaks its Terms and gets accounts blocked. The tools are free, run locally, and need no API key.

What it will not do: promise views or followers. The repo's own test shows the hook scorer catches bad hooks well (AUC 0.83) but does not pick winners (AUC 0.56). It filters out weak work before you shoot. Retention data decides the rest.

## 2. Process to activate (step by step)

| Step | Who | Action | Skill / file | Done when |
| --- | --- | --- | --- | --- |
| 0 | Account owner | Confirm account is Professional (Business or Creator) and Insights is available | Instagram settings | Insights visible |
| 1 | Marketing lead | Write the brand voice profile (3 sample reels or `templates/voice.md`) | `~/.claude/instagram/voice.md` | File exists. Every skill reads it |
| 2 | Content lead | Score the profile out of 100 and fix name, bio, link, highlights, pinned 3 | `/ig-profile` | Score 80 or higher, fixes applied |
| 3 | Content lead | Audit the last 20-30 posts: what worked, what to stop | `/ig-audit` (paste Insights) | Keep and stop lists agreed |
| 4 | Content lead | Research the niche: 10 accounts, outlier reels, swipe file | `/ig-viral` | Swipe file with named hook formulas |
| 5 | Content lead | Build week 1 plan: formats, times, 10 accounts to engage | `/ig-plan` | Calendar approved |
| 6 | Creator | Reels: pick hook, score it, script, time it before shooting | `/ig-reel` (`hookscore.py`, `beats.py`) | Hook rated OK or better, beats under target |
| 7 | Creator | Captions (first 125 chars, max 5 hashtags) and carousels | `/ig-caption`, `/ig-carousel` | Caption lint passes |
| 8 | Creator | Humanize every draft before it is shown | `/ig-human` | Human score PASS |
| 9 | Manager | **Approve and post manually** | Instagram app | Approved by a named person |
| 10 | Community mgr | Daily: stories, comments on 10 target accounts, replies, DMs | `/ig-story`, `/ig-comment`, `/ig-reply`, `/ig-dm` | Replied inside the agreed window |
| 11 | Content lead | Weekly review, then repeat steps 3-5 | `/ig-audit`, `/ig-plan` | Next week's plan reflects data |
| 12 | Content lead | Turn long assets (webinars, podcasts, client calls) into a week of posts | `/ig-repurpose` | Backlog of 5-7 posts |

**Weekly rhythm:** Mon plan, Tue-Fri create and post, daily 20 min engagement, Fri audit.

**Setup effort:** about 1 day for steps 0-5. After that, roughly 1-2 hours per post-ready piece, mostly shooting.

## 3. Questions to ask the team (with the answers we need)

### Goals and baseline
1. **What is the goal for the next 90 days: followers, reach, leads, or sales?** We need one primary number. Everything in `/ig-plan` is built backward from it.
2. **What are the current numbers?** Followers, average reach per Reel, saves, shares, profile visits, link clicks. Without a baseline we cannot show the boost worked.
3. **Which 3 posts worked best, and why do you think so?** Feeds `/ig-audit`.

### Audience and brand
4. **Who is the one target customer, and what do they search for?** Used for hooks and search terms in captions.
5. **How does the brand sound on camera? Who are the on-camera people?** Needed for `voice.md`. A script in the wrong voice does not get used.
6. **What can we never say or show?** Legal, compliance, competitor mentions, claims needing sign-off.

### Content and capacity
7. **How many Reels, carousels, and story days per week can the team actually produce?** The plan must match real capacity. Three good Reels beat seven rushed ones.
8. **Who shoots and edits?** The scripts are only the start. Shooting is the bottleneck.
9. **Which long assets do we already have (videos, webinars, newsletters)?** Fastest source of content via `/ig-repurpose`.

### Process and risk
10. **Who approves posts, and how fast?** Needs a named approver and a turnaround time.
11. **Do you use any auto-posting or auto-DM tools today?** Browser automation and unapproved tools break Instagram's Terms and risk action blocks. Keyword DM auto-replies are fine only through Instagram's own tools or approved partners.
12. **Do we have a Meta developer app and linked Page?** Only needed if the team wants API publishing later. Not needed to start.
13. **Is there paid budget to boost the top organic posts?** Organic winners from `/ig-audit` are the best candidates to put spend behind.

## 4. Questions the team will likely ask us (with answers)

**Q: Will this get us more followers?**
A: It raises the quality and consistency of what we post, and it kills weak hooks before we film them. It cannot guarantee reach. Growth is measured against the baseline in Q2 above.

**Q: Does it post for us?**
A: No. Every skill ends with a copy-ready block and a person posts. That is deliberate and keeps the account safe.

**Q: Will the content sound like AI?**
A: `/ig-human` removes em dashes, 154 stock phrases and invisible characters, then scores the result. It is a local heuristic, not a promise to beat any specific AI detector.

**Q: Is it safe for the account?**
A: Yes. No logins, no scraping at volume, no automation against Instagram. `/ig-viral` is a research workflow where a person browses their own session at human speed.

**Q: What does it cost?**
A: The skills are free (MIT). The real cost is team time, plus any paid boosting budget.

**Q: How do we know a hook is good?**
A: `hookscore.py` rates length, specificity, stakes, frontloading, and direct address. It reliably flags bad hooks. Treat a high score as "worth shooting", not as a prediction. The retention graph decides.

**Q: Can it work with our brand voice and compliance rules?**
A: Yes. `voice.md` holds the voice and the never-say list. Compliance sign-off stays with a human.

**Q: What if Instagram changes rules?**
A: Platform numbers go stale. Example: the hashtag cap dropped from 30 to 5 in December 2025. Instagram's current rules override anything in the repo, so we re-check quarterly.

## 5. 30-day rollout

- **Week 1:** voice file, profile fixed, audit, niche research, first plan.
- **Week 2:** 3 Reels + 1 carousel + daily stories, 20 min/day engagement.
- **Week 3:** keep the format that earned the highest saves/shares per reach, drop the lowest, repurpose one long asset.
- **Week 4:** full audit against the baseline, decide what to scale, decide on paid boost for the top 2 organic posts.

## 6. KPIs to track weekly

Reach per Reel, 3-second hold / average watch time, shares and saves per reach (stronger signal than likes), profile visits, link clicks, follower growth, DM conversations started. Compare against the baseline from Q2.

## 7. Decisions needed from the meeting

1. The one primary 90-day goal and its number.
2. A named owner for each role in section 2.
3. Posting cadence the team can sustain.
4. A named approver and turnaround time.
5. Whether to set aside a paid-boost budget.
6. Agreement to stay inside Instagram's Terms (no unapproved automation).
