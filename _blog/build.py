#!/usr/bin/env python3
"""Build the Pomorix blog.

Reads the post sources in _blog/posts/*.html and writes:
  blog/index.html            the blog home page
  blog/<slug>/index.html     one page per post (URL: /blog/<slug>/)
  blog/feed.xml              RSS feed
  sitemap.xml                the whole site's sitemap
  index.html                 refreshes the "From the blog" block on the home page

Uses only the Python standard library. Run it from anywhere:
  python3 _blog/build.py

Post source format: a JSON header between two lines of three dashes, then the
article body as HTML. See _blog/README.md for every field.
"""
import html
import json
import re
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "_blog" / "posts"
OUT = ROOT / "blog"
SITE = "https://pomorix.com"
PLAY = "https://play.google.com/store/apps/details?id=com.pomorix.app"
FONTS = "https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&amp;display=swap"

CATEGORIES = {
    "pomodoro": {"name": "Pomodoro Technique", "short": "Pomodoro"},
    "study": {"name": "Studying", "short": "Study"},
    "focus": {"name": "Focus & Productivity", "short": "Focus"},
    "habits": {"name": "Habits & Tracking", "short": "Habits"},
}

# Pages outside the blog, for the sitemap. (path, lastmod, changefreq, priority)
STATIC_PAGES = [
    ("", "2026-11-02", "monthly", "1.0"),
    ("privacy-policy.html", "2026-10-04", "yearly", "0.3"),
    ("terms-of-use.html", "2026-10-04", "yearly", "0.3"),
]

SCREEN_ALT = {
    "timer-pomodoro": "Pomorix Pomodoro timer running a 25-minute focus session",
    "flow-mode-dark": "Pomorix Flow mode counting up a deep work session in dark theme",
    "tasks": "Pomorix task list with session estimates and progress",
    "categories": "Pomorix focus categories with icons and colours",
    "progress-overview": "Pomorix focus stats with weekly chart, streak and daily average",
    "progress-overview-dark": "Pomorix focus stats in dark theme",
    "insights-categories": "Pomorix insights showing focus time by category",
    "focus-hours-heatmap": "Pomorix chart of your most productive hours",
    "focus-journal": "Pomorix focus journal with session notes",
    "journal-timeline": "Pomorix journal timeline of today's sessions",
    "journal-timeline-dark": "Pomorix journal timeline in dark theme",
    "focus-sounds": "Pomorix focus sounds: rain, forest, café, brown noise and more",
    "break-timer": "Pomorix break timer counting down a short break",
    "focus-pulse-game": "Pomorix Focus Pulse mini game for breaks",
    "timer-settings": "Pomorix timer settings for focus, short break and long break lengths",
    "goals": "Pomorix daily goal settings in sessions or minutes",
    "onboarding-focus-length": "Pomorix setup screen for choosing a focus length",
    "onboarding-plan": "Pomorix setup screen showing your focus plan",
    "onboarding-welcome": "Pomorix welcome screen",
    "alerts-sounds": "Pomorix alert sound settings",
    "first-session-celebration": "Pomorix celebrating a finished first focus session",
    "backup-restore": "Pomorix backup and restore screen",
}


def esc(s):
    return html.escape(str(s), quote=True)


def play_url(campaign, medium="blog"):
    return f"{PLAY}&amp;referrer=utm_source%3Dpomorix.com%26utm_medium%3D{medium}%26utm_campaign%3D{campaign}"


def slugify(text):
    text = re.sub(r"<[^>]+>", "", text)
    text = html.unescape(text).lower().replace("&", "and")
    text = re.sub(r"[^a-z0-9]+", "-", text).strip("-")
    return text[:60].rstrip("-")


def fmt_date(iso):
    d = date.fromisoformat(iso)
    return f"{d.day} {d.strftime('%B %Y')}"


def rfc822(iso):
    d = date.fromisoformat(iso)
    return d.strftime("%a, %d %b %Y 08:00:00 +0530")


def strip_tags(s):
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", s))).strip()


# ---------------------------------------------------------------- loading

