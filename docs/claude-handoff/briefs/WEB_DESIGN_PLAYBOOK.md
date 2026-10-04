---
tags: [ai-coach, web-design, ux, ui, claude-code, playbook]
source: "Jessica's saved Instagram reels (captions + comments) + general design practice"
reviewed: 2026-10-04
master: true
---
# Web design playbook and designer brief (single source of truth)

Master copy lives in Obsidian: 04 - AI Coach / Web Design. Copies in project repos are snapshots. Edit here, then re-copy.

## 0. Grok review prompt (paste this first, then paste or upload this whole file)

> You are a senior web designer and front-end reviewer. The attached playbook is my design standard. Read it fully. Then review the site or screenshot I give you against sections 3 to 7. Return: (1) the 5 biggest visual problems ranked by impact, (2) for each, the exact fix (spacing, type, colour, layout, copy), (3) anything that looks generic or "AI-made", (4) any rule in the playbook you disagree with and why. Do not praise. Do not rewrite the whole site. Be specific enough that Claude Code can apply each fix without asking questions.

How to load it into Grok (checked live in her Grok account on 2026-10-04): Grok has a Projects page (grok.com/project) whose New project dialog asks for a name, and its description says projects "set common instructions and attach files for conversations". Make one project, e.g. "Web design brain", paste section 0 and the brief in section 2 as the project instructions, and attach this file. Or just attach the file to a single chat. I did not create the project. Upload size limits were not confirmed.

## 1. What is in this and how good the evidence is

Built from about 30 saved reels that looked design related, out of 1,218 saved items the grid let me load. I read each reel's caption and top comments. I could not watch or transcribe the videos, so where a caption only says "comment SKILLS for the list", the actual list in the video is NOT captured. Tool and skill names below are what the creators claim. Check each before installing. Never paste a stranger's install command without reading it.

## 2. Designer brief (paste into CLAUDE.md or Claude project instructions)

Work as a senior web designer and front-end engineer for a premium, photography-led brand. Taste over features.

1. Before building: write a one-page design direction (audience, tone, 3 reference sites, type pair, colour palette with hex codes, spacing scale, button and card style). Get it approved or state assumptions. Save it as DESIGN.md in the repo and follow it.
2. Never ship default-looking output. No generic purple gradients, no stock card grids with identical icons, no centred-everything layouts, no lorem ipsum.
3. Use real hierarchy: one clear hero message, one primary action per screen, generous whitespace, max 2 typefaces, a consistent spacing scale and a restrained palette.
4. Photography leads. Crop deliberately, keep aspect ratios consistent, add a subtle overlay only where text sits on an image, and make sure text passes contrast.
5. Mobile first. Test at 375px and 1280px. Tap targets at least 44px. No horizontal scroll.
6. Motion: small and purposeful (fade or rise on scroll, hover states, 150 to 300ms easing). Respect prefers-reduced-motion.
7. Build every state: hover, focus, loading (skeletons, not blank screens), empty, error, success.
8. Accessibility: semantic HTML, alt text, visible focus rings, labels on form fields, contrast 4.5:1 for body text.
9. After each build pass: open the page in a real browser (Playwright), take desktop and mobile screenshots, list what looks off, fix it, repeat at least twice before saying it is done.
10. Do not copy another site. Use references for structure and feel only, then make it original.
11. Report at the end: what changed, what you checked, what is still weak.

## 3. Process that the reels agree on

- Collect references BEFORE prompting. Her saved reels repeat this: the best AI designs come from better inspiration, not better prompts. Sources named: Mobbin (real app screens), Awwwards (high-end layouts and motion), Cosmos and Pinterest (colour, branding), Layers (gallery of real websites by style and industry), NameThatUI (names for UI components so you can describe what you want). Refero (MCP) lets you pick parts of other sites as references. [itsmariahbrunner Da5aWOvJR2a, kiksvibecodes Dc2NQmty1Yx, gannon.meyer DX9mxYbAXug]
- Turn references into a written design system (DESIGN.md) first, then build. Reels describe Google Stitch rebuilding a design system from an Awwwards URL, and a "Skill UI" style tool that extracts a site's design system into markdown. [nicksadler.io DcwzsNnIKvc, monopolymccann Da9zw8_AaNd, nocode.joshua DWucfVJzQgU]
- "AI slop" comes from default styling, not weak prompts. Fix by giving Claude a real design system and design skills. [monopolymccann DbaR9TYR-W1, DbcgeuMyrlA]
- Close the loop with a browser: Playwright lets Claude screenshot what it built and catch problems before you see them. [nick_saraev DbyJNRdPyCj, tessa.fairbrook Dbd6PFPq3-c]
- Pick a palette with a tool (Coolors) and copy hex codes into the project. [kiksvibecodes Dc2NQmty1Yx]

## 4. Design skills and tools the creators recommend (all unverified claims)

