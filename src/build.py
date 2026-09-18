#!/usr/bin/env python3
"""
Static site generator for the parish demo site.

  src/site.json          – parish details, navigation, footer
  src/templates/*.html   – page chrome (header / nav / footer). On WordPress
                           this is the theme's header & footer template parts.
  src/content/*.html     – one file per page. A small front-matter block, then
                           the page body written as WordPress core-block markup,
                           so the same file can be pasted into the block editor.

Output goes to the repo root as pretty URLs (/events/index.html) so Netlify can
publish the folder as-is with no build step.

Usage:  python3 src/build.py            build everything
        python3 src/build.py --check    build, then verify internal links/images
"""
import json, re, sys, html, datetime, hashlib
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "src"
CONTENT = SRC / "content"
TEMPLATES = SRC / "templates"

site = json.loads((SRC / "site.json").read_text(encoding="utf-8"))
EVENTS = json.loads((SRC / "events.json").read_text(encoding="utf-8")) if (SRC / "events.json").exists() else []
PHOTOS = json.loads((SRC / "photos-report.json").read_text(encoding="utf-8")) if (SRC / "photos-report.json").exists() else {}
PHOTO_META = {p["slug"]: p for p in json.loads((SRC / "photos.json").read_text(encoding="utf-8"))} if (SRC / "photos.json").exists() else {}
UPLOADS = "/wp-content/uploads/2026/09/"
TODAY = datetime.date.today().isoformat()
# The demo is pinned to a fixed "today" so sample events always read as upcoming.
DEMO_TODAY = datetime.date.fromisoformat(site.get("demo_today", TODAY))

# ---------------------------------------------------------------- helpers
def read_page(path: Path):
    """Split '---' front matter from the body. Front matter is `key: value`."""
    text = path.read_text(encoding="utf-8")
    meta = {}
    body = text
    if text.startswith("---"):
        _, fm, body = text.split("---", 2)
        for line in fm.strip().splitlines():
            if ":" in line:
                k, v = line.split(":", 1)
                meta[k.strip()] = v.strip()
    slug = path.stem
    meta.setdefault("slug", slug)
    meta["path"] = "/" if slug == "index" else f"/{slug}/"
    meta.setdefault("title", slug.replace("-", " ").title())
    meta.setdefault("template", "page")
    meta.setdefault("description", site["description"])
    return meta, body.strip()

def esc(s):  # attribute-safe text
    return html.escape(s, quote=True)

def render(template: str, ctx: dict) -> str:
    """Tiny {{key}} substitution — no logic, keeps templates readable."""
    def sub(m):
        key = m.group(1).strip()
        val = ctx.get(key, "")
        return val if isinstance(val, str) else str(val)
    return re.sub(r"\{\{\s*([\w.]+)\s*\}\}", sub, template)

def is_current(href: str, path: str) -> bool:
    return href.split("#")[0] == path

def nav_html(current: str) -> str:
    """Primary navigation: nested <ul>, any depth. Desktop = hover dropdowns
    (3rd level flies out sideways), mobile = accordion (CSS/JS). Mirrors a
    WordPress Navigation block with Submenu items."""
    def items(nodes, depth=0):
        out = []
        for item in nodes:
            kids = item.get("children", [])
            cls = ' class="has-sub"' if kids else ""
            cur = ' aria-current="page"' if is_current(item["href"], current) else ""
            ext = ' target="_blank" rel="noopener"' if item["href"].startswith("http") else ""
            caret = '<svg class="caret" viewBox="0 0 12 12" aria-hidden="true"><path d="M1.5 4L6 8l4.5-4"/></svg>' if kids else ""
            out.append(f'<li{cls}><a href="{esc(item["href"])}"{cur}{ext}>{esc(item["label"])}{caret}</a>')
            if kids:
                out.append(f'<button class="nav-sub-toggle" type="button" aria-expanded="false" aria-label="Open {esc(item["label"])} menu"><svg viewBox="0 0 12 12" aria-hidden="true"><path d="M1.5 4L6 8l4.5-4"/></svg></button>')
                out.append("<ul>" + "".join(items(kids, depth + 1)) + "</ul>")
            out.append("</li>")
        return out
    out = ["<ul>"] + items(site["nav"])
    cta = site.get("nav_cta")
    if cta:
        out.append(f'<li class="nav__cta"><a href="{esc(cta["href"])}">{esc(cta["label"])}</a></li>')
    out.append("</ul>")
    return "\n".join(out)