def load_posts():
    posts = []
    errors = []
    for path in sorted(SRC.glob("*.html")):
        raw = path.read_text(encoding="utf-8")
        m = re.match(r"\s*---\s*\n(.*?)\n---\s*\n(.*)\Z", raw, re.S)
        if not m:
            errors.append(f"{path.name}: missing --- header ---")
            continue
        try:
            meta = json.loads(m.group(1))
        except json.JSONDecodeError as e:
            errors.append(f"{path.name}: header is not valid JSON ({e})")
            continue
        meta["slug"] = path.stem
        meta["body_src"] = m.group(2)
        for key in ("title", "seo_title", "description", "category", "date", "screen"):
            if not meta.get(key):
                errors.append(f"{path.name}: missing '{key}'")
        if meta.get("category") not in CATEGORIES:
            errors.append(f"{path.name}: unknown category '{meta.get('category')}'")
        if len(meta.get("description", "")) > 165:
            errors.append(f"{path.name}: description is {len(meta['description'])} chars (keep it under 160)")
        if len(meta.get("seo_title", "")) > 65:
            print(f"  note: {path.name}: seo_title is {len(meta['seo_title'])} chars; Google may shorten it")
        meta.setdefault("updated", meta.get("date"))
        meta.setdefault("order", 999)
        meta.setdefault("takeaways", [])
        meta.setdefault("faq", [])
        meta.setdefault("keywords", [])
        posts.append(meta)
    if errors:
        print("\n".join("ERROR " + e for e in errors))
        sys.exit(1)
    posts.sort(key=lambda p: (p["order"], p["slug"]))
    return posts


# ---------------------------------------------------------------- body

def phone_img(screen, root, width=180, lazy=True):
    alt = SCREEN_ALT.get(screen, "Pomorix app screen")
    return (
        f'<div class="phone" style="--w:{width}px">'
        f'<img src="{root}assets/img/screens/{screen}-360.webp" '
        f'srcset="{root}assets/img/screens/{screen}-360.webp 360w, {root}assets/img/screens/{screen}-720.webp 720w" '
        f'sizes="{width}px" width="360" height="800" alt="{esc(alt)}"'
        f'{" loading=" + chr(34) + "lazy" + chr(34) if lazy else ""} decoding="async"></div>'
    )


def play_button(campaign, small=False):
    cls = "play-btn play-btn-sm" if small else "play-btn"
    return (
        f'<a class="{cls}" href="{play_url(campaign)}" rel="noopener" aria-label="Get Pomorix on Google Play">'
        '<svg aria-hidden="true"><use href="#i-play"/></svg>'
        "<span><small>Get it on</small><strong>Google Play</strong></span></a>"
    )


def render_body(post, root):
    body = post["body_src"]
    campaign = "blog-" + post["slug"]

    # App callouts: <aside class="app-callout" data-screen="tasks"> ... </aside>
    def callout(m):
        screen, inner = m.group(1), m.group(2).strip()
        return (
            '<aside class="app-callout">'
            f'<div class="app-callout-media" aria-hidden="false">{phone_img(screen, root, 150)}</div>'
            '<div class="app-callout-copy"><span class="app-callout-tag">'
            f'<img src="{root}assets/img/icons/pomorix-logo-128.webp" alt="" width="22" height="22" loading="lazy">Try it in Pomorix</span>'
            f"{inner}<div class=\"app-callout-cta\">{play_button(campaign, small=True)}</div></div></aside>"
        )

    body = re.sub(r'<aside class="app-callout" data-screen="([a-z0-9-]+)">(.*?)</aside>', callout, body, flags=re.S)

    # Tables scroll sideways on small screens
    body = re.sub(r"(<table.*?</table>)", r'<div class="table-wrap">\1</div>', body, flags=re.S)

    # Give every h2 an id and collect the table of contents
    toc = []
    used = set()

    def h2(m):
        attrs, text = m.group(1), m.group(2)
        idm = re.search(r'id="([^"]+)"', attrs)
        hid = idm.group(1) if idm else slugify(text)
        base, n = hid, 2
        while hid in used:
            hid, n = f"{base}-{n}", n + 1
        used.add(hid)
        toc.append((hid, strip_tags(text)))
        if idm:
            return m.group(0)
        return f'<h2 id="{hid}"{attrs}>{text}</h2>'

    body = re.sub(r"<h2([^>]*)>(.*?)</h2>", h2, body, flags=re.S)

    # Root-relative placeholders for links to the home page
    body = body.replace("{root}", root)
    return body, toc


def word_count(post):
    text = strip_tags(post["body_src"]) + " " + " ".join(post["takeaways"])
    text += " " + " ".join(q + " " + a for q, a in post["faq"])
    return len(text.split())


# ---------------------------------------------------------------- page chrome

