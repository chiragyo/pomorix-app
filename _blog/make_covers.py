#!/usr/bin/env python3
"""Make the cover images for blog posts.

For each post in _blog/posts it writes, into blog/img/:
  <slug>-1200.webp, <slug>-800.webp   card / page art (app screen, no title text)
  <slug>-og.jpg                       1200 x 630 social preview with the title

Needs Pillow (pip install pillow). Existing images are skipped unless you pass
--force or name the slugs to redo:
  python3 _blog/make_covers.py
  python3 _blog/make_covers.py --force
  python3 _blog/make_covers.py pomodoro-technique
"""
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont

sys.path.insert(0, str(Path(__file__).resolve().parent))
import build  # noqa: E402

W, H = 1200, 630
FONT_FILE = "/System/Library/Fonts/Avenir Next.ttc"  # macOS; swap for any bold sans on other systems
HEAVY, DEMI, MEDIUM = 8, 2, 5

PALETTES = {
    "pomodoro": ((214, 84, 60), (92, 26, 20)),
    "study": ((84, 96, 214), (28, 32, 104)),
    "focus": ((19, 132, 106), (2, 61, 58)),
    "habits": ((214, 138, 44), (104, 54, 12)),
}


def font(index, size):
    try:
        return ImageFont.truetype(FONT_FILE, size, index=index)
    except OSError:
        return ImageFont.load_default(size)


def background(cat):
    c1, c2 = PALETTES[cat]
    base = Image.new("RGB", (W, H))
    px = base.load()
    for y in range(H):
        for x in range(W):
            t = min(1.0, max(0.0, (x * 0.55 + y) / (W * 0.55 + H)))
            px[x, y] = tuple(int(c1[i] + (c2[i] - c1[i]) * t) for i in range(3))
    glow = Image.new("L", (W, H), 0)
    ImageDraw.Draw(glow).ellipse((620, -260, 1340, 460), fill=120)
    glow = glow.filter(ImageFilter.GaussianBlur(120))
    base = Image.composite(Image.new("RGB", (W, H), (255, 255, 255)), base, glow.point(lambda v: int(v * 0.35)))
    return base.convert("RGBA")


def rings(img, cx, cy):
    layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    for r, a in ((330, 40), (250, 28), (410, 20)):
        d.ellipse((cx - r, cy - r, cx + r, cy + r), outline=(255, 255, 255, a), width=2)
    d.arc((cx - 330, cy - 330, cx + 330, cy + 330), 200, 250, fill=(255, 255, 255, 120), width=6)
    return Image.alpha_composite(img, layer)


def phone(img, screen, cx, top, width=290):
    shot = Image.open(build.ROOT / "assets/img/screens" / f"{screen}-720.webp").convert("RGBA")
    h = int(shot.height * width / shot.width)
    shot = shot.resize((width, h), Image.LANCZOS)
    radius = int(width * 0.12)
    mask = Image.new("L", shot.size, 0)
    ImageDraw.Draw(mask).rounded_rectangle((0, 0, width - 1, h - 1), radius, fill=255)
    pad = 11
    bw, bh = width + pad * 2, h + pad * 2
    left = cx - bw // 2
    shadow = Image.new("RGBA", img.size, (0, 0, 0, 0))
    ImageDraw.Draw(shadow).rounded_rectangle((left + 10, top + 30, left + bw + 10, top + bh + 30), radius + pad, fill=(0, 0, 0, 120))
    img = Image.alpha_composite(img, shadow.filter(ImageFilter.GaussianBlur(28)))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle((left, top, left + bw, top + bh), radius + pad, fill=(12, 20, 17, 255))
    img.paste(shot, (left + pad, top + pad), mask)
    cam = left + bw // 2
    d = ImageDraw.Draw(img)
    d.ellipse((cam - 7, top + pad + 12, cam + 7, top + pad + 26), fill=(12, 20, 17, 255))
    return img


def wrap(draw, text, fnt, width):
    words, lines, line = text.split(), [], ""
    for w in words:
        test = (line + " " + w).strip()
        if draw.textlength(test, font=fnt) <= width:
            line = test
        else:
            lines.append(line)
            line = w
    lines.append(line)
    return lines


def card_art(post):
    img = background(post["category"])
    img = rings(img, 860, 330)
    img = phone(img, post["screen"], 860, 92)
    layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    cat = build.CATEGORIES[post["category"]]
    d.text((72, 236), "POMORIX GUIDE", font=font(DEMI, 24), fill=(255, 255, 255, 190))
    d.text((68, 268), cat["short"], font=font(HEAVY, 96), fill=(255, 255, 255, 245))
    return Image.alpha_composite(img, layer).convert("RGB")


def og_art(post):
    img = background(post["category"])
    img = rings(img, 960, 330)
    img = phone(img, post["screen"], 960, 104, width=270)
    layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    cat = build.CATEGORIES[post["category"]]

    pill_font = font(DEMI, 24)
    tw = d.textlength(cat["name"].upper(), font=pill_font)
    d.rounded_rectangle((64, 64, 64 + tw + 40, 110), 23, fill=(255, 255, 255, 46))
    d.text((84, 72), cat["name"].upper(), font=pill_font, fill=(255, 255, 255, 235))

    title = post.get("og_title") or post["title"]
    for size in (62, 56, 50, 46, 42):
        tf = font(HEAVY, size)
        lines = wrap(d, title, tf, 680)
        if len(lines) <= 4:
            break
    y = 146
    for line in lines:
        d.text((64, y), line, font=tf, fill=(255, 255, 255, 255))
        y += int(size * 1.16)

    logo = Image.open(build.ROOT / "assets/img/icons/pomorix-logo-256.png").convert("RGBA").resize((56, 56), Image.LANCZOS)
    m = Image.new("L", (56, 56), 0)
    ImageDraw.Draw(m).rounded_rectangle((0, 0, 55, 55), 15, fill=255)
    d.text((136, 520), "Pomorix", font=font(HEAVY, 28), fill=(255, 255, 255, 255))
    d.text((136, 552), "pomorix.com", font=font(MEDIUM, 21), fill=(255, 255, 255, 200))
    img = Image.alpha_composite(img, layer)
    img.paste(logo, (64, 518), m)
    return img.convert("RGB")


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("-")]
    force = "--force" in sys.argv
    out = build.OUT / "img"
    out.mkdir(parents=True, exist_ok=True)
    made = 0
    for post in build.load_posts():
        slug = post["slug"]
        if args and slug not in args:
            continue
        if not force and not args and (out / f"{slug}-og.jpg").exists():
            continue
        art = card_art(post)
        art.save(out / f"{slug}-1200.webp", "WEBP", quality=80, method=6)
        art.resize((800, 420), Image.LANCZOS).save(out / f"{slug}-800.webp", "WEBP", quality=78, method=6)
        og_art(post).save(out / f"{slug}-og.jpg", "JPEG", quality=84, optimize=True, progressive=True)
        made += 1
        print("  cover:", slug)
    print(f"Made covers for {made} post(s).")


if __name__ == "__main__":
    main()
