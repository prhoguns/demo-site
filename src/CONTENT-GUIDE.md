# Content authoring guide — St. Columba Parish demo site

This site is a **demo/boilerplate** a small web business pitches to Catholic parishes in Toronto
(Archdiocese of Toronto). It is a static site (Netlify) whose page content is written in
**WordPress core-block markup**, so every page can later be recreated on WordPress.com where the
parish secretary edits it. Follow this guide literally.

## 1. Files

* One file per page: `src/content/<slug>.html`. The URL is `/<slug>/`.
* Build and check: `python3 src/build.py --check` (from the repo root). Fix every
  "missing" target that your pages caused. Never edit generated files at the repo root.
* A page file = front matter between `---` lines, then the page body.

```
---
title: Baptism
section: Sacraments
section_href: /sacraments/
order: 2
lede: One-sentence summary shown under the title (plain text, no HTML).
description: 150-char SEO description (plain text).
hero_image: baptism-baby-water        (optional photo slug; makes the title band a photo)
image: baptism-font                   (optional photo slug for social sharing)
---
<p class="wp-block-paragraph">…</p>
```

`section` groups sibling pages into the "In this section" strip; use exactly the section names
given in your assignment. `order` sorts the strip (1 = first).

## 2. The markup contract (WordPress core blocks only)

Allowed in page bodies — nothing else:

| Purpose | Markup |
|---|---|
| Paragraph | `<p class="wp-block-paragraph">…</p>` (`has-small-font-size`, `has-medium-font-size`, `lede`, `kicker` may be added) |
| Headings | `<h2 class="wp-block-heading">`, `<h3 class="wp-block-heading">` (h1 is the page title — never write one) |
| Lists | `<ul class="wp-block-list">` / `<ol class="wp-block-list">` |
| Buttons | `<div class="wp-block-buttons"><div class="wp-block-button"><a class="wp-block-button__link wp-element-button" href="/x/">Label</a></div><div class="wp-block-button is-style-outline"><a class="wp-block-button__link wp-element-button" href="/y/">Label</a></div></div>` |
| Image | `<!--img:photo-slug|Alt text-->` (expands to a full Image block with srcset) — see §4 |
| Columns | `<div class="wp-block-columns are-vertically-aligned-center media-row"><div class="wp-block-column media-row__img"><!--img:slug|alt--></div><div class="wp-block-column is-vertically-aligned-center">…text…</div></div>` (add `media-row--flip` on the columns to put the image on the right) |
| Group / card band | `<div class="wp-block-group has-parish-bg-background-color has-background">…</div>` (also `has-parish-bg-alt-background-color`, `has-parish-primary-background-color` for a dark navy band) |
| FAQ / accordion | `<details class="wp-block-details"><summary>Question?</summary><p class="wp-block-paragraph">Answer.</p></details>` |
| Quote | `<blockquote class="wp-block-quote"><p>…</p><cite>— Source</cite></blockquote>` |
| Separator | `<hr class="wp-block-separator has-alpha-channel-opacity">` |
| Table | `<figure class="wp-block-table"><table><thead><tr><th>…</th></tr></thead><tbody><tr><td>…</td></tr></tbody></table></figure>` |
| File / PDF link | `<div class="wp-block-file"><a href="/wp-content/uploads/2026/09/sample-form.pdf">Baptism registration form (PDF)</a><a class="wp-block-file__button wp-element-button" href="…">Download</a></div>` — only link PDFs that exist: `sample-form.pdf`, `sample-bulletin.pdf` |
| YouTube | `<figure class="wp-block-embed is-type-video is-provider-youtube"><div class="wp-block-embed__wrapper"><iframe src="https://www.youtube-nocookie.com/embed/VIDEO_ID" title="…" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture" allowfullscreen loading="lazy"></iframe></div></figure>` — only on pages where your assignment says so. The demo's placeholder Mass video is `PlbcLFoa3as` (Daily TV Mass from Loretto Abbey, Toronto; channel https://www.youtube.com/dailytvmass) |
| Google Map | `<figure class="wp-block-embed map"><div class="wp-block-embed__wrapper"><iframe src="https://www.google.com/maps?q=East+York,+Toronto,+ON&z=13&output=embed" title="Map" loading="lazy"></iframe></div></figure>` |
| Wide content | add `alignwide` to a group/columns to let it use the full 1200px width |

