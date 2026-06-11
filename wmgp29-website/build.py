#!/usr/bin/env python3
"""WMGP29 website generator.

Generates the full static site into ./site from ./data JSON + templates below.
Run:  python3 build.py        (then serve ./site with any static server)

Design contract:
- Core content is plain crawlable HTML (GEO requirement, MarComms Plan s7.7).
- JSON-LD on every page: Organization + Event sitewide, SportsEvent per sport,
  FAQPage wherever an FAQ block exists, NewsArticle on news pages.
- WCAG 2.2 AA: landmarks, skip link, labels, contrast-safe tokens (see CSS).
- Interactivity is layered on via assets/js (progressive enhancement).
"""
import json
import html
import shutil
from pathlib import Path

ROOT = Path(__file__).parent
OUT = ROOT / "site"
DATA = ROOT / "data"

BASE_URL = "https://wmgp29.com"
GAMES_DATES = "12–23 October 2029"

sports = json.loads((DATA / "sports.json").read_text())
venues = json.loads((DATA / "venues.json").read_text())
news = json.loads((DATA / "news.json").read_text())
marketplace = json.loads((DATA / "marketplace.json").read_text())
athletes = json.loads((DATA / "athletes.json").read_text())

COUNTRIES = ["Australia", "New Zealand", "United Kingdom", "Ireland", "Japan", "Singapore",
             "Malaysia", "Indonesia", "Germany", "Switzerland", "France", "Italy", "Spain",
             "Netherlands", "USA", "Canada", "China", "Hong Kong", "India", "South Africa",
             "Brazil", "South Korea", "Philippines", "Fiji", "Samoa", "Other"]


def img_url(photo_id: str, w: int = 900) -> str:
    return f"https://images.unsplash.com/{photo_id}?auto=format&fit=crop&w={w}&q=70"


def e(s) -> str:
    return html.escape(str(s), quote=True)


def media(photo_id, alt, emoji="🏅", badge=None, w=900):
    """Image block with styled emoji fallback if the photo can't load."""
    b = f'<span class="badge">{e(badge)}</span>' if badge else ""
    return (f'<div class="media has-img">{b}<span class="emoji-fallback" aria-hidden="true">{emoji}</span>'
            f'<img loading="lazy" src="{img_url(photo_id, w)}" alt="{e(alt)}"></div>')


def faq_block(items, heading="Good to know"):
    """FAQ accordion + FAQPage JSON-LD (GEO requirement)."""
    det = "".join(
        f'<details><summary>{e(q)}</summary><div class="answer"><p>{a}</p></div></details>'
        for q, a in items)
    ld = json.dumps({
        "@context": "https://schema.org", "@type": "FAQPage",
        "mainEntity": [{"@type": "Question", "name": q,
                        "acceptedAnswer": {"@type": "Answer", "text": a}} for q, a in items]
    })
    return (f'<section class="section-tight"><div class="container"><h2>{e(heading)}</h2>'
            f'<div class="faq">{det}</div></div></section>'
            f'<script type="application/ld+json">{ld}</script>')


ORG_EVENT_LD = json.dumps([
    {"@context": "https://schema.org", "@type": "SportsOrganization",
     "name": "World Masters Games Perth 2029", "alternateName": "WMGP29",
     "url": BASE_URL,
     "description": "Organising company for the 2029 World Masters Games in Perth, Western Australia — the world's largest international multi-sport participation event."},
    {"@context": "https://schema.org", "@type": "SportsEvent",
     "name": "World Masters Games Perth 2029",
     "startDate": "2029-10-12", "endDate": "2029-10-23",
     "eventAttendanceMode": "https://schema.org/OfflineEventAttendanceMode",
     "eventStatus": "https://schema.org/EventScheduled",
     "location": {"@type": "City", "name": "Perth", "address": {"@type": "PostalAddress",
                  "addressLocality": "Perth", "addressRegion": "WA", "addressCountry": "AU"}},
     "organizer": {"@type": "Organization", "name": "World Masters Games Perth 2029 Ltd"},
     "description": "World Masters Games Perth 2029 is a 12-day multi-sport participation event held 12–23 October 2029, targeting 30,000 registered participants from more than 100 nations across 55+ sports. Open to everyone who meets the minimum age for their sport (most sports 30+, some 25+). No qualification required.",
     "url": BASE_URL}
])

NAV = [
    ("sports/index.html", "Sports"),
    ("venues.html", "Venues"),
    ("destination.html", "Plan Your Trip"),
    ("marketplace.html", "Marketplace"),
    ("stories.html", "Stories"),
    ("connect.html", "Connect"),
    ("news/index.html", "News"),
]


def layout(*, title, desc, body, depth=0, page="", active="", extra_ld="", og_img=None):
    p = "../" * depth
    current = ' aria-current="page"'
    nav_items = "".join(
        f'<li><a href="{p}{href}"{current if href == active else ""}>{label}</a></li>'
        for href, label in NAV)
    og = og_img or img_url("photo-1573935448851-4b07c29ee181", 1200)
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{e(title)} | World Masters Games Perth 2029</title>
<meta name="description" content="{e(desc)}">
<meta property="og:title" content="{e(title)} | WMG Perth 2029">
<meta property="og:description" content="{e(desc)}">
<meta property="og:image" content="{og}">
<meta property="og:type" content="website">
<link rel="icon" href="data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'><text y='.9em' font-size='90'>🏅</text></svg>">
<link rel="stylesheet" href="{p}assets/css/style.css">
<script type="application/ld+json">{ORG_EVENT_LD}</script>
{extra_ld}
</head>
<body data-page="{page}">
<a class="skip-link" href="#main">Skip to main content</a>
<div class="ticker">🌏 Pre-registration is open — free, no commitment, first access to Early Bird pricing</div>
<header class="site-header">
  <div class="nav-bar">
    <a class="logo" href="{p}index.html"><span class="roundel" aria-hidden="true">🏅</span>
      <span>PERTH 2029<small>World Masters Games</small></span></a>
    <span class="profile-chip" aria-live="polite"></span>
    <button class="nav-toggle" aria-expanded="false" aria-controls="main-nav" aria-label="Menu">☰</button>
    <nav class="main-nav" id="main-nav" aria-label="Main">
      <ul>
        {nav_items}
        <li><a class="nav-cta" href="{p}register-interest.html">Register interest</a></li>
      </ul>
    </nav>
  </div>
</header>
<main id="main">
{body}
</main>
<a class="cart-fab" href="{p}my-games.html">🧳 My trip <span class="count">0</span></a>
<footer class="site-footer">
  <div class="container">
    <div class="footer-grid">
      <div>
        <h3>Perth 2029</h3>
        <ul>
          <li><a href="{p}about.html">About the Games</a></li>
          <li><a href="{p}registration.html">Registration &amp; pricing</a></li>
          <li><a href="{p}kansai.html">Kansai 2027 → Perth</a></li>
          <li><a href="{p}news/index.html">News</a></li>
        </ul>
      </div>
      <div>
        <h3>Take part</h3>
        <ul>
          <li><a href="{p}register-interest.html">Register your interest</a></li>
          <li><a href="{p}register.html">Try the registration planner</a></li>
          <li><a href="{p}clubs.html">Clubs &amp; teams</a></li>
          <li><a href="{p}volunteer.html">Volunteer &amp; ambassadors</a></li>
          <li><a href="{p}partners.html">Partner with us</a></li>
        </ul>
      </div>
      <div>
        <h3>Plan</h3>
        <ul>
          <li><a href="{p}sports/index.html">All sports A–Z</a></li>
          <li><a href="{p}venues.html">Venues &amp; clusters</a></li>
          <li><a href="{p}destination.html">Plan your trip</a></li>
          <li><a href="{p}marketplace.html">Experience Marketplace</a></li>
          <li><a href="{p}my-games.html">My Games itinerary</a></li>
        </ul>
      </div>
      <div>
        <h3>The fine print</h3>
        <ul>
          <li><a href="{p}accessibility.html">Accessibility</a></li>
          <li><a href="{p}privacy.html">Privacy &amp; data</a></li>
          <li><a href="{p}contact.html">Contact us</a></li>
        </ul>
        <div class="lang-select" aria-label="Language">
          <strong>EN</strong><span>日本語</span><span>Deutsch</span><span>Français</span><span>中文</span><span>Bahasa</span>
          <span class="small">— coming soon</span>
        </div>
      </div>
    </div>
    <div class="partner-strip" aria-label="Partners">
      <span>Australian Government — Office for Sport</span>
      <span>Tourism Western Australia · Walking on a Dream</span>
      <span>World Masters Sport</span>
      <span>Official Travel Partner — to be announced</span>
    </div>
    <div class="footer-legal">
      <p>World Masters Games Perth 2029 Ltd acknowledges the Whadjuk people of the Noongar nation, the traditional custodians of the land on which the Games will be held, and pays respect to Elders past and present.</p>
      <p>© 2026 World Masters Games Perth 2029 Ltd · #WMGPerth2029 · #WAtheDreamState · Demonstration site — sports program, venues and pricing are proposed and subject to confirmation.</p>
    </div>
  </div>
</footer>
<script src="{p}assets/js/data.js"></script>
<script src="{p}assets/js/app.js"></script>
<script src="{p}assets/js/features.js"></script>
</body>
</html>"""


def hero(*, kicker, title, sub, ctas="", photo="photo-1502680390469-be75c86b636f",
         alt="", home=False, countdown=False):
    cd = ('<div class="countdown" data-countdown aria-label="Countdown to the Opening Ceremony"></div>'
          '<p class="countdown-fun"><button type="button" data-countdown-fun>Show it in training Saturdays →</button></p>') if countdown else ""
    return f"""<section class="hero {'hero-home' if home else 'hero-page'}">
  <div class="hero-media" aria-hidden="true"><img src="{img_url(photo, 1600)}" alt=""></div>
  <div class="hero-inner">
    <span class="kicker">{kicker}</span>
    <h1>{title}</h1>
    <p class="sub">{sub}</p>
    {cd}
    <div class="hero-ctas">{ctas}</div>
  </div>
</section>"""


def write(path: str, content: str):
    f = OUT / path
    f.parent.mkdir(parents=True, exist_ok=True)
    f.write_text(content)


def sport_card(s, depth=0):
    p = "../" * depth
    return f"""<div class="card" data-sport-card data-cat="{e(s['category'])}" data-name="{e(s['name'].lower())}">
  {media(s['img'], s['imgAlt'], s['emoji'], badge=s['category'])}
  <div class="body">
    <h3><a class="card-cover" href="{p}sports/{s['id']}.html">{s['emoji']} {e(s['name'])}</a></h3>
    <p class="meta">📍 {e(s['venue'])} · 👥 {e(s['athletes'])} athletes expected</p>
    <div class="spacer"></div>
    <div class="fill-bar" role="img" aria-label="Interest level {s['fill']} percent"><span style="width:{s['fill']}%"></span></div>
    <p class="fill-note">{s['fill']}% of expected field already interested</p>
  </div>
  <a class="card-link" href="{p}sports/{s['id']}.html" aria-hidden="true" tabindex="-1"></a>