SPRITE = """  <svg width="0" height="0" style="position:absolute" aria-hidden="true" focusable="false">
    <symbol id="i-menu" viewBox="0 0 24 24"><path d="M4 7h16M4 12h16M4 17h16"/></symbol>
    <symbol id="i-close" viewBox="0 0 24 24"><path d="M6 6l12 12M18 6L6 18"/></symbol>
    <symbol id="i-check" viewBox="0 0 24 24"><path d="M5 12.5l4.5 4.5L19 7.5"/></symbol>
    <symbol id="i-clock" viewBox="0 0 24 24"><circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/></symbol>
    <symbol id="i-arrow" viewBox="0 0 24 24"><path d="M5 12h14M13 6l6 6-6 6"/></symbol>
    <symbol id="i-list" viewBox="0 0 24 24"><path d="M9 6h11M9 12h11M9 18h11M4.5 6h.01M4.5 12h.01M4.5 18h.01"/></symbol>
    <symbol id="i-bulb" viewBox="0 0 24 24"><path d="M9 18h6M10 21h4M12 3a6 6 0 0 0-3.6 10.8c.7.6 1.1 1.3 1.1 2.2h5c0-.9.4-1.6 1.1-2.2A6 6 0 0 0 12 3z"/></symbol>
    <symbol id="i-play" viewBox="0 0 30 33">
      <path fill="#32A071" d="M1.4.9L17.3 16.6 21.6 12.3 3.4.5C2.6 0 1.9.2 1.4.9z"/>
      <path fill="#00A0FF" d="M1.4.9C1.1 1.3.9 1.9.9 2.6v27.8c0 .7.2 1.3.5 1.7l15.9-15.5z"/>
      <path fill="#FF3A44" d="M1.4 32.1c.5.7 1.3.9 2 .4l18.2-11.8-4.3-4.1z"/>
      <path fill="#FFD400" d="M28.2 14.6l-6.6-2.3-4.3 4.3 4.3 4.1 6.6-2.3c1.6-1 1.6-2.8 0-3.8z"/>
    </symbol>
  </svg>"""


