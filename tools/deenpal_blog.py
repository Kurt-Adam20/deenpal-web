#!/usr/bin/env python3
"""
DeenPal multilingual SEO blog generator.

Renders blog posts from a JSON spec into the exact site template for all four
languages (EN root /blog/, NL/DE/FR under /xx/blog/), inserts cards into each
language's blog index, and updates sitemap.xml.

Usage:
    python3 tools/deenpal_blog.py path/to/today.json
    python3 tools/deenpal_blog.py path/to/today.json --check   # validate only, no writes

The JSON schema is documented in tools/README.md. Each post defines, per
language, a slug + metadata + a list of content "sections". The same four-way
hreflang block is written into every language version so they cross-link.
"""

import json
import re
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SITE = "https://getdeenpal.com"
APP_URL = "https://apps.apple.com/be/app/deenpal-muslim-assistant/id6766055425"

LANGS = ["en", "nl", "de", "fr"]

# Where each language's posts live, and the relative asset prefix from a post.
LANG_DIR = {"en": "blog", "nl": "nl/blog", "de": "de/blog", "fr": "fr/blog"}
ASSET_PREFIX = {"en": "../", "nl": "../../", "de": "../../", "fr": "../../"}
HTML_LANG = {"en": "en", "nl": "nl", "de": "de", "fr": "fr"}
OG_LOCALE = {"en": "en_US", "nl": "nl_NL", "de": "de_DE", "fr": "fr_FR"}

MONTHS = {
    "en": ["January", "February", "March", "April", "May", "June", "July",
           "August", "September", "October", "November", "December"],
    "nl": ["januari", "februari", "maart", "april", "mei", "juni", "juli",
           "augustus", "september", "oktober", "november", "december"],
    "de": ["Januar", "Februar", "März", "April", "Mai", "Juni", "Juli",
           "August", "September", "Oktober", "November", "Dezember"],
    "fr": ["janvier", "février", "mars", "avril", "mai", "juin", "juillet",
           "août", "septembre", "octobre", "novembre", "décembre"],
}

# Per-language site chrome (nav + footer + breadcrumb labels + CTA button text).
CHROME = {
    "en": {
        "home": "/", "blog": "/blog/",
        "crumb_home": "Home", "crumb_blog": "Blog",
        "nav": '''<li><a href="/#features" class="nav__link">Features</a></li>
        <li><a href="/#ai-modes" class="nav__link">AI</a></li>
        <li><a href="/#screens" class="nav__link">Screens</a></li>
        <li><a href="/blog/" class="nav__link">Blog</a></li>
        <li><a href="/#faq" class="nav__link">FAQ</a></li>''',
        "download_sm": "Download Free",
        "footer_back": "← Back to DeenPal", "footer_more": "More Articles",
        "footer_copy": "All rights reserved.",
    },
    "nl": {
        "home": "/nl/", "blog": "/nl/blog/",
        "crumb_home": "Home", "crumb_blog": "Blog",
        "nav": '''<li><a href="/nl/#features" class="nav__link">Functies</a></li>
        <li><a href="/nl/blog/" class="nav__link">Blog</a></li>
        <li><a href="/nl/#faq" class="nav__link">FAQ</a></li>''',
        "download_sm": "Download DeenPal",
        "footer_back": "← Terug naar DeenPal", "footer_more": "Meer artikelen",
        "footer_copy": "Alle rechten voorbehouden.",
    },
    "de": {
        "home": "/de/", "blog": "/de/blog/",
        "crumb_home": "Startseite", "crumb_blog": "Blog",
        "nav": '''<li><a href="/de/#features" class="nav__link">Funktionen</a></li>
        <li><a href="/de/blog/" class="nav__link">Blog</a></li>
        <li><a href="/de/#faq" class="nav__link">FAQ</a></li>''',
        "download_sm": "DeenPal laden",
        "footer_back": "← Zurück zu DeenPal", "footer_more": "Mehr Artikel",
        "footer_copy": "Alle Rechte vorbehalten.",
    },
    "fr": {
        "home": "/fr/", "blog": "/fr/blog/",
        "crumb_home": "Accueil", "crumb_blog": "Blog",
        "nav": '''<li><a href="/fr/#features" class="nav__link">Fonctionnalités</a></li>
        <li><a href="/fr/blog/" class="nav__link">Blog</a></li>
        <li><a href="/fr/#faq" class="nav__link">FAQ</a></li>''',
        "download_sm": "Télécharger",
        "footer_back": "← Retour à DeenPal", "footer_more": "Plus d'articles",
        "footer_copy": "Tous droits réservés.",
    },
}