</div>"""


# ----------------------------------------------------------------- homepage
def build_home():
    featured = ["swimming", "track-and-field", "football", "cycling-road", "badminton",
                "dragon-boat", "lawn-bowls", "triathlon"]
    feat_cards = "".join(sport_card(s) for s in sports if s["id"] in featured)
    flags = "🇦🇺 🇳🇿 🇯🇵 🇬🇧 🇮🇪 🇸🇬 🇲🇾 🇮🇩 🇩🇪 🇨🇭 🇫🇷 🇮🇹 🇪🇸 🇳🇱 🇺🇸 🇨🇦 🇨🇳 🇭🇰 🇮🇳 🇿🇦 🇧🇷 🇰🇷 🇵🇭 🇫🇯 🇼🇸 🇹🇴 🇰🇪 🇳🇬 🇵🇰 🇱🇰 🇻🇳 🇹🇭 🇦🇷 🇲🇽 🇸🇪 🇳🇴 🇫🇮 🇩🇰 🇵🇱 🇨🇿 🇦🇹 🇧🇪 🇵🇹 🇬🇷 🇹🇷 🇦🇪 🇨🇱 🇨🇴 🇯🇲 🇨🇰"
    latest = "".join(f"""<div class="card">
      {media(n['img'], n['imgAlt'], '📰', badge=n['tag'])}
      <div class="body"><p class="news-date">{e(n['date'])}</p>
      <h3><a href="news/{n['id']}.html">{e(n['title'])}</a></h3>
      <p class="meta">{e(n['excerpt'])}</p></div>
      <a class="card-link" href="news/{n['id']}.html" aria-hidden="true" tabindex="-1"></a></div>""" for n in news[:3])

    body = hero(
        kicker=f"🇦🇺 Perth, Western Australia · {GAMES_DATES}",
        title="Your time.<br>Your Games.<br>Perth 2029.",
        sub="The world's biggest multi-sport event for everyday athletes 25/30+ — 30,000 competitors, "
            "100+ nations, 55+ sports, 12 days in the world's sunniest capital. No qualifying. Just turn up and play.",
        ctas='<a class="btn btn-primary btn-big" href="register-interest.html">Register your interest — free</a>'
             '<a class="btn btn-ghost btn-big" href="#quiz-section">Find your sport 🎯</a>',
        photo="photo-1502680390469-be75c86b636f",
        home=True, countdown=True) + f"""

<div class="stat-band"><div class="container stat-grid">
  <div class="stat"><span class="big" data-count-to="30000">0</span><span class="lbl">athletes expected</span></div>
  <div class="stat"><span class="big" data-count-to="100" data-count-suffix="+">0</span><span class="lbl">nations</span></div>
  <div class="stat"><span class="big" data-count-to="55" data-count-suffix="+">0</span><span class="lbl">sports</span></div>
  <div class="stat"><span class="big" data-count-to="12">0</span><span class="lbl">days of play</span></div>
  <div class="stat"><span class="big" data-interest-counter data-count-to="20000">0</span><span class="lbl">already interested</span></div>
</div></div>

<section class="section"><div class="container">
  <h2 class="center">However you play, you're in 🙌</h2>
  <div class="grid grid-4" style="margin-top:1.6rem">
    <a class="audience-card" href="register-interest.html"><img loading="lazy" src="{img_url('photo-1461896836934-ffe607ba8211', 600)}" alt="Sprinter on the track">
      <div class="ac-body"><h3>I'm competing 🏅</h3><p>Pick your sport, find your age group, chase that medal.</p></div></a>
    <a class="audience-card" href="destination.html"><img loading="lazy" src="{img_url('photo-1591375372156-542495912da9', 600)}" alt="Quokka on Rottnest Island">
      <div class="ac-body"><h3>I'm the support crew 💛</h3><p>Beaches, wine country, quokkas — best supporter gig in sport.</p></div></a>
    <a class="audience-card" href="volunteer.html"><img loading="lazy" src="{img_url('photo-1559027615-cd4628902d4a', 600)}" alt="Smiling volunteers">
      <div class="ac-body"><h3>I'm volunteering 🙋</h3><p>5,000+ roles. Front-row seat to the best games on earth.</p></div></a>
    <a class="audience-card" href="clubs.html"><img loading="lazy" src="{img_url('photo-1574629810360-7efbbe195018', 600)}" alt="Team huddle">
      <div class="ac-body"><h3>I'm bringing my club 👯</h3><p>Groups of 5+ save 10% — and unlock club rewards.</p></div></a>
  </div>
</div></section>

<section class="section" id="quiz-section" style="background:var(--sand-100)"><div class="container">
  <div class="quiz-card" id="quiz">
    <h3>Not sure which sport? Let's find out in 30 seconds 🎯</h3>
    <div class="quiz-live">
      <p class="quiz-progress"></p>
      <p class="quiz-q"></p>
      <div class="quiz-opts"></div>
    </div>
    <div class="quiz-result" aria-live="polite"></div>
    <noscript><p>Enable JavaScript for the quiz — or browse all sports <a style="color:#fff" href="sports/index.html">here</a>.</p></noscript>
  </div>
</div></section>

<section class="section"><div class="container">
  <h2>Pick your battlefield ⚔️</h2>
  <p class="muted">Eight of the 55+ proposed sports. Every one in age groups from 25/30 to 85+.</p>
  <div class="grid grid-4">{feat_cards}</div>
  <p class="center" style="margin-top:1.8rem"><a class="btn btn-secondary btn-big" href="sports/index.html">Browse all sports A–Z →</a></p>
</div></section>

<section class="section" style="background:var(--ocean-100)"><div class="container">
  <div class="grid grid-2" style="align-items:center">
    <div>
      <h2>October in Perth = chef's kiss 🤌</h2>
      <div class="weather-dial"><span class="temp">21°</span>
        <span class="desc"><strong>Average October day</strong>8+ hours of sunshine · ocean at its clearest · wildflower season</span></div>
      <p style="margin-top:1rem">Compete in the morning, Indian Ocean swim by lunch, Margaret River on your rest day. <a href="destination.html">Plan the whole adventure →</a></p>
    </div>
    <div class="card">{media('photo-1591375372156-542495912da9', 'Quokka smiling on Rottnest Island', '🦘', badge='Rottnest Island')}
      <div class="body"><h3>Meet the locals</h3><p class="meta">The quokka selfie is basically a mandatory event.</p></div></div>
  </div>
</div></section>

<section class="section"><div class="container center">
  <h2>The world is already in 🌏</h2>
  <p class="muted">Athletes from 50+ countries have registered interest so far</p>
  <p class="flag-wall" aria-label="Flags of countries with registered interest">{flags}</p>
</div></section>

<section class="section"><div class="container">
  <h2>Fresh from the Games 📰</h2>
  <div class="grid grid-3">{latest}</div>
  <p class="center" style="margin-top:1.6rem"><a class="btn btn-ghost" href="news/index.html">All news →</a></p>
</div></section>

<section class="section-tight"><div class="container">
  <div class="band"><div class="band-media" aria-hidden="true"><img loading="lazy" src="{img_url('photo-1530549387789-4c1017266635', 1400)}" alt=""></div>
    <div><h2>Be first in line 🏁</h2>
    <p>Free pre-registration takes under a minute. First dibs on Early Bird pricing, your sport's updates, and Founding Participant status.</p></div>
    <a class="btn btn-primary btn-big" href="register-interest.html">Count me in</a></div>
</div></section>
""" + faq_block([
        ("Who can compete at the World Masters Games?",
         "Everyone who meets the minimum age for their sport — most sports from 30, some (like swimming and diving) from 25. There is no qualifying standard: World Masters Games Perth 2029 is open to all, from former Olympians to first-time competitors."),
        ("When and where is Perth 2029?",
         "12–23 October 2029 in Perth, Western Australia — 12 days, 55+ proposed sports, around 40 venues across nine clusters, opening at Optus Stadium."),
        ("How many people will take part?",
         "Perth 2029 is targeting 30,000 registered participants from more than 100 nations — around 15,000 international athletes, 8,000 from interstate Australia and 7,000 from Western Australia — plus tens of thousands of travelling supporters."),
        ("When does registration open and what will it cost?",
         "Paid registration opens in October 2028. Indicative pricing (subject to final approval): Early Bird around A$275, Standard A$325, Late A$425, plus sport entry fees. Pre-register now — it's free — for first access to Early Bird pricing."),
        ("Do I compete against people my own age?",
         "Yes. Every sport runs in age groups, typically five-year bands (30–34, 35–39 … 85+), so you compete against your peers."),
    ], heading="Quick answers")

    write("index.html", layout(
        title="12–23 October 2029 · 30,000 athletes · 100+ nations",
        desc="World Masters Games Perth 2029: 30,000 athletes, 100+ nations, 55+ sports, 12 days, 12–23 October 2029. Open to all 25/30+, no qualifying. Free pre-registration open now.",
        body=body, page="home"))


# ------------------------------------------------------- register interest
def build_interest():
    sport_checks = "".join(
        f'<label><input type="checkbox" name="sports" value="{s["id"]}">{s["emoji"]} {e(s["name"])}</label>'
        for s in sorted(sports, key=lambda x: x["name"]))
    countries = "".join(f'<option value="{e(c)}">{e(c)}</option>' for c in COUNTRIES)
    body = hero(
        kicker="Free · no commitment · under a minute",
        title="Put your hand up 🙋",
        sub="Pre-register for Perth 2029 and get first access to Early Bird pricing, your sport's news, "
            "travel package previews and Founding Participant status.",
        photo="photo-1571008887538-b36bb32f4571", countdown=False) + f"""