def head(*, title, description, canonical, root, og_type, image, image_alt, jsonld, extra=""):
    ld = "\n".join(
        f'  <script type="application/ld+json">\n{json.dumps(obj, ensure_ascii=False, indent=2)}\n  </script>'
        for obj in jsonld
    )
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{esc(title)}</title>
  <meta name="description" content="{esc(description)}">
  <link rel="canonical" href="{canonical}">
  <meta name="robots" content="index, follow, max-image-preview:large">
  <meta name="theme-color" content="#f6f9f7" media="(prefers-color-scheme: light)">
  <meta name="theme-color" content="#0b1411" media="(prefers-color-scheme: dark)">
  <meta property="og:type" content="{og_type}">
  <meta property="og:site_name" content="Pomorix">
  <meta property="og:url" content="{canonical}">
  <meta property="og:title" content="{esc(title)}">
  <meta property="og:description" content="{esc(description)}">
  <meta property="og:image" content="{image}">
  <meta property="og:image:width" content="1200">
  <meta property="og:image:height" content="630">
  <meta property="og:image:alt" content="{esc(image_alt)}">
  <meta property="og:locale" content="en_US">
{extra}  <meta name="twitter:card" content="summary_large_image">
  <meta name="twitter:title" content="{esc(title)}">
  <meta name="twitter:description" content="{esc(description)}">
  <meta name="twitter:image" content="{image}">
  <link rel="alternate" type="application/rss+xml" title="Pomorix blog" href="{SITE}/blog/feed.xml">
  <link rel="icon" href="{root}favicon.ico" sizes="any">
  <link rel="icon" href="{root}favicon-32.png" type="image/png" sizes="32x32">
  <link rel="apple-touch-icon" href="{root}apple-touch-icon.png">
  <link rel="manifest" href="{root}site.webmanifest">
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link rel="stylesheet" href="{FONTS}">
  <link rel="stylesheet" href="{root}assets/css/styles.css">
  <script src="{root}assets/js/main.js" defer></script>
{ld}
</head>"""


def header(root, blog_home):
    blog_link = "./" if blog_home else "../"
    current = ' aria-current="page"' if blog_home else ""
    return f"""  <header class="site-header" id="top">
    <div class="container header-inner">
      <a class="brand" href="{root}" aria-label="Pomorix home">
        <img src="{root}assets/img/icons/pomorix-logo-128.webp" alt="" width="38" height="38">
        <span>Pomorix</span>
      </a>
      <nav class="nav" aria-label="Main">
        <ul class="nav-links" id="nav-links">
          <li><a href="{root}#features">Features</a></li>
          <li><a href="{root}#screenshots">Screenshots</a></li>
          <li><a href="{root}#how-it-works">How it works</a></li>
          <li><a href="{blog_link}"{current}>Blog</a></li>
          <li><a href="{root}#faq">FAQ</a></li>
        </ul>
        <a class="btn btn-primary btn-sm header-cta" href="{play_url('blog-header')}" rel="noopener">Get the app</a>
        <button class="nav-toggle" type="button" aria-controls="nav-links" aria-expanded="false" aria-label="Open menu">
          <svg class="icon" aria-hidden="true"><use href="#i-menu"/></svg>
        </button>
      </nav>
    </div>
  </header>"""


def footer(root, guides):
    blog = f"{root}blog/"
    guide_items = "\n".join(
        f'            <li><a href="{blog}{p["slug"]}/">{esc(p.get("nav_label") or p["title"])}</a></li>' for p in guides
    )
    return f"""  <footer class="site-footer">
    <div class="container">
      <div class="footer-grid footer-grid-5">
        <div>
          <a class="brand" href="{root}" aria-label="Pomorix home">
            <img src="{root}assets/img/icons/pomorix-logo-128.webp" alt="" width="38" height="38" loading="lazy">
            <span>Pomorix</span>
          </a>
          <p>A calm Pomodoro timer, focus timer and study timer for Android.</p>
        </div>
        <div>
          <h2>Product</h2>
          <ul>
            <li><a href="{root}#features">Features</a></li>
            <li><a href="{root}#screenshots">Screenshots</a></li>
            <li><a href="{root}#how-it-works">How it works</a></li>
            <li><a href="{root}#faq">FAQ</a></li>
          </ul>
        </div>
        <div>
          <h2>Guides</h2>
          <ul>
{guide_items}
            <li><a href="{blog}">All articles</a></li>
          </ul>
        </div>
        <div>
          <h2>Get the app</h2>
          <ul>
            <li><a href="{play_url('blog-footer')}" rel="noopener">Google Play</a></li>
            <li><a href="mailto:pomorixapp@gmail.com">pomorixapp@gmail.com</a></li>
          </ul>
        </div>
        <div>
          <h2>Legal</h2>
          <ul>
            <li><a href="{root}privacy-policy.html">Privacy Policy</a></li>
            <li><a href="{root}terms-of-use.html">Terms of Use</a></li>
          </ul>
        </div>
      </div>
      <div class="footer-bottom">
        <span>© 2026 Pomorix. All rights reserved.</span>
        <span>Pomodoro Technique® is a registered trademark of Francesco Cirillo. Pomorix is not affiliated with Francesco Cirillo. Google Play and the Google Play logo are trademarks of Google LLC.</span>
      </div>
    </div>
  </footer>"""


def cta_panel(root, campaign, heading="Ready for your first focus session?", text=None):
    text = text or "Pomorix gives you a Pomodoro timer, Flow mode, tasks, focus sounds and stats that show your progress. Free, no ads, no account."
    return f"""    <section class="section blog-cta-section">
      <div class="container">
        <div class="cta-panel">
          <img src="{root}assets/img/icons/pomorix-logo-256.png" alt="" width="88" height="88" loading="lazy">
          <h2>{esc(heading)}</h2>
          <p>{esc(text)}</p>
          {play_button(campaign)}
          <p class="cta-note">Free · No ads · Android 7.0 and up</p>
        </div>
      </div>
    </section>"""


def cover(post, root, size="800", lazy=True, sizes="(max-width: 640px) 100vw, 380px", cls=""):
    slug = post["slug"]
    return (
        f'<img class="{cls}" src="{root}blog/img/{slug}-800.webp" '
        f'srcset="{root}blog/img/{slug}-800.webp 800w, {root}blog/img/{slug}-1200.webp 1200w" '
        f'sizes="{sizes}" width="1200" height="630" alt=""'
        f'{" loading=" + chr(34) + "lazy" + chr(34) if lazy else " fetchpriority=" + chr(34) + "high" + chr(34)} decoding="async">'
    )


def post_card(post, root, minutes, heading="h3"):
    cat = CATEGORIES[post["category"]]
    return f"""          <li class="post-card" data-cat="{post['category']}">
            <a href="{root}blog/{post['slug']}/">
              <span class="post-card-media cat-{post['category']}">{cover(post, root)}</span>
              <span class="post-card-body">
                <span class="cat-pill cat-{post['category']}">{esc(cat['name'])}</span>
                <{heading} class="post-card-title">{esc(post['title'])}</{heading}>
                <span class="post-card-desc">{esc(post['description'])}</span>
                <span class="post-card-meta"><svg class="icon" aria-hidden="true"><use href="#i-clock"/></svg>{minutes} min read</span>
              </span>
            </a>
          </li>"""


ORG = {"@type": "Organization", "name": "Pomorix", "url": SITE + "/",
       "logo": {"@type": "ImageObject", "url": SITE + "/assets/img/icons/icon-512.png", "width": 512, "height": 512}}


# ---------------------------------------------------------------- pages

def build_post(post, posts, minutes, guides):
    root = "../../"
    slug = post["slug"]
    url = f"{SITE}/blog/{slug}/"
    cat = CATEGORIES[post["category"]]
    body, toc = render_body(post, root)
    image = f"{SITE}/blog/img/{slug}-og.jpg"

    # Related posts: explicit list first, then the same category, then the rest
    by_slug = {p["slug"]: p for p in posts}
    related = [by_slug[s] for s in post.get("related", []) if s in by_slug and s != slug]
    for p in posts:
        if len(related) >= 3:
            break
        if p["slug"] != slug and p not in related and p["category"] == post["category"]:
            related.append(p)
    for p in posts:
        if len(related) >= 3:
            break
        if p["slug"] != slug and p not in related:
            related.append(p)

    jsonld = [
        {
            "@context": "https://schema.org",
            "@type": "BlogPosting",
            "headline": post["title"],
            "description": post["description"],
            "image": [image],
            "datePublished": post["date"],
            "dateModified": post["updated"],
            "author": {"@type": "Organization", "name": "Pomorix team", "url": SITE + "/"},
            "publisher": ORG,
            "mainEntityOfPage": {"@type": "WebPage", "@id": url},
            "articleSection": cat["name"],
            "keywords": ", ".join(post["keywords"]),
            "wordCount": word_count(post),
            "inLanguage": "en",
        },
        {
            "@context": "https://schema.org",
            "@type": "BreadcrumbList",
            "itemListElement": [
                {"@type": "ListItem", "position": 1, "name": "Home", "item": SITE + "/"},
                {"@type": "ListItem", "position": 2, "name": "Blog", "item": SITE + "/blog/"},
                {"@type": "ListItem", "position": 3, "name": post["title"], "item": url},
            ],
        },
    ]
    if post["faq"]:
        jsonld.append({
            "@context": "https://schema.org",
            "@type": "FAQPage",
            "mainEntity": [
                {"@type": "Question", "name": strip_tags(q),
                 "acceptedAnswer": {"@type": "Answer", "text": strip_tags(a)}}
                for q, a in post["faq"]
            ],
        })

    extra = (
        f'  <meta property="article:published_time" content="{post["date"]}">\n'
        f'  <meta property="article:modified_time" content="{post["updated"]}">\n'
        f'  <meta property="article:section" content="{esc(cat["name"])}">\n'
    )

    toc_items = "\n".join(f'              <li><a href="#{hid}">{esc(text)}</a></li>' for hid, text in toc)
    if post["faq"]:
        toc_items += '\n              <li><a href="#faq">Questions people ask</a></li>'

    takeaways = ""
    if post["takeaways"]:
        items = "\n".join(f"              <li>{t}</li>" for t in post["takeaways"])
        takeaways = f"""          <div class="takeaways">
            <p class="takeaways-title"><svg class="icon" aria-hidden="true"><use href="#i-bulb"/></svg>Key takeaways</p>
            <ul>
{items}
            </ul>
          </div>
