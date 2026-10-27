"""Markup for travel photo prints with their entry stamp (place and date)."""
import html
from datetime import date

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
