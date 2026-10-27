import shutil
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from PIL import Image

from scripts import build_photos
from scripts.build_photos import alt_text, read_list, render_items, replace_region
from tests.helpers import ROOT


def photo(place="Paris, France", date="2025-05-14", pid="1"):
    return {"id": pid, "date": date, "place": place,
            "src": f"/photos/img/{pid}-1200.webp", "thumb": f"/photos/img/{pid}-600.webp",
            "width": 1200, "height": 1500}


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
        self.assertIn('srcset="/photos/img/1-600.webp 600w, /photos/img/1-1200.webp 1200w"', out)
        self.assertIn('width="1200" height="1500"', out)
        self.assertIn('loading="lazy"', out)
        self.assertIn('alt="Travel photo by Mogdho Paul in Paris, France, May 2025"', out)
        self.assertNotIn("instagram", out)

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


class ReadList(unittest.TestCase):
    def setUp(self):
        self.dir = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.dir)
        self.csv = self.dir / "photos.csv"

    def write(self, text):
        self.csv.write_text(text, encoding="utf-8")
        return read_list(self.csv)

    def test_reads_rows_newest_first(self):
        rows = self.write('file,place,date\nold.jpg,Sylhet,2024-01-02\nnew.jpg,"Paris, France",2025-05-14\n')
        self.assertEqual([r["file"] for r in rows], ["new.jpg", "old.jpg"])
        self.assertEqual(rows[0]["place"], "Paris, France")

    def test_blank_place_allowed(self):
        self.assertIsNone(self.write("file,place,date\na.jpg,,2025-05-14\n")[0]["place"])

    def test_comment_and_empty_lines_skipped(self):
        rows = self.write("file,place,date\n# a note\n\na.jpg,Sylhet,2025-05-14\n")
        self.assertEqual(len(rows), 1)

    def test_bad_date_names_the_line(self):
        with self.assertRaisesRegex(ValueError, "line 2.*date"):
            self.write("file,place,date\na.jpg,Sylhet,14/05/2025\n")

    def test_bengali_place_rejected(self):
        with self.assertRaisesRegex(ValueError, "line 2.*English"):
            self.write("file,place,date\na.jpg,প্যারিস,2025-05-14\n")

    def test_other_name_spelling_rejected(self):
        with self.assertRaisesRegex(ValueError, "line 2"):
            self.write("file,place,date\na.jpg,Mogdha's home,2025-05-14\n")

    def test_missing_file_is_empty_list(self):
        self.assertEqual(read_list(self.dir / "nope.csv"), [])


class MainSafety(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.tmp)
        for rel in ("index.html", "photos/index.html"):
            (self.tmp / rel).parent.mkdir(parents=True, exist_ok=True)
            shutil.copy(ROOT / rel, self.tmp / rel)
        (self.tmp / "data").mkdir()
        (self.tmp / "data" / "photos.json").write_text("[]", encoding="utf-8")
        (self.tmp / "photos" / "img").mkdir()
        self.originals = self.tmp / "photo-originals"
        self.originals.mkdir()
        patcher = mock.patch.object(build_photos, "ROOT", self.tmp)
        patcher.start()
        self.addCleanup(patcher.stop)

    def add_original(self, name, size=(1600, 2000)):
        Image.new("RGB", size, (120, 140, 110)).save(self.originals / name, "JPEG")

    def set_list(self, text):
        (self.tmp / "data" / "photos.csv").write_text("file,place,date\n" + text, encoding="utf-8")

    def snapshot(self):
        return {p.relative_to(self.tmp).as_posix(): p.read_bytes()
                for p in self.tmp.rglob("*") if p.is_file()}

    def test_builds_images_json_and_pages(self):
        self.add_original("Paris Trip.JPG")
        self.add_original("sylhet.png", (800, 600))
        self.set_list('Paris Trip.JPG,"Paris, France",2025-05-14\nsylhet.png,Sylhet,2024-01-02\n')
        self.assertEqual(build_photos.main([]), 0)
        names = sorted(p.name for p in (self.tmp / "photos" / "img").iterdir())
        self.assertEqual(names, ["paris-trip-1200.webp", "paris-trip-600.webp",
                                 "sylhet-1200.webp", "sylhet-600.webp"])
        with Image.open(self.tmp / "photos" / "img" / "paris-trip-1200.webp") as im:
            self.assertEqual(im.size, (1200, 1500))
        home = (self.tmp / "index.html").read_text(encoding="utf-8")
        grid = (self.tmp / "photos" / "index.html").read_text(encoding="utf-8")
        self.assertEqual(grid.count('<figure class="photo fade"'), 2)
        self.assertIn("Paris, France", home)
        self.assertLess(grid.index("Paris, France"), grid.index("Sylhet"))

    def test_strip_shows_six_newest(self):
        rows = ""
        for i in range(8):
            self.add_original(f"p{i}.jpg", (400, 300))
            rows += f"p{i}.jpg,Place {i},2025-01-0{i + 1}\n"
        self.set_list(rows)
        build_photos.main([])
        home = (self.tmp / "index.html").read_text(encoding="utf-8")
        grid = (self.tmp / "photos" / "index.html").read_text(encoding="utf-8")
        self.assertEqual(home.count('<figure class="photo '), 6)
        self.assertEqual(grid.count('<figure class="photo '), 8)
        self.assertIn("Place 7", home)
        self.assertNotIn("Place 0", home)

    def test_missing_original_changes_nothing(self):
        self.set_list("ghost.jpg,Paris,2025-05-14\n")
        before = self.snapshot()
        self.assertEqual(build_photos.main([]), 1)
        self.assertEqual(self.snapshot(), before)

    def test_bad_list_changes_nothing(self):
        self.add_original("a.jpg")
        self.set_list("a.jpg,Paris,May 2025\n")
        before = self.snapshot()
        self.assertEqual(build_photos.main([]), 1)
        self.assertEqual(self.snapshot(), before)

    def test_removed_row_deletes_its_images(self):
        self.add_original("a.jpg")
        self.add_original("b.jpg")
        self.set_list("a.jpg,Paris,2025-05-14\nb.jpg,Sylhet,2025-05-13\n")
        build_photos.main([])
        self.set_list("b.jpg,Sylhet,2025-05-13\n")
        build_photos.main([])
        names = sorted(p.name for p in (self.tmp / "photos" / "img").iterdir())
        self.assertEqual(names, ["b-1200.webp", "b-600.webp"])

    def test_existing_images_reused_without_original(self):
        self.add_original("a.jpg")
        self.set_list("a.jpg,Paris,2025-05-14\n")
        build_photos.main([])
        (self.originals / "a.jpg").unlink()  # e.g. building on another computer
        self.assertEqual(build_photos.main([]), 0)

    def test_empty_list_shows_empty_note(self):
        self.set_list("")
        self.assertEqual(build_photos.main([]), 0)
        self.assertIn("empty-note", (self.tmp / "photos" / "index.html").read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