"""

    faq = ""
    if post["faq"]:
        items = "\n".join(
            f"""            <details>
              <summary>{q}</summary>
              <div class="answer"><p>{a}</p></div>
            </details>""" for q, a in post["faq"]
        )
        faq = f"""          <section class="post-faq" aria-labelledby="faq">
            <h2 id="faq">Questions people ask</h2>
            <div class="faq-list">
{items}
            </div>
          </section>
"""

    updated = ""
    if post["updated"] != post["date"]:
        updated = f' · Updated <time datetime="{post["updated"]}">{fmt_date(post["updated"])}</time>'

    related_cards = "\n".join(post_card(p, root, minutes[p["slug"]]) for p in related)

    page = f"""{head(title=post['seo_title'], description=post['description'], canonical=url, root=root, og_type='article', image=image, image_alt=post['title'], jsonld=jsonld, extra=extra)}
<body>
  <a class="skip-link" href="#main">Skip to content</a>
{SPRITE}

{header(root, False)}

  <main id="main">
    <article class="post">
      <header class="post-hero">
        <div class="container post-hero-inner">
          <nav class="breadcrumb" aria-label="Breadcrumb">
            <ol>
              <li><a href="{root}">Home</a></li>
              <li><a href="../">Blog</a></li>
              <li><span>{esc(cat['name'])}</span></li>
            </ol>
          </nav>
          <span class="cat-pill cat-{post['category']}">{esc(cat['name'])}</span>
          <h1>{esc(post['title'])}</h1>
          <p class="post-dek">{esc(post['description'])}</p>
          <p class="post-meta">By the Pomorix team · <time datetime="{post['date']}">{fmt_date(post['date'])}</time>{updated} · {minutes[slug]} min read</p>
        </div>
        <div class="container post-cover cat-{post['category']}">
          {cover(post, root, lazy=False, sizes="(max-width: 1180px) 100vw, 1180px")}
        </div>
      </header>

      <div class="container post-layout">
        <aside class="post-aside">
          <nav class="toc" aria-label="On this page">
            <p class="toc-title"><svg class="icon" aria-hidden="true"><use href="#i-list"/></svg>On this page</p>
            <ol>
{toc_items}
            </ol>
          </nav>
          <div class="aside-app">
            <img src="{root}assets/img/icons/pomorix-logo-128.webp" alt="" width="48" height="48" loading="lazy">
            <p><strong>Pomorix</strong>Pomodoro &amp; study focus timer for Android</p>
            <ul>
              <li><svg class="icon" aria-hidden="true"><use href="#i-check"/></svg>Pomodoro + Flow mode</li>
              <li><svg class="icon" aria-hidden="true"><use href="#i-check"/></svg>Tasks, stats &amp; streaks</li>
              <li><svg class="icon" aria-hidden="true"><use href="#i-check"/></svg>Free, no ads, no account</li>
            </ul>
            {play_button('blog-' + slug + '-aside', small=True)}
          </div>
        </aside>

        <div class="post-content">
          <details class="toc-mobile">
            <summary>On this page</summary>
            <ol>
{toc_items}
            </ol>
          </details>
{takeaways}          <div class="prose">
{body.strip()}
          </div>
{faq}        </div>
      </div>
    </article>

    <section class="section related" aria-labelledby="related-title">
      <div class="container">
        <h2 class="related-title" id="related-title">Keep reading</h2>
        <ul class="post-grid">
{related_cards}
        </ul>
      </div>
    </section>

