---
version: 1
slug: "frontend-src-pages-homepage-tsx"
primary_target: "frontend/src/pages/HomePage.tsx"
related_targets: ["frontend/src/pages/FindPage.tsx","frontend/src/pages/ReportPage.tsx","frontend/src/pages/MapPage.tsx"]
---

Scope: whole web app (home, guided finder, report, map, compare); home is Persuade, the rest Operate.
Audience: citizens choosing where to live; mobile and desktop equally. Constraints: nav items, data, API, tests' intent, WCAG 2.2 AA, 320 px.

## Direction contract

THESIS: The app is a trail system for Croatia: you stand at a trailhead, a signpost gives two directions (check an address, find a place for me), and every result is a place board. Refuses the split hero with a search card and a row of equal icon cards.

OWN-WORLD: Meadow-tinted ground #EEF3EA, forest ink #13261B, forest green #1D6E3A for actions, links and the trail line (the user asked for greener and more colour after the first build); one nature colour per measurement on instruments, home measurement cards and key facts; brown tourist-sign #5B3A1E with white type only for place identity (signpost planks, place board band, you-are-here). Status colours separate, always with words. Bricolage Grotesque display, Figtree text (Atkinson was tried; its slashed zero reads as technical). Small 6px board corners, rules and stations instead of shadowed cards.

STORY: In five seconds: what this is (big question), where to type (the signpost plank), the alternative (second plank). Then three stations explain how it works. The report opens as a place board with a template summary and status tags, environment first.

FIRST VIEWPORT: Desktop: h1 "Kako je živjeti ovdje?" huge top-left, one-sentence lead, a signpost post with two brown planks (address input plank, "Pronađi mjesto za mene" plank). The settlement mosaic of Croatia (6,759 polygons, jade scale by Skor za život) large to the right and bleeding, with a text caption and link to /karta. Mobile: question, signpost, then mosaic.

FORM: Candidate 6 of 7 (national-park and trail wayfinding). seed:1418b3f28c73e0f6. Raises: palette roles one job each (teletext), guide line naming where you are in the report (lexicon), back retraces the exact path through the finder (HyperCard).

FINISH: unreviewed and undocumented is unfinished; this build ends with the finish review, the verdict, DESIGN.md, and every shipping raster carrying its provenance