def section_links(meta: dict, pages: list) -> str:
    """'In this section' strip: sibling pages that share the same `section`."""
    sec = meta.get("section")
    if not sec:
        return ""
    sibs = [p for p in pages if p.get("section") == sec and p.get("template") != "home"]
    if len(sibs) < 2:
        return ""
    items = "".join(
        f'<li><a href="{esc(p["path"])}"{" aria-current=\"page\"" if p["path"] == meta["path"] else ""}>{esc(p["title"])}</a></li>'
        for p in sorted(sibs, key=lambda p: (int(p.get("order", 999)), p["title"]))
    )
    return f'<nav class="section-nav" aria-label="In this section"><p class="section-nav__title">In this section</p><ul>{items}</ul></nav>'

def footer_html() -> str:
    f = site["footer"]
    cols = []
    for col in f["columns"]:
        links = "".join(f'<li><a href="{esc(l["href"])}"{" target=\"_blank\" rel=\"noopener\"" if l["href"].startswith("http") else ""}>{esc(l["label"])}</a></li>' for l in col["links"])
        cols.append(f'<div class="site-footer__col"><h2 class="site-footer__heading">{esc(col["heading"])}</h2><ul>{links}</ul></div>')
    return "\n".join(cols)

def breadcrumb(meta: dict) -> str:
    sec = meta.get("section")
    sec_href = meta.get("section_href")
    if sec and sec_href:
        return f'<a href="{esc(sec_href)}">{esc(sec)}</a><span class="sep" aria-hidden="true">/</span>{esc(meta["title"])}'
    if sec:
        return f'{esc(sec)}<span class="sep" aria-hidden="true">/</span>{esc(meta["title"])}'
    return esc(meta["title"])

def schema_org(meta: dict) -> str:
    """JSON-LD: Church on the home page, BreadcrumbList on sub-pages, Event
    graph on the events page."""
    s = site
    if meta["template"] == "home":
        data = {
            "@context": "https://schema.org",
            "@type": "Church",
            "name": s["name"],
            "url": s["url"] + "/",
            "telephone": s["phone"],
            "email": s["email"],
            "address": {"@type": "PostalAddress", "streetAddress": s["address"]["street"],
                        "addressLocality": s["address"]["city"], "addressRegion": s["address"]["region"],
                        "postalCode": s["address"]["postal"], "addressCountry": "CA"},
            "geo": {"@type": "GeoCoordinates", "latitude": s["geo"]["lat"], "longitude": s["geo"]["lng"]},
            "hasMap": s["map_url"],
            "image": s["url"] + s["og_image"],
            "parentOrganization": {"@type": "Organization", "name": "Archdiocese of Toronto", "url": "https://www.archtoronto.org/"},
            "sameAs": [s.get("facebook"), s.get("instagram"), s.get("youtube")],
            "openingHoursSpecification": s.get("office_hours_schema", []),
        }
        return json.dumps(data, ensure_ascii=False)
    crumbs = [{"@type": "ListItem", "position": 1, "name": "Home", "item": s["url"] + "/"}]
    if meta.get("section") and meta.get("section_href") and meta["section_href"] != meta["path"]:
        crumbs.append({"@type": "ListItem", "position": 2, "name": meta["section"], "item": s["url"] + meta["section_href"]})
    crumbs.append({"@type": "ListItem", "position": len(crumbs) + 1, "name": meta["title"], "item": s["url"] + meta["path"]})
    graph = [{"@type": "BreadcrumbList", "itemListElement": crumbs}]
    if meta["slug"] == "events":
        for ev in EVENTS:
            if "date" not in ev:
                continue
            start = ev["date"] + ("T" + ev["start"] + ":00-04:00" if ev.get("start") else "")
            item = {"@type": "Event", "name": ev["title"], "startDate": start,
                    "eventStatus": "https://schema.org/EventScheduled",
                    "eventAttendanceMode": "https://schema.org/OfflineEventAttendanceMode",
                    "location": {"@type": "Place", "name": ev.get("location", s["name"]), "address": s["address"]["full"]},
                    "organizer": {"@type": "Organization", "name": s["name"], "url": s["url"] + "/"},
                    "description": ev.get("summary", "")}
            if ev.get("end"):
                item["endDate"] = ev["date"] + "T" + ev["end"] + ":00-04:00"
            graph.append(item)
    return json.dumps({"@context": "https://schema.org", "@graph": graph}, ensure_ascii=False)