**Never** write `<script>`, `<style>`, inline `style=""` (except `style="--cta-img:url(…)"` on CTA banners), `<div>` soup without block classes, or `<h1>`.
Everything visual must come from the classes below.

### Page-level components (all are Group/Columns blocks with an extra class)

```html
<!-- In-page section intro -->
<div class="section-head"><p class="eyebrow">Kicker</p><h2 class="wp-block-heading">Heading</h2><p>Intro sentence.</p></div>

<!-- Card grid (3 across; card-grid--2 / card-grid--4 also exist) -->
<div class="wp-block-group is-layout-grid card-grid alignwide">
  <div class="wp-block-group card">
    <!--img:slug|alt-->
    <div class="card__body"><p class="card__meta">Optional kicker</p><h3 class="wp-block-heading">Title</h3><p class="wp-block-paragraph">Text.</p><p><a class="text-link" href="/x/">Learn more</a></p></div>
  </div>
</div>

<!-- Ministry directory card (no photo) -->
<div class="wp-block-group is-layout-grid ministry-grid alignwide">
  <div class="wp-block-group ministry-card">
    <h3 class="wp-block-heading">Knights of Columbus</h3>
    <p class="meta"><strong>Meets:</strong> 2nd Monday, 7:30 PM · Parish hall</p>
    <p class="wp-block-paragraph">One or two sentences.</p>
    <p><a class="text-link" href="/knights-of-columbus/">Learn more</a></p>
  </div>
</div>

<!-- Mass schedule cards -->
<div class="wp-block-group is-layout-grid schedule alignwide">
  <div class="wp-block-group schedule__card"><h3 class="wp-block-heading">Sunday</h3>
    <ul class="wp-block-list times-list"><li><span>9:00 AM<span class="lang">English</span></span><time>Sun</time></li></ul></div>
</div>

<!-- Day cards (compact week view) -->
<div class="wp-block-group is-layout-grid days"><div class="wp-block-group day"><h4>Monday</h4><p>8:30 AM</p></div></div>

<!-- People -->
<div class="wp-block-group is-layout-grid people alignwide">
  <div class="wp-block-group person"><!--img:pastor-portrait|Rev. Daniel Moreau--><div class="person__body"><h3 class="wp-block-heading">Rev. Daniel Moreau</h3><p class="person__role">Pastor</p><p class="wp-block-paragraph">Short bio.</p><p><a href="mailto:pastor@stcolumbatoronto.ca">pastor@stcolumbatoronto.ca</a> · ext. 22</p></div></div>
</div>
<!-- compact variant: add class person--compact to .person -->

<!-- Numbered steps -->
<ol class="wp-block-list steps"><li><h3 class="wp-block-heading">Contact the office</h3><p>…</p></li></ol>

<!-- Info box (also infobox--dark) -->
<div class="wp-block-group infobox"><h3 class="wp-block-heading">Good to know</h3><p class="wp-block-paragraph">…</p></div>

<!-- Stats strip -->
<div class="wp-block-group is-layout-grid stats alignwide"><div class="wp-block-group stat"><strong>1,200</strong><span>families</span></div></div>

<!-- Timeline -->
<ul class="wp-block-list timeline"><li><time>1954</time><h3 class="wp-block-heading">Parish founded</h3><p>…</p></li></ul>

<!-- Quote band (full width, navy) -->
<div class="wp-block-group alignfull quote-band"><blockquote class="wp-block-quote"><p>“…”</p><cite>St. Columba</cite></blockquote></div>

<!-- CTA banners (photo background) -->
<div class="wp-block-group is-layout-grid cta-grid alignwide">
  <div class="wp-block-group cta" style="--cta-img:url('<!--img-src:youth-group-park-->')"><h3 class="wp-block-heading">Get involved</h3><p>…</p><div class="wp-block-buttons"><div class="wp-block-button is-style-light"><a class="wp-block-button__link wp-element-button" href="/ministries/">Find a ministry</a></div></div></div>
</div>

<!-- Gallery -->
<div class="wp-block-group is-layout-grid gallery alignwide"><!--img:slug|alt--><!--img:slug|alt--></div>

<!-- Request tiles (contact-style choices) -->
<div class="wp-block-group is-layout-grid request-tiles alignwide"><div class="wp-block-group request-tile"><h3 class="wp-block-heading">Request a Mass intention</h3><p>…</p><p><a class="text-link" href="/mass-intentions/">Request</a></p></div></div>

<!-- Pills (languages, tags) -->
<ul class="wp-block-list pill-list"><li>English</li><li>Español</li></ul>

<!-- Bulletin list -->
<ul class="wp-block-list bulletins"><li><span><time>September 13, 2026</time> — 24th Sunday in Ordinary Time</span><a class="btn btn--small" href="/wp-content/uploads/2026/09/sample-bulletin.pdf">PDF</a></li></ul>

<!-- News list -->
<ul class="wp-block-list news-list"><li><time>September 10, 2026</time><a href="/news/#slug">Headline</a><p>One-line summary.</p></li></ul>

<!-- Badge -->
<span class="badge badge--gold">New</span>

<!-- Events pulled from src/events.json (do not hand-write event cards) -->
<!--events:upcoming:3-->   <!--events:all-->   <!--events:calendar-->

<!-- Forms (ONLY on: contact, register, prayer-requests, mass-intentions, volunteer, hall-rentals) -->
<form class="contact-form" name="prayer-request" method="POST" data-netlify="true" netlify-honeypot="bot-field" action="/prayer-requests/?sent=1">
  <input type="hidden" name="form-name" value="prayer-request">
  <p class="hidden-field"><label>Leave this empty <input name="bot-field"></label></p>
  <div class="contact-form__row"><label>Your name <input type="text" name="name" autocomplete="name" required></label><label>Email <input type="email" name="email" autocomplete="email" required></label></div>
  <label>Your request <textarea name="message" required></textarea></label>
  <label class="check"><input type="checkbox" name="publish" value="yes"> You may share this intention at Mass</label>
  <button type="submit" class="btn">Send request</button>
  <p class="contact-form__note">Requests are read by the parish office. On WordPress this is a Form block.</p>
</form>
<div class="contact-form__thanks" hidden><p class="wp-block-paragraph"><strong>Thank you.</strong> Your message has been received.</p></div>
```

