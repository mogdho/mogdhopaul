import copy
import unittest

from scripts.content import ContentError, inline, load_content, render_text, validate
from tests.helpers import ROOT


class Inline(unittest.TestCase):
    def test_link(self):
        self.assertEqual(inline("my [photos page](/photos/)."), 'my <a href="/photos/">photos page</a>.')

    def test_html_escaped(self):
        self.assertEqual(inline("<b>hi</b> & co"), "&lt;b&gt;hi&lt;/b&gt; &amp; co")

    def test_bad_scheme_left_as_text(self):
        self.assertEqual(inline("[x](javascript:alert(1))"), "[x](javascript:alert(1))")

    def test_quote_in_url_escaped(self):
        self.assertNotIn('"onmouseover', inline('[x](https://a.b/"onmouseover=1)'))

    def test_mailto(self):
        self.assertIn('href="mailto:a@b.c"', inline("[mail](mailto:a@b.c)"))


class RenderText(unittest.TestCase):
    def test_paragraphs(self):
        self.assertEqual(render_text("One.\n\nTwo\nlines."), "<p>One.</p>\n<p>Two\nlines.</p>")

    def test_empty(self):
        self.assertEqual(render_text("  "), "")


class Validate(unittest.TestCase):
    def setUp(self):
        self.c = copy.deepcopy(load_content(ROOT))

    def assertRejects(self, field):
        with self.assertRaisesRegex(ContentError, field):
            validate(self.c)

    def test_repo_content_valid(self):
        validate(self.c)

    def test_banned_spelling(self):
        self.c["site"]["home"]["text"] = "Mogdha says hi"
        self.assertRejects(r"site\.home\.text")

    def test_bengali(self):
        self.c["site"]["about"]["sections"][0]["text"] = "প্যারিস"
        self.assertRejects(r"site\.about\.sections\[0\]\.text")

    def test_featured_must_be_three(self):
        for p in self.c["projects"]:
            p["featured"] = False
        self.c["projects"][0]["featured"] = True
        self.c["projects"][1]["featured"] = True
        self.assertRejects("featured")

    def test_bad_profile_url(self):
        self.c["site"]["profiles"][0]["url"] = "ftp://x"
        self.assertRejects(r"site\.profiles\[0\]\.url")

    def test_bad_photo_date(self):
        self.c["photos"] = [{"id": "a", "place": None, "date": "14/05/2025", "src": "/photos/img/a-1200.webp",
                             "thumb": "/photos/img/a-600.webp", "width": 1200, "height": 900}]
        self.assertRejects(r"photos\[0\]\.date")

    def test_photo_paths_inside_img(self):
        self.c["photos"] = [{"id": "a", "place": None, "date": "2025-05-14", "src": "/photos/img/../../x.webp",
                             "thumb": "/photos/img/a-600.webp", "width": 1200, "height": 900}]
        self.assertRejects(r"photos\[0\]\.src")

    def test_missing_field(self):
        del self.c["projects"][0]["url"]
        self.assertRejects(r"projects\[0\]\.url")

    def test_project_name_not_banned(self):
        self.c["projects"][2]["name"] = "Mugdho tool"
        self.assertRejects(r"projects\[2\]\.name")

    def test_identity_fits_google_description(self):
        self.c["site"]["identity"] = "Mogdho Paul " + "builds things. " * 12
        self.assertRejects(r"site\.identity.*160")

    def test_bad_group(self):
        self.c["projects"][2]["group"] = "linux"
        self.assertRejects(r"projects\[2\]\.group")


if __name__ == "__main__":
    unittest.main()