# ---------------------------------------------------------------- images
def photo_url(slug: str, width: int = 1024) -> str:
    """URL of the variant closest to `width` (falls back to the full image)."""
    info = PHOTOS.get(slug)
    if not info:
        return UPLOADS + slug + ".jpg"
    for w, name in info["variants"]:
        if w >= width:
            return UPLOADS + name
    return UPLOADS + slug + ".jpg"

def img_figure(slug: str, alt: str = "", classes: str = "", sizes: str = "") -> str:
    """A WordPress Image block with srcset from the generated variants."""
    info = PHOTOS.get(slug)
    if not info:
        return f'<!-- unknown photo: {slug} -->'
    alt = alt or PHOTO_META.get(slug, {}).get("alt", "")
    parts = [f"{UPLOADS}{n} {w}w" for w, n in info["variants"]] + [f"{UPLOADS}{slug}.jpg {info['width']}w"]
    sizes = sizes or "(max-width: 860px) calc(100vw - 40px), 740px"
    src = photo_url(slug, 1024)
    # width/height of the src variant keep the aspect ratio stable before load
    w = 1024 if info["width"] > 1024 else info["width"]
    h = round(info["height"] * w / info["width"])
    cls = "wp-block-image size-large" + (" " + classes if classes else "")
    return (f'<figure class="{cls}"><img src="{src}" srcset="{", ".join(parts)}" sizes="{sizes}" '
            f'alt="{esc(alt)}" width="{w}" height="{h}" loading="lazy" decoding="async"></figure>')

def image_placeholders(body: str) -> str:
    """<!--img:slug|alt|classes|sizes--> -> Image block; <!--img-src:slug|width--> -> a URL."""
    def fig(m):
        bits = [b.strip() for b in m.group(1).split("|")]
        bits += [""] * (4 - len(bits))
        return img_figure(bits[0], bits[1], bits[2], bits[3])
    body = re.sub(r"<!--img:([^>]+?)-->", fig, body)
    body = re.sub(r"<!--img-src:([\w-]+)(?:\|(\d+))?-->", lambda m: photo_url(m.group(1), int(m.group(2) or 1024)), body)
    return body

# ---------------------------------------------------------------- events
MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
WEEKDAYS = ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]

def fmt_time(t: str) -> str:
    h, m = (int(x) for x in t.split(":"))
    suffix = "AM" if h < 12 else "PM"
    h12 = h % 12 or 12
    return f"{h12}:{m:02d} {suffix}"

def gcal_link(ev: dict) -> str:
    """'Add to Google Calendar' template link (works on any plan, no JS)."""
    from urllib.parse import urlencode
    start = ev["date"].replace("-", "") + "T" + ev.get("start", "09:00").replace(":", "") + "00"
    end = ev["date"].replace("-", "") + "T" + ev.get("end", ev.get("start", "10:00")).replace(":", "") + "00"
    q = {"action": "TEMPLATE", "text": ev["title"], "dates": f"{start}/{end}", "ctz": "America/Toronto",
         "details": ev.get("summary", ""), "location": ev.get("location", site["name"]) + ", " + site["address"]["full"]}
    return "https://calendar.google.com/calendar/render?" + urlencode(q)

def dated_events():
    evs = [e for e in EVENTS if "date" in e and datetime.date.fromisoformat(e["date"]) >= DEMO_TODAY]
    return sorted(evs, key=lambda e: (e["date"], e.get("start", "")))