{cta_panel(root, 'blog-' + slug + '-end', post.get('cta_heading', 'Ready for your first focus session?'), post.get('cta_text'))}
  </main>

{footer(root, guides)}
</body>
</html>
"""
    out = OUT / slug / "index.html"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(page, encoding="utf-8")


def build_index(posts, minutes, guides):
    root = "../"
    url = f"{SITE}/blog/"
    featured = next((p for p in posts if p.get("featured")), posts[0])
    rest = [p for p in posts if p is not featured]
    title = "Pomodoro, Study & Focus Guides | Pomorix Blog"
    description = "Practical guides to the Pomodoro Technique, studying, deep focus and building habits, from the team behind the Pomorix focus timer."

    jsonld = [
        {
            "@context": "https://schema.org",
            "@type": "Blog",
            "name": "Pomorix Blog",
            "url": url,
            "description": description,
            "publisher": ORG,
            "inLanguage": "en",
            "blogPost": [
                {"@type": "BlogPosting", "headline": p["title"], "url": f"{SITE}/blog/{p['slug']}/",
                 "datePublished": p["date"], "image": f"{SITE}/blog/img/{p['slug']}-og.jpg"}
                for p in posts
            ],
        },
        {
            "@context": "https://schema.org",
            "@type": "BreadcrumbList",
            "itemListElement": [
                {"@type": "ListItem", "position": 1, "name": "Home", "item": SITE + "/"},
                {"@type": "ListItem", "position": 2, "name": "Blog", "item": url},
            ],
        },
    ]

    chips = ['<button class="chip" type="button" data-filter="all" aria-pressed="true">All topics</button>']
    for key, cat in CATEGORIES.items():
        count = sum(1 for p in rest if p["category"] == key)
        chips.append(f'<button class="chip" type="button" data-filter="{key}" aria-pressed="false">{esc(cat["name"])} <span>{count}</span></button>')
    chips_html = "\n            ".join(chips)

    fcat = CATEGORIES[featured["category"]]
    cards = "\n".join(post_card(p, root, minutes[p["slug"]], heading="h2") for p in rest)

    page = f"""{head(title=title, description=description, canonical=url, root=root, og_type='website', image=SITE + '/assets/img/og-image.jpg', image_alt='Pomorix blog: Pomodoro, study and focus guides', jsonld=jsonld)}
