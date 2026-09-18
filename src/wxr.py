#!/usr/bin/env python3
"""
WordPress export (WXR) generator.

Turns every page in src/content/ into a WordPress "page" whose content is
real block-editor markup (Gutenberg block delimiters around the HTML), plus
one "attachment" item per photo pointing at the live demo URL so the
WordPress importer can download the media and rewrite the image links.

    python3 src/wxr.py            -> wordpress-export.xml at the repo root

Import on WordPress.com: Tools -> Import -> WordPress -> upload the file,
tick "Download and import file attachments". Header, footer, menu and the
Additional CSS are set up separately in the Site Editor (see /site-guide/).
"""
import json, re, html, datetime
from pathlib import Path
from html.parser import HTMLParser

import build  # reuse the page reader and placeholder expansion

ROOT = build.ROOT
site = build.site
OUT = ROOT / "wordpress-export.xml"

VOID = {"img", "br", "hr", "input", "meta", "link", "source", "wbr"}

# ---------------------------------------------------------------- tiny DOM
class Node:
    __slots__ = ("tag", "attrs", "children", "parent")
    def __init__(self, tag, attrs=None, parent=None):
        self.tag, self.attrs, self.children, self.parent = tag, dict(attrs or []), [], parent
    def cls(self):
        return self.attrs.get("class", "").split()
    def has(self, c):
        return c in self.cls()

class Text:
    __slots__ = ("text",)
    def __init__(self, text):
        self.text = text

class DOM(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=False)
        self.root = Node("#root"); self.cur = self.root
    def handle_starttag(self, tag, attrs):
        n = Node(tag, attrs, self.cur); self.cur.children.append(n)
        if tag not in VOID:
            self.cur = n
    def handle_startendtag(self, tag, attrs):
        self.cur.children.append(Node(tag, attrs, self.cur))
    def handle_endtag(self, tag):
        n = self.cur
        while n is not self.root and n.tag != tag:
            n = n.parent
        if n is not self.root:
            self.cur = n.parent
    def handle_data(self, d):
        self.cur.children.append(Text(d))
    def handle_entityref(self, name):
        self.cur.children.append(Text(f"&{name};"))
    def handle_charref(self, name):
        self.cur.children.append(Text(f"&#{name};"))
    def handle_comment(self, d):
        self.cur.children.append(Text(f"<!--{d}-->"))

def parse(s):
    p = DOM(); p.feed(s); p.close(); return p.root

def attrs_str(n):
    return "".join(f' {k}="{html.escape(v, quote=True)}"' if v is not None else f" {k}" for k, v in n.attrs.items())

def serialize(n):
    if isinstance(n, Text):
        return n.text
    inner = "".join(serialize(c) for c in n.children)
    if n.tag in VOID:
        return f"<{n.tag}{attrs_str(n)}>"
    return f"<{n.tag}{attrs_str(n)}>{inner}</{n.tag}>"

def inner_html(n):
    return "".join(serialize(c) for c in n.children)

def elements(n):
    return [c for c in n.children if isinstance(c, Node)]

def only_inline(n):
    """True if the node contains no block-level children (safe as a paragraph/list item)."""
    block = {"p", "div", "h1", "h2", "h3", "h4", "ul", "ol", "figure", "table", "details", "blockquote", "form", "section", "nav"}
    return not any(isinstance(c, Node) and c.tag in block for c in n.children)

# ---------------------------------------------------------------- blocks
def j(d):
    return json.dumps(d, separators=(",", ":"), ensure_ascii=False)

def extra_classes(n, drop=()):
    return " ".join(c for c in n.cls() if c not in drop and not c.startswith("wp-block-") and c not in ("has-background",)) or None

def block(name, attrs, html_inner):
    a = " " + j(attrs) if attrs else ""
    return f"<!-- wp:{name}{a} -->\n{html_inner}\n<!-- /wp:{name} -->\n"

def html_block(s):
    return f"<!-- wp:html -->\n{s.strip()}\n<!-- /wp:html -->\n"

def color_attrs(n):
    a = {}
    for c in n.cls():
        m = re.match(r"has-([\w-]+)-background-color$", c)
        if m:
            a["backgroundColor"] = m.group(1)
        m = re.match(r"has-([\w-]+)-color$", c)
        if m and not c.endswith("-background-color"):
            a["textColor"] = m.group(1)
    return a

