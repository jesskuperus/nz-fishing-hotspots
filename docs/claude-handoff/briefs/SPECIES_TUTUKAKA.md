# SPECIES_TUTUKAKA.md - species brief for nz-fishing-hotspots (Tutukaka coast, Northland east)

Region: Tutukaka coast and Poor Knights shelf, Northland Pacific side.
Written 2026-10-04. Nothing here is pushed to the repo.

Source tags: **[OFFICIAL]** MPI / DOC / Fisheries NZ / NIWA. **[ANGLER]** fishing media, charter or guide site. **[UNVERIFIED]** general knowledge or single weak source, needs checking. Everything seasonal is a prior, not a forecast. Label species output "demo-grade" in the UI until checked.

## 0. Region rules (read first)

- Tutukaka is in the **Auckland and Kermadec** MPI rules area (covers Northland, Auckland, Waikato, Bay of Plenty). Fisheries management area for snapper/kingfish/etc is **Auckland East (FMA 1 / SNA1 / KIN1)**, North Cape to Cape Runaway. [OFFICIAL] https://www.mpi.govt.nz/fishing-aquaculture/recreational-fishing/fishing-rules/auckland-kermadec-fishing-rules
- Combined daily limit: 20 finfish per fisher, plus species limits inside it. Baitfish (50) and eels (6) are extra. [OFFICIAL, same page]
- **Poor Knights Islands Marine Reserve is full no-take.** No fishing of any kind, boat or shore. [OFFICIAL] https://www.doc.govt.nz/parks-and-recreation/places-to-go/northland/places/poor-knights-islands-marine-reserve/
  - WARNING: one local tourism page (explorewhangarei.co.nz, May 2026) says ~95% of the reserve is open to fishing. That contradicts DOC. Treat that page as wrong. Do not use it as a source.
  - The app map is centred on the Poor Knights shelf. Any "hotspot" mark, heatmap cell or species highlight inside the reserve boundary must be suppressed or shown as "no-take reserve". Get the boundary polygon from DOC/LINZ; the app showed no reserve text in my quick check (live page is JS-rendered, so verify in code). 
- Rules change. Link the NZ Fishing Rules app (MPI) from the app and show "limits last checked: <date>".

## 1. Species table

| Species | Behaviour / living habits (Tutukaka prior) | Source tag |
|---|---|---|
| Snapper | Spawn late Oct-Feb, peak Nov-Dec, triggered by ~18C water. Northland east coast hits 18C early-mid Nov. Spawners gather on shallow sand/shell, often 8-15 m, inside the 20 m contour. Individuals spawn in batches every few days. Big fish work inshore rocks/reefs in winter (green water after storms, berley). Most tagged snapper are recaptured within ~9 km of release (some move 10-90 km). | Spawn/temp: [ANGLER] newswire.co.nz 2026-04-24, cites NIWA work. Rock winter: [ANGLER] fishing.net.nz Northland report 28-05-26. Movement: [OFFICIAL] NIWA FRDop35 https://webstatic.niwa.co.nz/library/FRDop35.pdf |
| Kingfish | Reef, pinnacle, headland and island-edge fish, live-baited or jigged. Summer is the main season. Winter is contested: one source says many "disappear" offshore, a Far North report says big fish move inshore onto bait schools (blue koheru) in late autumn. | [ANGLER] nzdiver.com; fishing.net.nz Northland report (Doubtless Bay, not Tutukaka). Treat winter presence as [UNVERIFIED]. |
| Trevally | Inshore reef/sand schooling fish. Seasonal timing for Tutukaka not found. | Presence: [ANGLER] whangareionline.co.nz. Timing: [UNVERIFIED]. Catch seasonality chart exists at https://fs.fish.govt.nz/Page.aspx?pk=8&stock=TRE1&tk=41 (not read in detail; use it). |
| Kahawai | Surface schooling, follows bait, around headlands and river mouths. | Presence: [ANGLER]. Habits: [UNVERIFIED]. |
| Tarakihi | Charter sites list as a spring-late summer target. Bottom fish over reef/sand. | [ANGLER] grandcrucharters.nz (2024). Depth habits [UNVERIFIED]. |
| Red gurnard | Sand/mud bottom fish, taken as bycatch. | Listed as a Northland-area recreational fish: [OFFICIAL] fs.fish.govt.nz. Habits [UNVERIFIED]. |
| John dory | Listed as a stock in the region. Habits for Tutukaka not sourced. | [OFFICIAL] fs.fish.govt.nz (list only). Rest [UNVERIFIED]. |
| Hapuku / bass | Deep drop fish on channels and drop-offs offshore, not an inshore species. | [ANGLER] explorewhangarei.co.nz and whangareionline.co.nz. Depth/season [UNVERIFIED]. |
| Bluenose | Deep-water drop fish, same grounds as hapuku. | [ANGLER] as above. |
| Striped marlin | Summer game fish, warm northward currents bring them within range roughly Dec-Apr. | [ANGLER] explorewhangarei.co.nz. Hot-spots by water temperature [UNVERIFIED]. |
| Yellowfin tuna | Follows the same warm-water systems as marlin, Dec-Apr. | [ANGLER] same. |
| Mahi mahi | Summer, around floating debris and temperature breaks. | [ANGLER] same. |

