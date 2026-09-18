#!/usr/bin/env python3
"""Build portable static hosting and self-contained WordPress theme deliveries."""
import json, re, shutil, zipfile, posixpath, html
from pathlib import Path
import build, wxr
ROOT=build.ROOT
OUT=ROOT/'delivery'
WEB=OUT/'website'
THEME=OUT/'st-columba'

def without_host_metadata(text):
    text=re.sub(r'<link rel="canonical"[^>]*>\n?', '', text)
    text=re.sub(r'<meta property="og:url"[^>]*>\n?', '', text)
    text=re.sub(r'<meta property="og:image"[^>]*>\n?', '', text)
    text=re.sub(r'<script type="application/ld\+json">.*?</script>\n?', '', text, flags=re.S)
    text=re.sub(r'<!--(?!\s*wp:|\s*/wp:|PARISH_BODY).*?-->', '', text, flags=re.S)
    return text

def portable_url(url, directory):
    if not url.startswith('/') or url.startswith('//'): return url
    path, sep, suffix=re.split(r'([?#])',url,maxsplit=1) if re.search(r'[?#]',url) else (url,'','')
    if path.endswith('/'):path+='index.html'
    return posixpath.relpath(path.lstrip('/'), directory or '.') + sep + suffix

def portable_html(text, directory):
    # Convert URL-bearing attributes without touching SVG self-closing slashes or
    # WordPress/HTML closing syntax. CSS url() and each srcset candidate need
    # separate handling because their URL does not begin at the quote.
    def attribute(match):
        return match.group('prefix') + portable_url(match.group('url'), directory)
    text = re.sub(
        r'''(?P<prefix>\b(?:href|src|action|poster|data-[\w:-]+)=["'])(?P<url>/(?!/)[^"']*)''',
        attribute, text, flags=re.I)
    def css_url(match):
        # These inline custom properties are consumed by assets/site.css, so
        # browsers resolve their URL tokens from the stylesheet directory.
        return match.group('prefix') + portable_url(match.group('url'), 'assets')
    text = re.sub(
        r'''(?P<prefix>\burl\(\s*["']?)(?P<url>/(?!/)[^"'()\s]+)''',
        css_url, text, flags=re.I)
    def srcset(match):
        candidates=[]
        for candidate in match.group('value').split(','):
            parts=candidate.strip().split(None,1)
            if parts and parts[0].startswith('/'):
                parts[0]=portable_url(parts[0],directory)
            candidates.append(' '.join(parts))
        return match.group('prefix') + ', '.join(candidates) + match.group('quote')
    return re.sub(
        r'''(?P<prefix>\bsrcset=["'])(?P<value>[^"']*)(?P<quote>["'])''',
        srcset, text, flags=re.I)

def compact_theme_html(text):
    """Use one responsive source per photo to keep the uploadable theme compact."""
    return re.sub(r'\s+(?:srcset|sizes)="[^"]*"', '', text)

def zip_tree(folder, target, prefix=''):
    with zipfile.ZipFile(target,'w',zipfile.ZIP_DEFLATED) as z:
        for file in sorted(folder.rglob('*')):
            if file.is_file(): z.write(file, prefix+file.relative_to(folder).as_posix())

