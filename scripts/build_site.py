"""Build the public pages from content/*.json and templates/.

Usage:  python -m scripts.build_site
Writes index.html, about/index.html, projects/index.html, photos/index.html, one page per Windows
tool (alwaysnumlock/index.html and so on, from templates/tools/) and removes images in photos/img/
that no photo uses. If the content breaks a site rule, nothing is written.
"""
import argparse
import hashlib
import html
import json
import re
import sys
from pathlib import Path
from string import Template

from scripts.content import ContentError, inline, load_content, render_text
from scripts.render_photos import render_items

ROOT = Path(__file__).resolve().parent.parent
SITE = "https://mogdhopaul.com"
PAGES = {"index.html": "home", "about/index.html": "about",
         "projects/index.html": "projects", "photos/index.html": "photos"}
NAV = [("/", "Home"), ("/about/", "About"), ("/photos/", "Photos"), ("/projects/", "Projects")]
STRIP_COUNT = 3  # newest photos on the home page; all of them are on the Photos page
PORTRAIT_FILES = ("mogdhopaul.webp", "mogdhopaul.jpeg")  # replaced by the admin's Profile photo
e = html.escape

# Windows apps and Chrome extensions with their own download page at /<slug>/. The page body is templates/tools/<slug>.html.
# The download button points at the newest GitHub release, so a new release needs no site change.
TOOLS = {
    "alwaysnumlock": {
        "name": "AlwaysNumLock",
        "repo": "https://github.com/mogdho/AlwaysNumLock",
        "lead": "Keeps Num Lock on, always. Your number pad types numbers, every time, even after sleep.",
        "title": "AlwaysNumLock — Keep Num Lock On in Windows, by Mogdho Paul",
        "description": "Free Windows app by Mogdho Paul that keeps Num Lock switched on, even after sleep or "
                       "the lock screen. Download, double-click, done.",
    },
    "capslock-copypaste": {
        "name": "Capslock-CopyPaste",
        "repo": "https://github.com/mogdho/Capslock-CopyPaste",
        "lead": "Turns the Caps Lock key into copy and paste. Tap once to copy, tap twice to paste.",
        "title": "Capslock-CopyPaste — Copy and Paste with Caps Lock, by Mogdho Paul",
        "description": "Free Windows app by Mogdho Paul: tap Caps Lock once to copy and twice to paste. "
                       "Works with text, pictures and files.",
    },
    "copilot2gemini": {
        "name": "Copilot2Gemini",
        "repo": "https://github.com/mogdho/Copilot2Gemini",
        "lead": "Makes the Copilot key open Google Gemini instead. Or ChatGPT, Claude, any assistant you like.",
        "title": "Copilot2Gemini — Open Gemini with the Copilot Key, by Mogdho Paul",
        "description": "Free Windows app by Mogdho Paul that makes the Copilot key open Google Gemini, "
                       "ChatGPT or Claude in its own window.",
    },
    "nn-tab": {
        "kind": "chrome",
        "name": "NN-tab",
        "repo": "https://github.com/mogdho/NN-tab",
        "file": "NN-tab.zip",
        "lead": "A calm new tab page for Chrome: a clock, your bookmarks, a few notes and a quote. Nothing else.",
        "title": "NN-tab — A Minimal New Tab Page for Chrome, by Mogdho Paul",
        "description": "Free Chrome extension by Mogdho Paul: a quiet new tab page with a clock, bookmarks, "
                       "notes and a quote. Everything stays on your computer.",
    },
    "yt-mini-pip": {
        "kind": "chrome",
        "name": "yt-mini-PIP",
        "repo": "https://github.com/mogdho/yt-mini-PIP",
        # The release file name carries its version; rename it here when a new version comes out.
        "file": "yt-mini-pip-v1.1.zip",
        "lead": "Your YouTube video keeps playing in a small floating window when you switch tabs, "
                "and slides back when you return.",
        "title": "yt-mini-PIP — Auto Picture-in-Picture for YouTube, by Mogdho Paul",
        "description": "Free Chrome extension by Mogdho Paul that pops a playing YouTube video into a small "
                       "floating window when you switch tabs or apps.",
    },
    "ytmodify": {
        "kind": "chrome",
        "name": "ytModify",
        "repo": "https://github.com/mogdho/ytModify-extension",
        "file": "ytModify.zip",
        "lead": "Makes YouTube nicer to watch: a soft glow around the video, auto pop-out, "
                "the quality you want and a bigger player.",
        "title": "ytModify — A Nicer YouTube in Chrome, by Mogdho Paul",
        "description": "Free Chrome extension by Mogdho Paul: ambient glow, auto pop-out, fixed video quality "
                       "and a bigger player for YouTube.",
    },
    "how-many-time": {
        "kind": "web",
        "name": "How Many Times",
        "repo": "https://github.com/mogdho/how-many-time",
        "app": "https://mogdho.github.io/how-many-time/",
        "lead": "A private, one-tap counter for the habit you’re trying to cut down on. "
                "Tap once each time it happens, and see honestly how you’re doing.",
        "title": "How Many Times — A Private Habit Tracker, by Mogdho Paul",
        "description": "Free app by Mogdho Paul: tap one button each time you slip on a habit you're cutting "
                       "down on. Private, works offline, no sign-up.",
    },
}
for _slug, _tool in TOOLS.items():
    _tool.setdefault("kind", "windows")
    if _tool["kind"] != "web":
        _tool.setdefault("file", f"{_tool['name']}.exe")
    PAGES[f"{_slug}/index.html"] = f"tool:{_slug}"