<section class="section"><div class="container">
  <div id="interest-form-wrap">
  <form class="form-card" id="interest-form" novalidate>
    <div class="field"><label for="ri-name">First name</label>
      <input type="text" id="ri-name" name="firstName" autocomplete="given-name" placeholder="e.g. Sam"></div>
    <div class="field"><label for="ri-email">Email <span aria-hidden="true">*</span></label>
      <input type="email" id="ri-email" name="email" autocomplete="email" required placeholder="you@example.com"></div>
    <div class="field"><label for="ri-dob">Date of birth <span aria-hidden="true">*</span></label>
      <p class="hint">We use this to work out your age group in October 2029 — competition is in 5-year bands.</p>
      <input type="date" id="ri-dob" name="dob" autocomplete="bday" required data-dob-field="#age-reveal" min="1925-01-01" max="2004-10-23">
      <p class="age-reveal" id="age-reveal" aria-live="polite"></p></div>
    <div class="field"><label for="ri-country">Country</label>
      <select id="ri-country" name="country"><option value="">Choose…</option>{countries}</select></div>
    <fieldset class="field" style="border:none;padding:0;margin:0 0 1.15rem">
      <legend style="font-weight:700;font-family:var(--font-display);color:var(--ocean-900);padding:0;margin-bottom:.3rem">Sports you're eyeing 👀 <span class="muted" style="font-weight:400">(pick as many as you like)</span></legend>
      <div class="checks">{sport_checks}</div>
    </fieldset>
    <div class="field"><label for="ri-likely">How likely are you to come?</label>
      <select id="ri-likely" name="likelihood">
        <option>Book my flights already 🛫</option>
        <option selected>Very likely</option>
        <option>Curious — keep me posted</option>
      </select></div>
    <div class="field consent">
      <label style="display:flex;gap:.6rem;align-items:flex-start;font-weight:400">
        <input type="checkbox" name="consent" required style="width:1.3rem;height:1.3rem;margin-top:.2rem;accent-color:var(--coral-600)">
        <span>I'd like updates about World Masters Games Perth 2029. WMGP29 Ltd handles your details under the Australian Privacy Principles (and GDPR for EU/UK residents); you can unsubscribe or ask for deletion any time. See the <a href="privacy.html">privacy policy</a>.</span>
      </label>
    </div>
    <p class="field-error" id="interest-error" role="alert"></p>
    <button class="btn btn-primary btn-big" type="submit" style="width:100%">Register my interest 🎉</button>
    <p class="small muted center" style="margin:.8rem 0 0">Join <strong>18,000+</strong> athletes from 50+ countries already on the list</p>
  </form>
  </div>
  <div class="form-card" id="interest-done" hidden>
    <h2>You're on the list, <span id="interest-done-name">legend</span>! 🎉</h2>
    <p id="interest-done-age" style="font-weight:700;color:var(--green-700)"></p>
    <p>We'll be in touch with your sport's news first. Meanwhile…</p>
    <p><a class="btn btn-primary" href="register.html">Plan my registration →</a>
       <a class="btn btn-secondary" href="marketplace.html">Browse trip experiences</a>
       <a class="btn btn-ghost" href="connect.html">Find my people</a></p>
  </div>
</div></section>
""" + faq_block([
        ("Is pre-registration a commitment to compete?",
         "No. Pre-registration is free and creates no obligation — it simply gets you first-to-know status, priority Early Bird access when paid registration opens in October 2028, and sport-specific updates."),
        ("Why do you need my date of birth?",
         "Masters sport is organised in age groups, usually five-year bands. Your age on the first day of the Games (12 October 2029) determines your category, so we can send you the right competition information."),
        ("I'll be under 30 in 2029 — can I still take part?",
         "Some sports start at 25 (including swimming, diving, artistic swimming and open water). And everyone 18+ can volunteer — 5,000+ roles will open in 2028."),
    ], heading="Before you ask")
    write("register-interest.html", layout(
        title="Register your interest", page="interest",
        desc="Free pre-registration for World Masters Games Perth 2029. First access to Early Bird pricing, sport-specific updates and Founding Participant status. Takes under a minute.",
        body=body))


# ---------------------------------------------------------------- wizard
def build_wizard():
    sport_checks = "".join(
        f'<label><input type="checkbox" name="wiz-sport" value="{s["id"]}">{s["emoji"]} {e(s["name"])}</label>'
        for s in sorted(sports, key=lambda x: x["name"]))
    countries = "".join(f'<option value="{e(c)}">{e(c)}</option>' for c in COUNTRIES)
    extras = "".join(f"""<label><input type="checkbox" name="wiz-extra" value="{p['id']}">{p['emoji']} {e(p['name'])} — A${p['price']:,} <span class="muted">{e(p['unit'])}</span></label>"""
                     for p in marketplace if p["cat"] in ("Stay", "Day Experiences", "Extend Your Stay", "Ceremonies & Social"))
    body = hero(
        kicker="Interactive planner · everything in one place",
        title="Build your Games in 5 steps 🛠️",
        sub="Sports, age group, pricing tier, supporters and your WA adventure — one frictionless flow with a live total. "
            "Paid registration opens October 2028; your plan carries straight across.",
        photo="photo-1517649763962-0c623066013b") + f"""
<section class="section"><div class="container" id="wizard-main">
  <ol class="wizard-steps">
    <li>Sports</li><li>About you</li><li>Tier &amp; crew</li><li>Your trip</li><li>Review</li>
  </ol>

  <div class="wizard-panel active form-card" style="max-width:860px">
    <h2>1 · Pick your sport(s) 🏅</h2>
    <p class="hint">Second and additional sports are <strong>half-price</strong> on the sport entry fee.</p>
    <div class="checks">{sport_checks}</div>
    <p class="age-reveal show" id="multi-note" hidden style="margin-top:1rem">💪 Multi-sport legend! Your extra sport entries are 50% off.</p>
    <div class="wizard-nav"><span></span><button class="btn btn-primary" type="button" data-wiz-next>Next: about you →</button></div>
  </div>

  <div class="wizard-panel form-card" style="max-width:860px">
    <h2>2 · About you 🪪</h2>
    <div class="field"><label for="wiz-dob">Date of birth</label>
      <p class="hint">Sets your 5-year age group as at 12 October 2029.</p>
      <input type="date" id="wiz-dob" data-dob-field="#wiz-age-reveal" min="1925-01-01" max="2004-10-23">
      <p class="age-reveal" id="wiz-age-reveal" aria-live="polite"></p>
      <p class="field-error" id="wiz-dob-err" role="alert"></p></div>
    <div class="field"><label for="wiz-country">Country</label>
      <select id="wiz-country"><option value="">Choose…</option>{countries}</select>
      <p class="age-reveal show" id="intl-note" hidden style="margin-top:.6rem">🌏 International athlete: a $25 Early Bird incentive applies automatically.</p></div>
    <div class="wizard-nav"><button class="btn btn-ghost" type="button" data-wiz-back>← Back</button>
      <button class="btn btn-primary" type="button" data-wiz-next>Next: tier &amp; crew →</button></div>
  </div>

  <div class="wizard-panel form-card" style="max-width:860px">
    <h2>3 · Tier &amp; your crew 👯</h2>
    <div class="field"><span style="font-weight:700;font-family:var(--font-display);color:var(--ocean-900)">Registration tier</span>
      <p class="hint">Standard is A$325. Early Bird saves A$50 — and locks in guaranteed sport entry before fields fill.</p>
      <div class="checks" style="flex-direction:column;align-items:stretch">
        <label><input type="radio" name="wiz-tier" value="early" checked>🐦 <strong>Early Bird — A$275</strong>&nbsp;· guaranteed sport entry · priority pack collection · Founding Participant wall</label>
        <label><input type="radio" name="wiz-tier" value="standard">⭐ <strong>Standard — A$325</strong>&nbsp;· pre-Games venue training access · mid-priority collection</label>
        <label><input type="radio" name="wiz-tier" value="late">⏰ <strong>Late — A$425</strong>&nbsp;· everything essential, none of the perks</label>
      </div></div>
    <div class="field"><label for="wiz-supporters">Supporter passes (A$100 each)</label>
      <p class="hint">Games Village access, ceremonies, the lot — for partners, family and your loudest fans.</p>
      <input type="number" id="wiz-supporters" min="0" max="10" value="0" style="max-width:120px"></div>
    <div class="field"><label for="wiz-club">Club code (optional)</label>
      <p class="hint">Clubs of 5+ save 10% on registration. Try <strong>DEMO5</strong> to see it work.</p>
      <input type="text" id="wiz-club" placeholder="e.g. DEMO5" style="max-width:240px"></div>
    <div class="wizard-nav"><button class="btn btn-ghost" type="button" data-wiz-back>← Back</button>
      <button class="btn btn-primary" type="button" data-wiz-next>Next: your trip →</button></div>
  </div>

  <div class="wizard-panel form-card" style="max-width:860px">
    <h2>4 · Make it a trip 🧳</h2>
    <p class="hint">Add stays and experiences now or later — everything is bookable in one place. <a href="marketplace.html">Browse the full marketplace →</a></p>
    <div class="checks" style="flex-direction:column;align-items:stretch">{extras}</div>
    <div class="wizard-nav"><button class="btn btn-ghost" type="button" data-wiz-back>← Back</button>
      <button class="btn btn-primary" type="button" data-wiz-next>Review my Games →</button></div>
  </div>

  <div class="wizard-panel form-card" style="max-width:860px">
    <h2>5 · Your Games at a glance 🤩</h2>
    <div id="review-summary"></div>
    <div class="wizard-nav"><button class="btn btn-ghost" type="button" data-wiz-back>← Back</button>
      <button class="btn btn-primary btn-big" type="button" id="wiz-finish">Save my plan 🎉</button></div>
  </div>

  <div class="price-summary" aria-live="polite"><span>Your Games so far</span><span class="total" id="wiz-total">A$0</span></div>
</div>

<div class="container" id="wiz-done" hidden>
  <div class="form-card center">
    <h2>Plan saved! 🎊</h2>
    <p>Your sports, trip and pricing are stored on this device. When paid registration opens in <strong>October 2028</strong> on the World Masters Sport platform, everything carries across — pre-registrants go first.</p>
    <p><a class="btn btn-primary btn-big" href="my-games.html">See my day-by-day itinerary →</a></p>
    <p><a class="btn btn-ghost" href="connect.html">Find training buddies</a> <a class="btn btn-ghost" href="register-interest.html">Make sure I'm pre-registered</a></p>
  </div>
</div>
</section>
<noscript><div class="container"><p>The interactive planner needs JavaScript. All pricing detail is on the <a href="registration.html">registration &amp; pricing page</a>.</p></div></noscript>
"""
    write("register.html", layout(
        title="Registration planner", page="register",
        desc="Plan your World Masters Games Perth 2029 registration: pick sports, see your age group, compare pricing tiers, add supporters and build your WA trip — with a live total.",
        body=body))


# ---------------------------------------------------------------- sports
def build_sports():
    cats = ["All"] + sorted({s["category"] for s in sports})
    cat_btns = "".join(
        f'<button type="button" data-cat="{e(c)}" aria-pressed="{"true" if c == "All" else "false"}">{e(c)}</button>'
        for c in cats)
    cards = "".join(sport_card(s, depth=1) for s in sorted(sports, key=lambda x: x["name"]))
    body = hero(
        kicker="55+ proposed sports · every age group",
        title="Sports A–Z 🏟️",
        sub="From archery to windsurfing — find your sport, scope the venue, see who else is coming.",
        photo="photo-1461896836934-ffe607ba8211") + f"""