## 3. Parish facts (use these exactly — everything is fictional but consistent)

* **St. Columba Parish**, 1240 Columba Avenue, Toronto, ON M4K 2R6 (East York). Founded 1954. Archdiocese of Toronto.
  Phone 416-555-0142 · office@stcolumbatoronto.ca · Office Mon–Fri 9:00 AM–4:00 PM (closed 12–1).
  Charitable registration no. 10000 0000 RR0001 (placeholder). Parish hall seats 220; accessible entrance on the east side; elevator to the hall; hearing loop.
* **Clergy & staff**: Rev. Daniel Moreau, Pastor (ext. 22, pastor@…); Rev. Joseph Nguyen, Associate Pastor (ext. 23); Deacon Paul Ferreira (ext. 24); Teresa Alvarez, Office Manager (ext. 21); Ann Marie O'Connor, Parish Secretary (ext. 20, office@…); Marcus Lee, Youth & Young Adult Minister (ext. 27, youth@…); Claire Dubois, Director of Music (ext. 26, music@…); Sr. Agnes Ibeh, SSND, Pastoral Associate & Catechetical Coordinator (ext. 25, faith@…); Luis Ortega, Custodian.
  Use `pastor-portrait` for Fr. Moreau, `priest-with-book` for Fr. Nguyen, `priest-altar-green` for Deacon Ferreira; other staff have no photo (use the compact person card with no image).