<body>
  <a class="skip-link" href="#main">Skip to content</a>
{SPRITE}

{header(root, True)}

  <main id="main">
    <section class="blog-hero">
      <div class="container">
        <nav class="breadcrumb" aria-label="Breadcrumb">
          <ol>
            <li><a href="{root}">Home</a></li>
            <li><span aria-current="page">Blog</span></li>
          </ol>
        </nav>
        <span class="eyebrow">The Pomorix blog</span>
        <h1>Focus better, study smarter, <span class="accent">get more done.</span></h1>
        <p class="lead">Practical guides to the Pomodoro Technique, studying, deep work and lasting habits. Short on theory, long on what to do next.</p>
      </div>
    </section>

    <section class="blog-featured" aria-label="Start here">
      <div class="container">
        <a class="featured-card" href="{featured['slug']}/">
          <span class="featured-media cat-{featured['category']}">{cover(featured, root, lazy=False, sizes="(max-width: 960px) 100vw, 640px")}</span>
          <span class="featured-body">
            <span class="featured-label">Start here</span>
            <span class="cat-pill cat-{featured['category']}">{esc(fcat['name'])}</span>
            <span class="featured-title">{esc(featured['title'])}</span>
            <span class="post-card-desc">{esc(featured['description'])}</span>
            <span class="post-card-meta"><svg class="icon" aria-hidden="true"><use href="#i-clock"/></svg>{minutes[featured['slug']]} min read<span class="read-more">Read the guide<svg class="icon" aria-hidden="true"><use href="#i-arrow"/></svg></span></span>
          </span>
        </a>
      </div>
    </section>

    <section class="blog-list" aria-labelledby="all-articles">
      <div class="container">
        <div class="blog-list-head">
          <h2 id="all-articles">All articles</h2>
          <div class="chips" role="group" aria-label="Filter by topic">
            {chips_html}
          </div>
        </div>
        <ul class="post-grid" id="post-grid">
{cards}
        </ul>
      </div>
    </section>

{cta_panel(root, 'blog-index', 'Turn reading into focused hours', 'Pomorix puts these guides into practice: a Pomodoro timer, Flow mode, tasks, focus sounds, goals and streaks. Free, no ads, no account.')}
  </main>

{footer(root, guides)}
</body>
</html>
"""
    (OUT / "index.html").write_text(page, encoding="utf-8")


def build_feed(posts):
    newest = sorted(posts, key=lambda p: (p["date"], -p["order"]), reverse=True)
    items = "\n".join(
        f"""    <item>
      <title>{esc(p['title'])}</title>
      <link>{SITE}/blog/{p['slug']}/</link>
      <guid isPermaLink="true">{SITE}/blog/{p['slug']}/</guid>
      <pubDate>{rfc822(p['date'])}</pubDate>
      <category>{esc(CATEGORIES[p['category']]['name'])}</category>
      <description>{esc(p['description'])}</description>
    </item>""" for p in newest
    )
    last = max(p["updated"] for p in posts)
    feed = f"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom">
  <channel>
    <title>Pomorix Blog</title>
    <link>{SITE}/blog/</link>
    <atom:link href="{SITE}/blog/feed.xml" rel="self" type="application/rss+xml"/>
    <description>Guides to the Pomodoro Technique, studying, focus and habits from the team behind Pomorix.</description>
    <language>en</language>
    <lastBuildDate>{rfc822(last)}</lastBuildDate>
{items}
  </channel>
</rss>
"""
    (OUT / "feed.xml").write_text(feed, encoding="utf-8")