def esc(s: str) -> str:
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def post_url(lang: str, slug: str) -> str:
    return f"{SITE}/{LANG_DIR[lang]}/{slug}.html"


def date_label(d: date, lang: str) -> str:
    m = MONTHS[lang][d.month - 1]
    if lang == "en":
        return f"{m} {d.day}, {d.year}"
    return f"{d.day} {m} {d.year}"


# ---------------- section rendering ----------------
def render_sections(sections) -> str:
    out = []
    for s in sections:
        t = s["t"]
        if t == "p":
            out.append(f'        <p>{s["html"]}</p>')
        elif t == "h2":
            out.append(f'        <h2>{esc(s["text"])}</h2>')
        elif t == "h3":
            out.append(f'        <h3>{esc(s["text"])}</h3>')
        elif t == "ul":
            items = "\n".join(f"          <li>{i}</li>" for i in s["items"])
            out.append(f"        <ul>\n{items}\n        </ul>")
        elif t == "ol":
            items = "\n".join(f"          <li>{i}</li>" for i in s["items"])
            out.append(f"        <ol>\n{items}\n        </ol>")
        elif t == "quran":
            out.append(
                '        <div class="quran-quote">\n'
                f'          <p>{s["text"]}</p>\n'
                f'          <span class="ref">{esc(s["ref"])}</span>\n'
                "        </div>"
            )
        elif t == "highlight":
            note = s.get("note", "")
            note_html = (
                f'\n          <p style="margin:12px 0 0;font-size:14px;color:var(--text-secondary)">{note}</p>'
                if note else ""
            )
            out.append(
                '        <div class="dhikr-highlight">\n'
                f'          <div class="dhikr-highlight__arabic">{esc(s["arabic"])}</div>\n'
                f'          <div class="dhikr-highlight__trans">{esc(s["trans"])}</div>{note_html}\n'
                "        </div>"
            )
        elif t == "cards":
            cards = []
            for c in s["cards"]:
                cards.append(
                    '          <div class="benefit-card">\n'
                    f'            <div class="benefit-card__icon">{c.get("icon", "✨")}</div>\n'
                    f'            <div class="benefit-card__title">{esc(c["title"])}</div>\n'
                    f'            <div class="benefit-card__text">{c["text"]}</div>\n'
                    "          </div>"
                )
            out.append(
                '        <div class="benefit-cards">\n' + "\n".join(cards) + "\n        </div>"
            )
        else:
            raise ValueError(f"Unknown section type: {t}")
    return "\n\n".join(out)


def hreflang_block(post) -> str:
    lines = []
    for lg in LANGS:
        lines.append(
            f'  <link rel="alternate" hreflang="{lg}" href="{post_url(lg, post["langs"][lg]["slug"])}" />'
        )
    # x-default points to English
    lines.append(
        f'  <link rel="alternate" hreflang="x-default" href="{post_url("en", post["langs"]["en"]["slug"])}" />'
    )
    return "\n".join(lines)