def main():
    OUT.mkdir(exist_ok=True)
    # Only replace outputs owned by this packaging script.
    for folder in (WEB,THEME):
        if folder.exists():shutil.rmtree(folder)
        folder.mkdir()
    pages=[]
    for source in sorted(build.CONTENT.glob('*.html')):
        meta,body=build.read_page(source)
        if meta.get('publish')=='false':continue
        body=build.image_placeholders(build.events_placeholders(body))
        pages.append((meta,body))
    for folder in ('assets','wp-content'):
        shutil.copytree(ROOT/folder,WEB/folder)
    (WEB/'robots.txt').write_text('User-agent: *\nAllow: /\n')
    # Netlify and Cloudflare both recognise this optional static header file.
    (WEB/'_headers').write_text('/*\n  X-Content-Type-Options: nosniff\n  Referrer-Policy: strict-origin-when-cross-origin\n')
    (THEME/'shells').mkdir();(THEME/'site').mkdir()
    shutil.copytree(ROOT/'assets',THEME/'site/assets')
    theme_pages=[]
    theme_text=[]
    for meta,body in pages:
        relative='index.html' if meta['slug']=='index' else meta['slug']+'/index.html'
        original=(ROOT/relative).read_text()
        cleaned=without_host_metadata(original)
        dest=WEB/relative;dest.parent.mkdir(parents=True,exist_ok=True)
        dest.write_text(portable_html(cleaned,posixpath.dirname(relative)))
        # Replace only page content, preserving the shared header and page layout.
        assert body in original, meta['slug']
        shell=compact_theme_html(without_host_metadata(original.replace(body,'<!--PARISH_BODY-->',1)))
        (THEME/'shells'/(meta['slug']+'.html')).write_text(shell)
        theme_body=compact_theme_html(body)
        blocks=wxr.html_block(theme_body) if meta['slug']=='index' else wxr.to_blocks(theme_body)
        theme_pages.append(dict(slug=meta['slug'],title=meta['title'],body=theme_body,blocks=blocks))
        theme_text.extend((shell,blocks))
    (WEB/'404.html').write_text(portable_html(without_host_metadata((ROOT/'404.html').read_text()),''))
    for file in (ROOT/'src/wordpress').iterdir():
        if file.is_file():shutil.copy2(file,THEME/file.name)
    (THEME/'pages.json').write_text(json.dumps(theme_pages,ensure_ascii=False))
    # Copy only media actually referenced by the theme. The full static package
    # retains srcsets; WordPress gets the 1024px sources used by each page.
    media=set(re.findall(r'/wp-content/uploads/[^"\x27\s<>),]+','\n'.join(theme_text)))
    for url in sorted(media):
        source=ROOT/url.lstrip('/')
        if not source.is_file(): raise FileNotFoundError(source)
        target=THEME/'site'/url.lstrip('/')
        target.parent.mkdir(parents=True,exist_ok=True)
        shutil.copy2(source,target)
    zip_tree(WEB,OUT/'website-netlify-cloudflare.zip')
    zip_tree(THEME,OUT/'st-columba-wordpress-theme.zip','st-columba/')
    (OUT/'START-HERE.txt').write_text('''ST. COLUMBA PARISH — UPLOAD PACKAGES

NETLIFY: Drag the website folder into Netlify Drop.
CLOUDFLARE: In Workers & Pages, create a Pages project with Direct Upload.
Upload website-netlify-cloudflare.zip (or the website folder).
LOCAL PREVIEW: Open website/index.html in your browser. Internet access is
needed for web fonts, video and maps; the pages, images and search are local.

WORDPRESS: Appearance > Themes > Add New > Upload Theme.
Choose st-columba-wordpress-theme.zip, install it, and activate it.
Activation adds the bundled pages and selects Home. Existing pages with matching
slugs are preserved. Use a fresh WordPress site for the complete demonstration.
All photos and styles are included; no separate XML import is needed.
Requires permission to upload custom themes (some hosted plans restrict this).
Pages can be edited under Pages. The homepage is a Custom HTML block.

The website and theme are two formats; WordPress cannot import a static folder
through the Media Library. Do not upload this whole delivery directory.

Forms open a draft in the visitor's email app, with a review step before sending.
They do not rely on Netlify Forms or silently store submissions. The contact
address remains the generic demonstration address. Configure actual parish
contact details before using the site for real enquiries.

Daily TV Mass uses the broadcaster's updating YouTube playlist. No API key,
server function or daily site rebuild is required. The playlist also contains
rosary videos; visitors can choose a Mass from its playlist menu.

Photo attributions and licence links remain on the Photo Credits page.
The audit and developer setup files are excluded from the public packages.
Rebuild after source changes: python3 src/build.py --check && python3 src/package.py
''')
    print('Built',len(pages),'pages in',WEB)
    for p in OUT.glob('*.zip'):print(p.name,round(p.stat().st_size/1024/1024,1),'MB')
if __name__=='__main__':main()
