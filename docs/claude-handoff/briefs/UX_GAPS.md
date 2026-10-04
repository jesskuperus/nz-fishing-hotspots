# UX gaps: nz-fishing-hotspots (region corrected to Tutukaka)

## READ FIRST: region corrections (these override the list below)

Original list below was written for Taranaki by mistake. Apply these corrections:

1. Remove the gap "no region switch / Taranaki needs its own region config". Region stays Tutukaka. Keep a region config object internally so a second region is cheap later, but no switcher UI.
2. Drop every Taranaki / Central-area rule reference. Rules area is Auckland and Kermadec, FMA Auckland East (SNA1).
3. NEW, high priority: Poor Knights Marine Reserve is full no-take (DOC). The map box is centred on the Poor Knights shelf, so suppress hotspots/heatmap inside the reserve polygon and show a "no-take reserve" overlay and legend. Source: https://www.doc.govt.nz/parks-and-recreation/places-to-go/northland/places/poor-knights-islands-marine-reserve/ . Do not trust explorewhangarei.co.nz on this.
4. Species guide: use SPECIES_TUTUKAKA.md as data source; split "Marlin/Tuna"; show source chips and "last checked" for limits.
5. Snapper spawn aggregation prior should use the live SST layer (~18C threshold) not only the month.
6. Rules link: NZ Fishing Rules app (MPI) from every species card.
Everything else (loading/error state, data-as-of stamp, reduced motion, aria-live, shareable URL, robots/sitemap/favicon, no feedback button) is unchanged.

---

## Original audit (14 ranked gaps)


Method: read the live page source at https://nz-fishing-hotspots.vercel.app/ (4 Oct 2026) against the playbook (Obsidian 04 - AI Coach / Web Design, "Web design playbook and designer brief", sections 2, 5, 6, 7). This is a code-read audit. I did not take desktop or mobile screenshots, so layout and tap-target findings marked (check) need the Playwright pass in step 1 of the plan.

The playbook is written for marketing sites. Rules that apply to an app map: loading/empty/error states (6.7), permissions only when needed (6.13), links open exact content (6.15), tap targets, contrast, focus, motion, pre-launch checks (7).

## Priority list (ranked by impact)

1. No visible loading, error or offline state for the daily data. Source has a "loading" string twice and no skeleton or error handling for failed layer fetches. Spec: skeleton over the sheet and a "Updating today's data..." bar on the map; error card with Retry; "Data as of <date/time>" always visible. (6.7, 2.7)
2. "Real vs demo" is easy to miss. A banner exists, but marks, species tags and names are invented. Spec: every card with demo data carries a small "Demo" chip; real layers carry "Live: <source>, <date>". Playbook rule from her own prototypes: one clear sample-data label, kept. Do not add more badges than that; put the chip inside the card header only.
3. Species guide is static copy. The "Species guide" tab shows five hardcoded rows (Peak/Good/Steady/Early) with no reason or source. Spec: use the card format in SPECIES_TUTUKAKA.md section 4 (this-month chip, where, how they feed, source badge).
4. "Marlin / Tuna" is a grouped filter. The page itself says it is not a legal species. Spec: split into real species; filter by species list per region.
5. Accessibility gaps. No prefers-reduced-motion rule found; no aria-live region for the status/summary text that changes when the species filter or day changes; two dialogs exist (role="dialog") but check focus trap and Escape to close. Spec: add `@media (prefers-reduced-motion: reduce)`, `aria-live="polite"` on the summary and route-feedback lines, focus return to the opener on close. (2.6, 2.8)
6. Small type and tap targets (check). Source uses 11-13px text in the panel, filter and chips; playbook wants body 16px and 44px tap targets. Spec: body 14px minimum on mobile, chips and icon buttons at least 44x44 touch area, keep the compact map chrome.
7. Colours are fine on contrast on paper (ink #e7f2f8 and dim #8fa8b8 on #070d14), but the colour scale for score (purple best) is not colour-blind safe on its own. Spec: add the number or a pattern/outline to the top marks, and a legend with labels, not only colours.
8. No region switch. When Taranaki is added, the title, meta description, og tags and regs panel are all Tutukaka-specific. Spec: region selector in the header, one config object per region (bbox, marks, regs, species list, title).
9. Permissions: no geolocation use today. Good by rule 6.13. If "near me" is added, ask only when the user taps it.
10. Deep links (6.15). Selected mark, day, species filter and layer are not in the URL. Spec: sync state to the URL hash (`#region=taranaki&day=1&species=snapper&mark=12`) so shared links open the exact view.
11. Fishing-specific information the app lacks: tide times with a bite-window bar (tides are hardcoded per the current repo notes), wind and swell safety flag ("not safe to launch" banner), bar/launch conditions, sunrise/sunset, moon phase, last-updated time, and unit toggle (m/ft, C/F). Rank by usefulness: safety flag, tides, sunrise/sunset, moon.
12. Pre-launch checks (7): favicon exists inline, but /favicon.ico, /robots.txt and /sitemap.xml return 404; no canonical tag; no apple-touch-icon or web manifest (so no "Add to Home Screen" install look); og-image exists. Spec: add the missing files, add a custom 404 page, and a basic privacy line if any logging or analytics is added.
13. Share/feedback loop: Jess declined a feedback button earlier ("Don't add 3"), so do not add one. Instead make "Copy link to this view" the only share action.
14. Offline: anglers are often out of signal. Spec (optional, later): service worker cache of the last data and the trip pack, with an "Offline, showing data from <time>" bar.

## Suggested build order for Claude Code (small, safe first)

1. Run Playwright at 375px and 1280px, screenshot every tab and sheet state, confirm the (check) items.
2. Items 1, 2, 5, 12 (states, labels, a11y, pre-launch files). No design change.
3. Items 3, 4 and the species card (needs SPECIES_TUTUKAKA.md data).
4. Item 10 (URL state), then 8 (region config) only if Taranaki is going in.
5. Item 11 safety flag and tides once real tide data exists.

Rules for this pass: keep the dark nautical look, no new fonts, no new libraries, no placeholder copy, keep the "sample data" labelling rule, and do not push to main without her go-ahead.
