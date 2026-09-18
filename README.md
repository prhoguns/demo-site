# St. Columba Parish — demo website

A complete, generic website for a Catholic parish in the Archdiocese of Toronto, built as the
demonstration/boilerplate site for pitching to parishes. The reference implementation is the
St. Philip Neri Parish site; this demo has every feature of that site plus more.

* **Static site** (no build step on Netlify): the repo root is the publish directory.
* **WordPress-ready**: page content is WordPress core-block markup, so the whole site can be
  imported into a WordPress.com Personal-plan site (`wordpress-export.xml`) and edited by the
  parish office. See `/site-guide/` on the site.
* **Real photos** (Wikimedia Commons, Pexels) with credits at `/credits/`. No AI images.

## Layout

```
src/site.json          parish details, navigation, footer
src/events.json        one list of events -> calendar, event cards, JSON-LD
src/photos.json        photo manifest (source URL, credit, licence)
src/content/*.html     one file per page: front matter + block markup
src/templates/         page chrome (header / nav / footer)
src/build.py           generator  -> /index.html, /<slug>/index.html, sitemap, search index
src/photos.py          downloads photos, writes WordPress-style sizes to wp-content/uploads/
src/wxr.py             WordPress export (WXR) with Gutenberg block delimiters
src/CONTENT-GUIDE.md   the authoring contract every page follows
assets/                site.css, site.js, icons
wp-content/uploads/    photos and sample PDFs (paths match WordPress)
```

## Working on the site

```bash
python3 src/build.py --check      # rebuild every page and verify internal links
python3 -m http.server 8765       # preview at http://localhost:8765
python3 src/photos.py             # (re)generate photo sizes from src/photos.json
python3 src/wxr.py                # regenerate wordpress-export.xml
```

Edit pages in `src/content/`, never the generated files at the root. Commit the generated
files too — Netlify publishes the repo as-is.