* **Mass times**: Saturday 5:00 PM (Sunday Vigil); Sunday 9:00 AM, 11:00 AM (livestreamed, choir), 1:00 PM in Spanish (1st & 3rd Sundays) / in Tagalog (2nd Sundays) / in Italian (4th Sundays), 5:00 PM (youth & young adult Mass).
  Weekdays Mon–Fri 8:30 AM; Wednesday also 7:00 PM; Saturday 9:00 AM. Holy days: 8:30 AM, 11:00 AM, 7:00 PM. Statutory holidays: 9:00 AM only.
  **Confessions**: Saturday 3:30–4:30 PM; Wednesday 6:15–6:45 PM; by appointment. **Adoration**: Thursdays 9:00 AM–12:00 PM; First Fridays 7:00–8:00 PM with Benediction. **Rosary** weekdays after the 8:30 Mass; Novena to Our Lady of Perpetual Help Wednesdays 7:30 PM.
* **Languages** in the parish: English, Spanish, Tagalog, Italian, Portuguese, Tamil communities.
* **Giving**: online through the Archdiocese of Toronto secure portal (link `https://community.archtoronto.org/` labelled "Give online"), Pre-Authorized Giving (PAG) form (`/wp-content/uploads/2026/09/sample-form.pdf`), offertory envelopes, e-transfer to giving@stcolumbatoronto.ca, ShareLife (`https://sharelife.org/`), bequests. Tax receipts issued each February.
* **Real external links you may use** (and only these): https://www.archtoronto.org/ · https://www.archtoronto.org/en/outreach/safe-environment/ · https://sharelife.org/ · https://www.catholic-cemeteries.ca/ · https://readings.livingwithchrist.ca/ · https://www.vocationstoronto.ca/ · https://www.orat.ca/ · https://www.bishopreportingsystem.ca/ · https://www.ontario.ca/page/accessibility-ontario · https://www.vatican.va/archive/ENG0015/_INDEX.HTM (Catechism) · https://www.usccb.org/ · https://www.cccb.ca/ · https://formed.org/ · https://alphacanada.org/ · https://www.tcdsb.org/ (Toronto Catholic District School Board) · https://www.kofc.org/ · https://www.cwl.ca/ · https://www.ssvp.ca/ · https://devp.org/ (Development and Peace) · https://www.youtube.com/ · https://dailytvmass.com/ · https://www.google.com/maps
  External links get `target="_blank" rel="noopener"`.
* **Internal links** — only to these paths (they all exist or are being written):
  `/` `/about/` `/new-here/` `/clergy-and-staff/` `/history/` `/parish-councils/` `/gallery/` `/questions/` `/our-faith/` `/becoming-catholic/` `/beliefs-and-teachings/` `/prayers/` `/pastoral-plan/` `/archdiocese-of-toronto/` `/chaplaincies/` `/refugee-sponsorship/` `/vocations/` `/safe-environment/` `/volunteer-screening/` `/accessibility/` `/report-misconduct/` `/privacy/` `/parish-school/` `/hall-rentals/` `/register/` `/mass-times/` `/livestream/` `/adoration/` `/devotions/` `/mass-intentions/` `/prayer-requests/` `/music-ministry/` `/reconciliation/` `/contact/` `/give/` `/bulletin/` `/news/` `/events/` `/sacraments/` `/baptism/` `/first-communion/` `/confirmation/` `/marriage/` `/holy-orders/` `/anointing-of-the-sick/` `/funerals/` `/sacramental-preparation/` `/papal-blessings/` `/ministries/` `/youth-ministry/` `/young-adults/` `/children-and-families/` `/knights-of-columbus/` `/catholic-womens-league/` `/st-vincent-de-paul/` `/liturgical-ministries/` `/faith-formation/` `/cultural-communities/` `/outreach/` `/seniors/` `/volunteer/` `/legion-of-mary/` `/bereavement-ministry/` `/altar-servers/` `/hospitality/` `/marriage-and-family/` `/credits/` `/site-guide/` `/style-guide/`

## 4. Photos (slug → subject). Use `<!--img:slug|alt-->`; pick the most fitting; don't reuse the same photo more than ~3 times site-wide.

