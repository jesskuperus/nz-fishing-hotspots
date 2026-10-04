# Claude Code handoff: nz-fishing-hotspots (Tutukaka), 4 Oct 2026

Everything produced today by Instinct, in one place. Nothing here has been applied to app code or deployed. Docs only, on branch docs-claude-handoff (not main).

## Context
- App: Tutukaka coast fishing-spot map (Poor Knights shelf, about 56 x 54 km box, 500 m grid). Live: https://nz-fishing-hotspots.vercel.app/ . Backend engine writes the daily GeoJSON at 05:30; front end is public/index.html.
- Region is Tutukaka (Northland, Pacific side). Not Taranaki. Ignore any Taranaki leftovers.
- Real data now: depth, sea temp, chlorophyll, currents, wind, swell, modelled tides. Still demo: fronts, species, mark names. Keep the single "sample data" labelling rule.
- Jess's rules: dark nautical look, no new fonts, no new libraries, no placeholder copy, no feedback button, do not push to main without her go-ahead (use a branch and PR).

## Files in this folder
| File | What it is |
|---|---|
| reserve-patch/ | Marine reserve fix (patch, new engine module, test, DOC boundaries). HOW_TO_APPLY.md inside. |
| data/tutukaka_restricted_areas.geojson | Mimiwhangata no-take (official NRC polygon) plus two APPROXIMATE amber info zones. Copy to public/ too. |
| briefs/RESTRICTED_AREAS_AND_BOATIE_INFO_BRIEF.md | Rules by area with official/other tags and source URLs, boating safety, forecast links, gaps, disclaimers. |
| briefs/SPECIES_TUTUKAKA.md | 12 species rows, seasonal priors, limits to verify, species card spec. |
| briefs/UX_GAPS.md | Region corrections first, then the 14 ranked UX gaps and a build order. |
| briefs/WEB_DESIGN_PLAYBOOK.md | Designer brief (section 2) and checklists (sections 5 to 7). Treat as a review list; it was written for marketing sites. |

Also in Drive (Jess's "Fishing app" folder): https://drive.google.com/drive/folders/1d0Ffdo3LoKgnmTvTIj_TeWAp62hwAO5B , including the full reserve-patch.zip with the patched index.html and pipeline.py.

## Key findings to keep in mind
1. The app had no reserve handling. All 25 top marks of 4 Oct were inside the Poor Knights no-take reserve; 131 cells touch a reserve.
2. Poor Knights: no fishing of any kind, no landing, 5 knots within 200 m of shore, reserve extends 800 m. DOC does not ban anchoring (asks for responsible anchoring). Ignore explorewhangarei.co.nz, which wrongly says 95% is open.
3. Mimiwhangata Rahui Tapu is no-take (NRC, since 31 Jul 2023) and sits on the north-west edge of the box. Suppress marks like the reserves.
4. Tutukaka/Ngunguru/Horahora s186A closure (26 Jun 2026 to 25 Jun 2028) closes species (shellfish, crab, octopus, rock lobster etc.) and bans nets in the harbour and rivers. Finfish like snapper are open. Show as an info overlay, do not suppress marks. Boundaries for the amber zones are approximate.
5. Spiny rock lobster (crayfish) has been closed from Parengarenga to Cape Rodney since 1 Apr 2026. Remove it from species or label it closed.
6. Maunganui Bay is outside the box. No taiapure or mataitai inside the box. No official boat ramp coordinates were found, so none are in the data: do not invent any.
7. Reserve data not covered: older Mimiwhangata marine park polygon, any other local restrictions. Boundaries are not legal advice; link to the MPI NZ Fishing Rules app.

## Build order (small and safe first; one commit per step on a branch)
1. Apply the reserve patch (reserve-patch/). Run tests. Screenshot at 375px and 1280px, Reserves on and off.
2. Restrictions layer: add data/tutukaka_restricted_areas.geojson. Mimiwhangata is red dashed and suppresses marks (cell touches polygon plus about 110 m margin). The two amber zones are info overlays only. One "Restrictions" toggle grouping reserves plus these, default on. Keep the failed-to-load behaviour (error instead of marks). Footer: "Boundaries from DOC, NRC and gazette notices on <date>. Not legal advice; check the MPI rules app." Add tests per section 1 of the restricted-areas brief.
3. Remove or close-label crayfish. Replace hard-coded MPI limits with a rules card that links to the MPI Auckland and Kermadec page and says verify, or use the limits in SPECIES_TUTUKAKA.md section 3 with source chips and a "last checked" date.
4. UX_GAPS items 1, 2, 5, 12: loading/error/offline states and data-as-of stamp, one Demo chip in card headers, accessibility (reduced motion, aria-live, focus return), pre-launch files (favicon.ico, robots.txt, sitemap.xml, canonical, apple-touch-icon, manifest, 404).
5. Species guide from SPECIES_TUTUKAKA.md (card spec in section 4). Split "Marlin / Tuna" into real species. Drive the snapper spawn prior from the live SST layer (about 18 C), not only the month. Label demo-grade until checked.
6. Boating and safety info panel from the restricted-areas brief: lifejacket rules, bar and harbour crossing warnings, Northland Regional Council navigation notes, forecast links (link out, do not scrape), Poor Knights rules. No boat ramp pins unless an official list is sourced.
7. Shareable URL state (day, species, layer, mark), then "Copy link to this view" as the only share action. Keep an internal region config object, no region switcher.
8. Later, when real tide data exists: bite-window bar, wind and swell "not safe to launch" flag, sunrise/sunset, moon, unit toggle.

Done criteria: tests pass, no mark inside any no-take area, visual check at 375px and 1280px twice, short report of what changed, what was checked and what is still weak. Open a PR; do not merge or deploy until Jess says so.

## Paste-ready Claude Code prompt
```
Read docs/claude-handoff/HANDOFF.md first, then the files it lists in docs/claude-handoff/briefs/, data/ and reserve-patch/.

This docs branch (docs-claude-handoff) holds only these handoff files. Create a new branch called reserves-and-restrictions from it and work there. Follow the "Build order" in HANDOFF.md step by step, one commit per step. Start with step 1, the reserve patch: apply docs/claude-handoff/reserve-patch (see HOW_TO_APPLY.md), run the tests, and screenshot the map at 375px and 1280px with the Reserves toggle on and off. Then do step 2 (restrictions layer), step 3 (crayfish and rules card) and step 4 (UX gaps 1, 2, 5, 12).

Rules: the region is Tutukaka. Keep the dark nautical look. No new fonts or libraries. No placeholder copy and no invented facts: boat ramp locations, species limits and boundaries must come from the briefs and their official sources, or be left out. Keep the single "sample data" label. No feedback button. Never show a mark inside a no-take area. Do not push to main and do not deploy. Open a pull request when done.

After each step, open the page in a real browser, check mobile and desktop, fix what looks off, and repeat once. At the end report what changed, what you checked, and what is still weak. Stop after step 4 and wait for me before starting step 5.
```