def convert(n):
    """Convert one top-level element into block markup (recursing into groups)."""
    if isinstance(n, Text):
        t = n.text.strip()
        if not t or t.startswith("<!--"):
            return ""
        return block("paragraph", {}, f"<p>{t}</p>")
    tag, cls = n.tag, n.cls()
    ex = extra_classes(n)

    if tag == "p":
        a = {}
        if ex: a["className"] = ex
        for c in cls:
            m = re.match(r"has-(small|medium|large|x-large)-font-size", c)
            if m: a["fontSize"] = m.group(1)
        return block("paragraph", a, serialize(n))
    if tag in ("h2", "h3", "h4"):
        a = {"level": int(tag[1])}
        if ex: a["className"] = ex
        if "has-text-align-center" in cls: a["textAlign"] = "center"
        return block("heading", a, serialize(n))
    if tag in ("ul", "ol"):
        items = elements(n)
        if all(i.tag == "li" and only_inline(i) for i in items) and not (set(cls) & {"steps", "timeline", "bulletins", "news-list"}):
            a = {}
            if tag == "ol": a["ordered"] = True
            if ex: a["className"] = ex
            lis = "".join(block("list-item", {}, f"<li>{inner_html(i)}</li>") for i in items)
            return block("list", a, f"<{tag}{attrs_str(n)}>{lis}</{tag}>")
        return html_block(serialize(n))
    if tag == "figure" and "wp-block-image" in cls:
        img = next((c for c in elements(n) if c.tag == "img"), None)
        a = {"sizeSlug": "large"}
        if ex: a["className"] = ex
        return block("image", a, serialize(n))
    if tag == "figure" and "wp-block-table" in cls:
        return block("table", {}, serialize(n))
    if tag == "figure" and "wp-block-embed" in cls:
        iframe = next((c for c in elements(n) if c.tag == "div"), None)
        src = ""
        if iframe:
            f = next((c for c in elements(iframe) if c.tag == "iframe"), None)
            src = f.attrs.get("src", "") if f else ""
        if "youtube" in src:
            vid = src.rstrip("/").split("/")[-1].split("?")[0]
            url = f"https://www.youtube.com/watch?v={vid}"
            return block("embed", {"url": url, "type": "video", "providerNameSlug": "youtube", "responsive": True, "className": "wp-embed-aspect-16-9 wp-has-aspect-ratio"},
                         f'<figure class="wp-block-embed is-type-video is-provider-youtube wp-block-embed-youtube wp-embed-aspect-16-9 wp-has-aspect-ratio"><div class="wp-block-embed__wrapper">\n{url}\n</div></figure>')
        # maps / calendar: WordPress.com has dedicated blocks; leave a Custom HTML block with a note
        return html_block(f"<!-- Replace with the Google Calendar / Map block -->\n{serialize(n)}")
    if tag == "blockquote":
        a = {}
        if ex: a["className"] = ex
        return block("quote", a, serialize(n))
    if tag == "hr":
        return block("separator", {"className": ex} if ex else {}, serialize(n))
    if tag == "details":
        summary = next((c for c in elements(n) if c.tag == "summary"), None)
        inner = "".join(convert(c) for c in n.children if not (isinstance(c, Node) and c.tag == "summary"))
        return block("details", {}, f'<details class="wp-block-details"><summary>{inner_html(summary) if summary else ""}</summary>{inner}</details>')
    if tag == "div" and "wp-block-buttons" in cls:
        btns = []
        for b in elements(n):
            a_ = next((c for c in elements(b) if c.tag == "a"), None)
            if not a_: continue
            ba = {}
            style = next((c for c in b.cls() if c.startswith("is-style-")), None)
            if style: ba["className"] = style
            btns.append(block("button", ba, f'<div class="{b.attrs.get("class", "wp-block-button")}">{serialize(a_)}</div>'))
        a = {}
        if "is-content-justification-center" in cls: a["layout"] = {"type": "flex", "justifyContent": "center"}
        return block("buttons", a, f'<div class="wp-block-buttons">{"".join(btns)}</div>')
    if tag == "div" and "wp-block-columns" in cls:
        cols = []
        for c in elements(n):
            ca = {}
            cex = extra_classes(c)
            if cex: ca["className"] = cex
            if "is-vertically-aligned-center" in c.cls(): ca["verticalAlignment"] = "center"
            cols.append(block("column", ca, f'<div class="{c.attrs.get("class", "wp-block-column")}">{"".join(convert(x) for x in c.children)}</div>'))
        a = {}
        if ex: a["className"] = ex
        if "are-vertically-aligned-center" in cls: a["verticalAlignment"] = "center"
        if "alignwide" in cls: a["align"] = "wide"
        return block("columns", a, f'<div class="{n.attrs.get("class")}">{"".join(cols)}</div>')
    if tag == "div" and "wp-block-group" in cls:
        a = dict(color_attrs(n))
        if ex: a["className"] = ex
        if "alignwide" in cls: a["align"] = "wide"
        if "alignfull" in cls: a["align"] = "full"
        a["layout"] = {"type": "grid"} if "is-layout-grid" in cls else {"type": "constrained"}
        # groups whose children are custom structures (schedule cards, stats…) still convert child-by-child
        return block("group", a, f'<div class="{n.attrs.get("class")}"{"".join(f" {k}=\"{html.escape(v, True)}\"" for k, v in n.attrs.items() if k != "class")}>{"".join(convert(x) for x in n.children)}</div>')
    if tag == "div" and "wp-block-file" in cls:
        a_ = next((c for c in elements(n) if c.tag == "a"), None)
        return block("file", {"href": a_.attrs.get("href", "") if a_ else ""}, serialize(n))
    if tag == "div" and "section-head" in cls:
        return "".join(convert(c) for c in n.children)
    if tag == "form":
        return html_block(serialize(n))  # replace with the Form block on WordPress
    # anything else: keep as a Custom HTML block so nothing is lost
    return html_block(serialize(n))