| Name | What the creator says it does | Source reel |
|---|---|---|
| Frontend Design (Anthropic) | makes output more professional | itsmariahbrunner DbVs9yZM0ys |
| UI/UX Pro Max | makes it more cohesive | same |
| Taste | trains Claude on high quality web design, more original | same, tessa.fairbrook Dbd6PFPq3-c |
| Impeccable | refines typography and spacing, pulls from premium references | same, monopolymccann Da9zw8_AaNd |
| Emil Kowalski's skill | smooth animations, more premium feel | same, Dbd6PFPq3-c |
| Skill UI | reverse engineers any site's design system into markdown | monopolymccann Da9zw8_AaNd |
| Playwright CLI | opens a browser, screenshots, catches errors | Da9zw8_AaNd, nick_saraev DbyJNRdPyCj |
| Figma connection | design UI from Claude, then code | Dbd6PFPq3-c |
| Google Stitch | prompt to full frontend design, can import into AI Studio | nick_saraev DXWCgXvj2AR, nicksadler.io DcwzsNnIKvc |
| Open Design | open-source Claude Design alternative, animated sites | nick_saraev DYTw6VYPd9P, DaxsZr1yASQ |
| Refero (MCP) | use parts of real sites as reference | gannon.meyer DX9mxYbAXug |
| Layers, Coolors, SVGator, Manus | design gallery, palettes, logo animation, backend | kiksvibecodes Dc2NQmty1Yx |
| Watermelon UI, Aura (list) | UI libraries to upgrade a vibe-coded site. A commenter called the Watermelon UI landing page itself vibe-coded | buildwaleesh Db0LGhVz8JK |
| Brand guideline skill (Anthropic) | applies consistent brand colours and typography | DW2BRwOzHyo (video) |
| Design auditor | audits a finished site against 17 design rules, typography to WCAG | DW2BRwOzHyo (video) |
| Web app testing skill | clicks buttons, submits forms, screenshots to catch bugs | DW2BRwOzHyo (video) |
| Impeccable (major update) | gives three design variants, edit text and elements with sliders | Dbj7-pXMaIb (video) |
| Emil Kowalski skills | seven skills for animations | Dbj7-pXMaIb (video) |
| Taste V2 | places images well on a page | Dbj7-pXMaIb (video) |
| Refero Styles (styles.refero.design) | design.md files and examples from real sites, 2,000+ design files with colours, fonts, spacing | DbXFd74s91x, Dc2KI0HEqqk (video) |
| motionsites.ai | copy the code of animated landing pages | DbXFd74s91x (video) |
| Pinterest | find the exact component style to copy, eg glassmorphism | DbXFd74s91x (video) |
| Design.md as a skill | download a design.md for a style you like, load it as a reusable skill in Claude/ChatGPT so it knows type, spacing, colours | DcBcyjIOxUy (video) |
| Unlumen UI, Magic UI, Smooth UI, Retro UI | UI libraries: animations and shaders / animated components and templates / text effects and hero blocks / Figma kit with 300+ components | DbI2iubT1yA (video) |
| componentry.dev, motion.dev, Cult UI, Shader Gradient, Manus | animated React components / animation library / landing page pieces / animated 3D gradient backgrounds you copy out as code / agentic site builder (reels are ads for Manus) | DdTaFrPxL7S, Dc2KI0HEqqk (on-screen text) |

Safe default for Rhys: Frontend Design (Anthropic official) plus Playwright. Add one more only if the first pass looks generic. Stacking five costs Claude usage and she is low on credits. Her reels also say "stack two".

## 5. Visual rules checklist (general practice, use as the review list)

Layout: one idea per section; consistent 8px spacing scale; max line length 60 to 75 characters; align to a grid; section padding at least 64px desktop.
Type: two families max; body 16 to 18px; clear size jumps between H1, H2, body; tight tracking on large headings.
Colour: one primary, one accent, neutrals; contrast checked; dark text on light is safer than grey on grey.
Imagery: consistent crop, no stretched or low-res photos in the hero, lazy-load below the fold.
Components: buttons share one radius and height; cards share one shadow or border style.
Motion: subtle, consistent, never blocks reading.
Trust: real names, real proof, clear next step. Placeholder copy should be visibly marked.

## 6. UX rules saved from reels (agenticmatt DcmoHfNJDWO, rules 6 to 15 of a longer list; rules 1 to 5 were not captured)

6. X closes a modal or flow; left arrow goes back one screen.
7. Never show a blank screen while loading: skeleton, spinner or progress bar.
8. Keep scroll position when users leave a feed and return.
9. Tapping the selected bottom tab returns to top of that tab.
10. Load the next batch before users hit the bottom.
11. Likes, follows, saves update instantly, then sync.
12. Autosave unfinished input.
13. Ask for permissions only when the feature is used.
14. Quick actions open in a bottom sheet; swipe down dismisses.
15. Notifications and shared links open the exact content, not home.
Most are app rules. For a marketing site, 7, 12, 13 and 15 apply most.

## 7. Pre-launch checks (yatesvids Db15Zn0hSmH said "20 things to tell Claude to add before launching" but the list is in the video, not the caption)

My own baseline until the list is captured: favicon and social share image, page titles and meta descriptions, working contact form with a visible confirmation, 404 page, sitemap and robots, analytics, mobile test on a real phone, speed check, privacy page, no placeholder text, noindex removed on launch day. A commenter on that reel also said "favicon".