def event_card(ev: dict, featured=False) -> str:
    d = datetime.date.fromisoformat(ev["date"])
    when = WEEKDAYS[(d.weekday() + 1) % 7] + f", {MONTHS[d.month - 1]} {d.day}"
    if ev.get("start"):
        when += " · " + fmt_time(ev["start"]) + (" – " + fmt_time(ev["end"]) if ev.get("end") else "")
    links = ""
    if ev.get("href"):
        links += f'<a href="{esc(ev["href"])}">Details</a>'
    links += f'<a class="add-cal" href="{esc(gcal_link(ev))}" target="_blank" rel="noopener">Add to calendar</a>'
    cls = "wp-block-group event" + (" event--featured" if featured else "")
    return (f'<div class="{cls}"><div class="event__date"><span class="m">{MONTHS[d.month - 1]}</span><span class="d">{d.day}</span></div>'
            f'<div class="event__body"><h3 class="wp-block-heading">{esc(ev["title"])}</h3>'
            f'<p class="event__when">{when}' + (f' · {esc(ev["location"])}' if ev.get("location") else "") + '</p>'
            f'<p>{esc(ev.get("summary", ""))}</p><p class="event__links">{links}</p></div></div>')

def events_placeholders(body: str) -> str:
    """Replace <!--events:upcoming:N-->, <!--events:all--> and <!--events:calendar-->
    with markup generated from src/events.json (one source of truth)."""
    def upcoming(m):
        n = int(m.group(1))
        evs = dated_events()[:n]
        return '<div class="wp-block-group is-layout-grid events alignwide">' + "".join(event_card(e, i == 0 and n > 3) for i, e in enumerate(evs)) + "</div>"
    body = re.sub(r"<!--events:upcoming:(\d+)-->", upcoming, body)
    body = body.replace("<!--events:all-->", '<div class="wp-block-group is-layout-grid events alignwide">' + "".join(event_card(e) for e in dated_events()) + "</div>")
    if "<!--events:calendar-->" in body:
        data = json.dumps(EVENTS, ensure_ascii=False).replace("'", "&#39;")
        start = DEMO_TODAY.strftime("%Y-%m")
        cal = (f'<div class="wp-block-group alignwide month-cal" id="eventsCalendar" data-events=\'{data}\' data-start="{start}">'
               f'<div class="month-cal__head"><h3 class="wp-block-heading month-cal__month">Calendar</h3>'
               f'<div class="month-cal__nav"><button type="button" class="month-cal__prev" aria-label="Previous month">&lsaquo;</button>'
               f'<button type="button" class="month-cal__next" aria-label="Next month">&rsaquo;</button></div></div>'
               f'<div class="month-cal__grid" role="grid" aria-label="Parish calendar"></div>'
               f'<ul class="month-cal__list"></ul>'
               f'<ul class="month-cal__legend"><li class="parish"><i></i>Parish events</li><li class="liturgy"><i></i>Liturgy &amp; feasts</li><li class="devotion"><i></i>Devotions</li><li class="youth"><i></i>Youth &amp; young adults</li><li class="formation"><i></i>Faith formation</li><li class="community"><i></i>Community &amp; outreach</li></ul>'
               f'<p class="month-cal__fallback">The interactive calendar needs JavaScript. See the list of upcoming events below.</p></div>')
        body = body.replace("<!--events:calendar-->", cal)
    return body

