# Tutukaka Hotspots: restricted areas + boatie/fisher info (repo-ready brief for Claude Code)

Repo: jesskuperus/nz-fishing-hotspots. Builds on the reserve patch (DOC Marine Reserves layer: Poor Knights, Whangarei Harbour). Researched 4 Oct 2026. Tags: [OFFICIAL] = regulator/legislation/gazette page. [OTHER] = industry, council-adjacent or commercial site, treat as guidance and verify.

## 0. Scope notes (read first)
- Maunganui Bay / Deep Water Cove (Rakaumangamanga Rāhui Tapu) is in the Bay of Islands (about -35.19 to -35.23 lat), OUTSIDE the Tutukaka box. Only add it if the box is ever extended north. Layer: https://nrcmaps.nrc.govt.nz/imagery/rest/services/Regional_Plan_APPEALS_Coastal/MapServer/1 (query ?where=1=1&outSR=4326&f=geojson). Same service layer 24 is the Cape Brett seining/trawl protection area (commercial methods only, not relevant to rod fishing).
- No taiāpure or mātaitai reserve exists inside the Tutukaka box (DOC mātaitai/taiāpure Dec 2021 layers, queried 4 Oct 2026: nothing intersects lat -36.0 to -35.35). [OFFICIAL data, Dec 2021 vintage]. Two mātaitai applications for Whangārei Harbour / Bream Bay (Patuharakeke Mahinga Mātaitai ~115 km2; Poupouwhenua ~1 km2 at Marsden Pt) were open for submissions in July 2026, still proposals. Source: https://www.boatingnz.co.nz/2026/07/two-mataitai-reserves-proposed-for-whangarei-harbour-and-bream-bay/ [OTHER]. Recheck before any claim.
- No submarine cable/pipeline protected area found near Tutukaka: I searched the 2009 Protection Order text for Tutukaka/Ngunguru/Northland and found nothing. Not a full verification. General warning to avoid anchoring/fishing near cables is in the LINZ Nautical Almanac [OFFICIAL]. Check the paper/electronic chart for charted cables.
- I could not reach MPI's marine protected areas ArcGIS service from my sandbox, so Mimiwhangata's older "Marine Park" (1000 m offshore, Fisheries (Amateur Fishing) Regulations 2013 s69 / sched 14) polygon is not included. The newer NRC Rāhui Tapu layer is larger and supersedes it for the no-take rule.

## 1. Map layer to add: `data/tutukaka_restricted_areas.geojson` (attached, copy to public/ too)
Three features, WGS84 lng/lat, each with properties: id, name, category, severity, applies_to, rule/extra_rule, authority, source_tag, accuracy, source_url.

| id | What | Geometry quality | In force |
|---|---|---|---|
| mimiwhangata-rahui-tapu | No-take. No taking of marine life. | OFFICIAL NRC polygon (Regional Plan for Northland layer 27), unmodified | since 31 Jul 2023 |
| rehuotane-ki-tai | s186A closure around Tutukaka Harbour / Ngunguru Bay / Ngunguru + Horahora Rivers. Species closure, not a finfish closure. | APPROXIMATE: seaward corners are gazetted coords; landward edge is a straight line, river lines not drawn | 26 Jun 2026 to 25 Jun 2028 |
| ngunguru-estuary-cockle-pipi | Cockle/pipi take and possession banned | APPROXIMATE quadrilateral from 4 gazetted points | since 7 Jan 2016 |

