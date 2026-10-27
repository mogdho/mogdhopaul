"""Site content (content/*.json): loading, validation, and turning text into safe HTML.

Text fields are plain paragraphs (blank line = new paragraph) with one link syntax:
[link text](address), where the address is https://, http://, mailto: or a site path (/photos/).
Everything else, including any HTML, is escaped and shown as plain text.
"""
import html
import json
import re
import unicodedata
from datetime import date
from pathlib import Path

BANNED_NAMES = ("mugdho", "mogdha")
GROUPS = ("windows", "browser")
FEATURED_COUNT = 3
LINK = re.compile(r"\[([^\]\n]+)\]\(([^)\s]+)\)")
IMG_PATH = re.compile(r"^/photos/img/[a-z0-9-]+\.(webp|jpg)$")


class ContentError(ValueError):
    pass


def is_allowed_url(url):
    return bool(re.match(r"^(https?://[^\s\"'<>]+|mailto:[^\s\"'<>]+|/[^\s\"'<>]*)$", url or ""))


def inline(text):
    """Escape text, then turn allowed [text](address) links into <a> tags."""
    def link(m):
        label, url = m.group(1), html.unescape(m.group(2))
        if not is_allowed_url(url):
            return m.group(0)
        return f'<a href="{html.escape(url, quote=True)}">{label}</a>'
    escaped = html.escape(text, quote=False).replace('"', "&quot;")
    return LINK.sub(link, escaped)


def render_text(text):
    paras = [p.strip() for p in re.split(r"\n\s*\n", text or "") if p.strip()]
    return "\n".join(f"<p>{inline(p)}</p>" for p in paras)


def _check_text(value, field, required=True):
    if not isinstance(value, str):
        raise ContentError(f"{field}: missing")
    if required and not value.strip():
        raise ContentError(f"{field}: must not be empty")
    for ch in value:
        if (ch.isalpha() and not unicodedata.name(ch, "").startswith("LATIN")) or (ch.isdigit() and not ch.isascii()):
            raise ContentError(f"{field}: write it in English letters")
    if any(name in value.lower() for name in BANNED_NAMES):
        raise ContentError(f"{field}: contains another spelling of the name; use Mogdho Paul")
    for m in LINK.finditer(value):
        if not is_allowed_url(m.group(2)):
            raise ContentError(f"{field}: link address {m.group(2)!r} must start with https://, mailto: or /")


def _check_url(value, field):
    if not isinstance(value, str) or not is_allowed_url(value):
        raise ContentError(f"{field}: must be a link starting with https://, mailto: or /")


def _get(obj, key, field):
    if not isinstance(obj, dict) or key not in obj:
        raise ContentError(f"{field}: missing")
    return obj[key]


def validate(content):
    site = _get(content, "site", "site")
    _check_text(_get(site, "identity", "site.identity"), "site.identity")
    home = _get(site, "home", "site.home")
    for key in ("lead", "text", "video"):
        _check_text(_get(home, key, f"site.home.{key}"), f"site.home.{key}")
    about = _get(site, "about", "site.about")
    _check_text(_get(about, "lead", "site.about.lead"), "site.about.lead")
    for i, sec in enumerate(_get(about, "sections", "site.about.sections")):
        for key in ("heading", "text"):
            _check_text(_get(sec, key, f"site.about.sections[{i}].{key}"), f"site.about.sections[{i}].{key}")
    contact = _get(site, "contact", "site.contact")
    _check_url(_get(contact, "whatsapp", "site.contact.whatsapp"), "site.contact.whatsapp")
    email = _get(contact, "email", "site.contact.email")
    if not isinstance(email, str) or not re.match(r"^[^\s@<>\"']+@[^\s@<>\"']+\.[a-z]{2,}$", email, re.I):
        raise ContentError("site.contact.email: not an email address")
    for i, prof in enumerate(_get(site, "profiles", "site.profiles")):
        _check_text(_get(prof, "label", f"site.profiles[{i}].label"), f"site.profiles[{i}].label")
        _check_url(_get(prof, "url", f"site.profiles[{i}].url"), f"site.profiles[{i}].url")

    projects = _get(content, "projects", "projects")
    for i, p in enumerate(projects):
        f = f"projects[{i}]"
        for key in ("name", "description", "language"):
            _check_text(_get(p, key, f"{f}.{key}"), f"{f}.{key}")
        _check_text(_get(p, "home_blurb", f"{f}.home_blurb"), f"{f}.home_blurb", required=False)
        _check_url(_get(p, "url", f"{f}.url"), f"{f}.url")
        if _get(p, "group", f"{f}.group") not in GROUPS:
            raise ContentError(f"{f}.group: must be one of {', '.join(GROUPS)}")
        if not isinstance(_get(p, "featured", f"{f}.featured"), bool):
            raise ContentError(f"{f}.featured: must be true or false")
    if sum(1 for p in projects if p["featured"]) != FEATURED_COUNT:
        raise ContentError(f"projects: exactly {FEATURED_COUNT} must be featured on the home page")

    for i, ph in enumerate(_get(content, "photos", "photos")):
        f = f"photos[{i}]"
        _check_text(_get(ph, "id", f"{f}.id"), f"{f}.id")
        place = _get(ph, "place", f"{f}.place")
        if place is not None:
            _check_text(place, f"{f}.place")
        try:
            date.fromisoformat(_get(ph, "date", f"{f}.date"))
        except (TypeError, ValueError):
            raise ContentError(f"{f}.date: must look like 2025-05-14") from None
        for key in ("src", "thumb"):
            if not IMG_PATH.match(str(_get(ph, key, f"{f}.{key}"))):
                raise ContentError(f"{f}.{key}: must be an image in /photos/img/")
        for key in ("width", "height"):
            if not isinstance(_get(ph, key, f"{f}.{key}"), int) or ph[key] <= 0:
                raise ContentError(f"{f}.{key}: must be a positive number")


def load_content(root):
    root = Path(root)
    content = {}
    for name in ("site", "projects", "photos"):
        try:
            content[name] = json.loads((root / "content" / f"{name}.json").read_text(encoding="utf-8"))
        except (OSError, ValueError) as exc:
            raise ContentError(f"content/{name}.json: {exc}") from None
    validate(content)
    return content
