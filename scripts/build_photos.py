"""Add travel photos to the site from photos you pick by hand.

Reads data/photos.csv (columns: file, place, date) and the original images in photo-originals/,
saves resized WebP copies to photos/img/ (location data stripped), writes data/photos.json and
rewrites the marked photo regions in index.html (6 newest) and photos/index.html (all).
Nothing is written unless every photo is ready first.

Usage:  python -m scripts.build_photos
"""
import argparse
import csv
import html
import io
import json
import re
import sys
import unicodedata
from datetime import date
from pathlib import Path

from PIL import Image, ImageOps

ROOT = Path(__file__).resolve().parent.parent
STRIP_COUNT = 6
SIZES = (1200, 600)
EMPTY = '<p class="empty-note">Photos from the road are on their way.</p>'
MONTHS = ["January", "February", "March", "April", "May", "June", "July",
          "August", "September", "October", "November", "December"]
# Other spellings of the owner's name must never appear on the site.
BANNED_NAMES = ("mugdho", "mogdha")


def _date(photo):
    return date.fromisoformat(photo["date"])


def alt_text(photo):
    d = _date(photo)
    when = f"{MONTHS[d.month - 1]} {d.year}"
    if photo.get("place"):
        return f"Travel photo by Mogdho Paul in {photo['place']}, {when}"
    return f"Travel photo by Mogdho Paul, {when}"


def render_items(photos, limit, eager=0):
    """Print markup for photos; the first `eager` images load immediately (they sit in the first screen)."""
    shown = photos[:limit] if limit else photos
    if not shown:
        return EMPTY
    e = html.escape
    out = []
    for i, p in enumerate(shown):
        d = _date(p)
        load = 'fetchpriority="high" ' if i == 0 and eager else ("" if i < eager else 'loading="lazy" ')
        place = f'<span class="photo__place">{e(p["place"])}</span>' if p.get("place") else ""
        out.append(
            f'<figure class="photo fade">'
            f'<img src="{e(p["thumb"])}" srcset="{e(p["thumb"])} 600w, {e(p["src"])} 1200w" '
            f'sizes="(min-width: 48rem) 25vw, 50vw" alt="{e(alt_text(p))}" '
            f'width="{p["width"]}" height="{p["height"]}" {load}decoding="async">'
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


def _check_place(place, line):
    for ch in place:
        if (ch.isalpha() and not unicodedata.name(ch, "").startswith("LATIN")) or (ch.isdigit() and not ch.isascii()):
            raise ValueError(f"line {line}: write the place in English letters (got {place!r})")
    if any(name in place.lower() for name in BANNED_NAMES):
        raise ValueError(f"line {line}: place {place!r} contains another spelling of your name")


def read_list(path):
    """Rows of the photo list, newest first. Raises ValueError naming the line of any mistake."""
    if not path.exists():
        return []
    rows = []
    lines = path.read_text(encoding="utf-8-sig").splitlines()
    for line_no, row in enumerate(csv.reader(lines), start=1):
        if line_no == 1 or not row or not "".join(row).strip() or row[0].lstrip().startswith("#"):
            continue
        if len(row) != 3:
            raise ValueError(f"line {line_no}: expected file,place,date")
        file, place, when = (cell.strip() for cell in row)
        try:
            date.fromisoformat(when)
        except ValueError:
            raise ValueError(f"line {line_no}: date must look like 2025-05-14 (got {when!r})") from None
        if place:
            _check_place(place, line_no)
        rows.append({"file": file, "place": place or None, "date": when})
    return sorted(rows, key=lambda r: r["date"], reverse=True)


def _slug(filename):
    return re.sub(r"[^a-z0-9]+", "-", Path(filename).stem.lower()).strip("-") or "photo"


def _resized(original, width):
    with Image.open(original) as im:
        im = ImageOps.exif_transpose(im).convert("RGB")
    if im.width > width:
        im = im.resize((width, round(im.height * width / im.width)), Image.LANCZOS)
    buf = io.BytesIO()
    im.save(buf, "WEBP", quality=80)  # re-encoding drops EXIF, including GPS location
    return buf.getvalue(), im.size


def main(argv=None):
    argparse.ArgumentParser(description="Add travel photos from data/photos.csv to the site.").parse_args(argv)
    img_dir = ROOT / "photos" / "img"
    originals = ROOT / "photo-originals"

    # 1. Read the list and prepare every image in memory (no writes yet)
    try:
        rows = read_list(ROOT / "data" / "photos.csv")
    except ValueError as exc:
        print(f"photos.csv: {exc}. Nothing changed.", file=sys.stderr)
        return 1

    pending, photos = {}, []
    for row in rows:
        pid = _slug(row["file"])
        big, small = img_dir / f"{pid}-1200.webp", img_dir / f"{pid}-600.webp"
        try:
            if big.exists() and small.exists():
                with Image.open(big) as im:
                    size = im.size
            else:
                src = originals / row["file"]
                if not src.exists():
                    print(f"Missing photo-originals/{row['file']}. Nothing changed.", file=sys.stderr)
                    return 1
                pending[big], size = _resized(src, SIZES[0])
                pending[small], _ = _resized(src, SIZES[1])
        except OSError as exc:
            print(f"Could not read {row['file']}: {exc}. Nothing changed.", file=sys.stderr)
            return 1
        photos.append({"id": pid, "date": row["date"], "place": row["place"],
                       "src": f"/photos/img/{big.name}", "thumb": f"/photos/img/{small.name}",
                       "width": size[0], "height": size[1]})

    home_path, grid_path = ROOT / "index.html", ROOT / "photos" / "index.html"
    home = replace_region(home_path.read_text(encoding="utf-8"), "strip", render_items(photos, STRIP_COUNT, eager=3))
    grid = replace_region(grid_path.read_text(encoding="utf-8"), "grid", render_items(photos, None))

    # 2. Write
    img_dir.mkdir(parents=True, exist_ok=True)
    for path, data in pending.items():
        path.write_bytes(data)
    keep = {Path(p["src"]).name for p in photos} | {Path(p["thumb"]).name for p in photos}
    for old in img_dir.glob("*.webp"):
        if old.name not in keep:
            old.unlink()
    data_path = ROOT / "data" / "photos.json"
    data_path.parent.mkdir(parents=True, exist_ok=True)
    data_path.write_text(json.dumps(photos, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    home_path.write_text(home, encoding="utf-8")
    grid_path.write_text(grid, encoding="utf-8")
    print(f"{len(photos)} photos on the site ({len(pending) // 2} new).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