<section class="section"><div class="container">
  <div class="search-row">
    <label for="sport-search" class="small" style="align-self:center;font-weight:700">Search</label>
    <input type="text" id="sport-search" placeholder="Try 'swim', 'cycling', 'bowls'…" aria-describedby="sport-count">
    <span id="sport-count" class="small muted" style="align-self:center">{len(sports)} sports</span>
  </div>
  <div class="cat-filter" id="sport-cats">{cat_btns}</div>
  <div class="grid grid-4">{cards}</div>
  <p class="small muted" style="margin-top:1.4rem">Sports program is proposed and subject to confirmation through 2027–2028 as sport agreements are signed. Expected field sizes are planning ranges based on Sydney 2009, Auckland 2017 and Taipei 2025.</p>
</div></section>
""" + faq_block([
        ("How are age groups decided?",
         "By your age on 12 October 2029, the first day of the Games, in five-year bands from each sport's minimum age (most 30+, aquatic sports from 25)."),
        ("Can I enter more than one sport?",
         "Absolutely — multi-sporting is a masters games tradition. Your second and additional sport entry fees are 50% off, and the schedule is designed to minimise clashes."),
        ("When will the sports program be final?",
         "Sports are progressively confirmed from late 2027, with the full program locked before registration opens in October 2028. Pre-registrants get each confirmation first."),
    ])
    write("sports/index.html", layout(
        title="Sports A–Z", page="sports", active="sports/index.html", depth=1,
        desc="All 55+ proposed sports of World Masters Games Perth 2029 — venues, expected fields and age groups, from swimming and athletics to dragon boat and lawn bowls.",
        body=body))

    for s in sports:
        ld = json.dumps({
            "@context": "https://schema.org", "@type": "SportsEvent",
            "name": f"{s['name']} — World Masters Games Perth 2029",
            "startDate": "2029-10-12", "endDate": "2029-10-23",
            "location": {"@type": "Place", "name": s["venue"],
                         "address": {"@type": "PostalAddress", "addressLocality": "Perth", "addressRegion": "WA", "addressCountry": "AU"}},
            "organizer": {"@type": "Organization", "name": "World Masters Games Perth 2029 Ltd"},
            "description": f"{s['name']} at World Masters Games Perth 2029, {GAMES_DATES}, at {s['venue']}. Expected field {s['athletes']} athletes. Minimum age {s['minAge']}. Five-year age groups, no qualification required."
        })
        cluster = next((v for v in venues if v["id"] == s["cluster"]), None)
        rel = [x for x in sports if x["category"] == s["category"] and x["id"] != s["id"]][:3]
        rel_cards = "".join(sport_card(x, depth=1) for x in rel)
        body = hero(
            kicker=f"{s['category']} · minimum age {s['minAge']}",
            title=f"{s['emoji']} {e(s['name'])}",
            sub=s["blurb"],
            ctas='<a class="btn btn-primary" href="../register-interest.html">Register interest in this sport</a>'
                 '<a class="btn btn-ghost" href="../register.html">Add to my plan</a>',
            photo=s["img"]) + f"""
<div class="container breadcrumbs"><a href="../index.html">Home</a> › <a href="index.html">Sports</a> › {e(s['name'])}</div>
<section class="section-tight"><div class="container grid grid-3">
  <div class="card"><div class="body"><h3>📍 Venue</h3><p>{e(s['venue'])}</p>
    <p class="meta"><a href="../venues.html">{(cluster['emoji'] + ' ' + e(cluster['name'])) if cluster else 'Venue cluster map'} →</a></p></div></div>
  <div class="card"><div class="body"><h3>👥 Expected field</h3><p>{e(s['athletes'])} athletes</p>
    <div class="fill-bar" role="img" aria-label="Interest level {s['fill']} percent"><span style="width:{s['fill']}%"></span></div>
    <p class="fill-note">{s['fill']}% of expected field already interested — early birds get guaranteed entry</p></div></div>
  <div class="card"><div class="body"><h3>🌏 Strong from</h3><p class="meta">{e(s['markets'])}</p></div></div>
</div></section>
<section class="section-tight"><div class="container">
  <div class="band"><div class="band-media" aria-hidden="true"><img loading="lazy" src="{img_url(s['img'], 1400)}" alt=""></div>
    <div><h2>Your age group is waiting</h2>
    <p>{e(s['name'])} runs in five-year age bands from {s['minAge']}+ — you race your peers, whether that's the 30–34s or the 80+ legends.</p></div>
    <a class="btn btn-primary btn-big" href="../register-interest.html">I'm in 🙌</a></div>
</div></section>
<section class="section"><div class="container"><h2>More {e(s['category'])} sports</h2>
  <div class="grid grid-3">{rel_cards}</div></div></section>
""" + faq_block([
            (f"What is the minimum age for {s['name']} at Perth 2029?",
             f"The minimum age for {s['name']} is {s['minAge']}. Competition runs in five-year age groups based on your age on 12 October 2029."),
            (f"Where will {s['name']} be held?",
             f"{s['name']} is proposed for {s['venue']} in the {cluster['name'] if cluster else 'Perth'} cluster. Venues are confirmed progressively ahead of registration opening in October 2028."),
            (f"How many athletes will compete in {s['name']}?",
             f"Planning ranges expect {s['athletes']} {s['name']} athletes at Perth 2029, based on entries at Sydney 2009, Auckland 2017 and Taipei 2025."),
        ], heading=f"{s['name']} essentials")
        write(f"sports/{s['id']}.html", layout(
            title=f"{s['name']} at Perth 2029", page="sport", depth=1, active="sports/index.html",
            desc=f"{s['name']} at World Masters Games Perth 2029 ({GAMES_DATES}): venue {s['venue']}, expected field {s['athletes']}, minimum age {s['minAge']}, five-year age groups, no qualification.",
            body=body, extra_ld=f'<script type="application/ld+json">{ld}</script>',
            og_img=img_url(s["img"], 1200)))


# ---------------------------------------------------------------- venues
def build_venues():
    dots = "".join(
        f"""<g class="map-dot" tabindex="0" role="button" data-cluster="{v['id']}" aria-label="{e(v['name'])}">
        <circle cx="{v['mapX']}" cy="{v['mapY']}" r="4.5"></circle>
        <text x="{v['mapX'] + 6}" y="{v['mapY'] + 2}">{e(v['name'].split(' &')[0].split(' (')[0])}</text></g>"""
        for v in venues)
    cluster_cards = "".join(f"""<div class="card">
      {media(v['img'], v['imgAlt'], v['emoji'], badge=str(len(v['venues'])) + ' venues')}
      <div class="body"><h3>{v['emoji']} {e(v['name'])}</h3><p class="meta">{e(v['desc'])}</p>
      <ul class="small" style="margin:0;padding-left:1.1rem">{''.join('<li>' + e(x) + '</li>' for x in v['venues'])}</ul></div></div>"""
                            for v in venues)
    body = hero(
        kicker="9 clusters · ~40 venues · one compact city",
        title="Where the magic happens 🗺️",
        sub="Perth's venues sit in nine tight clusters — stadium to beach to regatta centre, most within 30 minutes of the Games Village.",
        photo="photo-1573935448851-4b07c29ee181") + f"""
<section class="section"><div class="container">
  <div class="venue-map-wrap">
    <div class="venue-map">
      <svg viewBox="0 0 100 100" role="img" aria-label="Stylised map of Perth showing nine venue clusters. Use the buttons to explore each cluster.">
        <rect x="0" y="0" width="100" height="100" rx="6" fill="#e3f0fa"></rect>
        <path d="M22,0 C28,18 24,34 30,48 C36,62 28,80 34,100 L0,100 L0,0 Z" fill="#9fd0ee" opacity=".8"></path>
        <path d="M30,48 C44,50 54,46 70,52 C80,55 88,52 100,56" stroke="#5fa8d8" stroke-width="3.4" fill="none" stroke-linecap="round"></path>
        <text x="6" y="92" font-size="5" fill="#0a3d66" font-weight="bold">Indian Ocean</text>
        <text x="63" y="64" font-size="4.2" fill="#0d4f85">Swan River</text>
        {dots}
      </svg>
    </div>
    <div class="cluster-info" id="cluster-info" aria-live="polite">
      <h3>Tap a dot to explore 👆</h3><p>Each dot is a venue cluster — grouped so you spend your Games competing and celebrating, not commuting.</p>
    </div>
  </div>
  <h2 style="margin-top:2.5rem">All nine clusters</h2>
  <div class="grid grid-3">{cluster_cards}</div>
  <p class="small muted">Proposed venues, subject to confirmation through venue agreements in 2027–2028. Accredited participants are expected to travel free on Perth public transport, as at Melbourne 2002 and Sydney 2009.</p>
</div></section>
""" + faq_block([
        ("How do I get between venues?",
         "Perth 2029 venues are grouped into nine compact clusters. Free public transport for accredited participants is planned (as at Melbourne 2002 and Sydney 2009), with Games shuttles to outer venues and a 12-day shuttle pass available in the Experience Marketplace."),
        ("Where are the Opening and Closing Ceremonies?",
         "The Opening Ceremony is proposed for Optus Stadium on 12 October 2029; the Closing Ceremony for Langley Park on the city foreshore on 23 October 2029."),
        ("Which venues host the biggest sports?",
         "Swimming and most indoor sports centre on the Perth HPC and HBF Arena precinct at Mount Claremont; track and field at WA Athletics Stadium; rowing, dragon boat, canoe sprint and triathlon at Champion Lakes Regatta Centre."),
    ])
    write("venues.html", layout(
        title="Venues & clusters", page="venues", active="venues.html",
        desc="World Masters Games Perth 2029 venues: around 40 venues in nine compact clusters — Optus Stadium, Perth HPC, Champion Lakes, Cottesloe Beach and more — with an interactive cluster map.",
        body=body))


# ---------------------------------------------------------------- marketplace
def build_marketplace():
    cats = ["All"] + list(dict.fromkeys(p["cat"] for p in marketplace))
    btns = "".join(f'<button type="button" data-cat="{e(c)}" aria-pressed="{"true" if c == "All" else "false"}">{e(c)}</button>' for c in cats)
    cards = "".join(f"""<div class="card" data-product="{p['id']}" data-cat="{e(p['cat'])}">
      {media(p['img'], p['imgAlt'], p['emoji'], badge=p['cat'])}
      <div class="body"><h3>{p['emoji']} {e(p['name'])}</h3>
      <p class="meta">{e(p['desc'])}</p>
      <div class="tag-row">{''.join('<span class="tag">' + e(t) + '</span>' for t in p['tags'])}</div>
      <div class="spacer"></div>
      <p class="price-tag">A${p['price']:,} <small>{e(p['unit'])}</small></p>
      <button class="btn btn-primary" type="button" data-add>Add to my trip</button></div></div>"""
                    for p in marketplace)
    body = hero(
        kicker="Stays · experiences · regional escapes — one cart",
        title="The Experience Marketplace 🧳",
        sub="Build your whole WA adventure alongside your competition: accommodation, transfers, day trips, "
            "ceremonies and once-in-a-lifetime regional escapes. Same access for everyone, every tier.",
        photo="photo-1566995541428-f2246c17cda1") + f"""
