---
version: 1
slug: "frontend-src-pages-homepage-tsx"
primary_target: "frontend/src/pages/HomePage.tsx"
related_targets: ["frontend/src/pages/FindPage.tsx","frontend/src/pages/ReportPage.tsx","frontend/src/pages/MapPage.tsx"]
---

Scope: whole web app (home, guided finder, report, map, compare); home is Persuade, the rest Operate.
Audience: citizens choosing where to live; mobile and desktop equally. Constraints: nav items, data, API, tests' intent, WCAG 2.2 AA, 320 px.

## Direction contract

THESIS: The report is an instrument panel for a place: each environmental measurement has its own drawn gauge that settles on the real value. Everything else is paper and ink so the readings are what you see. Replaces the "Putokaz" trail world, which the user found too generic.

OWN-WORLD: Paper #F6F5F1, ink #15171A, actions in ink, links blue. One colour per measurement and only for it: flood cobalt #1F55D0, air violet #6A46D1, green #18804A, roads amber #A85A00, fire #C4381A, sun #845800, walking teal, transit magenta. Status colours separate, always with icon and word. Instrument Serif (display, readouts) and Instrument Sans (text). Panels 14px corners with a 4px colour strip on top.

STORY: Home: big serif question, one address field, the finder as second way in, the settlement mosaic, then the six measurements in their colours. Report: address, score readout, summary, six key readings that jump to their instruments, then the instruments.

FIRST VIEWPORT: Desktop home: question left, mosaic right bleeding off the edge. Report: address and score, summary, readings strip.

FORM: Water gauge, rulers with WHO and EU marks and a needle, 300 m dot circle, road ruler, radar, sun arc. Drawings are aria-hidden; numbers and sentences carry the meaning.

FINISH: unreviewed and undocumented is unfinished; this build ends with the finish review, the verdict, DESIGN.md, and every shipping raster carrying its provenance