Toronto churches: `hero-church-interior` (St. Michael's Cathedral nave during Mass), `cathedral-nave`, `cathedral-spire` (portrait), `cathedral-exterior`, `stained-glass-window` (portrait), `basilica-facade` (St. Paul's), `basilica-interior`, `basilica-nave`, `parish-church-exterior` (St. Basil's), `parish-church-spire` (portrait), `neighbourhood-church` (St. Helen's façade, portrait), `church-tower` (portrait).
Other churches: `oratory-nave` (portrait), `votive-candles-red`, `notre-dame-altar`, `notre-dame-nave`.
Toronto: `toronto-skyline`, `toronto-skyline-night`, `toronto-autumn-street`, `high-park-autumn`.
Liturgy/devotion: `adoration-monstrance`, `chalice-paten`, `adoration-altar`, `candles-chapel` (portrait), `candles-rows`, `stained-glass-triptych`, `mass-congregation`, `mass-pews`, `mass-elevation`, `church-light-crucifix`, `holy-communion`, `chalice-hands`, `altar-servers`, `rosary-hands`, `rosary-pew`, `rosary-candle`, `elderly-hands-rosary` (portrait), `confessional`.
Sacraments: `baptism-font` (portrait), `baptism-pouring` (portrait), `baptism-baby-water` (portrait), `first-communion-girls` (portrait), `first-communion-candle` (portrait), `first-communion-hands` (portrait), `wedding-aisle` (portrait), `wedding-altar`, `wedding-vows` (portrait).
People: `parish-choir`, `youth-choir`, `boys-choir` (portrait), `food-bank-volunteers`, `free-food-table` (portrait), `donation-box`, `youth-group-park`, `youth-friends`, `teens-walking`, `bible-study-women` (portrait), `bible-reading-pews`, `young-adults-pews`, `young-adults-guitar`, `children-blessing`, `volunteer-elderly`, `senior-laughing`, `volunteer-tablet`, `priest-altar-green` (portrait), `pastor-portrait`, `priest-with-book`, `seminarian-reading` (portrait), `children-stained-glass`, `mother-child-church`, `family-celebration`, `priest-greeting`.

Portrait photos work best in `media-row` columns or `people` cards; landscape photos for hero_image, cards and galleries.

## 5. Writing standards

* Warm, clear, pastoral, practical. Second person ("you"), plain English, Canadian spelling (centre, parish programme → use "program"), no jargon without a gloss, no exclamation marks in body text.
* Every page: 400–900 words of *real, specific* content (times, fees, who to contact, what to bring, how long it takes, what happens next). A pastor reading it should think "this is exactly what our page should say".
* Structure: opening paragraph (`lede` in front matter is separate) → 2–5 sections with h2 → practical details (steps/FAQ/infobox) → closing "Questions? Contact …" paragraph or CTA buttons. Use at least one photo per page (most pages: 2–3) and at least one non-paragraph component (FAQ, steps, cards, columns, infobox, table).
* Fees/offerings are "suggested" and modest (e.g. Mass intention offering $10; baptism no fee, donation welcome; wedding church offering $500 incl. musician; hall rental $350/evening). Timelines: baptism prep 1 evening; marriage prep contact 12 months ahead, course required; confirmation Grade 7; First Communion Grade 2; OCIA September–Easter Vigil.
* Archdiocese of Toronto realities to reflect: Safe Environment / Strengthening the Caring Community policy, volunteer screening (police check for high-risk ministries), ShareLife annual appeal, Catholic Cemeteries & Funeral Services, Office for Refugees (ORAT), Formation for Discipleship, Living with Christ daily readings, Toronto Catholic District School Board schools.
* Ministry pages: what the group does, who it's for, when/where it meets, how to join, the contact (a fictional lay coordinator with first name + surname and a role email like kofc@stcolumbatoronto.ca), 2–4 FAQs, a photo, and a "Related" button row.
* Alt text describes the photo (not the page). Never claim a stock photo shows St. Columba specifically — write alt text like "Parishioners praying the rosary" not "St. Columba parishioners…".
* Do not invent additional pages or links; do not write the events calendar or event cards by hand (use the `<!--events:…-->` placeholders where your assignment says).
* All text must be original — do not copy paragraphs from other parish websites.
