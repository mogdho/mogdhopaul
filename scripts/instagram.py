"""Instagram API (with Instagram Login) client: fetch posts, pick photo posts, read the place from a caption."""
import json
import re
import unicodedata
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass

API = "https://graph.instagram.com"
FIELDS = "id,caption,media_type,media_url,permalink,timestamp,children{media_type,media_url}"
MAX_ITEMS = 100
# Other spellings of the owner's name must never appear on the site.
BANNED_NAMES = ("mugdho", "mogdha")


class InstagramError(Exception):
    pass


@dataclass
class Post:
    id: str
    permalink: str
    timestamp: str
    image_url: str
    place: str | None


def _get_json(url, urlopen):
    try:
        with urlopen(url, timeout=30) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except (urllib.error.URLError, OSError, ValueError) as exc:
        raise InstagramError(f"request failed: {exc}") from exc
    if isinstance(data, dict) and "error" in data:
        raise InstagramError(str(data["error"].get("message", data["error"])))
    return data


def fetch_media(token, urlopen=urllib.request.urlopen):
    """All recent media items (newest first), following pages up to MAX_ITEMS."""
    query = urllib.parse.urlencode({"fields": FIELDS, "limit": 50, "access_token": token})
    url = f"{API}/me/media?{query}"
    items = []
    while url and len(items) < MAX_ITEMS:
        page = _get_json(url, urlopen)
        items.extend(page.get("data", []))
        url = page.get("paging", {}).get("next")
    return items[:MAX_ITEMS]


def refresh_token(token, urlopen=urllib.request.urlopen):
    """Exchange a long-lived token for a fresh one (valid another 60 days)."""
    query = urllib.parse.urlencode({"grant_type": "ig_refresh_token", "access_token": token})
    data = _get_json(f"{API}/refresh_access_token?{query}", urlopen)
    if not data.get("access_token"):
        raise InstagramError("no access_token in refresh response")
    return data["access_token"]


def _is_non_latin(ch):
    """Letters or digits outside the Latin script (e.g. Bengali letters or digits)."""
    if ch.isalpha():
        return not unicodedata.name(ch, "").startswith("LATIN")
    return ch.isdigit() and not ch.isascii()


def extract_place(caption):
    """Place name from a caption: the text after a pin emoji, else the first line. None if it doesn't look like a place."""
    if not caption:
        return None
    lines = [ln.strip() for ln in caption.splitlines() if ln.strip()]
    if not lines:
        return None
    pinned = [ln for ln in lines if "\U0001F4CD" in ln]
    text = pinned[0].split("\U0001F4CD", 1)[1] if pinned else lines[0]

    text = re.sub(r"[#@]\w+", " ", text)
    if any(_is_non_latin(ch) for ch in text):
        return None
    if any(name in text.lower() for name in BANNED_NAMES):
        return None
    text = "".join(ch if ch.isalnum() or ch in " ,.-'" else " " for ch in text)
    text = re.sub(r"\s+", " ", text).strip(" ,.-")

    if not text or len(text) > 40 or len(text.split()) > 5:
        return None
    return text


def _image_url(item):
    kind = item.get("media_type")
    if kind == "IMAGE":
        return item.get("media_url")
    if kind == "CAROUSEL_ALBUM":
        for child in item.get("children", {}).get("data", []):
            if child.get("media_type") == "IMAGE":
                return child.get("media_url")
    return None


def _post_key(value):
    """Comparable form of a post id or link: 'p/ABC123' for links (any host form, query or slash), else the id."""
    m = re.search(r"instagram\.com/((?:p|reel|tv)/[^/?#]+)", value or "")
    return m.group(1) if m else (value or "").strip()


def select_posts(media, exclude, limit=60):
    """Photo posts in API order, minus excluded ids/links, up to limit."""
    hidden = {_post_key(e) for e in exclude}
    posts = []
    for item in media:
        if _post_key(item.get("id")) in hidden or _post_key(item.get("permalink")) in hidden:
            continue
        url = _image_url(item)
        if not url:
            continue
        posts.append(Post(item["id"], item["permalink"], item["timestamp"], url,
                          extract_place(item.get("caption"))))
        if len(posts) >= limit:
            break
    return posts