## 8. Reels used

Captions and comments read for (30): DbI2iubT1yA, Dc2KI0HEqqk, DcBcyjIOxUy, Dc2NQmty1Yx, Ddbqxo_Ec-L, Dbd6PFPq3-c, DcwzsNnIKvc, Db0LGhVz8JK, DcmoHfNJDWO, Db15Zn0hSmH, Dbj7-pXMaIb, DbaR9TYR-W1, DbcgeuMyrlA, DbXFd74s91x, DbVs9yZM0ys, DX9mxYbAXug, DYTw6VYPd9P, DaxsZr1yASQ, Da9zw8_AaNd, DX-ABm3snaU, DaYet-0T-TV, DW2BRwOzHyo, DWucfVJzQgU, DXWCgXvj2AR, DTJDRaPj5aV, DYVcebWB9Vk, Da5aWOvJR2a, DdTaFrPxL7S, DX-mKvWvtdN, DbyJNRdPyCj.
Link format: https://www.instagram.com/p/<id>/
Caption is only "comment X for the list", video now read for most, see section 9 (content is in the video or a DM, not captured): DcBcyjIOxUy (style guide), DW2BRwOzHyo (top 5 Claude website skills), Dbj7-pXMaIb, DbXFd74s91x, DaYet-0T-TV (Fable 5 / Higgsfield), DX-mKvWvtdN (STUDIO skill), DdTaFrPxL7S (web tools list), Dc2KI0HEqqk, DbI2iubT1yA (top 4 UI libraries), Ddbqxo_Ec-L (25 websites).
Off topic or not used: DdPla7NBD-Y, DTJDRaPj5aV (general Google tools).
Not loaded: the reels I opened all loaded, but the Saved grid itself only listed 1,218 of her saves via scrolling, and I filtered by caption text. A design reel with a blank or non-English caption would be missed.


## 9. Gap fill, 4 Oct 2026: video frames and audio read for the "comment X" reels

Method: opened each reel, pulled the video file, machine-transcribed the audio and read burned-in on-screen text from sampled frames. Transcription can mishear names. Everything below is the creator's claim, not verified.

- DW2BRwOzHyo "top 5 Claude website skills": 1 Brand guideline skill (Anthropic), 2 UI UX Pro Max (says 240 styles, 127 font pairings, 99 UX guidelines), 3 Design auditor (17 rules incl. WCAG), 4 Front-end design skill (official Anthropic, install first), 5 Web app testing skill. Matches the safe default: Frontend Design plus a test skill.
- Dbj7-pXMaIb: Impeccable, Emil Kowalski (7 animation skills, ex Linear and Vercel per creator), Taste V2. Says results were built in one shot in about 10 minutes.
- DbXFd74s91x: inspiration beats prompting. Three sources: Refero Styles (design.md files), motionsites.ai (animation, copyable code), Pinterest (component styles). Two more links were bonus and not stated aloud.
- DcBcyjIOxUy "style" guide: pick a style on a gallery, download its design.md, load it as a reusable skill so the AI already knows typography, spacing, colours and components. The audio names "Refactoring UI" as the place to find it, which may be a mishearing. The creator says ChatGPT's site builder gave the best results for them. The full "style" guide itself is still gated behind a comment.
- DbI2iubT1yA top 4 UI libraries (was "content not captured"): Unlumen UI, Magic UI, Smooth UI, Retro UI. See table.
- DdTaFrPxL7S and Dc2KI0HEqqk (no speech, text on screen only): componentry.dev, manus.im, motion.dev, Cult UI, Shader Gradient, Refero Styles. Both are partly Manus ads (#ad). Full list is behind a "WEB" or "CODE" comment and not captured.
- DaYet-0T-TV "Fable 5 / Higgsfield": the creator says to add a custom connector in the Claude desktop app (connectors, manage connectors, add custom connector) and paste a prompt to build animated sites from Higgsfield. The connector name, URL and prompt were not stated aloud. Pitches selling sites for $500 to $1,000 and a free Higgsfield trial of 100 credits. Treat as promotion.
- DX-mKvWvtdN "STUDIO" skill: not web design. It is a "packshot" Claude skill that turns product photos into studio-style shots using Nano Banana 2. Moved out of the design list.
- Ddbqxo_Ec-L: caption is "200 startup ideas", the video is an image carousel with no video file. Not design. Moved out of the design list.
- Earlier TokScript export (June 2026) holds 5 transcripts, none about web design: second-brain with Claude and Obsidian (raycfu), a Claude skills list (samdespomarketing, DW96NIHSkik), a "Content" workflow (ibraviz.ai), a productivity tools reel (vanessasantosleon).

Still not captured: the lists behind "comment X" gates (DcBcyjIOxUy style guide, DbXFd74s91x bonus links, DdTaFrPxL7S and Dc2KI0HEqqk lists, DaYet-0T-TV prompt, 20 pre-launch things in Db15Zn0hSmH, UX rules 1 to 5 in DcmoHfNJDWO). Those come by DM only.