# What changes between a Windows app, a Chrome extension and a web app page.
KINDS = {
    "windows": {"kicker": "Free for Windows", "note": "Free · Windows 10 and 11 · Nothing to install",
                "os": "Windows 10, Windows 11", "category": "UtilitiesApplication"},
    "chrome": {"kicker": "Free for Chrome", "note": "Free · Chrome, Edge and Brave · No account",
               "os": "Google Chrome", "category": "BrowserApplication"},
    "web": {"kicker": "Free app", "note": "Free · Any phone or computer · No sign-up",
            "os": "Any", "category": "LifestyleApplication"},
}


def download_url(tool):
    """Where the button goes. Downloads link straight to the file in the newest release, so the browser
    downloads it without opening GitHub; a web app links to the app itself."""
    if tool["kind"] == "web":
        return tool["app"]
    return f"{tool['repo']}/releases/latest/download/{tool['file']}"


def project_href(project):
    """A project with its own download page links there; the others link to GitHub."""
    url = project["url"].rstrip("/").lower()
    for slug, tool in TOOLS.items():
        if url in (tool["repo"].lower(), tool.get("app", "").rstrip("/").lower()):
            return f"/{slug}/"
    return project["url"]


def _indent(block, spaces):
    pad = " " * spaces
    return "\n".join(pad + line if line else line for line in block.splitlines())


def _template(name):
    return Template((ROOT / "templates" / f"{name}.html").read_text(encoding="utf-8"))


def _version(*names):
    """Version tag from the files' bytes. The site sits behind a cache that keeps files for hours,
    so every link to a file that changes carries this tag: new contents, new address."""
    h, found = hashlib.sha256(), False
    for name in names:
        if (ROOT / name).exists():
            h.update((ROOT / name).read_bytes())
            found = True
    return f"?v={h.hexdigest()[:10]}" if found else ""


def _portrait_version():
    return _version(*PORTRAIT_FILES)


ADMIN_MODULES = ("core.js", "github.js", "images.js")
ADMIN_ASSETS = re.compile(r"(  <!-- assets: written by scripts/build_site.py -->\n).*?(  <!-- /assets -->)", re.S)