# ---------------- full page template ----------------
def render_page(post, lang, d: date) -> str:
    L = post["langs"][lang]
    ap = ASSET_PREFIX[lang]
    ch = CHROME[lang]
    url = post_url(lang, L["slug"])
    iso = d.isoformat()
    body = render_sections(L["sections"])
    cta = L["cta"]
    fn = L.get("footer_nav", {})

    footer_nav_html = ""
    if fn:
        prev = fn.get("prev")
        rel = fn.get("related")
        prev_html = (
            f'          <a href="{prev["href"]}" class="nav-article">\n'
            f'            <div class="nav-article__dir">←</div>\n'
            f'            <div class="nav-article__title">{esc(prev["title"])}</div>\n'
            f'          </a>' if prev else "<span></span>"
        )
        rel_html = (
            f'          <a href="{rel["href"]}" class="nav-article" style="text-align:right">\n'
            f'            <div class="nav-article__dir">→</div>\n'
            f'            <div class="nav-article__title">{esc(rel["title"])}</div>\n'
            f'          </a>' if rel else "<span></span>"
        )
        footer_nav_html = (
            '\n        <nav class="article-footer-nav" aria-label="More articles">\n'
            f'{prev_html}\n{rel_html}\n        </nav>'
        )

    return f'''<!DOCTYPE html>
<html lang="{HTML_LANG[lang]}" data-theme="dark">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=5.0" />
  <title>{esc(L["title"])} | DeenPal</title>
  <meta name="description" content="{esc(L["meta_desc"])}" />
  <meta name="robots" content="index, follow, max-snippet:-1, max-image-preview:large" />
  <link rel="canonical" href="{url}" />
{hreflang_block(post)}
  <meta property="og:type" content="article" />
  <meta property="og:url" content="{url}" />
  <meta property="og:title" content="{esc(L.get("og_title", L["title"]))}" />
  <meta property="og:description" content="{esc(L.get("og_desc", L["meta_desc"]))}" />
  <meta property="og:image" content="{SITE}/assets/img/og-image.jpg" />
  <meta property="og:site_name" content="DeenPal" />
  <meta property="og:locale" content="{OG_LOCALE[lang]}" />
  <meta name="twitter:card" content="summary_large_image" />
  <meta name="twitter:title" content="{esc(L.get("og_title", L["title"]))}" />
  <meta name="twitter:description" content="{esc(L.get("twitter_desc", L.get("og_desc", L["meta_desc"])))}" />
  <meta name="twitter:image" content="{SITE}/assets/img/og-image.jpg" />
  <link rel="icon" type="image/png" href="/favicon-96x96.png" sizes="96x96" />
  <link rel="icon" type="image/svg+xml" href="/favicon.svg" />
  <link rel="shortcut icon" href="/favicon.ico" />
  <link rel="apple-touch-icon" sizes="180x180" href="/apple-touch-icon.png" />
  <link rel="manifest" href="/site.webmanifest" />
  <link rel="preconnect" href="https://fonts.googleapis.com" />
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
  <link rel="preload" href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&family=IBM+Plex+Mono:wght@400;500;600&display=swap" as="style" onload="this.onload=null;this.rel='stylesheet'" />
  <noscript><link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&family=IBM+Plex+Mono:wght@400;500;600&display=swap" /></noscript>
  <link rel="stylesheet" href="{ap}assets/css/style.css" />
  <script type="application/ld+json">
  {{
    "@context": "https://schema.org",
    "@type": "Article",
    "headline": {json.dumps(L.get("og_title", L["title"]))},
    "description": {json.dumps(L["meta_desc"])},
    "image": "{SITE}/assets/img/og-image.jpg",
    "datePublished": "{iso}T10:00:00Z",
    "dateModified": "{iso}T10:00:00Z",
    "inLanguage": "{lang}",
    "author": {{ "@type": "Organization", "name": "DeenPal", "url": "{SITE}" }},
    "publisher": {{ "@type": "Organization", "name": "DeenPal", "logo": {{ "@type": "ImageObject", "url": "{SITE}/assets/img/icon.png" }} }},
    "mainEntityOfPage": {{ "@type": "WebPage", "@id": "{url}" }}
  }}
  </script>
  <script type="application/ld+json">
  {{
    "@context": "https://schema.org",
    "@type": "BreadcrumbList",
    "itemListElement": [
      {{ "@type": "ListItem", "position": 1, "name": "{ch['crumb_home']}", "item": "{SITE}{ch['home']}" }},
      {{ "@type": "ListItem", "position": 2, "name": "{ch['crumb_blog']}", "item": "{SITE}{ch['blog']}" }},
      {{ "@type": "ListItem", "position": 3, "name": {json.dumps(L["title"])}, "item": "{url}" }}
    ]
  }}
  </script>
  <style>
    .blog-article {{ padding-top: 80px; }}
    .article-hdr {{ padding: 64px 0 48px; border-bottom: 1px solid var(--border); max-width: 760px; margin: 0 auto; }}
    .article-hdr__cat {{ font-size: 12px; font-weight: 700; color: #C9A96E; text-transform: uppercase; letter-spacing: 0.6px; margin-bottom: 16px; display: block; }}
    .article-hdr__title {{ font-size: clamp(28px, 5vw, 44px); font-weight: 900; letter-spacing: -1px; color: var(--text); margin-bottom: 20px; line-height: 1.1; }}
    .article-hdr__meta {{ font-size: 14px; color: var(--text-secondary); font-family: var(--font-mono, monospace); display: flex; gap: 16px; flex-wrap: wrap; }}
    .article-body {{ max-width: 760px; margin: 0 auto; padding: 56px 0 96px; }}
    .article-body h2 {{ font-size: 24px; font-weight: 800; color: var(--text); margin: 52px 0 16px; padding-bottom: 12px; border-bottom: 1px solid var(--border); }}
    .article-body h3 {{ font-size: 18px; font-weight: 700; color: var(--text); margin: 32px 0 12px; }}
    .article-body p {{ font-size: 17px; line-height: 1.8; color: var(--text-secondary); margin-bottom: 18px; }}
    .article-body ul, .article-body ol {{ padding-left: 24px; margin-bottom: 20px; }}
    .article-body li {{ font-size: 16px; line-height: 1.75; color: var(--text-secondary); margin-bottom: 10px; }}
    .article-body strong {{ color: var(--text); font-weight: 700; }}
    .article-body a {{ color: #C9A96E; text-decoration: underline; }}
    .quran-quote {{ background: rgba(201,169,110,0.06); border-left: 3px solid #C9A96E; padding: 20px 24px; margin: 28px 0; border-radius: 0 12px 12px 0; }}
    .quran-quote p {{ margin: 0; font-size: 16px; font-style: italic; color: var(--text); }}
    .quran-quote .ref {{ font-size: 13px; color: #C9A96E; margin-top: 8px; display: block; font-style: normal; font-family: monospace; }}
    .benefit-cards {{ display: grid; grid-template-columns: 1fr 1fr; gap: 16px; margin: 24px 0; }}
    .benefit-card {{ background: var(--surface); border: 1px solid var(--border); border-radius: 16px; padding: 24px; }}
    .benefit-card__icon {{ font-size: 28px; margin-bottom: 12px; }}
    .benefit-card__title {{ font-size: 16px; font-weight: 700; color: var(--text); margin-bottom: 8px; }}
    .benefit-card__text {{ font-size: 14px; color: var(--text-secondary); line-height: 1.6; }}
    .dhikr-highlight {{ background: var(--surface); border: 1px solid var(--border); border-radius: 16px; padding: 24px; margin: 20px 0; text-align: center; }}
    .dhikr-highlight__arabic {{ font-size: 28px; color: #C9A96E; font-family: serif; margin-bottom: 8px; }}
    .dhikr-highlight__trans {{ font-size: 15px; color: var(--text); font-weight: 600; }}
    .article-cta {{ background: var(--surface); border: 1px solid var(--border); border-radius: 20px; padding: 40px; margin: 56px 0 0; text-align: center; }}
    .article-cta h3 {{ font-size: 22px; font-weight: 800; color: var(--text); margin-bottom: 12px; }}
    .article-cta p {{ font-size: 15px; color: var(--text-secondary); margin-bottom: 24px; max-width: 480px; margin-left: auto; margin-right: auto; }}
    .article-footer-nav {{ display: grid; grid-template-columns: 1fr 1fr; gap: 16px; margin-top: 56px; }}
    .nav-article {{ background: var(--surface); border: 1px solid var(--border); border-radius: 16px; padding: 20px; text-decoration: none; transition: border-color 0.2s; }}
    .nav-article:hover {{ border-color: rgba(201,169,110,0.5); }}
    .nav-article__dir {{ font-size: 13px; color: #C9A96E; margin-bottom: 6px; font-family: monospace; }}
    .nav-article__title {{ font-size: 15px; font-weight: 700; color: var(--text); line-height: 1.3; }}
  </style>
</head>
<body>
  <nav class="nav" id="nav" role="navigation" aria-label="Main navigation">
    <div class="nav__inner container">
      <a href="{ch['home']}" class="nav__logo" aria-label="DeenPal Home">
        <span class="nav__logo-icon"><img src="{ap}assets/img/icon.png" alt="" width="28" height="28" style="border-radius:7px;display:block;object-fit:cover;" /></span>
        <span class="nav__logo-text">DeenPal</span>
      </a>
      <button class="nav__hamburger" id="hamburger" aria-label="Toggle menu" aria-expanded="false"><span></span><span></span><span></span></button>
      <ul class="nav__links" id="navLinks" role="list">
        {ch['nav']}
      </ul>
      <div class="nav__actions">
        <a href="{APP_URL}" class="btn btn--gold btn--sm" target="_blank" rel="noopener">{ch['download_sm']}</a>
      </div>
    </div>
  </nav>

  <main class="blog-article">
    <div class="container">
      <header class="article-hdr">
        <span class="article-hdr__cat">{esc(L["category"])}</span>
        <h1 class="article-hdr__title">{esc(L["h1"])}</h1>
        <div class="article-hdr__meta">
          <span>DeenPal Team</span>
          <span>·</span>
          <time datetime="{iso}">{date_label(d, lang)}</time>
          <span>·</span>
          <span>{esc(L["read_label"])}</span>
        </div>
      </header>

      <article class="article-body">

{body}

        <div class="article-cta">
          <h3>{esc(cta["title"])}</h3>
          <p>{esc(cta["text"])}</p>
          <a href="{APP_URL}" target="_blank" rel="noopener" class="btn btn--gold btn--lg">{esc(cta["btn"])}</a>
        </div>{footer_nav_html}

      </article>
    </div>
  </main>

  <footer class="footer" role="contentinfo">
    <div class="container">
      <div class="footer__bottom" style="padding-top:0;border-top:none;justify-content:center;gap:24px">
        <a href="{ch['home']}" style="color:var(--text-secondary);font-size:14px;text-decoration:none">{ch['footer_back']}</a>
        <p class="footer__copy">© <span id="year"></span> DeenPal. {ch['footer_copy']}</p>
        <a href="{ch['blog']}" style="color:var(--text-secondary);font-size:14px;text-decoration:none">{ch['footer_more']}</a>
      </div>
    </div>
  </footer>

  <script src="{ap}assets/js/main.js" defer></script>
</body>
</html>
'''


