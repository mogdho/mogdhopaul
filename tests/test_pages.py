import json
import re
import unittest

from scripts.build_site import TOOLS, download_url, project_href
from tests.helpers import PAGES, ROOT, parse

# Expected values come from content/*.json, so edits made in the admin still pass.
# Checks pinned to today's wording live in test_content_snapshot.py (skipped on GitHub).
_SITE = json.loads((ROOT / "content" / "site.json").read_text(encoding="utf-8"))
_PROJECTS = json.loads((ROOT / "content" / "projects.json").read_text(encoding="utf-8"))
IDENTITY = _SITE["identity"]
SAME_AS = [p["url"] for p in _SITE["profiles"]]
CONTACT = [f"mailto:{_SITE['contact']['email']}", _SITE["contact"]["whatsapp"]]
BANNED = ("Mugdho", "Mogdha", "AI-Assisted")
URLS = {"home": "/", "about": "/about/", "projects": "/projects/", "photos": "/photos/",
        "alwaysnumlock": "/alwaysnumlock/", "capslock-copypaste": "/capslock-copypaste/",
        "copilot2gemini": "/copilot2gemini/", "nn-tab": "/nn-tab/", "yt-mini-pip": "/yt-mini-pip/",
        "ytmodify": "/ytmodify/", "how-many-time": "/how-many-time/",
        "converter": "/currency-converter/"}
NAV_URLS = ("/", "/about/", "/photos/", "/projects/")
MORSE = "-- --- --. -.. .... --- / .--. .- ..- .-.."


class CommonPageRules:
    page_key = None

    def setUp(self):
        self.p = parse(PAGES[self.page_key])

    def test_title_has_name(self):
        self.assertIn("Mogdho Paul", self.p.title)

    def test_title_meta_no_video_role(self):
        for s in (self.p.title, self.p.meta["description"]):
            self.assertNotRegex(s.lower(), "video editor|motion designer")

    def test_meta_description(self):
        d = self.p.meta["description"]
        self.assertIn("Mogdho Paul", d)
        self.assertLessEqual(len(d), 160)

    def test_canonical(self):
        self.assertIn(("canonical", f"https://mogdhopaul.com{URLS[self.page_key]}"), self.p.links)

    def test_og_twitter(self):
        for k in ("og:title", "og:description", "og:url", "og:image", "twitter:card"):
            self.assertIn(k, self.p.meta)

    def test_one_h1(self):
        self.assertEqual(self.p.h1_count, 1)

    def test_analytics(self):
        self.assertIn("G-LDY4Z5D7MW", self.p.html)

    def test_banned_strings(self):
        for b in BANNED:
            self.assertNotIn(b, self.p.html)
        self.assertIsNone(re.search(r"[ঀ-৿]", self.p.html))
        self.assertNotIn("Bucharest", self.p.title + self.p.meta["description"] + json.dumps(self.p.jsonld))

    def test_no_emoji(self):
        self.assertIsNone(re.search(r"[\U0001F300-\U0001FAFF☀-➿]", self.p.html))

    def test_footer_links(self):
        for u in SAME_AS + CONTACT:
            self.assertIn(u, self.p.hrefs)

    def test_nav(self):
        for u in NAV_URLS:
            self.assertIn(u, self.p.hrefs)

    def test_more_menu_has_converter(self):
        self.assertIn('<summary><span>More</span></summary>', self.p.html)
        menu = self.p.html[self.p.html.index('class="site-nav__menu"'):]
        self.assertIn('href="/currency-converter/"', menu[:menu.index("</ul>")])

    def test_images_have_alt_and_size(self):
        for img in self.p.imgs:
            self.assertTrue(img.get("alt"), img)
            self.assertIn("width", img)
            self.assertIn("height", img)


class HomePage(CommonPageRules, unittest.TestCase):
    page_key = "home"

    def test_identity_line(self):
        self.assertIn(IDENTITY, self.p.text)

    def test_person_jsonld(self):
        person = next(d for d in self.p.jsonld if d.get("@type") == "Person")
        self.assertEqual(person["name"], "Mogdho Paul")
        self.assertEqual(person["sameAs"], SAME_AS)
        self.assertEqual(person["description"], IDENTITY)
        self.assertEqual(person["nationality"]["name"], "Bangladesh")
        self.assertEqual(person["url"], "https://mogdhopaul.com/")
        self.assertNotIn("alternateName", person)

    def test_video_section(self):
        self.assertIn('id="video-title"', self.p.html)
        self.assertIn("video editing", self.p.text.lower())

    def test_morse_name(self):
        self.assertIn(MORSE, self.p.text)

    def test_photo_strip(self):
        self.assertIn('class="photo-strip"', self.p.html)