def _admin_page():
    """admin/index.html with versioned links. The import map makes app.js load versioned copies of the
    modules it imports, so a cached old module is never mixed with a new one."""
    path = ROOT / "admin" / "index.html"
    if not path.exists():
        return None
    imports = {f"/admin/{m}": f"/admin/{m}{_version(f'admin/{m}')}" for m in ADMIN_MODULES}
    assets = (
        f'  <link rel="stylesheet" href="/style.css{_version("style.css")}">\n'
        f'  <link rel="stylesheet" href="/admin/admin.css{_version("admin/admin.css")}">\n'
        f'  <script type="importmap">{json.dumps({"imports": imports})}</script>\n'
        f'  <script type="module" src="/admin/app.js{_version("admin/app.js")}"></script>\n'
    )
    page = path.read_text(encoding="utf-8")
    if not ADMIN_ASSETS.search(page):
        raise ContentError("admin/index.html: the assets markers are missing")
    return ADMIN_ASSETS.sub(lambda m: m.group(1) + assets + m.group(2), page)


def _jsonld(data):
    text = json.dumps(data, indent=2, ensure_ascii=False).replace("</", "<\\/")
    return f'\n  <script type="application/ld+json">\n{_indent(text, 2)}\n  </script>\n'


def _project_items(projects, indent, home):
    items = []
    for p in projects:
        text = (p["home_blurb"] or p["description"]) if home else p["description"]
        items.append(
            '<li class="project">\n'
            f'  <h3><a href="{e(project_href(p))}">{e(p["name"])}</a></h3>\n'
            f'  <p>{inline(text)}</p>\n'
            f'  <span class="project__lang">{e(p["language"])}</span>\n'
            '</li>'
        )
    return _indent("\n".join(items), indent)


SKILL_LABELS = (("stack", "Tech stack"), ("tools", "Tools"))
# Skill icons: single-colour icons from the Iconify library, saved by the admin into skill-icons/.
SKILL_ICON_DIR = "skill-icons"
DEFAULT_SKILL_ICONS = {"stack": "tabler:code", "tools": "tabler:tools"}  # for skills without their own icon


def skill_icon_path(icon_id):
    prefix, name = icon_id.split(":")
    return f"{SKILL_ICON_DIR}/{prefix}--{name}.svg"


def skill_mark(name):
    """Initials, shown only when no icon file can be found."""
    words = [w for w in name.replace("&", " ").split() if w[0].isalnum()]
    if len(words) > 1:
        return "".join(w[0] for w in words[:3]).upper()
    return (words[0] if words else name)[:2].capitalize()


def _skill_item(item, group):
    for icon_id in (item["icon"], DEFAULT_SKILL_ICONS[group]):
        if icon_id and (ROOT / skill_icon_path(icon_id)).exists():
            inner = f'<span class="skill__icon" style="--icon: url(/{skill_icon_path(icon_id)})"></span>'
            break
    else:
        inner = e(skill_mark(item["name"]))
    return (f'<li class="skill"><span class="skill__stamp" aria-hidden="true">{inner}</span>'
            f'<span class="skill__name">{e(item["name"])}</span></li>')


def _skills(skills):
    """Home page skills: one row per group, each skill as an ink stamp. Empty groups are left out."""
    rows = []
    for key, label in SKILL_LABELS:
        if skills[key]:
            items = "".join(_skill_item(item, key) for item in skills[key])
            rows.append(f'  <div class="skills__row">\n    <dt>{label}</dt>\n'
                        f'    <dd><ul class="skills__items">{items}</ul></dd>\n  </div>')
    if not rows:
        return ""
    return _indent(
        '<section aria-labelledby="skills-title">\n'
        '  <h2 id="skills-title">Skills</h2>\n'
        '  <dl class="skills">\n' + "\n".join(_indent(r, 2) for r in rows) + '\n  </dl>\n'
        '</section>', 4) + "\n"


