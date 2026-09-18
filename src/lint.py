#!/usr/bin/env python3
"""Content lint: enforces the CONTENT-GUIDE contract on src/content/*.html."""
import re, sys, json
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
CONTENT = ROOT / "src/content"
site = json.loads((ROOT / "src/site.json").read_text())
photos = {p["slug"] for p in json.loads((ROOT / "src/photos.json").read_text())}
guide = (ROOT / "src/CONTENT-GUIDE.md").read_text()
allowed_internal = set(re.findall(r"`(/[\w-]*/?)`", guide.split("**Internal links**")[1].split("## 4.")[0]))
allowed_external = set(re.findall(r"https?://[^\s·)]+", guide.split("**Real external links you may use**")[1].split("External links get")[0]))
pages = {p.stem for p in CONTENT.glob("*.html")}

problems = 0
def warn(page, msg):
    global problems
    problems += 1
    print(f"  {page}: {msg}")

EXEMPT = {"credits", "index"}   # generated credits page; the home page owns its hero <h1>
for f in sorted(CONTENT.glob("*.html")):
    if f.stem in EXEMPT:
        continue
    text = f.read_text()
    if not text.startswith("---"):
        warn(f.name, "no front matter"); continue
    _, fm, body = text.split("---", 2)
    meta = dict(l.split(":", 1) for l in fm.strip().splitlines() if ":" in l)
    meta = {k.strip(): v.strip() for k, v in meta.items()}
    if "title" not in meta: warn(f.name, "missing title")
    if f.stem not in ("index", "404") and "description" not in meta: warn(f.name, "missing description")
    if re.search(r"<script|<style", body, re.I): warn(f.name, "script/style tag")
    if re.search(r"<h1[\s>]", body): warn(f.name, "<h1> in body")
    for m in re.finditer(r'style="([^"]*)"', body):
        if "--cta-img" not in m.group(1) and "--hero-img" not in m.group(1) and f.stem != "index":
            warn(f.name, f"inline style: {m.group(1)[:60]}")
    for m in re.finditer(r'href="([^"#]+)(#[^"]*)?"', body):
        u = m.group(1)
        if u.startswith("http"):
            if not any(u.startswith(a.rstrip("/")) for a in allowed_external) and "stcolumbatoronto" not in u and "youtube" not in u and "maps.google" not in u and "community.archtoronto" not in u:
                warn(f.name, f"external link not in allowed list: {u}")
        elif u.startswith("/"):
            base = u.split("?")[0]
            if base.startswith("/wp-content/"):
                if not (ROOT / base.lstrip("/")).exists(): warn(f.name, f"missing file {base}")
            elif base not in allowed_internal and base.strip("/") not in pages:
                warn(f.name, f"internal link not in list: {base}")
        elif u.startswith("mailto:") or u.startswith("tel:") or u == "#":
            pass
        else:
            warn(f.name, f"odd href: {u}")
    for m in re.finditer(r"<!--img:([^|>]+)", body):
        if m.group(1).strip() not in photos: warn(f.name, f"unknown photo {m.group(1).strip()}")
    for m in re.finditer(r"<!--img:[^|]+\|\s*(\|| -->|-->)", body):
        warn(f.name, "image without alt text")
    for key in ("hero_image", "image"):
        v = meta.get(key)
        if v and not v.startswith("/") and v not in photos: warn(f.name, f"{key} unknown photo {v}")
    words = len(re.sub(r"<[^>]+>", " ", body).split())
    if f.stem not in ("index", "404", "credits") and words < 350: warn(f.name, f"thin page ({words} words)")
    if body.count("<form") and f.stem not in ("contact", "register", "prayer-requests", "mass-intentions", "volunteer", "hall-rentals", "style-guide", "liturgical-ministries", "papal-blessings"):
        warn(f.name, "form on a page not expected to have one")
print(f"lint: {len(pages)} pages, {problems} problem(s)")
sys.exit(1 if problems else 0)