# ---------------- index card insertion ----------------
def index_card_en(post, L, d: date) -> str:
    return f'''
        <article class="blog-card" data-reveal>
          <div class="blog-card__img {post.get("img_class", "blog-card__img--1")}" role="img" aria-label="{esc(L["h1"])}"></div>
          <div class="blog-card__body">
            <span class="blog-card__cat">{esc(L["category"])}</span>
            <h3 class="blog-card__title"><a href="{L["slug"]}.html">{esc(L["title"])}</a></h3>
            <p class="blog-card__excerpt">{esc(L["excerpt"])}</p>
            <div class="blog-card__meta"><span>{esc(L["read_label"])}</span><span>·</span><time datetime="{d.isoformat()}">{date_label(d, "en")}</time></div>
          </div>
        </article>'''


def index_card_localized(post, L, d: date, lang: str) -> str:
    return f'''
        <a href="/{LANG_DIR[lang]}/{L["slug"]}.html" class="article-card">
          <span class="article-card__cat">{esc(L["category"])}</span>
          <h2 class="article-card__title">{esc(L["title"])}</h2>
          <p class="article-card__desc">{esc(L["excerpt"])}</p>
          <div class="article-card__meta"><span>{esc(L["read_label"])}</span><span>·</span><time datetime="{d.isoformat()}">{date_label(d, lang)}</time></div>
        </a>'''