# ---------------------------------------------------------------- build
def build():
    pages = []
    bodies = {}
    for f in sorted(CONTENT.glob("*.html")):
        meta, body = read_page(f)
        pages.append(meta)
        bodies[meta["slug"]] = body

    tpl = {p.stem: p.read_text(encoding="utf-8") for p in TEMPLATES.glob("*.html")}
    # cache-busting query on the shared assets, from their content hash
    asset_v = {name: hashlib.sha1((ROOT / "assets" / name).read_bytes()).hexdigest()[:8] for name in ("site.css", "site.js")}
    written = []
    for meta in pages:
        body = image_placeholders(events_placeholders(bodies[meta["slug"]]))
        # hero_image / image in front matter may be a photo slug
        for key, width in (("hero_image", 1536), ("image", 1024)):
            if meta.get(key) and not meta[key].startswith("/") and not meta[key].startswith("http"):
                meta[key] = photo_url(meta[key], width)
        template = tpl[meta["template"]]
        og_image = meta.get("image", site["og_image"])
        ctx = {
            "site_name": esc(site["name"]),
            "site_tagline": esc(site["tagline"]),
            "site_city": esc(site["city"]),
            "site_url": site["url"],
            "site_phone": esc(site["phone"]),
            "site_email": esc(site["email"]),
            "site_address": esc(site["address"]["full"]),
            "site_map_url": esc(site["map_url"]),
            "site_office_hours": esc(site.get("office_hours", "")),
            "site_facebook": esc(site.get("facebook", "#")),
            "site_instagram": esc(site.get("instagram", "#")),
            "site_youtube": esc(site.get("youtube", "#")),
            "page_title": esc(meta["title"]),
            "head_title": esc(meta["title"] + " | " + site["name"]) if meta["template"] != "home" else esc(site["name"] + " | " + site["city"]),
            "page_description": esc(meta["description"]),
            "page_path": meta["path"],
            "page_eyebrow": breadcrumb(meta),
            "page_lede": esc(meta.get("lede", "")),
            "page_lede_html": f'<p class="page-hero__lede">{esc(meta["lede"])}</p>' if meta.get("lede") else "",
            "page_hero_image": esc(meta.get("hero_image", "")),
            "page_hero_class": " page-hero--image" if meta.get("hero_image") else "",
            "page_hero_style": f' style="--hero-img:url(\'{esc(meta["hero_image"])}\')"' if meta.get("hero_image") else "",
            "og_image": site["url"] + og_image,
            "canonical": site["url"] + meta["path"],
            "nav": nav_html(meta["path"]),
            "section_nav": section_links(meta, pages),
            "footer_columns": footer_html(),
            "schema_org": schema_org(meta),
            "content": body,
            "body_class": meta.get("body_class", ""),
            "year": str(datetime.date.today().year),
            "css_v": asset_v["site.css"],
            "js_v": asset_v["site.js"],
        }
        out = render(template, ctx)
        dest = ROOT / "index.html" if meta["slug"] == "index" else ROOT / meta["slug"] / "index.html"
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(out, encoding="utf-8")
        written.append(meta)

    # search index for the header search (title, url, section, description)
    index = [{"t": m["title"], "u": m["path"], "s": m.get("section", ""), "d": m.get("description", "")}
             for m in written if m.get("noindex") != "true"]
    (ROOT / "assets/search.json").write_text(json.dumps(index, ensure_ascii=False), encoding="utf-8")

    # Netlify serves /404.html for unknown paths
    if "404" in bodies:
        pass  # rendered as /404/index.html above; also copy to root
        (ROOT / "404.html").write_text((ROOT / "404" / "index.html").read_text(encoding="utf-8"), encoding="utf-8")

    # sitemap + robots
    urls = "".join(
        f'  <url><loc>{site["url"]}{m["path"]}</loc><lastmod>{TODAY}</lastmod><changefreq>{"weekly" if m["path"] in ("/", "/events/", "/bulletin/") else "monthly"}</changefreq><priority>{"1.0" if m["path"] == "/" else "0.7"}</priority></url>\n'
        for m in written if m.get("noindex") != "true")
    (ROOT / "sitemap.xml").write_text(f'<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n{urls}</urlset>\n', encoding="utf-8")
    (ROOT / "robots.txt").write_text(f"User-agent: *\nAllow: /\nSitemap: {site['url']}/sitemap.xml\n", encoding="utf-8")
    print(f"built {len(written)} pages")
    return written

def check(pages):
    """Verify every internal href/src resolves to a page or file in the repo."""
    known = {p["path"] for p in pages}
    missing = {}   # target -> set of pages that reference it
    for p in pages:
        f = ROOT / "index.html" if p["slug"] == "index" else ROOT / p["slug"] / "index.html"
        htmltext = f.read_text(encoding="utf-8")
        targets = [u for u in re.findall(r'(?:href|src)="([^"]+)"', htmltext)]
        for srcset in re.findall(r'srcset="([^"]+)"', htmltext):
            targets += [part.strip().split(" ")[0] for part in srcset.split(",")]
        for url in targets:
            u = url.split("#")[0].split("?")[0]
            if not u or u.startswith(("http", "mailto:", "tel:", "data:")):
                continue
            ok = (u in known) if u.endswith("/") else (ROOT / u.lstrip("/")).exists()
            if not ok:
                missing.setdefault(u, set()).add(p["path"])
    for u in sorted(missing):
        refs = sorted(missing[u])
        print(f"  missing {u}  <- {', '.join(refs[:4])}{' …' if len(refs) > 4 else ''} ({len(refs)} page(s))")
    print(f"link check: {len(missing)} missing target(s)")
    return len(missing)

if __name__ == "__main__":
    pages = build()
    if "--check" in sys.argv:
        sys.exit(1 if check(pages) else 0)
