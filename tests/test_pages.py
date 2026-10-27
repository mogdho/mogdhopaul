import json
import re
import unittest

from tests.helpers import PAGES, ROOT, parse

_SITE = json.loads((ROOT / "content" / "site.json").read_text(encoding="utf-8"))
IDENTITY = _SITE["identity"]
SAME_AS = [p["url"] for p in _SITE["profiles"]]
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
        for u in SAME_AS + ["mailto:mogdhapal@gmail.com", "https://wa.me/+8801998955221"]:
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
        self.assertIn("https://video-showcase.mogdhopaul.com/", self.p.hrefs)
        self.assertIn("video editing", self.p.text.lower())

    def test_morse_name(self):
        self.assertIn(MORSE, self.p.text)

    def test_photo_strip(self):
        self.assertIn('class="photo-strip"', self.p.html)


class AboutPage(CommonPageRules, unittest.TestCase):
    page_key = "about"

    def test_story_facts(self):
        t = self.p.text.lower()
        for s in ("Brahmanbaria", "Dhaka", "Bangladesh", "Tagore", "Morse code", "SEO", "video editing"):
            self.assertIn(s.lower(), t)
        self.assertGreaterEqual(len(self.p.text.split()), 500)

    def test_no_sensitive(self):
        t = self.p.text.lower()
        for s in ("blood group", "religion", "marital", "mental health", "hindu"):
            self.assertNotIn(s, t)

    def test_jsonld(self):
        page = next(d for d in self.p.jsonld if d.get("@type") in ("AboutPage", "ProfilePage"))
        self.assertEqual(page["mainEntity"]["name"], "Mogdho Paul")


class ProjectsPage(CommonPageRules, unittest.TestCase):
    page_key = "projects"

    def test_projects_listed(self):
        for name in ("Hotspot-Auto-Connect", "Copilot2Gemini", "Capslock-CopyPaste", "NN-tab", "leaflet", "video-showcase-paul"):
            self.assertIn(name, self.p.text)
            self.assertIn(f"https://github.com/mogdho/{name}", self.p.hrefs)


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
    def test_private_files_not_published(self):
        cfg = (ROOT / "_config.yml").read_text(encoding="utf-8")
        for name in ("docs", "tests", "scripts", "PRODUCT.md", "DESIGN.md", "data"):
            self.assertIn(f"- {name}", cfg)


if __name__ == "__main__":
    unittest.main()