def newest_first(photos):
    """Newest date first; photos with the same date: the one uploaded last first (uploads are added at the end)."""
    return [p for _, p in sorted(enumerate(photos), key=lambda ip: (ip[1]["date"], ip[0]), reverse=True)]


DOWNLOAD_ICON = ('<svg class="button__icon" viewBox="0 0 24 24" width="20" height="20" aria-hidden="true" '
                 'focusable="false"><path d="M12 4v11m0 0-4.5-4.5M12 15l4.5-4.5M5 19.5h14" fill="none" '
                 'stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>')


OPEN_ICON = ('<svg class="button__icon" viewBox="0 0 24 24" width="20" height="20" aria-hidden="true" '
             'focusable="false"><path d="M8 16 17 7m0 0H9.5M17 7v7.5" fill="none" stroke="currentColor" '
             'stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>')


def download_button(tool, extra_class=""):
    if tool["kind"] == "web":
        return f'<a class="button{extra_class}" href="{e(download_url(tool))}">{OPEN_ICON}Open the app</a>'
    return (f'<a class="button{extra_class}" href="{e(download_url(tool))}" download>'
            f'{DOWNLOAD_ICON}Download {e(tool["name"])}</a>')


def _cover(page, site, v=""):
    if page.startswith("tool:"):
        slug = page[5:]
        tool = TOOLS[slug]
        logo = f"{slug}/img/logo.webp"  # square app icon, shown on a paper tile beside the name
        logo_html = ("  <figure class=\"app-logo\">\n"
                     f'    <img src="/{logo}{_version(logo)}" alt="{e(tool["name"])} logo" '
                     'width="256" height="256" fetchpriority="high">\n'
                     "  </figure>\n") if (ROOT / logo).exists() else ""
        return _indent(
            '<div class="cover__body cover__body--tool">\n'
            + logo_html +
            '  <div>\n'
            '    <p class="cover__kicker"><a href="/projects/">Projects</a>'
            f'<span aria-hidden="true"> / </span>{KINDS[tool["kind"]]["kicker"]}</p>\n'
            f'    <h1 class="cover__name">{e(tool["name"])}</h1>\n'
            f'    <p class="cover__lead">{e(tool["lead"])}</p>\n'
            '    <div class="download">\n'
            f'      {download_button(tool, " button--cover")}\n'
            f'      <p class="download__note">{KINDS[tool["kind"]]["note"]}</p>\n'
            '    </div>\n'
            '  </div>\n'
            '</div>', 6)
    if page == "home":
        return _indent(
            '<div class="cover__body cover__body--home">\n'
            '  <div class="cover__text">\n'
            '    <h1 class="cover__name">Mogdho Paul</h1>\n'
            f'    <p class="cover__lead">{e(site["identity"])}</p>\n'
            '  </div>\n'
            '  <figure class="passport-photo">\n'
            '    <picture>\n'
            f'      <source srcset="/mogdhopaul.webp{v}" type="image/webp">\n'
            f'      <img src="/mogdhopaul.jpeg{v}" alt="Portrait of Mogdho Paul" '
            'width="480" height="600" fetchpriority="high">\n'
            '    </picture>\n'
            '  </figure>\n'
            '</div>', 6)
    heading, lead = {
        "about": ("About Mogdho Paul", inline(site["about"]["lead"])),
        "projects": ("Projects by Mogdho Paul",
                     "Small tools I built because something annoyed me enough. Each one is free and on GitHub."),
        "photos": ("Travel photos",
                   "Places I've been, stamped with where and when. Taken by Mogdho Paul, newest first. "
                   'More on <a href="https://www.instagram.com/mogdhopaul/">my Instagram</a>.'),
    }[page]
    return _indent(
        '<div class="cover__body">\n'
        '  <div>\n'
        f'    <h1 class="cover__name">{heading}</h1>\n'
        f'    <p class="cover__lead">{lead}</p>\n'
        '  </div>\n'
        '</div>', 6)