def to_blocks(body: str) -> str:
    root = parse(body)
    return "".join(convert(c) for c in root.children)

# ---------------------------------------------------------------- WXR
def cdata(s):
    return "<![CDATA[" + s.replace("]]>", "]]]]><![CDATA[>") + "]]>"

def item_page(pid, meta, content, parent_id=0, order=0):
    now = datetime.datetime(2026, 9, 18, 12, 0, 0)
    d = now.strftime("%Y-%m-%d %H:%M:%S")
    return f"""
  <item>
    <title>{html.escape(meta["title"])}</title>
    <link>{site["url"]}{meta["path"]}</link>
    <pubDate>{now.strftime("%a, %d %b %Y %H:%M:%S +0000")}</pubDate>
    <dc:creator>{cdata("parishoffice")}</dc:creator>
    <guid isPermaLink="false">{site["url"]}/?page_id={pid}</guid>
    <description></description>
    <content:encoded>{cdata(content)}</content:encoded>
    <excerpt:encoded>{cdata(meta.get("lede", ""))}</excerpt:encoded>
    <wp:post_id>{pid}</wp:post_id>
    <wp:post_date>{cdata(d)}</wp:post_date>
    <wp:post_date_gmt>{cdata(d)}</wp:post_date_gmt>
    <wp:comment_status>{cdata("closed")}</wp:comment_status>
    <wp:ping_status>{cdata("closed")}</wp:ping_status>
    <wp:post_name>{cdata("home" if meta["slug"] == "index" else meta["slug"])}</wp:post_name>
    <wp:status>{cdata("publish")}</wp:status>
    <wp:post_parent>{parent_id}</wp:post_parent>
    <wp:menu_order>{order}</wp:menu_order>
    <wp:post_type>{cdata("page")}</wp:post_type>
    <wp:post_password>{cdata("")}</wp:post_password>
    <wp:is_sticky>0</wp:is_sticky>
    <wp:postmeta><wp:meta_key>{cdata("_yoast_wpseo_metadesc")}</wp:meta_key><wp:meta_value>{cdata(meta.get("description", ""))}</wp:meta_value></wp:postmeta>
  </item>"""

