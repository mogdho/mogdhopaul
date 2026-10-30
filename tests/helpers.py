"""Shared helpers for the site tests: load a page and pull out what SEO checks need."""
import json
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PAGES = {
    "home": ROOT / "index.html",
    "about": ROOT / "about" / "index.html",
    "projects": ROOT / "projects" / "index.html",
    "photos": ROOT / "photos" / "index.html",
    "alwaysnumlock": ROOT / "alwaysnumlock" / "index.html",
    "capslock-copypaste": ROOT / "capslock-copypaste" / "index.html",
    "copilot2gemini": ROOT / "copilot2gemini" / "index.html",
    "nn-tab": ROOT / "nn-tab" / "index.html",
    "yt-mini-pip": ROOT / "yt-mini-pip" / "index.html",
    "ytmodify": ROOT / "ytmodify" / "index.html",
    "how-many-time": ROOT / "how-many-time" / "index.html",
}


class Page(HTMLParser):
    def __init__(self, html):
        super().__init__(convert_charrefs=True)
        self.html = html
        self.title = ""
        self.meta = {}
        self.links = []
        self.h1_count = 0
        self.hrefs = []
        self.jsonld = []
        self.imgs = []
        self._text = []
        self._in = None  # "title", "jsonld", "skip"
        self._buf = []
        self.feed(html)
        self.text = " ".join(" ".join(self._text).split())

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == "title":
            self._in, self._buf = "title", []
        elif tag == "script" and a.get("type") == "application/ld+json":
            self._in, self._buf = "jsonld", []
        elif tag in ("script", "style"):
            self._in = "skip"
        elif tag == "meta":
            key = a.get("name") or a.get("property")
            if key:
                self.meta[key] = a.get("content", "")
        elif tag == "link":
            self.links.append((a.get("rel", ""), a.get("href", "")))
        elif tag == "h1":
            self.h1_count += 1
        elif tag == "a" and "href" in a:
            self.hrefs.append(a["href"])
        elif tag == "img":
            self.imgs.append(a)

    def handle_endtag(self, tag):
        if self._in == "title" and tag == "title":
            self.title = "".join(self._buf).strip()
            self._in = None
        elif self._in == "jsonld" and tag == "script":
            self.jsonld.append(json.loads("".join(self._buf)))
            self._in = None
        elif self._in == "skip" and tag in ("script", "style"):
            self._in = None

    def handle_data(self, data):
        if self._in in ("title", "jsonld"):
            self._buf.append(data)
        elif self._in is None:
            self._text.append(data)


def parse(path):
    return Page(Path(path).read_text(encoding="utf-8"))