def insert_into_index(lang: str, cards_html: str, write: bool):
    index_path = ROOT / LANG_DIR[lang] / "index.html"
    html = index_path.read_text(encoding="utf-8")
    if lang == "en":
        anchor = '<div class="blog-page__grid">'
    else:
        anchor = '<div class="articles-grid">'
    if anchor not in html:
        raise RuntimeError(f"Grid anchor not found in {index_path}")
    # Insert new cards immediately after the grid opening tag (newest first).
    new_html = html.replace(anchor, anchor + cards_html, 1)
    if write:
        index_path.write_text(new_html, encoding="utf-8")
    return index_path


# ---------------- sitemap ----------------
def update_sitemap(posts, d: date, write: bool):
    sm_path = ROOT / "sitemap.xml"
    xml = sm_path.read_text(encoding="utf-8")
    blocks = []
    for post in posts:
        for lang in LANGS:
            url = post_url(lang, post["langs"][lang]["slug"])
            if url in xml:
                continue
            prio = "0.8" if lang == "en" else "0.7"
            blocks.append(
                f"\n  <url>\n    <loc>{url}</loc>\n"
                f"    <lastmod>{d.isoformat()}</lastmod>\n"
                f"    <changefreq>monthly</changefreq>\n"
                f"    <priority>{prio}</priority>\n  </url>\n"
            )
    if blocks:
        insertion = "".join(blocks) + "\n</urlset>"
        xml = xml.replace("</urlset>", insertion)
    if write:
        sm_path.write_text(xml, encoding="utf-8")
    return len(blocks)