def build_sitemap(posts):
    rows = []
    for path, lastmod, freq, prio in STATIC_PAGES[:1]:
        rows.append((f"{SITE}/{path}", lastmod, freq, prio))
    rows.append((f"{SITE}/blog/", max(p["updated"] for p in posts), "weekly", "0.8"))
    for p in posts:
        rows.append((f"{SITE}/blog/{p['slug']}/", p["updated"], "monthly", "0.7"))
    for path, lastmod, freq, prio in STATIC_PAGES[1:]:
        rows.append((f"{SITE}/{path}", lastmod, freq, prio))
    body = "\n".join(
        f"""  <url>
    <loc>{loc}</loc>
    <lastmod>{lastmod}</lastmod>
    <changefreq>{freq}</changefreq>
    <priority>{prio}</priority>
  </url>""" for loc, lastmod, freq, prio in rows
    )
    (ROOT / "sitemap.xml").write_text(
        f'<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n{body}\n</urlset>\n',
        encoding="utf-8",
    )


def update_home(posts, minutes):
    """Refresh the 'From the blog' cards between the markers in index.html."""
    home = ROOT / "index.html"
    text = home.read_text(encoding="utf-8")
    start, end = "<!-- blog:latest:start -->", "<!-- blog:latest:end -->"
    if start not in text or end not in text:
        print("  note: index.html has no blog markers; skipped the home page block")
        return
    picks = [p for p in posts if p.get("home")][:3] or posts[:3]
    cards = "\n".join(post_card(p, "", minutes[p["slug"]]) for p in picks)
    block = f"{start}\n        <ul class=\"post-grid\">\n{cards}\n        </ul>\n        {end}"
    text = re.sub(re.escape(start) + r".*?" + re.escape(end), lambda _: block, text, flags=re.S)
    home.write_text(text, encoding="utf-8")


def check_links(posts):
    """Make sure every relative link in the built blog points at a real file."""
    problems = []
    for page in [OUT / "index.html"] + [OUT / p["slug"] / "index.html" for p in posts]:
        text = page.read_text(encoding="utf-8")
        ids = set(re.findall(r'id="([^"]+)"', text))
        for href in re.findall(r'(?:href|src)="([^"]+)"', text):
            if href.startswith(("http", "mailto:", "data:")):
                continue
            path, _, frag = href.partition("#")
            if not path:
                if frag and frag not in ids:
                    problems.append(f"{page.relative_to(ROOT)}: missing anchor #{frag}")
                continue
            target = (page.parent / path).resolve()
            if target.is_dir():
                target = target / "index.html"
            if not target.exists():
                problems.append(f"{page.relative_to(ROOT)}: broken link {href}")
        for srcset in re.findall(r'srcset="([^"]+)"', text):
            for part in srcset.split(","):
                src = part.strip().split(" ")[0]
                if not (page.parent / src).resolve().exists():
                    problems.append(f"{page.relative_to(ROOT)}: missing image {src}")
    return problems


FOLDER_LINK = re.compile(r'href="((?:\.{1,2}/|[a-z0-9-]+/)(?:[^":#?]*/)?)(#[^"]*)?"')


def point_links_at_files():
    """Turn folder links like "blog/" or "../#faq" into "blog/index.html" and
    "../index.html#faq". Web servers add index.html by themselves, but a browser
    opening the files straight from disk does not, so this keeps every page
    working both on GitHub Pages and from a local folder."""
    pages = [ROOT / "index.html", ROOT / "privacy-policy.html", ROOT / "terms-of-use.html", OUT / "index.html"]
    pages += sorted(OUT.glob("*/index.html"))
    for page in pages:
        text = page.read_text(encoding="utf-8")
        fixed = FOLDER_LINK.sub(lambda m: f'href="{m.group(1)}index.html{m.group(2) or ""}"', text)
        if fixed != text:
            page.write_text(fixed, encoding="utf-8")


def main():
    posts = load_posts()
    minutes = {p["slug"]: max(1, round(word_count(p) / 230)) for p in posts}
    guides = [p for p in posts if p.get("footer")][:5]
    OUT.mkdir(exist_ok=True)
    for p in posts:
        build_post(p, posts, minutes, guides)
    build_index(posts, minutes, guides)
    build_feed(posts)
    build_sitemap(posts)
    update_home(posts, minutes)
    point_links_at_files()
    problems = check_links(posts)
    total = sum(word_count(p) for p in posts)
    print(f"Built {len(posts)} posts ({total:,} words) into blog/, plus feed.xml and sitemap.xml")
    missing_covers = [p["slug"] for p in posts if not (OUT / "img" / f"{p['slug']}-og.jpg").exists()]
    if missing_covers:
        print("  note: no cover images yet for: " + ", ".join(missing_covers) + " (run _blog/make_covers.py)")
    if problems:
        print("\n".join("LINK " + x for x in problems))
        sys.exit(1)


if __name__ == "__main__":
    main()
