# Pomorix website

The marketing site for **Pomorix**, the Pomodoro and study focus timer for Android, served at **https://pomorix.com**.

It is a plain static site: HTML, one CSS file and one small JS file. There is no build step, no framework and no backend, so it runs free on GitHub Pages.

## What's in the folder

```
index.html            Home page (hero, features, screenshots, how it works, FAQ, download)
privacy-policy.html   Privacy Policy (the app links to this exact URL)
terms-of-use.html     Terms of Use (the app links to this exact URL)
404.html              "Page not found" page, used by GitHub Pages automatically
assets/css/styles.css All styles (light and dark themes follow the visitor's system setting)
assets/js/main.js     Mobile menu, screenshot carousel buttons, scroll animations
assets/img/screens/   App screenshots (WebP, 360 px and 720 px wide)
assets/img/icons/     Logo and app icons
assets/img/og-image.jpg  Social preview image (1200 × 630)
favicon.ico, favicon-32.png, apple-touch-icon.png, site.webmanifest
robots.txt, sitemap.xml  For search engines (sitemap.xml is written by the blog builder)
blog/                 The built blog: blog/index.html, one folder per post, feed.xml, img/
_blog/posts/          Blog post sources (edit these, not blog/)
_blog/build.py        Builds the blog pages, RSS feed, sitemap and the home page "From the blog" cards
_blog/make_covers.py  Makes each post's cover and social images
CNAME                 Tells GitHub Pages to serve the site on pomorix.com
.nojekyll             Tells GitHub Pages to serve the files as they are
```

`_legacy_flutter_site/` holds the old Flutter web version of the site. It is listed in `.gitignore`, so it never gets uploaded or published. Delete it once you no longer need it.

## Preview on your computer

```bash
cd pomorix_web
python3 -m http.server 8000
```

Then open http://localhost:8000. You can also just double-click `index.html`: every page and link works from the folder too.

## Publish on GitHub Pages

1. Create a new repository on GitHub, for example `pomorix-website`. It can be public, or private on a paid GitHub plan.
2. Upload this folder:

   ```bash
   cd pomorix_web
   git init -b main
   git add .
   git commit -m "Pomorix website"
   git remote add origin https://github.com/YOUR-USERNAME/pomorix-website.git
   git push -u origin main
   ```

3. On GitHub, open the repository's **Settings → Pages**.
4. Under **Build and deployment**, set **Source** to **Deploy from a branch**, then pick branch **main** and folder **/ (root)**, and click **Save**.
5. GitHub publishes the site in a minute or two. You can watch progress in the repository's **Actions** tab.

## Connect your domain (pomorix.com)

The `CNAME` file already contains `pomorix.com`, so GitHub knows which domain to serve.

**1. Add DNS records at your domain registrar** (GoDaddy, Namecheap, Cloudflare, Google Domains/Squarespace and so on):

| Type  | Host / Name | Value                     |
|-------|-------------|---------------------------|
| A     | @           | 185.199.108.153           |
| A     | @           | 185.199.109.153           |
| A     | @           | 185.199.110.153           |
| A     | @           | 185.199.111.153           |
| AAAA  | @           | 2606:50c0:8000::153       |
| AAAA  | @           | 2606:50c0:8001::153       |
| AAAA  | @           | 2606:50c0:8002::153       |
| AAAA  | @           | 2606:50c0:8003::153       |
| CNAME | www         | YOUR-USERNAME.github.io   |

Remove any older A, AAAA or CNAME records for `@` and `www` that point elsewhere (for example a registrar "parking" page). If you use Cloudflare, set these records to **DNS only** (grey cloud) until HTTPS is working.

**2. In GitHub → Settings → Pages**, type `pomorix.com` under **Custom domain** and click **Save**. GitHub checks the DNS; this can take from a few minutes up to 24 hours.

