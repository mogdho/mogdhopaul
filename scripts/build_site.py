"""Build the public pages from content/*.json and templates/.

Usage:  python -m scripts.build_site
Writes the main pages (home, about, projects, photos), the currency converter, one page per tool
in TOOLS (alwaysnumlock/index.html and so on, from templates/tools/), and removes images in
photos/img/ and skill-icons/ that nothing uses. If the content breaks a site rule, nothing is written.
"""
import argparse
import hashlib
import html
import json
import re
import sys
from pathlib import Path
from string import Template

from scripts.content import IDENTITY_BANNED, ContentError, inline, load_content, render_text
from scripts.render_photos import alt_text, render_items

ROOT = Path(__file__).resolve().parent.parent
SITE = "https://mogdhopaul.com"
PAGES = {"index.html": "home", "about/index.html": "about",
         "projects/index.html": "projects", "photos/index.html": "photos",
         "currency-converter/index.html": "converter"}
NAV = [("/", "Home"), ("/about/", "About"), ("/photos/", "Photos"), ("/projects/", "Projects")]
MORE = [("/currency-converter/", "Currency converter")]  # the "More" dropdown at the end of the menu
STRIP_COUNT = 3  # newest photos on the home page; all of them are on the Photos page
PORTRAIT_FILES = ("mogdhopaul.webp", "mogdhopaul.jpeg")  # replaced by the admin's Profile photo
AUTHOR = {"@type": "Person", "name": "Mogdho Paul", "url": f"{SITE}/"}  # for structured data
FREE = {"@type": "Offer", "price": "0", "priceCurrency": "USD"}
e = html.escape

