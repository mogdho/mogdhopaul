import io
import json
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from PIL import Image

from scripts import build_photos
from scripts.build_photos import alt_text, local_date, render_items, replace_region
from scripts.instagram import InstagramError
from tests.helpers import ROOT

FIX = ROOT / "tests" / "fixtures"


def photo(place="Paris, France", date="2025-05-14", pid="1"):
    return {"id": pid, "permalink": f"https://www.instagram.com/p/{pid}/", "date": date, "place": place,
            "src": f"/photos/img/{pid}-1200.webp", "thumb": f"/photos/img/{pid}-600.webp",
            "width": 1200, "height": 1500}


def jpeg_bytes(w=1600, h=2000):
    buf = io.BytesIO()
    Image.new("RGB", (w, h), (120, 140, 110)).save(buf, "JPEG")
    return buf.getvalue()


class Render(unittest.TestCase):
    def test_alt_with_place(self):
        self.assertEqual(alt_text({"place": "Paris, France", "date": "2025-05-14"}),
                         "Travel photo by Mogdho Paul in Paris, France, May 2025")

    def test_alt_without_place(self):
        self.assertEqual(alt_text({"place": None, "date": "2025-05-14"}),
                         "Travel photo by Mogdho Paul, May 2025")

    def test_escapes_place(self):
        out = render_items([photo(place='A & B "<x>"')], None)
        self.assertIn("A &amp; B &quot;&lt;x&gt;&quot;", out)
        self.assertNotIn("<x>", out)

    def test_empty_state(self):
        self.assertIn('class="empty-note"', render_items([], None))

    def test_limit(self):
        self.assertEqual(render_items([photo(pid=str(i)) for i in range(8)], 6).count("<figure"), 6)

    def test_label_date_only(self):
        out = render_items([photo(place=None)], None)
        self.assertIn(">14 May 2025<", out)
        self.assertNotIn("photo__place", out)

    def test_item_markup(self):
        out = render_items([photo()], None)
        self.assertIn('class="photo fade"', out)
        self.assertIn('href="https://www.instagram.com/p/1/"', out)
        self.assertIn('srcset="/photos/img/1-600.webp 600w, /photos/img/1-1200.webp 1200w"', out)
        self.assertIn('width="1200" height="1500"', out)
        self.assertIn('loading="lazy"', out)
        self.assertIn('alt="Travel photo by Mogdho Paul in Paris, France, May 2025"', out)


class Dates(unittest.TestCase):
    def test_dhaka_date_after_local_midnight(self):
        self.assertEqual(local_date("2025-05-14T20:30:00+0000"), "2025-05-15")

    def test_dhaka_date_same_day(self):
        self.assertEqual(local_date("2025-05-14T10:00:00+0000"), "2025-05-14")


class Loading(unittest.TestCase):
    def test_first_prints_eager(self):
        out = render_items([photo(pid=str(i)) for i in range(5)], None, eager=3).split("<figure")[1:]
        self.assertEqual(['loading="lazy"' in f for f in out], [False, False, False, True, True])


class Regions(unittest.TestCase):
    HTML = "<div>\n<!-- photos:grid:start -->\nold\n<!-- photos:grid:end -->\n</div>"

    def test_replace(self):
        out = replace_region(self.HTML, "grid", "NEW")
        self.assertEqual(out, "<div>\n<!-- photos:grid:start -->\nNEW\n<!-- photos:grid:end -->\n</div>")

    def test_replace_is_repeatable(self):
        once = replace_region(self.HTML, "grid", "NEW")
        self.assertEqual(replace_region(once, "grid", "NEW"), once)

    def test_missing_markers(self):
        with self.assertRaises(ValueError):
            replace_region("<div></div>", "grid", "NEW")