def _meta(page, site, v=""):
    profiles = [p["url"] for p in site["profiles"]]
    if page.startswith("tool:"):
        slug = page[5:]
        tool = TOOLS[slug]
        app = {
            "@context": "https://schema.org", "@type": "SoftwareApplication", "name": tool["name"],
            "url": f"{SITE}/{slug}/", "description": tool["description"],
            "operatingSystem": KINDS[tool["kind"]]["os"], "applicationCategory": KINDS[tool["kind"]]["category"],
            ("installUrl" if tool["kind"] == "web" else "downloadUrl"): download_url(tool),
            "isAccessibleForFree": True,
            "offers": {"@type": "Offer", "price": "0", "priceCurrency": "USD"},
            "author": {"@type": "Person", "name": "Mogdho Paul", "url": f"{SITE}/"},
        }
        return tool["title"], tool["description"], "website", _jsonld(app)
    if page == "home":
        person = {
            "@context": "https://schema.org", "@type": "Person", "name": "Mogdho Paul",
            "url": f"{SITE}/", "image": f"{SITE}/mogdhopaul.jpeg{v}",
            "jobTitle": "Developer & SEO Specialist", "description": site["identity"],
            "nationality": {"@type": "Country", "name": "Bangladesh"},
            "homeLocation": {"@type": "Country", "name": "Bangladesh"},
            "email": f"mailto:{site['contact']['email']}",
            "knowsAbout": ["Web Development", "Search Engine Optimization", "Workflow Automation", "JavaScript",
                           "AutoHotkey", "Video Editing", "Premiere Pro", "After Effects", "Travel Photography"],
            "sameAs": profiles,
        }
        return ("Mogdho Paul — Developer & SEO Specialist from Bangladesh", site["identity"], "profile", _jsonld(person))
    if page == "about":
        about = {"@context": "https://schema.org", "@type": "ProfilePage", "url": f"{SITE}/about/",
                 "name": "About Mogdho Paul",
                 "mainEntity": {"@type": "Person", "name": "Mogdho Paul", "url": f"{SITE}/"}}
        return ("About Mogdho Paul — Developer from Bangladesh",
                "The story of Mogdho Paul: growing up in Brahmanbaria and Dhaka, learning SEO and web development, "
                "and travelling with a camera.", "profile", _jsonld(about))
    if page == "projects":
        return ("Projects by Mogdho Paul — Small Web Tools & Automations",
                "Small web tools and Windows automations built by Mogdho Paul: AutoHotkey utilities, Chrome "
                "extensions, an invoice generator and more.", "website", "")
    return ("Travel Photos by Mogdho Paul",
            "Travel photos by Mogdho Paul: old towns, cities and quiet places, each stamped with where and when it "
            "was taken.", "website", "")


def _main_block(page, content):
    site, projects = content["site"], content["projects"]
    if page.startswith("tool:"):
        slug = page[5:]
        tool = TOOLS[slug]
        fields = {"button": download_button(tool), "repo": e(tool["repo"]), "name": e(tool["name"]),
                  "file": e(tool.get("file", "")), "folder": e(tool.get("file", "").removesuffix(".zip"))}
        # Chrome extensions share the same "add it to Chrome" and "update or remove" sections.
        for key in ("install", "remove"):
            fields[key] = (_template(f"tools/_chrome-{key}").substitute(fields).strip()
                           if tool["kind"] == "chrome" else "")
        return _template(f"tools/{slug}").substitute(fields)
    photos = newest_first(content["photos"])
    if page == "home":
        return _template("home").substitute(
            photos=render_items(photos, STRIP_COUNT, eager=3, link="/photos/"),
            lead=inline(site["home"]["lead"]),
            intro=_indent(render_text(site["home"]["text"]), 8),
            skills=_skills(site["skills"]),
            projects=_project_items([p for p in projects if p["featured"]], 8, home=True),
            video=_indent(render_text(site["home"]["video"]), 8),
        )
    if page == "about":
        sections = "\n\n".join(f"<h2>{html.escape(s['heading'], quote=False)}</h2>\n{render_text(s['text'])}"
                               for s in site["about"]["sections"])
        return _template("about").substitute(sections=_indent(sections, 6))
    if page == "projects":
        return _template("projects").substitute(
            windows=_project_items([p for p in projects if p["group"] == "windows"], 6, home=False),
            extensions=_project_items([p for p in projects if p["group"] == "extensions"], 6, home=False),
            browser=_project_items([p for p in projects if p["group"] == "browser"], 6, home=False),
        )
    return _template("photos").substitute(photos=render_items(photos, None))