### Rendering and logic rules
- Mimiwhangata: red dashed like the reserves, "No fishing or taking of any marine life". Suppress marks in it exactly like reserves (cell touches polygon + ~110 m margin). In the box this sits at lat -35.38 to -35.46, lon 174.39 to 174.52 (north-west edge).
- Rehuotane Ki Tai and Ngunguru Estuary: amber, NOT suppression. Do not remove fish marks. Show as an info overlay with tooltip: "Closed to taking: cockle, crab, garfish/piper, mussel, octopus, pāua, pipi, rock lobster, rock oyster, sea cucumber, sea horse, sea snail, starfish, tuatua. Nets banned in Tutukaka Harbour, Ngunguru and Horahora rivers. Finfish (e.g. snapper) not closed by this notice." Add "approximate boundary, check the gazette map".
- Add a "Restrictions" toggle (default on) grouping Reserves + these. Keep the failed-to-load behaviour from the reserve patch: if the file fails, show an error rather than marks.
- Add a visible footer "Boundaries from DOC, NRC and gazette notices on <date>. Not legal advice; check MPI rules app."
- Add tests: no scored cell inside Mimiwhangata (+margin); the two amber layers do not remove marks; GeoJSON validates.

## 2. Rules by area (with sources)

### Poor Knights Islands Marine Reserve (DOC, Marine Reserves Act 1971) [OFFICIAL]
Source: https://www.doc.govt.nz/parks-and-recreation/places-to-go/northland/places/poor-knights-islands-marine-reserve/
- No fishing of any kind, from boat or shore. No taking or disturbing marine life, shellfish, seaweed, rocks, shells. No feeding fish. Penalties: confiscation of gear, vessels, vehicles, fines, imprisonment.
- Reserve is 2,410 ha, extends 800 m around the islands.
- 5 knots within 200 m of shore, within 50 m of other boats/swimmers or any dive-flag boat. No discharge of waste, ballast, sewage. Anchor responsibly, minimum chain.
- No landing on any island or rock. Don't tie boats to shoreline (pests, fire).
- Vessels over 45 m banned from an area 9 km (5 nm) around the islands.
- Report poaching: 0800 4 POACHER (0800 476 224) or 0800 DOCHOT (0800 362 468).
- Note: DOC's page says no anchoring ban; it asks for responsible anchoring. "No anchoring" is not a DOC rule I could find.