def item_attachment(aid, slug, alt):
    url = f"{site['url']}/wp-content/uploads/2026/09/{slug}.jpg"
    d = "2026-09-18 12:00:00"
    return f"""
  <item>
    <title>{html.escape(slug)}</title>
    <link>{url}</link>
    <pubDate>Fri, 18 Sep 2026 12:00:00 +0000</pubDate>
    <dc:creator>{cdata("parishoffice")}</dc:creator>
    <guid isPermaLink="false">{url}</guid>
    <description></description>
    <content:encoded>{cdata("")}</content:encoded>
    <excerpt:encoded>{cdata("")}</excerpt:encoded>
    <wp:post_id>{aid}</wp:post_id>
    <wp:post_date>{cdata(d)}</wp:post_date>
    <wp:post_date_gmt>{cdata(d)}</wp:post_date_gmt>
    <wp:comment_status>{cdata("closed")}</wp:comment_status>
    <wp:ping_status>{cdata("closed")}</wp:ping_status>
    <wp:post_name>{cdata(slug)}</wp:post_name>
    <wp:status>{cdata("inherit")}</wp:status>
    <wp:post_parent>0</wp:post_parent>
    <wp:menu_order>0</wp:menu_order>
    <wp:post_type>{cdata("attachment")}</wp:post_type>
    <wp:post_password>{cdata("")}</wp:post_password>
    <wp:is_sticky>0</wp:is_sticky>
    <wp:attachment_url>{cdata(url)}</wp:attachment_url>
    <wp:postmeta><wp:meta_key>{cdata("_wp_attachment_image_alt")}</wp:meta_key><wp:meta_value>{cdata(alt)}</wp:meta_value></wp:postmeta>
  </item>"""

def main():
    pages = []
    for f in sorted(build.CONTENT.glob("*.html")):
        meta, body = build.read_page(f)
        if meta.get("noindex") == "true":
            continue  # the 404 page is a Netlify-only file
        body = build.image_placeholders(build.events_placeholders(body))
        # the static-only calendar becomes a note + Google Calendar placeholder on WordPress
        body = re.sub(r'<div class="wp-block-group alignwide month-cal"[\s\S]*?</div>\s*$', "", body, flags=re.M)
        pages.append((meta, body))

    # section landing pages become parents so the WordPress page list is tidy
    ids = {}
    next_id = 100
    for meta, _ in pages:
        ids[meta["path"]] = next_id; next_id += 1
    items = []
    for meta, body in pages:
        parent = ids.get(meta.get("section_href", ""), 0) if meta.get("section_href") != meta["path"] else 0
        content = to_blocks(body) if meta["template"] != "home" else html_block(body)
        items.append(item_page(ids[meta["path"]], meta, content, parent, int(meta.get("order", 0) or 0)))
    aid = 5000
    for slug, p in build.PHOTO_META.items():
        items.append(item_attachment(aid, slug, p.get("alt", ""))); aid += 1
    for pdf in ("sample-form", "sample-bulletin"):
        items.append(item_attachment(aid, pdf, "").replace(f"{pdf}.jpg", f"{pdf}.pdf")); aid += 1

    xml = f"""<?xml version="1.0" encoding="UTF-8" ?>
<!-- Generated from the St. Columba Parish demo site. Import: Tools -> Import -> WordPress. -->
<rss version="2.0"
  xmlns:excerpt="http://wordpress.org/export/1.2/excerpt/"
  xmlns:content="http://purl.org/rss/1.0/modules/content/"
  xmlns:wfw="http://wellformedweb.org/CommentAPI/"
  xmlns:dc="http://purl.org/dc/elements/1.1/"
  xmlns:wp="http://wordpress.org/export/1.2/">
<channel>
  <title>{html.escape(site["name"])}</title>
  <link>{site["url"]}</link>
  <description>{html.escape(site["tagline"])}</description>
  <pubDate>Fri, 18 Sep 2026 12:00:00 +0000</pubDate>
  <language>en-CA</language>
  <wp:wxr_version>1.2</wp:wxr_version>
  <wp:base_site_url>{site["url"]}</wp:base_site_url>
  <wp:base_blog_url>{site["url"]}</wp:base_blog_url>
  <wp:author><wp:author_id>1</wp:author_id><wp:author_login>{cdata("parishoffice")}</wp:author_login><wp:author_email>{cdata(site["email"])}</wp:author_email><wp:author_display_name>{cdata("Parish Office")}</wp:author_display_name><wp:author_first_name>{cdata("")}</wp:author_first_name><wp:author_last_name>{cdata("")}</wp:author_last_name></wp:author>
  <generator>parish-demo-site</generator>
{"".join(items)}
</channel>
</rss>
"""
    OUT.write_text(xml, encoding="utf-8")
    print(f"wrote {OUT.name}: {len(pages)} pages, {aid - 5000} attachments, {len(xml) // 1024} KB")

if __name__ == "__main__":
    main()