<section class="section"><div class="container">
  <div class="cat-filter" id="mp-cats">{btns}</div>
  <div class="grid grid-3">{cards}</div>
  <p class="small muted" style="margin-top:1.5rem">Demonstration catalogue with indicative pricing. The live marketplace launches with registration in October 2028, delivered with the Official Travel Partner and Tourism WA's Extend Your Stay program — bookings, payments and cancellations will be handled by the travel partner's booking system.</p>
</div></section>
<section class="section-tight"><div class="container">
  <div class="band"><div class="band-media" aria-hidden="true"><img loading="lazy" src="{img_url('photo-1582967788606-a171c1080cb0', 1400)}" alt=""></div>
    <div><h2>Came for the Games. Stayed for WA. 🐋</h2>
    <p>International athletes stay 14+ nights on average. Margaret River, Ningaloo Reef and the Kimberley are the reason. Your medal can wait a week.</p></div>
    <a class="btn btn-primary btn-big" href="destination.html">Plan the adventure</a></div>
</div></section>
""" + faq_block([
        ("Do I need to register before booking experiences?",
         "When the live marketplace opens in October 2028, browsing is open to everyone and bookings are made through your participant account, so registration comes first. On this preview site you can build a demo trip cart to see how it works."),
        ("Are marketplace prices tied to my registration tier?",
         "No. The Experience Marketplace is identical for every participant — Early Bird, Standard or Late. What shapes your WA experience is what you choose, not what tier you paid."),
        ("What about cancellations and refunds for experiences?",
         "Experience and accommodation bookings follow each operator's published cancellation terms, shown at the time of booking. Travel insurance is strongly recommended for all participants."),
    ])
    write("marketplace.html", layout(
        title="Experience Marketplace", page="marketplace", active="marketplace.html",
        desc="The Perth 2029 Experience Marketplace: Games-rate accommodation, venue shuttles, Rottnest and Swan Valley day trips, Noongar cultural walks, and regional WA escapes to Margaret River, Ningaloo and the Kimberley.",
        body=body))


# ---------------------------------------------------------------- my games
def build_mygames():
    body = hero(
        kicker="Your personal Games, day by day",
        title="My Games 📅",
        sub="Your sports, your bookings, ceremonies and free days — automatically arranged across the 12 days. (AI-personalised itineraries arrive with the Games app.)",
        photo="photo-1506377247377-2a5b3b417ebb") + """
<section class="section"><div class="container">
  <div id="empty-itinerary" hidden class="form-card center">
    <h2>Nothing planned yet 🤷</h2>
    <p>Pick your sports in the planner or add experiences from the marketplace, and your day-by-day Games appears here.</p>
    <p><a class="btn btn-primary" href="register.html">Open the planner</a> <a class="btn btn-secondary" href="marketplace.html">Browse experiences</a></p>
  </div>
  <div id="itinerary-wrap" hidden>
    <div style="display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:1rem">
      <h2 id="itinerary-title">My Perth 2029</h2>
      <button class="btn btn-ghost" type="button" id="print-itinerary">🖨️ Print / save PDF</button>
    </div>
    <p class="small muted">Competition days are indicative until schedules are released through registration. Booked experiences are placed on free days automatically — drag-and-drop arrives with the live platform.</p>
    <div id="itinerary"></div>
  </div>
</div></section>
<noscript><div class="container"><p>The itinerary builder needs JavaScript. The Games run 12–23 October 2029 — Opening Ceremony 12 October at Optus Stadium, Closing 23 October at Langley Park.</p></div></noscript>
"""
    write("my-games.html", layout(
        title="My Games itinerary", page="mygames",
        desc="Your personal World Masters Games Perth 2029 itinerary: competition days, booked experiences, ceremonies and free days across 12–23 October 2029.",
        body=body))


# ---------------------------------------------------------------- connect
def build_connect():
    com = athletes["community"]
    sports_f = "".join(f'<option>{e(s)}</option>' for s in sorted({p["sport"] for p in com}))
    countries_f = "".join(f'<option>{e(c)}</option>' for c in sorted({p["country"] for p in com}))
    ages_f = "".join(f'<option>{e(a)}</option>' for a in sorted({p["ageBand"] for p in com}))
    body = hero(
        kicker="30,000 future teammates, training partners & rivals",
        title="Find your people 🤝",
        sub="Masters sport runs on mates. Find athletes in your sport, your age group or your corner of the world — before you even land in Perth.",
        photo="photo-1547347298-4074fc3086f0") + f"""
<section class="section"><div class="container">
  <div class="search-row" role="group" aria-label="Filter athletes">
    <label class="small" style="align-self:center;font-weight:700" for="f-sport">Sport</label>
    <select id="f-sport" style="max-width:220px"><option>All</option>{sports_f}</select>
    <label class="small" style="align-self:center;font-weight:700" for="f-country">Country</label>
    <select id="f-country" style="max-width:220px"><option>All</option>{countries_f}</select>
    <label class="small" style="align-self:center;font-weight:700" for="f-age">Age group</label>
    <select id="f-age" style="max-width:160px"><option>All</option>{ages_f}</select>
    <span class="small muted" style="align-self:center" id="people-count"></span>
  </div>
  <div class="grid grid-2" id="people-list"></div>
  <p class="small muted" style="margin-top:1.4rem">Sample community for demonstration. The live connection hub — with opt-in profiles, club groups and AI social matching — launches with registration. Connection requests always require both athletes to opt in.</p>
</div></section>
<section class="section-tight"><div class="container">
  <div class="grid grid-3">
    <div class="card"><div class="body"><h3>🏟️ Sport communities</h3><p class="meta">Every sport gets its own Perth 2029 community group from 2027 — meet your field before the first whistle.</p></div></div>
    <div class="card"><div class="body"><h3>👯 Club &amp; team finder</h3><p class="meta">Need a keeper, a cox or a fourth for the pairs? Post a spot, fill your boat. <a href="clubs.html">Clubs &amp; teams →</a></p></div></div>
    <div class="card"><div class="body"><h3>🤖 Smart matching</h3><p class="meta">The Games app will suggest connections by sport, age group, language and interests — opt-in, always.</p></div></div>
  </div>
</div></section>
<noscript><div class="container"><p>The connection hub needs JavaScript — but the community is real: register your interest and we'll connect you with your sport's group.</p></div></noscript>
"""
    write("connect.html", layout(
        title="Connect — find your people", page="connect", active="connect.html",
        desc="Find training partners, teammates and rivals for World Masters Games Perth 2029 — filter the athlete community by sport, country and age group, and connect before the Games.",
        body=body))


# ---------------------------------------------------------------- stories
def build_stories():
    cards = "".join(f"""<div class="card amb-card">
      {media(a['img'], a['imgAlt'], '🌟', badge=a['tier'] + ' ambassador')}
      <div class="body">
        <div class="flag-age"><h3 style="margin:0">{e(a['name'])}</h3><span class="flag" aria-hidden="true">{a['flag']}</span></div>
        <p class="meta">{e(a['sport'])} · {e(a['country'])} · <strong>{a['age2029']} at the Games</strong></p>
        <blockquote>“{e(a['quote'])}”</blockquote>
        <button class="amb-toggle" type="button" aria-expanded="false">Fun fact, Perth pick &amp; story ↓</button>
        <div class="amb-extra">
          <p>⚡ <strong>Fun fact:</strong> {e(a['funFact'])}</p>
          <p>📍 <strong>Perth pick:</strong> {e(a['perthPick'])}</p>
          <p>{e(a['story'])}</p>
          <p><a href="sports/{a['sportId']}.html">See {e(a['sport'])} at Perth 2029 →</a></p>
        </div>
      </div></div>""" for a in athletes["ambassadors"])
    body = hero(
        kicker="Real athletes · real stories · zero retirement plans",
        title="The ones to watch 🌟",
        sub="Meet the masters athletes leading the charge to Perth — from a 38-year-old triathlete to a 72-year-old bowler whose birthday falls on finals day.",
        photo="photo-1517438476312-10d79c077509") + f"""
<section class="section"><div class="container">
  <div class="grid grid-3">{cards}</div>
</div></section>
<section class="section-tight"><div class="container">
  <div class="band"><div class="band-media" aria-hidden="true"><img loading="lazy" src="{img_url('photo-1594737625785-a6cbdabd333c', 1400)}" alt=""></div>
    <div><h2>Got a story like theirs?</h2>
    <p>We're building the Perth 2029 ambassador squad across every sport and priority market — 30 to 50 athletes whose stories make other athletes book flights.</p></div>
    <a class="btn btn-primary btn-big" href="volunteer.html#ambassadors">Nominate yourself or a mate</a></div>
</div></section>
<p class="container small muted">Ambassador profiles shown are illustrative personas for this demonstration site; the real ambassador program launches through 2027 with named athletes.</p>
"""
    write("stories.html", layout(
        title="Athlete stories", page="stories", active="stories.html",
        desc="Meet the masters athletes heading to World Masters Games Perth 2029 — swimmers, sprinters, bowlers and cyclists aged 38 to 72 sharing why they're coming to Perth.",
        body=body))


# ---------------------------------------------------------------- registration & pricing
def build_registration():
    body = hero(
        kicker="Registration opens October 2028 · pre-registration open now",
        title="Pricing, straight up 💸",
        sub="Standard registration is A$325. Early Birds pay A$275 — and get guaranteed sport entry before fields fill. Here's everything, with no fine-print surprises.",
        photo="photo-1556122071-e404eaedb77f") + """