### Mimiwhangata Rāhui Tapu [OFFICIAL] https://www.nrc.govt.nz/environment/coast/marine-protection-areas/
- No taking of marine life. Not affecting kina daily limits or authorised customary fishing (permit needed). Boundary description (NRC): southern boundary 6.2 km offshore from Tauranga Kawau Point (just north of Titi Island), seaward boundary 8.7 km NW past Rimariki Island; northern boundary 2.9 km NNE from Paparahi Point, then 5.7 km NE out to sea.
- Older Mimiwhangata Marine Park (DOC): 1000 m offshore between Paparahi Pt and Te Ruatahi Island; no taking marine life. https://www.doc.govt.nz/parks-and-recreation/places-to-go/northland/places/mimiwhangata-coastal-park/ [OFFICIAL]
- NRC has prosecuted breaches (news item Nov 2024, https://www.nrc.govt.nz/news/2024/november/commercial-fisher-caught-as-council-clamps-down-on-rahui-tapu-rulebreakers/ [OFFICIAL]).

### Tutukaka / Ngunguru / Horahora: Rehuotane Ki Tai s186A closure [OFFICIAL]
- Gazette notice 2026 (MPI 1999): https://www.nzsportfishing.co.nz/wp-content/uploads/2026/06/Tutukaka-Gazette-notice-15-Jun-2026.pdf (hosted copy of the gazette notice; gazette ref 2026-sl3442). Decision summary: https://www.nzsportfishing.co.nz/fisheries/fisheries-management/customary/tutukaka-ngunguru-temporary-closure-2025-26/ [OTHER]. Earlier 2024 notice on gazette.govt.nz: https://gazette.govt.nz/notice/id/2024-go14 [OFFICIAL].
- Applies 26 Jun 2026 to close of 25 Jun 2028. Species closed listed above. Nets (except Danish seine, trawl, landing net to land a lawfully caught fish) banned in Tutukaka Harbour, Ngunguru River, Horahora River. Bobs, ring pots and whitebait nets are not "nets" under the notice.
- Gazetted seaward corners: 35°35.775'S 174°32.227'E (shore north of Middle Gable) due east to 35°35.775'S 174°36.250'E; to 35°41.141'S 174°34.315'E; west to 35°41.141'S 174°30.632'E (Paparoa).
- Ngunguru Estuary cockle/pipi closure: https://www.nzsportfishing.co.nz/wp-content/uploads/2026/02/Tutukaka-cockle-closure-Gazette-Dec15.pdf (gazette 2015-go7263). Gazette copy hosted by NZSFC [OTHER host, OFFICIAL notice]. Also referenced in MPI's page https://www.mpi.govt.nz/consultations/proposed-temporary-fishery-closure-and-a-netting-ban-at-tutukaka-harbour-ngunguru-bay-and-ngunguru-river-northland [OFFICIAL].
- Practical meaning: pāua, mussels, oysters, pipi, cockles, tuatua, crabs, octopus, sea cucumber and rock lobster are closed inshore. Kina is not on the closed list. Rod fishing for finfish is open.

### Rock lobster (crayfish): major change [OFFICIAL] https://www.mpi.govt.nz/fishing-aquaculture/recreational-fishing/fishing-rules/auckland-kermadec-fishing-rules
- From 1 April 2026 spiny rock lobster cannot be taken (recreational or commercial) from Pārengarenga Harbour to Cape Rodney. That covers all of Tutukaka. Penalty up to $100,000 and forfeiture. Packhorse rock lobster daily limit 3 in CRA 1 and 2 (check the table on that page).
- This matters for the app's species list: remove any "crayfish" species/hotspot, or label it closed.

### Other MPI rules to verify before display [OFFICIAL] same MPI Auckland/Kermadec page, fetched 4 Oct 2026
- Combined finfish bag limit 20 per fisher (plus 50 baitfish, 6 eels).
- Snapper (Auckland East, SNA1, North Cape to Cape Runaway): 7 per fisher, min 30 cm. Kingfish 3, min 75 cm. Hāpuku/bass 2 (accumulation 3). Bluenose 5. Southern bluefin tuna 1. Trevally min 25, tarakihi min 25, red gurnard min 25, kahawai no size limit. Blue cod min 30.
- Kina: 150 per fisher in FMA 1 (since 1 Aug 2024). Pāua and oyster limits: not verified (the table garbled in my fetch), read them on the page. Scallops season 1 Sep to 31 Mar. Check the page's "Closed areas and special restrictions" section yourself and the MPI NZ Fishing Rules app; the page itself says to use the app.
- Recreational Management Controls Notice No.1 2026 (in force 1 Apr 2026): https://www.mpi.govt.nz/dmsdocument/71138-Fisheries-Recreational-Management-Controls-Notice-No.-1-2026 [OFFICIAL]
- Add a rules card in the app that links to the MPI page and says "verify, rules change" rather than hard-coding limits unless Jess wants a limits table.

### Safety and boating rules [OFFICIAL] NRC
- Lifejackets must be worn on vessels 6 m or less when underway, when there is heightened risk (crossing a bar, bad weather), when being towed. Carry correctly fitting lifejackets for everyone on board. https://www.nrc.govt.nz/maritime/safe-boating/safe-boating-rules/
- Navigation Safety Bylaw 2017 applies region-wide; NRC says a new bylaw is "coming soon". https://www.nrc.govt.nz/maritime/bylaws-and-rules/navigation-safety-bylaws/ . Tutukaka, Whangaruru and Whananaki harbour limits come from the Tutukākā, Whangaruru and Whananaki Harbours Control Act 1926 (Schedule 1 of the bylaw): https://nrc.objective.com/portal/general/navbylaw2017/navbylaw2017?pointId=s14799293893621
- Speed: national 5 knots within 200 m of shore, 50 m of other boats/swimmers or dive-flag boats (quoted by DOC from the Marine Reserves regs; general rule is in Maritime Rules).
- Marine pest "six or one" clean hull rule to visit Northland marinas: antifoul within 6 months, or lift-and-wash within 1 month of leaving an infected area. https://www.nrc.govt.nz/ and https://www.tutukaka.co.nz/visiting-vessels [OTHER, marina summary of NRC rule]. Verify on NRC.
- Exotic caulerpa: keep gear and boat free of seaweed; report to MPI 0800 80 99 66 (DOC page).

### Bars and harbour crossing [mixed]
- NRC: Ngunguru, Pataua and Whananaki are smaller bar-type harbours that can be hard in certain weather. Local knowledge essential, "If in doubt, don't go out", skipper decides, lifejackets for bar crossings. https://www.nrc.govt.nz/maritime/safe-boating/bar-harbours/ [OFFICIAL]
- National Code of Practice for Bar Crossings (Maritime NZ) https://www.maritimenz.govt.nz/recreational-craft/on-the-water/rules-and-safety/crossing-the-bar/ [OFFICIAL]
- Tutukaka Harbour channel: boats drawing over 1.8 m (5.9 ft) should use the channel within 2 hours either side of low tide. Marina basin dredged to 2 m below chart datum. New starboard channel buoy on the outer approach to keep boats off the northern shoreline. https://www.tutukaka.co.nz/visiting-vessels [OTHER, marina operator]. Live webcams there too.
- Suggested UI: a "Crossings" info icon on Ngunguru, Pataua, Whananaki and Tutukaka entrances (approx points: Tutukaka 35.62S 174.54E; Ngunguru 35.63S 174.52E; verify against charts) that opens the NRC text. Do NOT show any "safe to cross" advice. Say "Bar/entrance can be dangerous around low tide; check forecast and local advice."

### Boat ramps [OTHER, no official list obtained]
- Tūtūkākā ramp at the marina: both sides back in use since Nov 2025 after the northern pontoon was rebuilt, main launch point for Poor Knights trips, busy in summer. https://www.boatingnz.co.nz/2025/11/new-pontoon-restores-full-access-at-tutukaka-boat-ramp/ [OTHER]
- Ngunguru ramp and water-ski lane: https://www.whangareinz.com/Discover/Destinations/Tutukaka-coast [OTHER]. Whananaki North ramp and Pataua North reserve ramp: https://rvexplorer.co.nz/Northland_Tutukaka.cfm [OTHER].
- Official source for ramps: Whangārei District Council "Beaches and coastal facilities" GIS map https://www.wdc.govt.nz/Community/Facilities/Parks-and-recreation/Coastal-Facilities [OFFICIAL, no coordinates scraped]. Recommended: add ramps only after pulling coordinates from WDC GIS; otherwise link to it. Don't invent coordinates.

### Forecast sources (link out, don't scrape) [OFFICIAL, MetService]
- Brett coastal forecast: https://www.metservice.com/marine/coastal/locations/brett
- Bream Head to Cape Colville recreational: https://www.metservice.com/marine/recreational/locations/bream-colville
- Tutukaka tides: https://www.metservice.com/marine/regions/northland/tides/locations/tutukaka-harbour
- Northland recreational: https://www.metservice.com/marine/regions/northland/recreational
- Add a "Before you go" card with these links and one line: "Check the marine forecast and bar conditions. This app is not a safety tool."

## 3. What I could not get
- Official polygon for Rehuotane Ki Tai (FNZ publishes a map image only: https://www.nzsportfishing.co.nz/wp-content/uploads/2026/06/Tutukaka-closure-map-final-Jun26.jpg). Digitise from it if exact edges matter. Ours is approximate.
- MPI's own marine protected areas service (maps.mpi.govt.nz ... MARINE_MarineProtectedAreas) timed out from my sandbox; Claude Code may be able to query it.
- Verified Tutukaka-specific speed limits, mooring and anchorage zones. NRC has "Recognised recreational anchorage" polygons (layer 36 of the same Regional Plan service, unnamed, 48 features); I did not add them since they have no names.
- Official list of ramps with coordinates.
- Pāua/oyster daily limits (garbled table in my fetch). Do not display until read on the MPI page.

## 4. Disclaimers to show in app
"Sources: DOC, NRC, MPI/Fisheries NZ, MetService. Boundaries are indicative. Always check current MPI rules (NZ Fishing Rules app) and local conditions."