class AboutPage(CommonPageRules, unittest.TestCase):
    page_key = "about"

    def test_sections_listed(self):
        for sec in _SITE["about"]["sections"]:
            self.assertIn(sec["heading"], self.p.text)

    def test_jsonld(self):
        page = next(d for d in self.p.jsonld if d.get("@type") in ("AboutPage", "ProfilePage"))
        self.assertEqual(page["mainEntity"]["name"], "Mogdho Paul")


class ProjectsPage(CommonPageRules, unittest.TestCase):
    page_key = "projects"

    def test_projects_listed(self):
        for project in _PROJECTS:
            self.assertIn(project["name"], self.p.text)
            self.assertIn(project_href(project), self.p.hrefs)

    def test_extensions_have_their_own_section(self):
        html = self.p.html
        section = html[html.index("<h2>Chrome extensions</h2>"):html.index("<h2>In the browser</h2>")]
        for project in _PROJECTS:
            self.assertEqual(project["group"] == "extensions", f'>{project["name"]}</a>' in section, project["name"])


class ToolPageRules(CommonPageRules):
    def test_download_goes_straight_to_the_file(self):
        # The button downloads the newest release's file; no stop on the GitHub page.
        tool = TOOLS[self.page_key]
        url = download_url(tool)
        if tool["kind"] == "web":  # a web app opens the app itself
            self.assertTrue(url.startswith("https://"))
            self.assertGreaterEqual(self.p.hrefs.count(url), 2)
            self.assertIn("Open the app", self.p.text)
            return
        self.assertRegex(url, r"^https://github\.com/mogdho/[\w-]+/releases/latest/download/[\w.-]+\.(exe|zip)$")
        self.assertGreaterEqual(self.p.hrefs.count(url), 2)  # top of the page and at the end
        self.assertIn(f'href="{url}" download', self.p.html)

    def test_links_to_other_tools(self):
        # Pages that link to each other get found and ranked; discontinued tools aren't promoted.
        for slug, tool in TOOLS.items():
            if slug != self.page_key and not tool.get("discontinued"):
                self.assertIn(f"/{slug}/", self.p.hrefs)
        self.assertIn("/currency-converter/", self.p.hrefs)

    def test_search_title_and_breadcrumbs(self):
        tool = TOOLS[self.page_key]
        self.assertIn(tool["name"], self.p.title)
        self.assertLessEqual(len(self.p.meta["description"]), 155)
        crumbs = next(d for d in self.p.jsonld if d.get("@type") == "BreadcrumbList")
        self.assertEqual([i["name"] for i in crumbs["itemListElement"]], ["Home", "Projects", tool["name"]])

    def test_own_share_image(self):
        self.assertTrue(self.p.meta["og:image"].startswith(f"https://mogdhopaul.com/{self.page_key}/og.jpg?v="))
        self.assertEqual(self.p.meta["og:image"], self.p.meta["twitter:image"])

    def test_links_source(self):
        self.assertIn(TOOLS[self.page_key]["repo"], self.p.hrefs)

    def test_software_jsonld(self):
        app = next(d for d in self.p.jsonld if d.get("@type") == "SoftwareApplication")
        self.assertEqual(app["name"], TOOLS[self.page_key]["name"])
        self.assertEqual(app["author"]["name"], "Mogdho Paul")

    def test_setup_steps(self):
        self.assertIn('class="steps"', self.p.html)
        if TOOLS[self.page_key]["kind"] == "windows":
            self.assertIn("Start with Windows", self.p.text)
        elif TOOLS[self.page_key]["kind"] == "web":
            self.assertIn("Add to Home Screen", self.p.text)
        else:
            for words in ("Extract All", "chrome://extensions", "Developer mode", "Load unpacked"):
                self.assertIn(words, self.p.text)
            self.assertIn(TOOLS[self.page_key]["file"].removesuffix(".zip"), self.p.text)

    def test_no_dev_talk(self):
        # Pages are for everyday users: no script files, code or install-a-runtime steps.
        for word in ("AutoHotkey", ".ahk", "script", "registry", "taskschd", "admin rights"):
            self.assertNotIn(word.lower(), self.p.text.lower())


class AlwaysNumLockPage(ToolPageRules, unittest.TestCase):
    page_key = "alwaysnumlock"


