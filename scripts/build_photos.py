"""Pull Instagram photos into the site.

Fetches posts, saves resized WebP images to photos/img/, writes data/photos.json and
rewrites the marked photo regions in index.html (6 newest) and photos/index.html (all).
Nothing is written unless every step before writing succeeds.

Usage:  IG_TOKEN=... python -m scripts.build_photos
        python -m scripts.build_photos --fixture media.json   (local JSON instead of the API)
"""
import argparse
import html
import io
import json
import os
import sys
import urllib.request
from datetime import date
from pathlib import Path

from PIL import Image

from scripts.instagram import InstagramError, fetch_media, select_posts

ROOT = Path(__file__).resolve().parent.parent
STRIP_COUNT = 6
SIZES = (1200, 600)
EMPTY = '<p class="empty-note">Photos from the road are on their way.</p>'
MONTHS = ["January", "February", "March", "April", "May", "June", "July",
          "August", "September", "October", "November", "December"]


def _date(photo):
    return date.fromisoformat(photo["date"])


def alt_text(photo):
    d = _date(photo)
    when = f"{MONTHS[d.month - 1]} {d.year}"
    if photo.get("place"):
        return f"Travel photo by Mogdho Paul in {photo['place']}, {when}"
    return f"Travel photo by Mogdho Paul, {when}"


def render_items(photos, limit):
    shown = photos[:limit] if limit else photos
    if not shown:
        return EMPTY
    e = html.escape
    out = []
    for p in shown:
        d = _date(p)
        place = f'<span class="photo__place">{e(p["place"])}</span>' if p.get("place") else ""
        out.append(
            f'<figure class="photo fade">'
            f'<a href="{e(p["permalink"])}">'
            f'<img src="{e(p["thumb"])}" srcset="{e(p["thumb"])} 600w, {e(p["src"])} 1200w" '
            f'sizes="(min-width: 48rem) 25vw, 50vw" alt="{e(alt_text(p))}" '
            f'width="{p["width"]}" height="{p["height"]}" loading="lazy" decoding="async">'
            f'</a>'
            f'<figcaption class="photo__label">{place}'
            f'<time datetime="{d.isoformat()}">{d.day} {MONTHS[d.month - 1]} {d.year}</time>'
            f'</figcaption></figure>'
        )
    return "\n".join(out)


def replace_region(page, name, content):
    start, end = f"<!-- photos:{name}:start -->", f"<!-- photos:{name}:end -->"
    i, j = page.find(start), page.find(end)
    if i < 0 or j < i:
        raise ValueError(f"markers for '{name}' not found")
    return page[:i + len(start)] + "\n" + content + "\n" + page[j:]


def _default_download(url):
    with urllib.request.urlopen(url, timeout=60) as resp:
        return resp.read()


def _resized(raw, width):
    im = Image.open(io.BytesIO(raw)).convert("RGB")
    if im.width > width:
        im = im.resize((width, round(im.height * width / im.width)), Image.LANCZOS)
    buf = io.BytesIO()
    im.save(buf, "WEBP", quality=80)  # re-encoding drops EXIF/location metadata
    return buf.getvalue(), im.size


def _read_exclude(path):
    if not path.exists():
        return set()
    lines = (ln.split("#", 1)[0].strip() for ln in path.read_text(encoding="utf-8").splitlines())
    return {ln for ln in lines if ln}


def main(argv=None, download=None):
    parser = argparse.ArgumentParser(description="Pull Instagram photos into the site.")
    parser.add_argument("--fixture", help="read media JSON from this file instead of the API")
    args = parser.parse_args(argv)
    download = download or _default_download

    img_dir = ROOT / "photos" / "img"
    data_path = ROOT / "data" / "photos.json"

    # 1. Fetch (no writes yet)
    try:
        if args.fixture:
            media = json.loads(Path(args.fixture).read_text(encoding="utf-8")).get("data", [])
        else:
            token = os.environ.get("IG_TOKEN")
            if not token:
                print("IG_TOKEN is not set", file=sys.stderr)
                return 1
            media = fetch_media(token)
    except InstagramError as exc:
        print(f"Instagram fetch failed, nothing changed: {exc}", file=sys.stderr)
        return 1

    posts = select_posts(media, _read_exclude(ROOT / "data" / "photos-exclude.txt"))

    # 2. Prepare every image in memory (still no writes)
    pending = {}
    photos = []
    for post in posts:
        big = img_dir / f"{post.id}-1200.webp"
        small = img_dir / f"{post.id}-600.webp"
        try:
            if big.exists() and small.exists():
                with Image.open(big) as im:
                    size = im.size
            else:
                raw = download(post.image_url)
                big_bytes, size = _resized(raw, SIZES[0])
                small_bytes, _ = _resized(raw, SIZES[1])
                pending[big], pending[small] = big_bytes, small_bytes
        except (OSError, ValueError) as exc:
            print(f"Image for post {post.id} failed, nothing changed: {exc}", file=sys.stderr)
            return 1
        photos.append({
            "id": post.id, "permalink": post.permalink, "date": post.timestamp[:10], "place": post.place,
            "src": f"/photos/img/{big.name}", "thumb": f"/photos/img/{small.name}",
            "width": size[0], "height": size[1],
        })

    home_path, grid_path = ROOT / "index.html", ROOT / "photos" / "index.html"
    home = replace_region(home_path.read_text(encoding="utf-8"), "strip", render_items(photos, STRIP_COUNT))
    grid = replace_region(grid_path.read_text(encoding="utf-8"), "grid", render_items(photos, None))

    # 3. Write
    img_dir.mkdir(parents=True, exist_ok=True)
    for path, data in pending.items():
        path.write_bytes(data)
    keep = {Path(p["src"]).name for p in photos} | {Path(p["thumb"]).name for p in photos}
    for old in img_dir.glob("*.webp"):
        if old.name not in keep:
            old.unlink()
    data_path.parent.mkdir(parents=True, exist_ok=True)
    data_path.write_text(json.dumps(photos, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    home_path.write_text(home, encoding="utf-8")
    grid_path.write_text(grid, encoding="utf-8")
    print(f"{len(photos)} photos ({len(pending) // 2} new)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
