# WMGP29 — World Masters Games Perth 2029 website

A fully designed, deeply interactive website for the 2029 World Masters Games in Perth
(12–23 October 2029), built from the WMGP29 Business Plan v2 and Marketing, Communications
& Participant Recruitment Plan v2.1, plus research into masters-games sites (Taipei 2025,
Kansai 2027, Lahti 2028 winter games, Australian & Pan Pacific Masters Games) and current
web design best practice.

## Run it

```bash
cd wmgp29-website
python3 build.py            # generates ./site (80 pages)
python3 -m http.server -d site 8000
# → http://localhost:8000
```

No dependencies — Python 3 standard library only. Output is a fully static site,
deployable to GitHub Pages or any static host.

## What's in it

**Content (GEO/SEO-first, crawlable HTML):**
- Homepage with countdown, animated stats, audience cards, flag wall, FAQ
- 55 individual sport pages generated from `data/sports.json` (venue, field size,
  interest bars, SportsEvent JSON-LD, sport-specific FAQ)
- Venues & clusters with an interactive SVG map of Perth
- Registration & pricing (indicative tiers per MarComms Plan §15), refund policy summary
- Plan Your Trip destination section, Kansai 2027 → Perth conversion page,
  clubs & teams, volunteers & ambassadors, partners, news engine,
  accessibility / privacy / contact

**Interactive layer (vanilla JS + localStorage, no frameworks):**
- *Register Your Interest* — pre-registration with DOB → live age-group-at-Games calculation
- *Registration planner* — 5-step frictionless wizard: sports (multi-sport 50% discount),
  age/country ($25 international incentive), tier comparison, supporters & club codes (10%),
  travel add-ons, live price total and review
- *Experience Marketplace* — filterable catalogue across 6 categories with "Add to my trip" cart
- *My Games* — day-by-day personal itinerary across the 12 Games days (printable)
- *Connect* — find-your-people community filters by sport/country/age + connection requests
- *Stories* — ambassador wall with expandable athlete profiles
- *Find-your-sport quiz*, fun countdown ("training Saturdays"), confetti micro-interactions

**Standards honoured (from the plans):**
- WCAG 2.2 AA: skip link, landmarks, labels, 4.5:1+ contrast tokens, 48px targets,
  keyboard-complete, `prefers-reduced-motion`, single h1 per page
- GEO (MarComms §7.7): Organization/SportsEvent/FAQPage/NewsArticle JSON-LD on every page,
  FAQ blocks on homepage/sports/venues/pre-registration, zero-JS core content,
  specific citable facts in copy, sitemap.xml + robots.txt
- Brand rules: Sport → Place → Event message order; warm, specific, distinctly-Perth tone;
  Whadjuk Noongar acknowledgment; TWA/Walking on a Dream partner placeholders

## Integration hooks

All interactive features are working demos persisting to `localStorage`. Marked `TODO:API`
in `assets/js/features.js`:
- Pre-registration → CRM endpoint (Business Plan §12.2; CRM live Sep 2026)
- Wizard handoff → WMS registration platform (registration opens Oct 2028)
- Marketplace cart → Official Travel Partner booking system
- Connection requests → participant platform social matching

## Imagery

Photography is hotlinked from Unsplash (the pattern already used in this repo).
Every image has a styled gradient + emoji fallback that activates automatically if a
photo fails to load, so the design never breaks. Swap points for official Games
photography: `img` fields in `data/*.json`.

## Structure

```
wmgp29-website/
  build.py            # generator + link checker (templates live here)
  data/               # sports, venues, news, marketplace, athletes (single source of truth)
  assets/css/style.css  # design tokens & components ("Indian Ocean" palette)
  assets/js/app.js      # shared: countdown, age calc, counters, image fallback, confetti
  assets/js/features.js # quiz, wizard, marketplace, itinerary, connect, ambassador wall
  site/               # generated output (committed for easy preview/deploy)
```