<section class="section"><div class="container">
  <div class="tiers">
    <div class="tier featured"><span class="pop">Best value + guaranteed entry</span>
      <h3>🐦 Early Bird</h3><p class="price">A$275 <small>save A$50</small></p>
      <p class="small muted">Oct 2028 – Apr 2029</p>
      <ul>
        <li class="yes">Everything in the base package</li>
        <li class="yes"><strong>Guaranteed sport entry</strong> — protected place if your field fills</li>
        <li class="yes">Priority pack collection (skip the queue)</li>
        <li class="yes">Premium participant pack + commemorative item</li>
        <li class="yes">Founding Participant wall + digital badge</li>
        <li class="yes">First access to travel packages</li>
        <li class="yes">Extra A$25 off for international athletes</li>
      </ul>
      <div class="spacer"></div><a class="btn btn-primary" href="register-interest.html">Get first access</a></div>
    <div class="tier"><h3>⭐ Standard</h3><p class="price">A$325</p>
      <p class="small muted">May – Jul 2029</p>
      <ul>
        <li class="yes">Everything in the base package</li>
        <li class="yes">Pre-Games training access at competition venues</li>
        <li class="yes">Mid-priority pack collection</li>
        <li class="yes">Next in line if fields fill</li>
        <li class="no">No guaranteed sport entry</li>
        <li class="no">No Founding Participant recognition</li>
      </ul>
      <div class="spacer"></div><a class="btn btn-secondary" href="register-interest.html">Stay in the loop</a></div>
    <div class="tier"><h3>⏰ Late</h3><p class="price">A$425</p>
      <p class="small muted">Aug – Sep 2029</p>
      <ul>
        <li class="yes">Everything in the base package</li>
        <li class="no">General collection queue (30,000 athletes…)</li>
        <li class="no">Waitlist if your sport is full — swimming, athletics and triathlon will fill</li>
        <li class="no">No venue training access</li>
      </ul>
      <div class="spacer"></div><a class="btn btn-ghost" href="register-interest.html">Don't be this person</a></div>
  </div>

  <h2 style="margin-top:3rem">In every tier 🎒</h2>
  <div class="grid grid-3">
    <div class="card"><div class="body"><h3>🏅 Compete</h3><p class="meta">Competition entry (unlimited sports, subject to capacity), official results and timing, placegetter medals, sports medicine at venues.</p></div></div>
    <div class="card"><div class="body"><h3>🎉 Celebrate</h3><p class="meta">Opening and Closing Ceremony access, Games Village entry and nightly entertainment, the social program.</p></div></div>
    <div class="card"><div class="body"><h3>🪪 Belong</h3><p class="meta">Digital accreditation across all venues, participant pack with event guide, participant portal with your schedule.</p></div></div>
  </div>

  <h2 style="margin-top:3rem">Extras &amp; discounts</h2>
  <div class="table-wrap"><table class="data">
    <tr><th>Category</th><th>Indicative price</th><th>The deal</th></tr>
    <tr><td>Supporter / accompanying person</td><td>~A$90–110</td><td>Village, ceremonies, accreditation and supporter pack — competition not included</td></tr>
    <tr><td>Non-playing official</td><td>~A$110</td><td>Coaches, managers and scorers linked to a registered team — medal-eligible with the team</td></tr>
    <tr><td>Club &amp; team discount</td><td><strong>10% off</strong></td><td>Five or more from one club, applied automatically with your club code</td></tr>
    <tr><td>Multi-sport discount</td><td><strong>50% off</strong></td><td>Second and additional sport entry fees half price</td></tr>
    <tr><td>International Early Bird incentive</td><td><strong>A$25 off</strong></td><td>Automatic for athletes registering from outside Australia in the Early Bird window</td></tr>
    <tr><td>International payment plan</td><td>50% now / 50% later</td><td>Split payments for international Early Bird registrations — second instalment six months before the Games</td></tr>
  </table></div>

  <h2 style="margin-top:3rem">Change of plans? Covered. 🛟</h2>
  <div class="grid grid-3">
    <div class="card"><div class="body"><h3>14-day cooling off</h3><p class="meta">Full refund within 14 days of registering, any reason, no questions.</p></div></div>
    <div class="card"><div class="body"><h3>Transfers</h3><p class="meta">Pass your registration (tier benefits included) to another eligible athlete any time up to 30 days out — A$30 admin fee.</p></div></div>
    <div class="card"><div class="body"><h3>Cancellations</h3><p class="meta">50% Games-fee refund 6+ months out, 25% at 3–6 months. Inside 3 months, transfer instead. Full refund if WMGP29 cancels the Games.</p></div></div>
  </div>
  <p class="small muted" style="margin-top:1.4rem">All prices are indicative planning figures pending Board approval, published at least 12 months before registration opens. Registration will run on the World Masters Sport platform. The full refund, transfer and deferral policy is published before registration opens and linked from every registration page.</p>
</div></section>
""" + faq_block([
        ("When does paid registration open?",
         "October 2028 — about 12 months before the Games. Pre-registrants get priority access to the Early Bird window before general release."),
        ("Why register Early Bird?",
         "Guaranteed sport entry is the big one: if your sport's field fills (swimming, athletics and triathlon are expected to), Early Bird athletes keep protected places while later registrants join a waitlist. Plus A$50 saved, priority collection and Founding Participant status."),
        ("What's NOT included in registration?",
         "Flights, accommodation and experiences — though all are bookable in one place through the Experience Marketplace, and the Official Travel Partner offers packages from every priority market. Sport entry fees are charged per sport, with multi-sport entries 50% off."),
        ("Is there a payment plan?",
         "Yes — international athletes registering in the Early Bird window can split payment 50/50, with the second instalment charged six months before the Games."),
    ])
    write("registration.html", layout(
        title="Registration & pricing", page="pricing",
        desc="World Masters Games Perth 2029 pricing: Early Bird A$275, Standard A$325, Late A$425 (indicative). Club discounts, multi-sport discounts, international incentives, payment plans and a 14-day cooling-off refund.",
        body=body))


# ---------------------------------------------------------------- destination
def build_destination():
    picks = [p for p in marketplace if p["cat"] in ("Day Experiences", "Extend Your Stay")]
    pick_cards = "".join(f"""<div class="card">
      {media(p['img'], p['imgAlt'], p['emoji'], badge=p['cat'])}
      <div class="body"><h3>{p['emoji']} {e(p['name'])}</h3><p class="meta">{e(p['desc'])}</p>
      <div class="spacer"></div><p><a href="marketplace.html">Book in the marketplace →</a></p></div></div>"""
                         for p in picks)
    body = hero(
        kicker="Walking on a Dream · Western Australia",
        title="The Games with a holiday built in 🌅",
        sub="October in Perth: 21°C, eight hours of sunshine, the clearest ocean of the year. Bring the family — the average athlete brings their crew and stays two weeks+.",
        photo="photo-1566995541428-f2246c17cda1") + f"""
<section class="section"><div class="container">
  <div class="grid grid-2" style="align-items:center">
    <div>
      <h2>Why athletes pick Perth</h2>
      <p>☀️ <strong>The weather is a teammate.</strong> October is Perth's sweet spot — warm days, cool evenings, low humidity, the famous afternoon sea breeze.</p>
      <p>🏖️ <strong>The city is the venue.</strong> Race the Swan River foreshore, swim off Cottesloe, finish in stadiums — then walk to dinner.</p>
      <p>✈️ <strong>Closer than you think.</strong> Direct flights from London, Paris, Tokyo, Singapore, KL, Jakarta, Johannesburg, Guangzhou and Auckland.</p>
      <p>🦘 <strong>The support crew wins too.</strong> Quokkas, wine country, whale season and wildflowers — while you're busy winning medals.</p>
    </div>
    <div class="weather-dial" role="img" aria-label="October in Perth: average 21 degrees, more than 8 hours of daily sunshine">
      <span class="temp">21°</span>
      <span class="desc"><strong>October average</strong>8+ sunshine hours daily · 19° ocean · wildflower season · whale-watching season</span>
    </div>
  </div>
</div></section>
<section class="section" style="background:var(--sand-100)"><div class="container">
  <h2>Extend the dream 🛣️</h2>
  <p class="muted">International athletes average 14+ nights. These are the reasons why.</p>
  <div class="grid grid-3">{pick_cards}</div>
</div></section>
<section class="section-tight"><div class="container">
  <div class="band"><div class="band-media" aria-hidden="true"><img loading="lazy" src="{img_url('photo-1529108190281-9a4f620bc2d8', 1400)}" alt=""></div>
    <div><h2>Whadjuk Noongar Country</h2>
    <p>The Games are held on the lands of the Whadjuk people of the Noongar nation — and Noongar culture is woven through the Games, from the Welcome to Country to guided experiences on Country.</p></div>
    <a class="btn btn-primary" href="marketplace.html">Cultural experiences</a></div>
</div></section>
""" + faq_block([
        ("What's the weather like in Perth in October?",
         "Spring at its best: average maximums around 21°C, more than eight hours of daily sunshine, low humidity and light morning winds — near-ideal competition conditions. Pack for warm days and mild evenings."),
        ("How do I get to Perth?",
         "Perth Airport has direct flights from London, Paris, Tokyo, Singapore, Kuala Lumpur, Jakarta, Johannesburg, Guangzhou, Auckland and all Australian capitals. The Official Travel Partner will offer packages (flights + stay + registration) from every priority market from October 2028."),
        ("Should my family come?",
         "Yes — most masters athletes travel with partners, family or friends (the average is about one supporter per athlete). Supporter passes include the Games Village and ceremonies, and October is peak WA holiday weather without peak crowds."),
        ("What's worth seeing beyond Perth?",
         "Margaret River wine country (3 hours south), Rottnest Island and its quokkas (30 minutes by ferry), the Coral Coast and Ningaloo Reef (swim with whale sharks' gentler cousins — humpbacks migrate in October), and the Kimberley in the far north."),
    ])
    write("destination.html", layout(
        title="Plan your trip — Perth & WA", page="destination", active="destination.html",
        desc="Plan your World Masters Games Perth 2029 trip: October weather (21°C, 8+ sunshine hours), direct flights, family-friendly supporter experiences, and WA escapes from Rottnest to Margaret River, Ningaloo and the Kimberley.",
        body=body))


# ---------------------------------------------------------------- kansai
def build_kansai():
    body = hero(
        kicker="World Masters Games Kansai · 14–30 May 2027",
        title="Doing Kansai?<br>Perth is next. 🇯🇵→🇦🇺",
        sub="50,000 athletes will make history in Japan in 2027. Twenty-nine months later, the world's masters meet again in Perth. One journey, two unforgettable Games.",
        photo="photo-1480796927426-f609979314bd",
        ctas='<a class="btn btn-primary btn-big" href="register-interest.html">Register interest for Perth</a>') + f"""
<section class="section"><div class="container">
  <div class="grid grid-3">
    <div class="card"><div class="body"><h3>🏯 At Kansai 2027</h3><p class="meta">Find the Perth 2029 pavilion at the Games — meet our ambassadors, preview your sport's Perth plans and sign up on the spot for first Early Bird access.</p></div></div>
    <div class="card"><div class="body"><h3>🤝 Partner Games</h3><p class="meta">Perth 2029 and the Kansai Organising Committee work together under a formal agreement, so your masters journey continues seamlessly from Japan to Australia.</p></div></div>
    <div class="card"><div class="body"><h3>🎌 The handover</h3><p class="meta">Watch for Perth's moment at the Kansai Closing Ceremony — then start planning. Direct Tokyo–Perth flights, and October weather worth the trip alone.</p></div></div>
  </div>
  <div class="band" style="margin-top:2rem"><div class="band-media" aria-hidden="true"><img loading="lazy" src="{img_url('photo-1502680390469-be75c86b636f', 1400)}" alt=""></div>
    <div><h2>「次は、パースで。」</h2>
    <p>See you in Perth. Japanese-language Games information, in-market travel agents and Japanese-speaking Games services are all part of the Perth 2029 plan — Japan is one of our most important guest nations.</p></div>
    <a class="btn btn-primary btn-big" href="register-interest.html">先行登録 — Register interest</a></div>
