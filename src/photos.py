#!/usr/bin/env python3
"""
Photo pipeline.

  src/photos.json  – manifest: [{slug, url, source, page_url, credit, license, use, alt}]
  downloads each original once (cached in the scratchpad), then writes
  WordPress-style sizes to wp-content/uploads/2026/09/:
      slug.jpg              (full, max 1920px wide)
      slug-480x###.jpg  slug-768x###.jpg  slug-1024x###.jpg  slug-1536x###.jpg
  and regenerates src/content/credits.html from the manifest.

Usage: python3 src/photos.py            process every photo in the manifest
       python3 src/photos.py --only slug  process one
"""
import json, sys, io, urllib.request, hashlib
from pathlib import Path
from PIL import Image, ImageOps

ROOT = Path(__file__).resolve().parent.parent
UPLOADS = ROOT / "wp-content/uploads/2026/09"
CACHE = Path("/tmp/claude-1000/-home-philips-Documents-website-demo-site/78041085-5775-429a-bb9d-62fdc03f1113/scratchpad/photo-cache")
MANIFEST = ROOT / "src/photos.json"
SIZES = (480, 768, 1024, 1536)
FULL = 1600
QUALITY = 80

def fetch(url: str) -> bytes:
    CACHE.mkdir(parents=True, exist_ok=True)
    key = CACHE / (hashlib.sha1(url.encode()).hexdigest() + ".bin")
    if key.exists():
        return key.read_bytes()
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (parish-demo-site build)"})
    with urllib.request.urlopen(req, timeout=60) as r:
        data = r.read()
    key.write_bytes(data)
    return data

def process(p: dict) -> dict:
    UPLOADS.mkdir(parents=True, exist_ok=True)
    img = Image.open(io.BytesIO(fetch(p["url"])))
    img = ImageOps.exif_transpose(img).convert("RGB")
    if "crop" in p:  # optional aspect crop e.g. "3:2"
        w, h = img.size; cw, ch = (int(x) for x in p["crop"].split(":"))
        target = cw / ch
        if w / h > target:
            nw = int(h * target); img = img.crop(((w - nw) // 2, 0, (w - nw) // 2 + nw, h))
        else:
            nh = int(w / target); img = img.crop((0, (h - nh) // 2, w, (h - nh) // 2 + nh))
    if img.width > FULL:
        img = img.resize((FULL, round(img.height * FULL / img.width)), Image.LANCZOS)
    full = UPLOADS / f"{p['slug']}.jpg"
    img.save(full, "JPEG", quality=QUALITY, optimize=True, progressive=True)
    variants = []
    for w in SIZES:
        if w >= img.width:
            continue
        v = img.resize((w, round(img.height * w / img.width)), Image.LANCZOS)
        name = f"{p['slug']}-{w}x{v.height}.jpg"
        v.save(UPLOADS / name, "JPEG", quality=QUALITY, optimize=True, progressive=True)
        variants.append((w, name))
    return {"slug": p["slug"], "width": img.width, "height": img.height, "variants": variants}

def srcset_snippet(info: dict, sizes_attr: str = "(max-width: 860px) calc(100vw - 40px), 740px") -> str:
    parts = [f"/wp-content/uploads/2026/09/{n} {w}w" for w, n in info["variants"]]
    parts.append(f"/wp-content/uploads/2026/09/{info['slug']}.jpg {info['width']}w")
    return f'srcset="{", ".join(parts)}" sizes="{sizes_attr}"'

def write_credits(manifest: list):
    by_source = {}
    for p in manifest:
        by_source.setdefault(p["source"], []).append(p)
    rows = []
    for source in sorted(by_source):
        rows.append(f'<h2 class="wp-block-heading">{source}</h2>')
        rows.append('<ul class="wp-block-list">')
        for p in sorted(by_source[source], key=lambda x: x["slug"]):
            credit = p.get("credit", "")
            link = f'<a href="{p["page_url"]}" target="_blank" rel="noopener">{credit}</a>' if p.get("page_url") else credit
            rows.append(f'<li><strong>{p.get("alt", p["slug"])}</strong> — {link} · {p["license"]}</li>')
        rows.append("</ul>")
    body = "\n".join(rows)
    (ROOT / "src/content/credits.html").write_text(f"""---
title: Photo Credits
section: About this site
description: Attribution for the photographs used on this demo parish website.
lede: Every photograph on this demo site is a real photo released under a free licence. Replace them with your own parish photos when the site goes live.
---
<p class="wp-block-paragraph">This demonstration site uses photographs shared by their photographers under free licences. Thank you to each of them. When a parish adopts this site, these images are swapped for the parish's own photographs and this page can be removed.</p>
{body}
<p class="wp-block-paragraph has-small-font-size">Licence summaries: the <a href="https://unsplash.com/license" target="_blank" rel="noopener">Unsplash License</a> and <a href="https://www.pexels.com/license/" target="_blank" rel="noopener">Pexels License</a> allow free use without attribution (credit given here anyway); <a href="https://creativecommons.org/licenses/by-sa/4.0/" target="_blank" rel="noopener">CC BY-SA</a> and <a href="https://creativecommons.org/licenses/by/4.0/" target="_blank" rel="noopener">CC BY</a> images require the attribution shown above.</p>
""", encoding="utf-8")

if __name__ == "__main__":
    manifest = json.loads(MANIFEST.read_text())
    only = sys.argv[sys.argv.index("--only") + 1] if "--only" in sys.argv else None
    report_path = ROOT / "src/photos-report.json"
    report = json.loads(report_path.read_text()) if report_path.exists() else {}
    for p in manifest:
        if only and p["slug"] != only:
            continue
        try:
            info = process(p)
            report[p["slug"]] = info
            print(f"ok   {p['slug']}  {info['width']}x{info['height']}  {[w for w,_ in info['variants']]}")
        except Exception as e:
            print(f"FAIL {p['slug']}: {e}")
    write_credits(manifest)
    report_path.write_text(json.dumps(report, indent=1))