**3. Tick "Enforce HTTPS"** once GitHub has issued the certificate (the box becomes clickable when it's ready).

With these records, `www.pomorix.com` redirects to `pomorix.com` automatically.

**Recommended:** verify the domain in your GitHub account (**Settings → Pages → Add a verified domain**, from your profile settings, not the repository). This stops anyone else from using pomorix.com on GitHub Pages.

The IP addresses above are GitHub's published Pages addresses. If GitHub ever changes them, its guide "Managing a custom domain for your GitHub Pages site" has the current list.

## After the site is live

- **Google Search Console:** add `pomorix.com` as a property, verify it with a DNS TXT record, and submit `https://pomorix.com/sitemap.xml` under **Sitemaps**.
- **Check the social preview:** paste `https://pomorix.com` into a link preview checker (for example LinkedIn's Post Inspector) to see the card.
- **Play Console:** set the website field of the store listing to `https://pomorix.com`.
- **Measure installs from the site:** every Google Play button carries a `referrer` with `utm_source=pomorix.com` and a campaign name (`header`, `hero`, `final_cta`, `footer`). These show up in Play Console's acquisition reports.

## The blog

The blog lives at `https://pomorix.com/blog/`, with each article at `/blog/<slug>/`. There are 20 articles in four topics: Pomodoro Technique, Studying, Focus & Productivity, and Habits & Tracking.

You write posts in `_blog/posts/`, and a small script turns them into finished pages. **Don't edit files in `blog/` by hand**: the next build overwrites them.

### What the builder does for every post

- Page title, meta description, canonical URL, Open Graph and Twitter tags
- Structured data: `BlogPosting`, `BreadcrumbList`, and `FAQPage` when the post has questions
- Table of contents, reading time, "Key takeaways" box, FAQ section and three related posts
- Google Play buttons tagged `utm_medium=blog` and `utm_campaign=blog-<slug>`, so Play Console shows which article brought each install
- The blog home page, `blog/feed.xml` (RSS), the whole-site `sitemap.xml`, and the three "From the blog" cards on the home page
- A link check: the build stops if any link or image is broken

### Write a new post

1. Copy an existing file in `_blog/posts/` and rename it. The file name becomes the URL, so use the search phrase in lowercase with dashes (for example `pomodoro-for-reading.html`).
2. Edit the header between the `---` lines. It is JSON, so keep the double quotes and commas.

   | Field | What it is |
   |---|---|
   | `title` | The H1 on the page |
   | `seo_title` | The browser/Google title, ideally under 60 characters |
   | `og_title` | Optional shorter title for the social image |
   | `description` | Google snippet, 140 to 160 characters |
   | `category` | `pomodoro`, `study`, `focus` or `habits` |
   | `date` / `updated` | `YYYY-MM-DD`. Set `updated` when you revise a post |
   | `order` | Position on the blog home page |
   | `screen` | The app screenshot on the cover, a name from `assets/img/screens/` without `-360.webp` |
   | `keywords` | Search phrases the post targets |
   | `related` | Up to 3 slugs to show under "Keep reading" |
   | `takeaways` | 3 to 4 short bullet points |
   | `faq` | Question and answer pairs (plain text) |
   | `featured`, `home`, `footer` | Optional: the "Start here" post, the 3 posts on the home page, the 5 links in the footer |

3. Write the body in plain HTML: `<h2>` for sections (these build the table of contents), `<h3>`, `<p>`, lists and `<table>`. Link to other posts with `../other-slug/`.
4. To add an app promotion box, use:

   ```html
   <aside class="app-callout" data-screen="tasks">
   <h3>Short heading</h3>
   <p>One or two sentences about a real Pomorix feature.</p>
   </aside>
   ```

   The builder adds the phone screenshot and the Google Play button.
5. Build:

   ```bash
   cd pomorix_web
   python3 _blog/make_covers.py
   python3 _blog/build.py
   ```

   `make_covers.py` needs Pillow (`pip3 install pillow`) and the Avenir Next font that comes with macOS. It only makes images for posts that don't have them yet. Add `--force` to redo all of them.
6. Preview locally, then commit and push. GitHub Pages publishes the new files.

Keep app claims to features Pomorix really has. The Play listing (`docs/play_store/en-US_listing.txt` in the app project) is the reference.

### Helping the blog rank

- After publishing, open Google Search Console and use **URL Inspection → Request indexing** for each new post. Resubmit `sitemap.xml` under **Sitemaps**.
- Publish regularly. One or two new posts a month does more than many posts at once.
- Link every new post from 2 or 3 older posts on the same topic, and back to the pillar guides (`pomodoro-technique`, `pomodoro-technique-for-studying`).
- Update posts that start getting impressions in Search Console. Improve the title, answer more questions, then set `updated`.
- Share posts where your users already are: study subreddits, student Discord servers, Quora answers, Medium or LinkedIn (with a link back), and the "website" field on the Play listing.
- In Play Console, check acquisition by `utm_campaign` to see which articles bring installs, then write more like them.

### Ideas for the next posts

Each targets a common search and leads naturally to a Pomorix feature:

1. Pomodoro Technique for reading (categories, Reading default length)
2. Pomodoro for writing a thesis or dissertation (tasks with session estimates)
3. Study with me: how to recreate the feeling alone (focus sounds, timer)
4. Active recall vs rereading: how to study for exams (study sessions)
5. Spaced repetition schedule for exams (tasks, journal)
6. How to study at night without wrecking your sleep (day start time setting)
7. Time blocking vs Pomodoro: how to use both
8. The 52/17 rule explained
9. How to focus when working from home (auto Do Not Disturb)
10. Study break games: do they help? (Focus Pulse)
11. How to stay motivated to study (goals, streaks)
12. Morning study routine for students
13. How to study for long hours without burning out
14. Pomodoro for language learning
15. How to use a focus journal to improve your study sessions (journal and notes)

## Making changes

- **Text:** edit `index.html` directly. If you change an FAQ answer, update the matching answer in the `FAQPage` JSON-LD block near the top of the file, so search engines see the same text as visitors.
- **Screenshots:** replace files in `assets/img/screens/` with new ones of the same name. Each screen has two sizes: `-360.webp` and `-720.webp` (1080 × 2400 phone screenshots scaled to 360 and 720 px wide).
- **Legal pages:** edit `privacy-policy.html` and `terms-of-use.html`. Keep these file names: the Android app links to them.
- **New pages:** give the page its own `<title>`, description and canonical link, and add it to `STATIC_PAGES` in `_blog/build.py` so it stays in the sitemap (the build rewrites `sitemap.xml`).
- **Sitemap dates:** blog dates come from each post's `updated` field. For other pages, update the date in `STATIC_PAGES` in `_blog/build.py`, then rebuild.

## Notes

- All links between pages are relative and point at real files (`blog/index.html`, not `blog/`), so the site works in three places with no changes: opened straight from this folder (double-click `index.html`), at `YOUR-USERNAME.github.io/pomorix-website/`, and on pomorix.com. `python3 _blog/build.py` rewrites any `folder/` link to `folder/index.html` on every page, so keep running it after edits. Canonical tags and the sitemap still use the clean addresses (`/blog/`), so Google indexes those. The only exception is `404.html`, which uses root paths because GitHub serves it at any missing address; it looks right once the custom domain is live.
- The site has no cookies, analytics or trackers. Fonts load from Google Fonts.
- Google Play and the Google Play logo are trademarks of Google LLC. The Play button is drawn in code and links to the official listing.