class MainSafety(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        for rel in ("index.html", "photos/index.html"):
            (self.tmp / rel).parent.mkdir(parents=True, exist_ok=True)
            shutil.copy(ROOT / rel, self.tmp / rel)
        (self.tmp / "data").mkdir()
        (self.tmp / "data" / "photos.json").write_text("[]", encoding="utf-8")
        (self.tmp / "data" / "photos-exclude.txt").write_text("# one id or link per line\n", encoding="utf-8")
        (self.tmp / "photos" / "img").mkdir()
        self.fixture = self.tmp / "media.json"
        page1 = json.loads((FIX / "media_page1.json").read_text(encoding="utf-8"))
        page1.pop("paging")
        self.fixture.write_text(json.dumps(page1), encoding="utf-8")
        patcher = mock.patch.object(build_photos, "ROOT", self.tmp)
        patcher.start()
        self.addCleanup(patcher.stop)
        self.addCleanup(shutil.rmtree, self.tmp)

    def snapshot(self):
        return {p.relative_to(self.tmp).as_posix(): p.read_bytes()
                for p in self.tmp.rglob("*") if p.is_file() and p != self.fixture}

    def run_fixture(self, download):
        return build_photos.main(["--fixture", str(self.fixture)], download=download)

    def test_api_failure_changes_nothing(self):
        before = self.snapshot()
        with mock.patch.object(build_photos, "fetch_media", side_effect=InstagramError("expired")), \
                mock.patch.dict("os.environ", {"IG_TOKEN": "x"}):
            self.assertEqual(build_photos.main([]), 1)
        self.assertEqual(self.snapshot(), before)

    def test_download_failure_changes_nothing(self):
        before = self.snapshot()

        def broken(url):
            raise OSError("network down")

        self.assertEqual(self.run_fixture(broken), 1)
        self.assertEqual(self.snapshot(), before)

    def test_missing_token_fails_cleanly(self):
        before = self.snapshot()
        with mock.patch.dict("os.environ", {}, clear=True):
            self.assertEqual(build_photos.main([]), 1)
        self.assertEqual(self.snapshot(), before)

    def test_fixture_run_writes_everything(self):
        self.assertEqual(self.run_fixture(lambda url: jpeg_bytes()), 0)
        data = json.loads((self.tmp / "data" / "photos.json").read_text(encoding="utf-8"))
        self.assertEqual([d["id"] for d in data], ["101", "103"])
        self.assertEqual(data[0]["place"], "Paris, France")
        self.assertEqual(data[0]["date"], "2025-05-14")
        self.assertEqual((data[0]["width"], data[0]["height"]), (1200, 1500))
        self.assertEqual(sorted(p.name for p in (self.tmp / "photos" / "img").iterdir()),
                         ["101-1200.webp", "101-600.webp", "103-1200.webp", "103-600.webp"])
        home = (self.tmp / "index.html").read_text(encoding="utf-8")
        grid = (self.tmp / "photos" / "index.html").read_text(encoding="utf-8")
        self.assertEqual(home.count('<figure class="photo fade"'), 2)
        self.assertEqual(grid.count('<figure class="photo fade"'), 2)
        self.assertNotIn("empty-note", grid)

    def test_strip_shows_six_newest(self):
        page = {"data": [{"id": str(i), "media_type": "IMAGE", "media_url": f"https://cdn.example/{i}.jpg",
                          "permalink": f"https://www.instagram.com/p/{i}/",
                          "timestamp": "2025-05-14T10:00:00+0000"} for i in range(8)]}
        self.fixture.write_text(json.dumps(page), encoding="utf-8")
        self.run_fixture(lambda url: jpeg_bytes(400, 300))
        home = (self.tmp / "index.html").read_text(encoding="utf-8")
        grid = (self.tmp / "photos" / "index.html").read_text(encoding="utf-8")
        self.assertEqual(home.count('<figure class="photo '), 6)
        self.assertEqual(grid.count('<figure class="photo '), 8)

    def test_removed_post_image_deleted(self):
        self.run_fixture(lambda url: jpeg_bytes())
        (self.tmp / "data" / "photos-exclude.txt").write_text("101\n", encoding="utf-8")
        self.run_fixture(lambda url: jpeg_bytes())
        names = sorted(p.name for p in (self.tmp / "photos" / "img").iterdir())
        self.assertEqual(names, ["103-1200.webp", "103-600.webp"])

    def test_existing_images_not_downloaded_again(self):
        self.run_fixture(lambda url: jpeg_bytes())

        def must_not_download(url):
            raise AssertionError("downloaded again: " + url)

        self.assertEqual(self.run_fixture(must_not_download), 0)


if __name__ == "__main__":
    unittest.main()