class CapslockCopyPastePage(ToolPageRules, unittest.TestCase):
    page_key = "capslock-copypaste"


class Copilot2GeminiPage(ToolPageRules, unittest.TestCase):
    page_key = "copilot2gemini"


class NNTabPage(ToolPageRules, unittest.TestCase):
    page_key = "nn-tab"


class YtMiniPipPage(ToolPageRules, unittest.TestCase):
    page_key = "yt-mini-pip"


class YtModifyPage(ToolPageRules, unittest.TestCase):
    page_key = "ytmodify"


class HowManyTimesPage(ToolPageRules, unittest.TestCase):
    page_key = "how-many-time"


class PhotosPage(CommonPageRules, unittest.TestCase):
    page_key = "photos"

    def test_photo_grid(self):
        self.assertIn('class="photo-grid"', self.p.html)

    def test_intro_mentions_name(self):
        self.assertIn("Mogdho Paul", self.p.text)

    def test_gallery_data_for_image_search(self):
        photos = json.loads((ROOT / "content" / "photos.json").read_text(encoding="utf-8"))
        gallery = next(d for d in self.p.jsonld if d.get("@type") == "ImageGallery")
        self.assertEqual(len(gallery["image"]), len(photos))
        for img in gallery["image"]:
            self.assertEqual(img["creator"]["name"], "Mogdho Paul")
            self.assertTrue(img["contentUrl"].startswith("https://mogdhopaul.com/photos/img/"))
            self.assertIn("Mogdho Paul", img["name"])

    def test_photo_files_have_descriptive_names(self):
        photos = json.loads((ROOT / "content" / "photos.json").read_text(encoding="utf-8"))
        for p in photos:
            self.assertTrue((ROOT / p["src"].lstrip("/")).exists(), p["src"])
            self.assertTrue((ROOT / p["thumb"].lstrip("/")).exists(), p["thumb"])



class ConverterPage(CommonPageRules, unittest.TestCase):
    page_key = "converter"

    def test_both_currencies(self):
        for value in ('value="RON"', 'value="EUR"'):
            self.assertIn(value, self.p.html)

    def test_referral_link_is_marked(self):
        self.assertIn("https://remit.ly/2n0wkpg8", self.p.hrefs)
        self.assertIn('rel="sponsored noopener"', self.p.html)
        self.assertIn("referral link", self.p.text)

    def test_calculator_script(self):
        self.assertRegex(self.p.html, r'src="/currency-converter/converter\.js\?v=\w+"')
        js = (ROOT / "currency-converter" / "converter.js").read_text(encoding="utf-8")
        self.assertIn("INCENTIVE = 0.025", js)
        self.assertIn("2n0wkpg8", self.p.html)

    def test_explains_the_incentive(self):
        self.assertIn("2.5%", self.p.text)


class Sitemap(unittest.TestCase):
    def test_all_pages(self):
        xml = (ROOT / "sitemap.xml").read_text(encoding="utf-8")
        for u in URLS.values():
            self.assertIn(f"<loc>https://mogdhopaul.com{u}</loc>", xml)


class Publishing(unittest.TestCase):
    def test_tooling_not_published(self):
        cfg = (ROOT / "_config.yml").read_text(encoding="utf-8")
        for name in ("content", "templates", "scripts", "tests", "docs"):
            self.assertIn(f"- {name}", cfg)

    def test_build_publishes_every_page(self):
        # The online build only commits the folders it is told about.
        wf = (ROOT / ".github" / "workflows" / "build.yml").read_text(encoding="utf-8")
        add = next(line for line in wf.splitlines() if "git add -A" in line).split()
        for slug in TOOLS:
            self.assertIn(slug, add)

    def test_build_starts_from_latest_main(self):
        # Two saves close together: the second run must rebuild on top of the first run's pages,
        # not on its own older commit, or its push conflicts.
        wf = (ROOT / ".github" / "workflows" / "build.yml").read_text(encoding="utf-8")
        self.assertRegex(wf, r"uses: actions/checkout@v4\n\s+with:\n\s+ref: main")


class AdminPrivacy(unittest.TestCase):
    def test_robots_disallows_admin(self):
        self.assertIn("Disallow: /admin/", (ROOT / "robots.txt").read_text(encoding="utf-8"))

    def test_admin_noindex(self):
        self.assertIn('content="noindex, nofollow"', (ROOT / "admin" / "index.html").read_text(encoding="utf-8"))

    def test_admin_not_in_sitemap(self):
        self.assertNotIn("/admin", (ROOT / "sitemap.xml").read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
