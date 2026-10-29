"""Checks pinned to today's wording, run on this PC only.

On GitHub these are skipped, so the owner can change the email, delete a project or rewrite
the About page in the admin without publishing failing. Run locally before big edits to see
what the SEO groundwork relied on.
"""
import os
import unittest

from tests.helpers import PAGES, parse


@unittest.skipIf(os.environ.get("GITHUB_ACTIONS"), "content snapshot: local only")
class ContentSnapshot(unittest.TestCase):
    def test_about_story_facts(self):
        p = parse(PAGES["about"])
        t = p.text.lower()
        for s in ("Brahmanbaria", "Dhaka", "Bangladesh", "Tagore", "Morse code", "SEO", "video editing"):
            self.assertIn(s.lower(), t)
        self.assertGreaterEqual(len(p.text.split()), 500)

    def test_about_no_sensitive(self):
        t = parse(PAGES["about"]).text.lower()
        for s in ("blood group", "religion", "marital", "mental health", "hindu"):
            self.assertNotIn(s, t)

    def test_video_showcase_linked(self):
        self.assertIn("https://video-showcase.mogdhopaul.com/", parse(PAGES["home"]).hrefs)

    def test_known_projects_listed(self):
        p = parse(PAGES["projects"])
        for name in ("Hotspot-Auto-Connect", "Copilot2Gemini", "NN-tab", "leaflet", "video-showcase-paul"):
            self.assertIn(name, p.text)
            self.assertIn(f"https://github.com/mogdho/{name}", p.hrefs)


if __name__ == "__main__":
    unittest.main()
