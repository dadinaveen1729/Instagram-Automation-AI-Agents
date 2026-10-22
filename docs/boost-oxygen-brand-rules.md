# Boost Oxygen: how each rule is enforced

Source: Abi Todd's email (Oct 2026) and the Brand Identity Toolkit 2025. Checks live in
`automation/compliance.py` (copy) and `automation/render.py` (visuals). BLOCK = rewrite or drop.
FLAG = a person reviews it before it can publish.

| Rule | How it is enforced |
| --- | --- |
| "canister", not "can" | BLOCK on the noun "can/cans/canned" (modal "can" is fine) |
| "aroma", not "flavor" (OxyBurst excepted) | BLOCK on "flavor" unless OxyBurst is mentioned |
| "Boost Oxygen" for the brand | Auto-corrected casing; BLOCK if left wrong |
| Never "air" / "canned air" for the product | BLOCK on "canned air", "air in a can"; FLAG any "air" outside "than normal air" / "air quality" |
| Full product names with size and capacity (SPORT Orange \| Large (10L)) | FLAG any product line, aroma or size named without a confirmed full name. Only one full name is confirmed so far |
| Never generate or alter product canisters | Pipeline draws text cards only. Product visuals come only from approved photos (`assets/approved/`), placed whole: no crop, filter, overlay or redraw |
| Approved logos only | Only files in `assets/logo/`, uniform scaling only. Missing file = no logo drawn and the post is FLAGGED |
| Toolkit fonts and colors | Oswald SemiBold caps headlines, Open Sans body, toolkit palette, secondary circles in the right order under a headline. Not implemented: -10 letter tracking |
| Friendly, natural, light humor, not salesy | Writing prompt plus FLAG on hyperbole/superlatives and salesy phrases |
| Minimal emoji, max 5 hashtags | FLAG above 1 emoji; BLOCK above 5 hashtags |
| No direct or implied medical claims | BLOCK on treat/cure/diagnose/heal/prevent/therapy and condition names. FLAG softer wording (relief, respiratory, recover, shortness of breath, acclimation...) with the exact phrase listed for Abi |
| "Made in USA" exact phrase | Variants auto-corrected to "Made in USA" |
| Disclaimers exactly as written | Supplied disclaimer is appended unchanged whenever promo wording appears, and is excluded from the humanizer. BLOCK if altered |
| No invented details, stats, testimonials, results | Numbers must match the approved-facts list or they are FLAGGED. BLOCK on testimonial, rating and ranking claims. Missing information goes in `reviewer_notes` |
| Approval before publishing | Weekly PR must be merged. Flagged posts sit in `review/` and cannot publish until `reviewed_by` is set |

## Questions for Abi / Rob (these block go-live)
1. **Logo files.** Please send the approved full-color and reverse logo files for `assets/logo/`.
2. **Approved photos.** Which product and lifestyle photos may we use? The toolkit's photos are Getty or
   "illustrative", and the toolkit says licensing must be secured.
3. **Full product names and capacities.** Only "SPORT Orange | Large (10L)" is known. We need the full
   names for every line, aroma and size.
4. **Toolkit vs your email.** The toolkit's own copy says "lightweight can", "relief from shortness of
   breath", "relieve", "respiratory support" and "recover", which conflict with the no-medical-claims and
   canister rules. We follow your email and flag those phrases. Should toolkit headlines like "Relief
   within reach" be allowed at all?
5. **"Breathe better" / "Breathe stronger"** are toolkit headlines that may read as implied claims. OK to use?
6. **Alt text and accessibility** wording for photos (not defined in the toolkit).
7. **Posting rights:** who is the Meta Business account admin who will connect the Instagram account?

## Known limitations
- The brand and compliance checks are pattern-based. They catch the listed wording, not every possible
  implied claim, so Abi's review stays the final gate.
- Reels are text-card videos with silent audio. Real footage and music are not generated.
- Auto-publishing needs the Meta developer app setup and has not been tested against a live account.