def build(root=None):
    """All pages as {relative path: html}. Raises ContentError if the content breaks a rule."""
    global ROOT
    if root is not None and Path(root) != ROOT:
        saved, ROOT = ROOT, Path(root)
        try:
            return build()
        finally:
            ROOT = saved
    content = load_content(ROOT)
    site = content["site"]
    profiles = _indent("\n".join(f'<li><a href="{e(p["url"])}" rel="me">{e(p["label"])}</a></li>'
                                 for p in site["profiles"]), 8)
    v = _portrait_version()
    css_v, js_v = _version("style.css"), _version("script.js")
    pages = {}
    for rel, page in PAGES.items():
        title, description, og_type, jsonld = _meta(page, site, v)
        path = "/" if page == "home" else f"/{page.removeprefix('tool:')}/"
        nav = _indent("\n".join(
            f'<li><a href="{href}"{" aria-current=" + chr(34) + "page" + chr(34) if href == path else ""}>{label}</a></li>'
            for href, label in NAV), 12)
        pages[rel] = _template("base").substitute(
            title=e(title), description=e(description), canonical=f"{SITE}{path}", og_type=og_type,
            jsonld=jsonld, cover_class="" if page == "home" else " cover--short", nav=nav,
            css_v=css_v, js_v=js_v, cover=_cover(page, site, v), image=f"{SITE}/mogdhopaul.jpeg{v}", main=_main_block(page, content).rstrip("\n"),
            whatsapp=e(site["contact"]["whatsapp"]), email=e(site["contact"]["email"]), profiles=profiles,
        )
    return pages


def unused_skill_icons(root, site):
    """Icon files no skill uses any more (the default icons are always kept)."""
    keep = {Path(skill_icon_path(i)).name for i in DEFAULT_SKILL_ICONS.values()}
    keep |= {Path(skill_icon_path(it["icon"])).name for g in site["skills"].values() for it in g if it["icon"]}
    folder = Path(root) / SKILL_ICON_DIR
    return sorted(p for p in folder.glob("*") if p.is_file() and p.name not in keep) if folder.exists() else []


def unused_images(root, photos):
    keep = {Path(p[k]).name for p in photos for k in ("src", "thumb")}
    img = Path(root) / "photos" / "img"
    return sorted(p for p in img.glob("*") if p.is_file() and p.name not in keep) if img.exists() else []


def main(argv=None):
    argparse.ArgumentParser(description="Build the site pages from content/.").parse_args(argv)
    try:
        pages = build(ROOT)
        content = load_content(ROOT)
        photos = content["photos"]
        admin = _admin_page()
    except ContentError as exc:
        print(f"Content problem, nothing changed: {exc}", file=sys.stderr)
        return 1
    if admin is not None:
        (ROOT / "admin" / "index.html").write_text(admin, encoding="utf-8")
    for rel, page in pages.items():
        out = ROOT / rel
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(page, encoding="utf-8")
    removed = unused_images(ROOT, photos) + unused_skill_icons(ROOT, content["site"])
    for path in removed:
        path.unlink()
    print(f"Built {len(pages)} pages, {len(photos)} photos, removed {len(removed)} unused image(s).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