# Tools with their own page at /<slug>/: Windows apps, Chrome extensions and a web app. The page body
# is templates/tools/<slug>.html. Download buttons point at the newest GitHub release, so a new
# release needs no site change.
TOOLS = {
    "alwaysnumlock": {
        "name": "AlwaysNumLock",
        "repo": "https://github.com/mogdho/AlwaysNumLock",
        "lead": "Keeps Num Lock on, always. Your number pad types numbers, every time, even after sleep.",
        "title": "Keep Num Lock On in Windows 11 & 10 – AlwaysNumLock | Mogdho Paul",
        "description": "Num Lock keeps turning off? AlwaysNumLock, a free Windows 11 and 10 app by Mogdho Paul, keeps it on after sleep, restart and the lock screen.",
        "short": "Keeps Num Lock on in Windows, even after sleep and the lock screen.",
    },
    "capslock-copypaste": {
        "name": "Capslock-CopyPaste",
        "repo": "https://github.com/mogdho/Capslock-CopyPaste",
        "lead": "Turns the Caps Lock key into copy and paste. Tap once to copy, tap twice to paste.",
        "title": "Caps Lock as Copy & Paste on Windows – Capslock-CopyPaste | Mogdho Paul",
        "description": "Turn Caps Lock into copy and paste on Windows: tap once to copy, twice to paste. Free app by Mogdho Paul that works with text, pictures and files.",
        "short": "Tap Caps Lock once to copy, twice to paste.",
    },
    "copilot2gemini": {
        "name": "Copilot2Gemini",
        "repo": "https://github.com/mogdho/Copilot2Gemini",
        "lead": "Makes the Copilot key open Google Gemini instead. Or ChatGPT, Claude, any assistant you like.",
        "title": "Remap the Copilot Key to Gemini – Copilot2Gemini | Mogdho Paul",
        "description": "Make the Copilot key on your Windows laptop open Google Gemini, ChatGPT or Claude instead. Free app by Mogdho Paul, nothing to set up.",
        "short": "Makes the Copilot key open Gemini, ChatGPT or Claude.",
    },
    "nn-tab": {
        "kind": "chrome",
        "name": "NN-tab",
        "repo": "https://github.com/mogdho/NN-tab",
        "file": "NN-tab.zip",
        "screenshot": "/nn-tab/img/dashboard-light.webp",
        "lead": "A calm new tab page for Chrome: a clock, your bookmarks, a few notes and a quote. Nothing else.",
        "title": "Minimal New Tab Page for Chrome – NN-tab | Mogdho Paul",
        "description": "A minimal new tab page for Chrome with a clock, bookmarks, notes and a quote. Free, private extension by Mogdho Paul: nothing leaves your computer.",
        "short": "A calm new tab page for Chrome: clock, bookmarks, notes.",
    },
    "yt-mini-pip": {
        "kind": "chrome",
        "name": "yt-mini-PIP",
        "repo": "https://github.com/mogdho/yt-mini-PIP",
        # The release file name carries its version; rename it here when a new version comes out.
        "file": "yt-mini-pip-v1.1.zip",
        "discontinued": True,  # keeps its page, but other pages don't point to it
        "lead": "Your YouTube video keeps playing in a small floating window when you switch tabs, "
                "and slides back when you return.",
        "title": "Auto Picture-in-Picture for YouTube – yt-mini-PIP | Mogdho Paul",
        "description": "Pop a YouTube video into picture-in-picture automatically when you switch tabs or apps, and back when you return. Free Chrome extension by Mogdho Paul.",
        "short": "Pops YouTube into a floating window when you switch tabs.",
    },
    "ytmodify": {
        "kind": "chrome",
        "name": "ytModify",
        "repo": "https://github.com/mogdho/ytModify-extension",
        "file": "ytModify.zip",
        "screenshot": "/ytmodify/img/popup.webp",
        "lead": "Makes YouTube nicer to watch: a soft glow around the video, auto pop-out, "
                "the quality you want and a bigger player.",
        "title": "YouTube Ambient Light, Auto PiP & Quality – ytModify | Mogdho Paul",
        "description": "Ambient light, auto picture-in-picture, fixed video quality and a bigger player for YouTube. Free Chrome extension by Mogdho Paul.",
        "short": "Ambient glow, auto pop-out and fixed quality for YouTube.",
    },
    "how-many-time": {
        "kind": "web",
        "name": "How Many Times",
        "repo": "https://github.com/mogdho/how-many-time",
        "app": "https://mogdho.github.io/how-many-time/",
        "screenshot": "/how-many-time/img/dashboard.webp",
        "lead": "A private, one-tap counter for the habit you’re trying to cut down on. "
                "Tap once each time it happens, and see honestly how you’re doing.",
        "title": "Private Habit Tracker, No Sign-Up – How Many Times | Mogdho Paul",
        "description": "A private habit tracker: tap one button each time you slip and see your month and week at a glance. Free, works offline, no sign-up. By Mogdho Paul.",
        "short": "A private one-tap tracker for a habit you’re cutting down.",
    },
}


def _register_tools():
    """Fill in the defaults (a Windows app downloading <name>.exe) and add each tool's page."""
    for slug, tool in TOOLS.items():
        tool.setdefault("kind", "windows")
        if tool["kind"] != "web":
            tool.setdefault("file", f"{tool['name']}.exe")
        PAGES[f"{slug}/index.html"] = f"tool:{slug}"


_register_tools()

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
    """A project with its own page on this site links there; the others link to GitHub."""
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
    """The tool's main button: download the file, or open the app for a web app."""
    if tool["kind"] == "web":
        return f'<a class="button{extra_class}" href="{e(download_url(tool))}">{OPEN_ICON}Open the app</a>'
    return (f'<a class="button{extra_class}" href="{e(download_url(tool))}" download>'
            f'{DOWNLOAD_ICON}Download {e(tool["name"])}</a>')


