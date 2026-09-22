# St. Monica's Parish demo website

A separate static demo project for St. Monica's Parish, Toronto, built from the parish demo generator but with its own St. Monica visual system and WordPress-ready package.

- Public parish details, schedules, announcements and imagery were gathered from `https://stmonicasto.archtoronto.org/en/` for demo planning.
- Source page content lives in `src/content/*.html` as WordPress-friendly block markup.
- `src/site.json` contains parish identity, navigation, contact details and footer links.
- `src/photos.json` records source image URLs and provenance.
- `wordpress-export.xml` can be regenerated for a future WordPress import.

## Build

```bash
python3 src/photos.py
python3 src/build.py --check
python3 src/wxr.py
python3 -m http.server 8766
```

## Deploy targets

- Netlify: publish this directory as-is (`netlify.toml` publish path is `.`).
- Cloudflare: this project uses `wrangler.jsonc` name `st-monica-parish-demo`; Cloudflare Pages can also publish this directory directly.

Image reuse should be confirmed with St. Monica's Parish / Archdiocese of Toronto before using this as a production site.
