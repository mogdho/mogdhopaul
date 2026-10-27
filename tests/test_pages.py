import json
import re
import unittest

from tests.helpers import PAGES, ROOT, parse

# Expected values come from content/*.json, so edits made in the admin still pass.
# Checks pinned to today's wording live in test_content_snapshot.py (skipped on GitHub).
_SITE = json.loads((ROOT / "content" / "site.json").read_text(encoding="utf-8"))
_PROJECTS = json.loads((ROOT / "content" / "projects.json").read_text(encoding="utf-8"))
IDENTITY = _SITE["identity"]
SAME_AS = [p["url"] for p in _SITE["profiles"]]
CONTACT = [f"mailto:{_SITE['contact']['email']}", _SITE["contact"]["whatsapp"]]
BANNED = ("Mugdho", "Mogdha", "AI-Assisted")
URLS = {"home": "/", "about": "/about/", "projects": "/projects/", "photos": "/photos/"}
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
        for u in URLS.values():
            self.assertIn(u, self.p.hrefs)

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
            self.assertIn(project["url"], self.p.hrefs)


class PhotosPage(CommonPageRules, unittest.TestCase):
    page_key = "photos"

    def test_photo_grid(self):
        self.assertIn('class="photo-grid"', self.p.html)

    def test_intro_mentions_name(self):
        self.assertIn("Mogdho Paul", self.p.text)



class Sitemap(unittest.TestCase):
    def test_all_pages(self):
        xml = (ROOT / "sitemap.xml").read_text(encoding="utf-8")
        for u in URLS.values():
            self.assertIn(f"<loc>https://mogdhopaul.com{u}</loc>", xml)


class Publishing(unittest.TestCase):
    def test_tooling_not_published(self):
        cfg = (ROOT / "_config.yml").read_text(encoding="utf-8")
        for name in ("content", "templates", "scripts", "tests", "docs", "PRODUCT.md", "DESIGN.md"):
            self.assertIn(f"- {name}", cfg)


class AdminPrivacy(unittest.TestCase):
    def test_robots_disallows_admin(self):
        self.assertIn("Disallow: /admin/", (ROOT / "robots.txt").read_text(encoding="utf-8"))

    def test_admin_noindex(self):
        self.assertIn('content="noindex, nofollow"', (ROOT / "admin" / "index.html").read_text(encoding="utf-8"))

    def test_admin_not_in_sitemap(self):
        self.assertNotIn("/admin", (ROOT / "sitemap.xml").read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
