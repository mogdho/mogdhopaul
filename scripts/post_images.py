"""Cover images for blog posts: a dark glass card with the post's title, topic and author.

Usage:  python -m scripts.post_images
For each post in content/posts.json, writes blog/<slug>/og.jpg (1200x630: the top of the article
and its share preview) and blog/<slug>/thumb.webp (the blog page's thumbnail). A post's images are
made again only when its title or topic changes (blog/images.json remembers what each was made from).

The card is drawn by headless Chrome, so this needs Chrome (or Chromium) and Pillow. Without them it
says so and changes nothing: the site then simply shows the post without an image.
"""
import glob
import hashlib
import html
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DESIGN = "glass-dark-1"  # change this to remake every card after a design change
TOPIC_LABEL = {"windows": "Windows", "chrome": "Chrome", "money": "Money", "other": "Life"}
# the site's greens glowing through a near-black background, placed a little differently per topic
GLOWS = {
    "windows": ["#1f7a5a", "#0f4d3a", "#3fa37c"],
    "chrome": ["#0f4d3a", "#2f8a68", "#3fa37c"],
    "money": ["#2f8a68", "#1f7a5a", "#9db5a8"],
    "other": ["#3fa37c", "#0f4d3a", "#2f8a68"],
}
SIZE, THUMB = (1200, 630), (480, 252)

CSS = """
@font-face { font-family: "Card Serif"; src: url("FONTS/young-serif-400.woff2"); }
@font-face { font-family: "Card Sans"; src: url("FONTS/schibsted-grotesk.woff2"); font-weight: 400 700; }
@font-face { font-family: "Card Mono"; src: url("FONTS/share-tech-mono-400.woff2"); }
html, body { margin: 0; width: 1200px; height: 630px; overflow: hidden; }
body { position: relative; background: #0b100e; font-family: "Card Sans"; color: #f4f6ef; }
.blob { position: absolute; border-radius: 50%; filter: blur(80px); opacity: .7; }
.b1 { width: 560px; height: 560px; left: -120px; top: -160px; }
.b2 { width: 620px; height: 620px; right: -160px; bottom: -260px; }
.b3 { width: 380px; height: 380px; left: 640px; top: 120px; opacity: .45; }
.glass {
  position: absolute; inset: 56px; box-sizing: border-box; padding: 52px 60px 44px;
  display: flex; flex-direction: column;
  background: rgba(255, 255, 255, 0.06); border: 1px solid rgba(255, 255, 255, 0.22); border-radius: 28px;
  backdrop-filter: blur(26px) saturate(140%);
  box-shadow: 0 20px 60px rgba(5, 25, 18, 0.35), inset 0 1px 0 rgba(255, 255, 255, 0.35);
}
.kicker { font-family: "Card Mono"; font-size: 24px; letter-spacing: .14em; text-transform: uppercase;
          color: rgba(244, 246, 239, .85); }
h1 { margin: auto 0; font-family: "Card Serif"; font-weight: 400; line-height: 1.05; letter-spacing: -0.015em;
     text-shadow: 0 2px 18px rgba(5, 25, 18, 0.25); }
.foot { display: flex; align-items: center; justify-content: space-between; padding-top: 24px;
        border-top: 1px solid rgba(255, 255, 255, 0.28); }
.author { display: flex; align-items: center; gap: 16px; font-size: 26px; font-weight: 600; }
.mark { display: grid; place-items: center; width: 48px; height: 48px; border-radius: 50%;
        background: rgba(255, 255, 255, .18); border: 1px solid rgba(255, 255, 255, .45);
        font-family: "Card Mono"; font-size: 19px; letter-spacing: .04em; }
.site { font-family: "Card Mono"; font-size: 22px; letter-spacing: .08em; color: rgba(244, 246, 239, .8); }
"""


def card_html(post, fonts_url):
    c1, c2, c3 = GLOWS[post["topic"]]
    n = len(post["title"])
    size = 76 if n <= 50 else 66 if n <= 66 else 58
    return (f"<!doctype html><meta charset=utf-8><style>{CSS.replace('FONTS', fonts_url)}</style>"
            f"<div class='blob b1' style='background:{c1}'></div>"
            f"<div class='blob b2' style='background:{c2}'></div>"
            f"<div class='blob b3' style='background:{c3}'></div>"
            "<div class=glass>"
            f"<div class=kicker>Blog · {TOPIC_LABEL[post['topic']]}</div>"
            f"<h1 style='font-size:{size}px'>{html.escape(post['title'])}</h1>"
            "<div class=foot><span class=author><span class=mark>MP</span>By Mogdho Paul</span>"
            "<span class=site>mogdhopaul.com</span></div>"
            "</div>")


def image_key(post):
    return hashlib.sha256(f"{DESIGN}|{post['title']}|{post['topic']}".encode()).hexdigest()[:16]


def find_chrome():
    if os.environ.get("CHROME"):
        return os.environ["CHROME"]
    for name in ("google-chrome", "google-chrome-stable", "chromium", "chromium-browser", "chrome"):
        if shutil.which(name):
            return shutil.which(name)
    local = Path.home() / "AppData" / "Local"
    for pattern in (str(local / "ms-playwright" / "chromium_headless_shell-*" / "*" / "chrome-headless-shell.exe"),
                    str(local / "ms-playwright" / "chromium-*" / "*" / "chrome.exe")):
        found = sorted(glob.glob(pattern))
        if found:
            return found[-1]
    return None


def render(chrome, page, png):
    subprocess.run([chrome, "--headless=new", "--disable-gpu", "--hide-scrollbars", "--no-sandbox",
                    "--allow-file-access-from-files", "--virtual-time-budget=3000",
                    f"--window-size={SIZE[0]},{SIZE[1]}", f"--screenshot={png}", page.as_uri()],
                   check=True, capture_output=True, timeout=120)


def main(root=ROOT):
    root = Path(root)
    posts = json.loads((root / "content" / "posts.json").read_text(encoding="utf-8"))
    made_path = root / "blog" / "images.json"
    made = json.loads(made_path.read_text(encoding="utf-8")) if made_path.exists() else {}
    todo = [p for p in posts if made.get(p["slug"]) != image_key(p)
            or not (root / "blog" / p["slug"] / "og.jpg").exists()]
    if not todo:
        print("Blog images are up to date.")
        return 0
    chrome = find_chrome()
    try:
        from PIL import Image
    except ImportError:
        Image = None
    if not chrome or Image is None:
        print("Skipped blog images: needs Chrome and Pillow (pip install pillow). Posts show without one.")
        return 0
    fonts_url = (root / "fonts").as_uri()
    with tempfile.TemporaryDirectory() as tmp:
        for post in todo:
            page, png = Path(tmp) / "card.html", Path(tmp) / "card.png"
            page.write_text(card_html(post, fonts_url), encoding="utf-8")
            render(chrome, page, png)
            folder = root / "blog" / post["slug"]
            folder.mkdir(parents=True, exist_ok=True)
            with Image.open(png) as im:
                im = im.convert("RGB")
                im.save(folder / "og.jpg", "JPEG", quality=86, optimize=True, progressive=True)
                im.resize(THUMB, Image.LANCZOS).save(folder / "thumb.webp", "WEBP", quality=82, method=6)
            made[post["slug"]] = image_key(post)
            print(f"Made the image for {post['slug']}")
    keep = {p["slug"] for p in posts}
    made = {slug: key for slug, key in sorted(made.items()) if slug in keep}
    made_path.write_text(json.dumps(made, indent=2) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
