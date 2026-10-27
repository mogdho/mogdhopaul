import io
import json
import unittest
import urllib.error

from scripts.instagram import (InstagramError, Post, extract_place, fetch_media,
                               refresh_token, select_posts)
from tests.helpers import ROOT

FIX = ROOT / "tests" / "fixtures"


def load(name):
    return json.loads((FIX / name).read_text(encoding="utf-8"))


class FakeOpen:
    """Stands in for urllib.request.urlopen: returns queued JSON bodies, records URLs."""

    def __init__(self, *bodies):
        self.bodies = list(bodies)
        self.urls = []

    def __call__(self, url, timeout=None):
        self.urls.append(url)
        body = self.bodies.pop(0)
        if isinstance(body, Exception):
            raise body
        return io.BytesIO(json.dumps(body).encode())


class ExtractPlace(unittest.TestCase):
    def test_pin_line_wins(self):
        self.assertEqual(extract_place("lovely day\n📍 Paris, France #travel"), "Paris, France")

    def test_first_line_cleaned(self):
        self.assertEqual(extract_place("Eiffel Tower, Paris 🇫🇷 #paris\nmore"), "Eiffel Tower, Paris")

    def test_hashtags_only(self):
        self.assertIsNone(extract_place("#travel #snow"))

    def test_none(self):
        self.assertIsNone(extract_place(None))

    def test_emoji_only(self):
        self.assertIsNone(extract_place("❄️❄️"))

    def test_bengali(self):
        self.assertIsNone(extract_place("প্যারিস"))

    def test_sentence(self):
        self.assertIsNone(extract_place("What a wonderful day walking around the old town with friends"))

    def test_html_chars_dropped(self):
        self.assertEqual(extract_place("Rock & <Roll> Café"), "Rock Roll Café")

    def test_bengali_digits_rejected(self):
        self.assertIsNone(extract_place("Cox's Bazar ২০২৪"))

    def test_banned_name_spellings_rejected(self):
        self.assertIsNone(extract_place("Mogdha's birthday"))
        self.assertIsNone(extract_place("with mugdho in Dhaka"))

    def test_mentions_dropped(self):
        self.assertEqual(extract_place("Louvre, Paris @someone"), "Louvre, Paris")


class SelectPosts(unittest.TestCase):
    def setUp(self):
        self.media = load("media_page1.json")["data"] + load("media_page2.json")["data"]

    def ids(self, posts):
        return [p.id for p in posts]

    def test_skips_video(self):
        self.assertNotIn("102", self.ids(select_posts(self.media, set())))

    def test_carousel_uses_first_image_child(self):
        post = next(p for p in select_posts(self.media, set()) if p.id == "103")
        self.assertEqual(post.image_url, "https://cdn.example/103b.jpg")
        self.assertEqual(post.place, "Old Town, Bucharest")

    def test_carousel_without_image_skipped(self):
        self.assertNotIn("104", self.ids(select_posts(self.media, set())))

    def test_order_and_fields(self):
        posts = select_posts(self.media, set())
        self.assertEqual(self.ids(posts), ["101", "103", "105"])
        self.assertEqual(posts[0], Post("101", "https://www.instagram.com/p/AAA101/",
                                        "2025-05-14T10:00:00+0000", "https://cdn.example/101.jpg",
                                        "Paris, France"))
        self.assertIsNone(posts[2].place)

    def test_exclude_by_id_and_permalink(self):
        posts = select_posts(self.media, {"101", "https://www.instagram.com/p/CCC103/"})
        self.assertEqual(self.ids(posts), ["105"])

    def test_limit(self):
        self.assertEqual(len(select_posts(self.media, set(), limit=1)), 1)

    def test_exclude_link_pasted_from_app(self):
        posts = select_posts(self.media, {"https://www.instagram.com/p/AAA101/?igsh=xyz123",
                                          "https://instagram.com/p/CCC103"})
        self.assertEqual(self.ids(posts), ["105"])


class Fetch(unittest.TestCase):
    def test_follows_paging(self):
        opener = FakeOpen(load("media_page1.json"), load("media_page2.json"))
        media = fetch_media("TOKEN", urlopen=opener)
        self.assertEqual(len(media), 5)
        self.assertIn("access_token=TOKEN", opener.urls[0])
        self.assertIn("graph.instagram.com/me/media", opener.urls[0])
        self.assertEqual(opener.urls[1], "https://graph.instagram.com/next-page")

    def test_api_error_raises(self):
        opener = FakeOpen({"error": {"message": "Invalid OAuth access token"}})
        with self.assertRaises(InstagramError):
            fetch_media("BAD", urlopen=opener)

    def test_http_error_raises(self):
        opener = FakeOpen(urllib.error.URLError("offline"))
        with self.assertRaises(InstagramError):
            fetch_media("TOKEN", urlopen=opener)

    def test_refresh_returns_token(self):
        opener = FakeOpen({"access_token": "NEW", "token_type": "bearer", "expires_in": 5183944})
        self.assertEqual(refresh_token("OLD", urlopen=opener), "NEW")
        self.assertIn("grant_type=ig_refresh_token", opener.urls[0])

    def test_refresh_error_raises(self):
        with self.assertRaises(InstagramError):
            refresh_token("OLD", urlopen=FakeOpen({"error": {"message": "expired"}}))


if __name__ == "__main__":
    unittest.main()