def _cover(page, site, v=""):
    if page.startswith("tool:"):
        tool = TOOLS[page[5:]]
        return _indent(
            '<div class="cover__body">\n'
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
        "converter": ("Leu and euro to taka",
                      "See what you send from Romania or Europe and what arrives in Bangladesh, with the 2.5% "
                      "government incentive added."),
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


def _breadcrumbs(trail):
    """Home › ... trail for search results, from [(name, path), ...] after Home."""
    items = [("Home", "/")] + trail
    return {"@context": "https://schema.org", "@type": "BreadcrumbList",
            "itemListElement": [{"@type": "ListItem", "position": i, "name": name, "item": f"{SITE}{path}"}
                                for i, (name, path) in enumerate(items, 1)]}


# The converter is listed with the tools in each page's "More free tools" section.
CONVERTER = {"name": "Currency converter", "path": "/currency-converter/", "label": "Web tool",
             "short": "Leu or euro to taka, with the 2.5% incentive added."}
KIND_LABELS = {"windows": "Windows app", "chrome": "Chrome extension", "web": "Web app"}


def _related(current):
    """"More free tools" at the end of each tool page and the converter: links between them help
    visitors find the next tool and help search engines find and rank every page. Discontinued tools
    keep their own page but aren't promoted here."""
    entries = [(t["name"], f"/{s}/", KIND_LABELS[t["kind"]], t["short"])
               for s, t in TOOLS.items() if not t.get("discontinued")]
    entries.append((CONVERTER["name"], CONVERTER["path"], CONVERTER["label"], CONVERTER["short"]))
    items = "\n".join(
        '      <li class="project">\n'
        f'        <h3><a href="{path}">{e(name)}</a></h3>\n'
        f'        <p>{e(short)}</p>\n'
        f'        <span class="project__lang">{label}</span>\n'
        '      </li>'
        for name, path, label, short in entries if path != current)
    return ('\n\n    <section aria-labelledby="more-tools-title" class="related">\n'
            '      <h2 id="more-tools-title">More free tools by Mogdho Paul</h2>\n'
            '      <ul class="project-list">\n'
            f'{items}\n'
            '      </ul>\n'
            '      <p class="muted more-link"><a href="/projects/">All projects</a></p>\n'
            '    </section>\n')


def _og_image(rel, fallback):
    """The page's own share card (<folder>/og.jpg) if it has one, otherwise the portrait."""
    og = rel.removesuffix("index.html") + "og.jpg"
    return f"{SITE}/{og}{_version(og)}" if (ROOT / og).exists() else fallback


def _meta(page, site, v="", photos=None):
    profiles = [p["url"] for p in site["profiles"]]
    if page.startswith("tool:"):
        slug = page[5:]
        tool = TOOLS[slug]
        app = {
            "@context": "https://schema.org", "@type": "SoftwareApplication", "name": tool["name"],
            "url": f"{SITE}/{slug}/", "description": tool["description"],
            "operatingSystem": KINDS[tool["kind"]]["os"], "applicationCategory": KINDS[tool["kind"]]["category"],
            ("installUrl" if tool["kind"] == "web" else "downloadUrl"): download_url(tool),
            "isAccessibleForFree": True, "offers": FREE, "author": AUTHOR,
        }
        if tool.get("screenshot"):
            app["screenshot"] = f"{SITE}{tool['screenshot']}"
        crumbs = _breadcrumbs([("Projects", "/projects/"), (tool["name"], f"/{slug}/")])
        return tool["title"], tool["description"], "website", _jsonld(app) + _jsonld(crumbs)
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
    if page == "converter":
        app = {"@context": "https://schema.org", "@type": "WebApplication", "name": "Leu and euro to taka converter",
               "url": f"{SITE}/currency-converter/", "applicationCategory": "FinanceApplication",
               "operatingSystem": "Any", "isAccessibleForFree": True, "offers": FREE, "author": AUTHOR}
        crumbs = _breadcrumbs([("Currency converter", "/currency-converter/")])
        return ("RON & EUR to BDT Converter, 2.5% Incentive | Mogdho Paul",
                "Convert Romanian leu (RON) or euro (EUR) to Bangladeshi taka (BDT) at today's rate, with the 2.5% "
                "remittance incentive. Free tool by Mogdho Paul.", "website", _jsonld(app) + _jsonld(crumbs))
    if page == "projects":
        return ("Free Windows Apps, Chrome Extensions & Web Tools | Mogdho Paul",
                "Free tools by Mogdho Paul: AlwaysNumLock, Copilot2Gemini, Capslock-CopyPaste, NN-tab, ytModify, "
                "a RON and EUR to BDT converter and more.", "website", "")
    return ("Travel Photos by Mogdho Paul",
            "Travel photos by Mogdho Paul: old towns, cities and quiet places, each stamped with where and when it "
            "was taken.", "website", _jsonld(_gallery(photos or [])))


def public_place(place):
    """The place as search engines see it. Parts the site keeps out of its search data (see
    IDENTITY_BANNED, e.g. the city Mogdho Paul lives in) are left out: "Bucharest, Romania" -> "Romania"."""
    parts = [p.strip() for p in (place or "").split(",") if p.strip() and not IDENTITY_BANNED.search(p)]
    return ", ".join(parts) or None


def _gallery(photos):
    """Photos page structured data: each photo with its date, place and credit, for image search."""
    images = []
    for p in newest_first(photos):
        place = public_place(p.get("place"))
        img = {
            "@type": "ImageObject",
            "contentUrl": f"{SITE}{p['src']}", "thumbnailUrl": f"{SITE}{p['thumb']}",
            "url": f"{SITE}/photos/#photo-{p['id']}",
            "name": alt_text({**p, "place": place}), "dateCreated": p["date"],
            "width": p["width"], "height": p["height"],
            "creator": AUTHOR, "creditText": "Mogdho Paul", "copyrightNotice": "© Mogdho Paul",
        }
        if place:
            img["contentLocation"] = {"@type": "Place", "name": place}
        images.append(img)
    return {"@context": "https://schema.org", "@type": "ImageGallery", "url": f"{SITE}/photos/",
            "name": "Travel photos by Mogdho Paul", "author": AUTHOR, "image": images}


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
        return _template(f"tools/{slug}").substitute(fields).rstrip("\n") + _related(f"/{slug}/")
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
    if page == "converter":
        page_html = _template("converter").substitute(js_v=_version("currency-converter/converter.js"))
        return page_html.rstrip("\n") + _related(CONVERTER["path"])
    if page == "projects":
        return _template("projects").substitute(
            windows=_project_items([p for p in projects if p["group"] == "windows"], 6, home=False),
            extensions=_project_items([p for p in projects if p["group"] == "extensions"], 6, home=False),
            browser=_project_items([p for p in projects if p["group"] == "browser"], 6, home=False),
        )
    return _template("photos").substitute(photos=render_items(photos, None))


def _nav(path):
    """The main menu: the main pages, then a "More" dropdown. A plain <details> menu, so it opens
    without JavaScript; script.js only closes it on an outside click or Escape."""
    def current(href):
        return ' aria-current="page"' if href == path else ""
    items = [f'<li><a href="{href}"{current(href)}>{label}</a></li>' for href, label in NAV]
    inside = any(href == path for href, _ in MORE)
    links = [f'      <li><a href="{href}"{current(href)}>{label}</a></li>' for href, label in MORE]
    items.append("\n".join([
        f'<li class="site-nav__more{" is-current" if inside else ""}">',
        '  <details>',
        '    <summary><span>More</span></summary>',
        '    <ul class="site-nav__menu">',
        *links,
        '    </ul>',
        '  </details>',
        '</li>']))
    return "\n".join(items)


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
        title, description, og_type, jsonld = _meta(page, site, v, content["photos"])
        path = "/" + rel.removesuffix("index.html")
        nav = _indent(_nav(path), 12)
        pages[rel] = _template("base").substitute(
            title=e(title), description=e(description), canonical=f"{SITE}{path}", og_type=og_type,
            jsonld=jsonld, cover_class="" if page == "home" else " cover--short", nav=nav,
            css_v=css_v, js_v=js_v, cover=_cover(page, site, v),
            image=_og_image(rel, f"{SITE}/mogdhopaul.jpeg{v}"),
            main=_main_block(page, content).rstrip("\n"), whatsapp=e(site["contact"]["whatsapp"]), email=e(site["contact"]["email"]), profiles=profiles,
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