Not covered: sharks, albacore, swordfish (a Northland report mentions swordfish deep dropping). No usable Tutukaka source, leave out or keep demo-grade.

## 2. Seasonal calendar (priors for the heatmap; confidence in brackets)

- **Jan-Feb**: snapper post-peak spawn, still on shallows [angler]. Kingfish and game fish season [angler]. 
- **Mar-Apr**: marlin/yellowfin/mahi tail off by April [angler, rough]. Snapper disperse after spawning [angler].
- **May-Aug**: snapper bigger fish move to rocky inshore, tarakihi/gurnard/deep drop options. Kingfish unclear [unverified].
- **Sep-Oct**: warming, spring snapper and tarakihi picking up [angler, charter]. 
- **Nov-Dec**: snapper spawn peak on 8-15 m sand/shell [angler, cites NIWA]. Kingfish and game fish arriving [angler].
Implementation hint: drive snapper "spawn aggregation" from the app's live SST layer (>= ~18C), not the calendar alone. The app already has Copernicus SST; this is a better prior than month.

## 3. Bag and size limits (flag for checking before display)

All from the MPI Auckland/Kermadec page above, [OFFICIAL], read 2026-10-04. Confirm in the NZ Fishing Rules app before the app shows them.

| Species | Daily limit | Min size |
|---|---|---|
| Snapper (Auckland East, SNA1) | 7 | 30 cm |
| Kingfish | 3 | 75 cm |
| Hapuku/bass | 2 (accumulation max 3 over multiple days) | none |
| Bluenose | 5 | none |
| Southern bluefin tuna | 1 | none |
| Trevally | within combined 20 | 25 cm |
| Tarakihi | within combined 20 | 25 cm |
| Red gurnard | within combined 20 | 25 cm |
| Kahawai | within combined 20 | none |
| John dory, yellowfin, mahi mahi, marlin | not in MPI individual tables; treat as combined 20 / gamefish rules [UNVERIFIED] | check |

Note: snapper is 7 here, versus 15 (Auckland/Kermadecs generally) and 10 (Auckland West). Do not reuse a generic snapper number.
Also in force: closures near Northland (e.g. spiny rock lobster closed Parengarenga to Cape Rodney from 1 April 2026) are on the MPI page; not relevant to finfish but useful for a "closed areas" layer.

## 4. Species card spec (per species)

- Header: name, photo/icon, "demo-grade" badge until sourced.
- Line 1: what it's doing now in the region (from calendar + live SST).
- Line 2: where (habitat: reef, sand/shell 8-15 m, pinnacle, deep drop) and which grid cells the heatmap is highlighting.
- Rules row: daily limit, min size, "last checked <date>", link to NZ Fishing Rules app.
- Source row: tag chip ([official]/[angler]/[unverified]) with link. 
- Reserve row: "Inside Poor Knights Marine Reserve: no fishing" when the cell is in the polygon.
- Remove "Marlin/Tuna" as a single group; split into striped marlin, yellowfin tuna, mahi mahi.

## 5. Data gaps

- No official seasonal data for Tutukaka; the only catch-by-month source I found is Fisheries NZ's per-stock page (e.g. TRE1), which is Auckland East wide, not Tutukaka. Use https://fs.fish.govt.nz/Page.aspx?fyk=38&pk=41&tk=99 for stock list and per-stock pages.
- Hapuku, bluenose, kahawai, John dory habits are not sourced for Tutukaka.
- Kingfish winter behaviour has conflicting sources.
- Two weak sources (charter/tourism pages) carry most of the game fish season claims.