</div></section>
""" + faq_block([
        ("I'm competing at Kansai 2027 — does anything carry over to Perth 2029?",
         "Your experience does! Register your interest with Perth 2029 (free) and you'll get first access to Early Bird pricing, plus sport-specific Perth updates from the moment Kansai ends. Perth 2029 will also have a pavilion at Kansai where you can sign up in person."),
        ("How does Perth compare with Kansai for travel?",
         "Perth is a 10-hour direct flight from Tokyo with no jet lag drama (Perth is in the same time zone as much of East Asia, UTC+8). October 2029 gives you 29 months after Kansai to plan — and the Official Travel Partner will offer Japan-market packages."),
        ("Will there be Japanese-language support at Perth 2029?",
         "Yes. Japanese is a priority language for Perth 2029 — Japanese-language content, in-market travel agents and multilingual Games-time services (including an AI-powered multilingual concierge) are all planned."),
    ])
    write("kansai.html", layout(
        title="Kansai 2027 → Perth 2029", page="kansai",
        desc="Competing at World Masters Games Kansai 2027? Perth 2029 is your next Games — 29 months later, direct flights from Japan, Japanese-language support and first Early Bird access for Kansai athletes.",
        body=body))


# ---------------------------------------------------------------- clubs
def build_clubs():
    body = hero(
        kicker="The most fun your club will ever have on tour",
        title="Bring the whole club 👯",
        sub="Masters sport travels in packs. Clubs of 5+ save 10% on every registration — and the more of you there are, the better the rewards get.",
        photo="photo-1574629810360-7efbbe195018",
        ctas='<a class="btn btn-primary btn-big" href="register-interest.html">Register your club\'s interest</a>') + """
<section class="section"><div class="container">
  <h2>The club rewards ladder 🪜</h2>
  <div class="grid grid-4">
    <div class="card"><div class="body"><h3>10 registered</h3><p class="meta">🚩 Your club banner flying at your competition venue</p></div></div>
    <div class="card"><div class="body"><h3>25 registered</h3><p class="meta">📣 Club feature across Perth 2029 website and social channels</p></div></div>
    <div class="card"><div class="body"><h3>50 registered</h3><p class="meta">⛺ Your own club marquee session in the Games Village</p></div></div>
    <div class="card"><div class="body"><h3>100+ registered</h3><p class="meta">👑 CEO welcome video + Games Village naming rights for one social event</p></div></div>
  </div>

  <h2 style="margin-top:3rem">Captains get the royal treatment 🫡</h2>
  <div class="grid grid-3">
    <div class="card"><div class="body"><h3>📊 Club dashboard</h3><p class="meta">See who's registered, nudge the stragglers, manage the whole squad from one screen.</p></div></div>
    <div class="card"><div class="body"><h3>📞 Direct line</h3><p class="meta">A real human at Perth 2029 for group bookings, fixture questions and the inevitable name spelling fixes.</p></div></div>
    <div class="card"><div class="body"><h3>🎒 Priority collection</h3><p class="meta">A dedicated captain window at the Accreditation Centre — collect for the whole club, skip every queue.</p></div></div>
  </div>
</div></section>
""" + faq_block([
        ("How does the club discount work?",
         "When registration opens in October 2028, your club registers as an affiliated club and receives a unique code. Five or more registrations using the code get 10% off each — applied automatically at checkout, on any tier."),
        ("Can we field teams across multiple sports?",
         "Yes — many clubs enter teams in several sports plus individuals in more. The multi-sport discount (50% off additional sport entries) stacks with the club discount."),
        ("We're short a player or two — can Perth 2029 help?",
         "That's exactly what the Connect hub is for: post your missing spot (a keeper, a cox, a fourth for the pairs) and find athletes from your sport and age group looking for a team."),
    ])
    write("clubs.html", layout(
        title="Clubs & teams", page="clubs",
        desc="Bring your club to World Masters Games Perth 2029: 10% group discount for 5+, captain dashboards, priority collection, and club rewards from venue banners to Games Village naming rights.",
        body=body))


# ---------------------------------------------------------------- volunteer
def build_volunteer():
    body = hero(
        kicker="5,000+ roles · recruitment opens 2028",
        title="The best seat in the house is a volunteer shirt 🙋",
        sub="Venues, Village, ceremonies, transport, athlete services — volunteers make the Games. Raise your hand now and be first in line.",
        photo="photo-1559027615-cd4628902d4a",
        ctas='<a class="btn btn-primary btn-big" href="register-interest.html">Register volunteer interest</a>') + """
<section class="section"><div class="container">
  <div class="grid grid-3">
    <div class="card"><div class="body"><h3>🏟️ Sport &amp; venues</h3><p class="meta">Field-of-play support, results running, athlete marshalling — closest to the action it gets.</p></div></div>
    <div class="card"><div class="body"><h3>🎪 Games Village &amp; city</h3><p class="meta">Welcome desks, wayfinding, the nightly social program and keeping 30,000 athletes smiling.</p></div></div>
    <div class="card"><div class="body"><h3>🚌 Operations</h3><p class="meta">Transport hubs, accreditation, logistics, media support — the engine room of a 12-day city-wide event.</p></div></div>
  </div>
  <div class="band" style="margin-top:2rem">
    <div><h2 id="ambassadors">Ambassadors wanted 🌟</h2>
    <p>We're also building a squad of 30–50 athlete ambassadors across sports and countries — masters athletes whose stories get other athletes off the couch and onto a plane. Know one? Are one?</p></div>
    <a class="btn btn-primary" href="register-interest.html">Put a name forward</a></div>
</div></section>
""" + faq_block([
        ("When does volunteer recruitment open?",
         "Formal recruitment opens in 2028, with training through 2029 ahead of the Games. Registering interest now puts you first in the queue when applications open."),
        ("What's the minimum age to volunteer?",
         "18. There's no upper limit — masters games volunteering is famously multigenerational, and many volunteers are masters athletes themselves on their rest days."),
        ("What do volunteers receive?",
         "Full training, uniform, meals on shift, recognition through the volunteer program — and the best view of the Games anyone gets. Volunteer accident insurance is provided."),
    ])
    write("volunteer.html", layout(
        title="Volunteer & ambassadors", page="volunteer",
        desc="Volunteer at World Masters Games Perth 2029 — 5,000+ roles across venues, the Games Village, ceremonies and operations. Recruitment opens 2028; register interest now. Ambassador program also recruiting.",
        body=body))


# ---------------------------------------------------------------- partners
def build_partners():
    body = hero(
        kicker="Reach 30,000 athletes + their travelling crews",
        title="Partner with the Games 🤝",
        sub="A 12-day, city-wide event with a high-value, high-dwell audience: active 30–75s from 100+ nations who plan trips, book experiences and remember who looked after them.",
        photo="photo-1556122071-e404eaedb77f",
        ctas='<a class="btn btn-primary btn-big" href="contact.html">Start the conversation</a>') + """
<section class="section"><div class="container">
  <div class="grid grid-3">
    <div class="card"><div class="body"><h3>🏟️ Founding partners</h3><p class="meta">The Australian Government (Office for Sport) and Tourism Western Australia are cornerstone investors in Perth 2029 — delivered under the Walking on a Dream destination brand.</p></div></div>
    <div class="card"><div class="body"><h3>🥇 Games partners</h3><p class="meta">Tiered partnerships across cash and value-in-kind — venues, Village activation, sport presentation, digital and broadcast moments across a four-year campaign.</p></div></div>
    <div class="card"><div class="body"><h3>🧳 Official service partners</h3><p class="meta">Official Travel, Charity and Merchandise partner appointments integrate directly into the participant journey — from booking to podium.</p></div></div>
  </div>
  <div class="grid grid-4" style="margin-top:2rem">
    <div class="card"><div class="body"><h3>30,000</h3><p class="meta">registered participants targeted</p></div></div>
    <div class="card"><div class="body"><h3>~1 per athlete</h3><p class="meta">travelling supporters — a doubled audience</p></div></div>
    <div class="card"><div class="body"><h3>14+ nights</h3><p class="meta">average international stay</p></div></div>
    <div class="card"><div class="body"><h3>12 days</h3><p class="meta">of city-wide activation, Village footfall and ceremonies</p></div></div>
  </div>
</div></section>
"""
    write("partners.html", layout(
        title="Partners & sponsorship", page="partners",
        desc="Partner with World Masters Games Perth 2029 — reach 30,000 athletes from 100+ nations plus travelling supporters across a 12-day city-wide event and a four-year campaign.",
        body=body))


# ---------------------------------------------------------------- news
def build_news():
    cards = "".join(f"""<div class="card">
      {media(n['img'], n['imgAlt'], '📰', badge=n['tag'])}
      <div class="body"><p class="news-date">{e(n['date'])}</p>
      <h3><a href="{n['id']}.html">{e(n['title'])}</a></h3><p class="meta">{e(n['excerpt'])}</p></div>
      <a class="card-link" href="{n['id']}.html" aria-hidden="true" tabindex="-1"></a></div>"""
                    for n in sorted(news, key=lambda x: x["date"], reverse=True))
    body = hero(
        kicker="Announcements · sport reveals · destination intel",
        title="Games news 📰",
        sub="Everything happening on the road to October 2029.",
        photo="photo-1504711434969-e33886168f5c") + f"""
<section class="section"><div class="container"><div class="grid grid-3">{cards}</div></div></section>"""
    write("news/index.html", layout(
        title="News", page="news", active="news/index.html", depth=1,
        desc="News from World Masters Games Perth 2029 — sport program announcements, registration milestones, Kansai 2027 partnership updates and Perth destination guides.",
        body=body))

    for n in news:
        ld = json.dumps({
            "@context": "https://schema.org", "@type": "NewsArticle",
            "headline": n["title"], "datePublished": n["date"],
            "publisher": {"@type": "Organization", "name": "World Masters Games Perth 2029 Ltd"},
            "description": n["excerpt"]})
        paras = "".join(f"<p>{e(p)}</p>" for p in n["body"].split("\n\n"))
        body = hero(kicker=f"{n['tag']} · {n['date']}", title=e(n["title"]), sub="",
                    photo=n["img"]) + f"""