# ---------------- validation ----------------
def validate(spec):
    posts = spec["posts"]
    seen_slugs = set()
    for i, post in enumerate(posts):
        for lang in LANGS:
            if lang not in post["langs"]:
                raise ValueError(f"Post {i}: missing language '{lang}'")
            L = post["langs"][lang]
            for key in ("slug", "title", "meta_desc", "category", "h1",
                        "read_label", "excerpt", "sections", "cta"):
                if key not in L:
                    raise ValueError(f"Post {i} [{lang}]: missing '{key}'")
            if not re.fullmatch(r"[a-z0-9\-]+", L["slug"]):
                raise ValueError(f"Post {i} [{lang}]: bad slug '{L['slug']}'")
            key = (lang, L["slug"])
            if key in seen_slugs:
                raise ValueError(f"Duplicate slug in this batch: {key}")
            seen_slugs.add(key)
            # don't silently overwrite an existing published file
            target = ROOT / LANG_DIR[lang] / f"{L['slug']}.html"
            if target.exists():
                raise ValueError(f"Post {i} [{lang}]: file already exists: {target}")
    return posts


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    flags = {a for a in sys.argv[1:] if a.startswith("--")}
    if not args:
        print("usage: deenpal_blog.py <spec.json> [--check]")
        sys.exit(1)
    spec = json.loads(Path(args[0]).read_text(encoding="utf-8"))
    d = date.fromisoformat(spec.get("date", date.today().isoformat()))
    write = "--check" not in flags

    posts = validate(spec)

    written = []
    for post in posts:
        for lang in LANGS:
            L = post["langs"][lang]
            page = render_page(post, lang, d)
            target = ROOT / LANG_DIR[lang] / f"{L['slug']}.html"
            if write:
                target.write_text(page, encoding="utf-8")
            written.append(str(target.relative_to(ROOT)))

    # index cards per language (all posts of the batch, newest first => reversed)
    for lang in LANGS:
        cards = ""
        for post in posts:
            L = post["langs"][lang]
            if lang == "en":
                cards = index_card_en(post, L, d) + cards
            else:
                cards = index_card_localized(post, L, d, lang) + cards
        insert_into_index(lang, cards, write)

    n_sitemap = update_sitemap(posts, d, write)

    mode = "CHECK (no files written)" if not write else "WRITTEN"
    print(f"[{mode}] {len(posts)} topic(s) x {len(LANGS)} languages = {len(written)} pages")
    for w in written:
        print(f"  + {w}")
    print(f"  sitemap: +{n_sitemap} urls; {len(LANGS)} blog indexes updated")
    print("\nPublished URLs:")
    for post in posts:
        for lang in LANGS:
            print(f"  {SITE}/{LANG_DIR[lang]}/{post['langs'][lang]['slug']}.html")


if __name__ == "__main__":
    main()