<div class="container breadcrumbs"><a href="../index.html">Home</a> › <a href="index.html">News</a> › {e(n['title'][:40])}…</div>
<section class="section"><div class="container"><article class="news-body">{paras}
<p style="margin-top:2rem"><a class="btn btn-primary" href="../register-interest.html">Register your interest</a> <a class="btn btn-ghost" href="index.html">← All news</a></p>
</article></div></section>"""
        write(f"news/{n['id']}.html", layout(
            title=n["title"], page="news-article", depth=1, active="news/index.html",
            desc=n["excerpt"], body=body,
            extra_ld=f'<script type="application/ld+json">{ld}</script>',
            og_img=img_url(n["img"], 1200)))


# ---------------------------------------------------------------- about + footer pages
def build_about():
    history = [("1985", "Toronto, Canada", "8,305"), ("1989", "Denmark (multi-city)", "5,437"),
               ("1994", "Brisbane, Australia", "23,659"), ("1998", "Portland, USA", "11,000"),
               ("2002", "Melbourne, Australia", "24,886"), ("2005", "Edmonton, Canada", "21,600"),
               ("2009", "Sydney, Australia", "28,676"), ("2013", "Turin, Italy", "~19,000"),
               ("2017", "Auckland, New Zealand", "28,578"), ("2025", "Taipei, Taiwan", "25,752"),
               ("2027", "Kansai, Japan", "50,000 target"), ("2029", "Perth, Australia", "30,000 target")]
    rows = "".join(f"<tr><td>{y}</td><td>{h}</td><td>{p}</td></tr>" for y, h, p in history)
    body = hero(
        kicker="Since Toronto 1985 · governed by World Masters Sport",
        title="The biggest games you've (maybe) never heard of 🌏",
        sub="The World Masters Games is the largest multi-sport participation event on earth — bigger than the Olympics by athlete count, and open to absolutely everyone who meets the age minimum.",
        photo="photo-1461896836934-ffe607ba8211") + f"""
<section class="section"><div class="container">
  <div class="grid grid-2">
    <div>
      <h2>What makes it special</h2>
      <p>🎟️ <strong>No qualifying. Ever.</strong> If you meet your sport's minimum age (most 30+, some 25+), you're in — first-timer or former Olympian.</p>
      <p>🎂 <strong>Age groups level the field.</strong> Five-year bands mean you race your peers — the 50–54s, the 70–74s, the 85+ legends.</p>
      <p>🌍 <strong>It's a world party.</strong> 100+ nations, a Games Village with nightly entertainment, and a closing ceremony that doubles as the world's biggest team reunion.</p>
      <p>🇦🇺 <strong>Australia's fourth time.</strong> Brisbane 1994, Melbourne 2002, Sydney 2009 — and now Perth 2029, the nation's return after 20 years.</p>
    </div>
    <div class="table-wrap"><table class="data">
      <caption style="text-align:left;font-weight:700;font-family:var(--font-display);padding:.4rem 0">World Masters Games through the years</caption>
      <tr><th>Year</th><th>Host</th><th>Athletes</th></tr>{rows}
    </table></div>
  </div>
  <div class="band" style="margin-top:2.5rem">
    <div><h2>Perth 2029, in one sentence</h2>
    <p>A 12-day, city-wide festival of sport for 30,000 everyday athletes from 100+ nations — designed participant-first, distinctly Western Australian, and built to leave masters sport stronger everywhere it touches.</p></div>
    <a class="btn btn-primary btn-big" href="register-interest.html">Be part of it</a></div>
</div></section>
""" + faq_block([
        ("Who runs the World Masters Games?",
         "World Masters Sport (formerly IMGA) owns the Games; each edition is delivered by a host organising company — for 2029, World Masters Games Perth 2029 Ltd, a not-for-profit backed by the Australian Government's Office for Sport and Tourism Western Australia."),
        ("How big is Perth 2029 compared with the Olympics?",
         "By athlete numbers, much bigger: Perth 2029 targets 30,000 participants versus around 10,500 athletes at an Olympic Games. The difference: every one of the 30,000 is there to play, not watch."),
        ("What happens between now and 2029?",
         "Sports are confirmed through 2027–2028, registration opens October 2028, volunteer recruitment starts 2028, and the Games open at Optus Stadium on 12 October 2029."),
    ])
    write("about.html", layout(
        title="About the Games", page="about",
        desc="About the World Masters Games: the world's largest multi-sport participation event since 1985, open to all 25/30+, no qualifying — and Perth 2029 is Australia's fourth edition.",
        body=body))


def build_footer_pages():
    write("accessibility.html", layout(
        title="Accessibility", page="accessibility",
        desc="Accessibility commitment for the World Masters Games Perth 2029 website: WCAG 2.2 AA, keyboard navigation, screen reader support, captions, and accessible venues and services at the Games.",
        body=hero(kicker="Everyone plays. Everyone browses.", title="Accessibility ♿",
                  sub="This site is built to WCAG 2.2 AA — and the Games are built the same way.",
                  photo="photo-1559027615-cd4628902d4a") + """
<section class="section"><div class="container" style="max-width:780px">
  <h2>On this website</h2>
  <p>Semantic structure and landmarks, full keyboard operation with visible focus, a skip link, labelled forms, text contrast at or above 4.5:1, 48px touch targets, support for 200% zoom, alt text on imagery, reduced-motion support, and core content that works without JavaScript. Found a barrier? <a href="contact.html">Tell us</a> — we'll fix it.</p>
  <h2>At the Games</h2>
  <p>Perth 2029's commitments include venue accessibility audits across all competition venues and the Games Village, accessible transport options, Auslan interpretation and audio description at the Opening and Closing Ceremonies, sensory-friendly sessions and quiet spaces where programming allows, and accessibility and inclusion training for every volunteer.</p>
</div></section>"""))

    write("privacy.html", layout(
        title="Privacy & data", page="privacy",
        desc="How World Masters Games Perth 2029 Ltd handles personal information — Australian Privacy Principles, GDPR for EU/UK residents, consent, access and deletion rights.",
        body=hero(kicker="Your data, handled properly", title="Privacy & data 🔐",
                  sub="The short version: we collect only what we need, we tell you what it's for, and you're in control.",
                  photo="photo-1504711434969-e33886168f5c") + """
<section class="section"><div class="container" style="max-width:780px">
  <p><strong>What we collect.</strong> Pre-registration collects your name, email, date of birth, country and sports of interest — used to send you relevant Games updates and to plan competition capacity. Nothing more is collected without telling you why.</p>
  <p><strong>The rules we follow.</strong> WMGP29 Ltd handles personal information under the Australian Privacy Act 1988 (Cth) and the Australian Privacy Principles. For residents of the EU and UK we apply GDPR standards, including lawful basis, data-transfer safeguards and the right to erasure. Jurisdiction-specific protections apply for Japan (APPI), China (PIPL), Indonesia (UU PDP) and India (DPDP Act).</p>
  <p><strong>Who we share with.</strong> Limited, governed data sharing supports Games delivery: Tourism Western Australia (tourism outcomes), World Masters Sport (registration platform) and the Australian Government (participation reporting) — all under written agreements with purpose limits and deletion timelines.</p>
  <p><strong>Your controls.</strong> Every email includes unsubscribe. You can request access, correction or deletion of your data at any time via <a href="contact.html">contact us</a>.</p>
  <p class="small muted">This demonstration page summarises the planned privacy framework; the full policy is published before any large-scale data collection begins.</p>
</div></section>"""))

    write("contact.html", layout(
        title="Contact", page="contact",
        desc="Contact World Masters Games Perth 2029 — participant questions, volunteering, partnerships, media and accessibility feedback.",
        body=hero(kicker="Real humans, Perth time (UTC+8)", title="Say hello 👋",
                  sub="Questions, ideas, partnership conversations or accessibility feedback — we'd love to hear from you.",
                  photo="photo-1573935448851-4b07c29ee181") + """
<section class="section"><div class="container">
  <div class="grid grid-3">
    <div class="card"><div class="body"><h3>🏅 Athletes & supporters</h3><p class="meta">hello@wmgp29.com<br>Sport, registration and travel questions</p></div></div>
    <div class="card"><div class="body"><h3>🤝 Partners & media</h3><p class="meta">partnerships@wmgp29.com · media@wmgp29.com</p></div></div>
    <div class="card"><div class="body"><h3>🙋 Volunteers & community</h3><p class="meta">volunteer@wmgp29.com<br>Recruitment opens 2028 — interest welcome now</p></div></div>
  </div>
  <p class="small muted" style="margin-top:1.5rem">World Masters Games Perth 2029 Ltd · Perth, Western Australia · Demonstration contact addresses.</p>
</div></section>"""))


# ---------------------------------------------------------------- data.js, sitemap, robots
def build_assets():
    shutil.copytree(ROOT / "assets", OUT / "assets", dirs_exist_ok=True)
    client = {
        "sports": [{"id": s["id"], "name": s["name"], "emoji": s["emoji"], "minAge": s["minAge"],
                    "venue": s["venue"], "category": s["category"], "imgAlt": s["imgAlt"],
                    "imgUrl": img_url(s["img"], 600)} for s in sports],
        "venues": [{"id": v["id"], "name": v["name"], "emoji": v["emoji"], "desc": v["desc"],
                    "venues": v["venues"]} for v in venues],
        "marketplace": [{"id": p["id"], "name": p["name"], "price": p["price"], "unit": p["unit"],
                         "cat": p["cat"], "emoji": p["emoji"]} for p in marketplace],
        "community": athletes["community"],
    }
    (OUT / "assets/js/data.js").write_text(
        "window.WMGP_DATA = " + json.dumps(client) + ";\n")


def build_meta():
    pages = ["index.html", "register-interest.html", "register.html", "registration.html",
             "marketplace.html", "my-games.html", "connect.html", "stories.html",
             "venues.html", "destination.html", "kansai.html", "clubs.html",
             "volunteer.html", "partners.html", "about.html", "accessibility.html",
             "privacy.html", "contact.html", "sports/index.html", "news/index.html"]
    pages += [f"sports/{s['id']}.html" for s in sports]
    pages += [f"news/{n['id']}.html" for n in news]
    urls = "".join(f"<url><loc>{BASE_URL}/{p}</loc></url>" for p in pages)
    write("sitemap.xml", f'<?xml version="1.0" encoding="UTF-8"?>\n'
          f'<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">{urls}</urlset>')
    write("robots.txt", f"User-agent: *\nAllow: /\nSitemap: {BASE_URL}/sitemap.xml\n")
    return pages


def check_links(pages):
    """Verify internal hrefs resolve to generated files."""
    import re
    missing = []
    for p in pages:
        content = (OUT / p).read_text()
        base = (OUT / p).parent
        for href in re.findall(r'href="([^"#]+?)(?:#[^"]*)?"', content):
            if href.startswith(("http", "mailto:", "data:")) or not href:
                continue
            target = (base / href).resolve()
            if not target.exists():
                missing.append((p, href))
    return missing


def main():
    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir()
    build_assets()
    build_home()
    build_interest()
    build_wizard()
    build_sports()
    build_venues()
    build_marketplace()
    build_mygames()
    build_connect()
    build_stories()
    build_registration()
    build_destination()
    build_kansai()
    build_clubs()
    build_volunteer()
    build_partners()
    build_news()
    build_about()
    build_footer_pages()
    pages = build_meta()
    missing = check_links(pages)
    print(f"Built {len(pages)} pages → {OUT}")
    if missing:
        print("BROKEN LINKS:")
        for p, h in missing:
            print(f"  {p} -> {h}")
        raise SystemExit(1)
    print("All internal links OK.")


if __name__ == "__main__":
    main()
