import copy
import json
import re
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from scripts import build_site
from scripts.build_site import build
from scripts.render_photos import alt_text, render_items
from tests.helpers import ROOT, Page


def photo(place="Paris, France", date="2025-05-14", pid="1"):
    return {"id": pid, "date": date, "place": place,
            "src": f"/photos/img/{pid}-1200.webp", "thumb": f"/photos/img/{pid}-600.webp",
            "width": 1200, "height": 1500}


class RenderPhotos(unittest.TestCase):
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

    def test_crop_position(self):
        out = render_items([{**photo(), "focus": {"x": 30, "y": 80}}], None)
        self.assertIn('style="object-position: 30% 80%"', out)

    def test_centre_crop_adds_nothing(self):
        for p in (photo(), {**photo(), "focus": {"x": 50, "y": 50}}):
            self.assertNotIn("object-position", render_items([p], None))

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



class Build(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.pages = build(ROOT)
        cls.content = {n: json.loads((ROOT / "content" / f"{n}.json").read_text(encoding="utf-8"))
                       for n in ("site", "projects")}

    def test_committed_pages_are_fresh(self):
        for rel, page in self.pages.items():
            self.assertEqual((ROOT / rel).read_text(encoding="utf-8"), page, rel)

    def test_featured_on_home(self):
        cards = re.findall(r'<h3><a href="([^"]+)"', self.pages["index.html"])
        self.assertEqual(cards, [p["url"] for p in self.content["projects"] if p["featured"]])

    def test_home_blurb_used_on_home_description_on_projects(self):
        # Any featured project with a short version; which ones are featured is the owner's choice.
        p = next((p for p in self.content["projects"]
                  if p["featured"] and p["home_blurb"] and "[" not in p["description"]), None)
        if p is None:
            self.skipTest("no featured project has a short version")
        self.assertIn(p["home_blurb"], Page(self.pages["index.html"]).text)
        self.assertIn(p["description"], Page(self.pages["projects/index.html"]).text)

    def test_profiles_drive_footer_and_jsonld(self):
        urls = [p["url"] for p in self.content["site"]["profiles"]]
        for rel, page in self.pages.items():
            parsed = Page(page)
            for u in urls:
                self.assertIn(u, parsed.hrefs, rel)
        person = next(d for d in Page(self.pages["index.html"]).jsonld if d.get("@type") == "Person")
        self.assertEqual(person["sameAs"], urls)



class Main(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.tmp)
        for d in ("content", "templates"):
            shutil.copytree(ROOT / d, self.tmp / d)
        (self.tmp / "photos" / "img").mkdir(parents=True)
        patcher = mock.patch.object(build_site, "ROOT", self.tmp)
        patcher.start()
        self.addCleanup(patcher.stop)

    def edit(self, name, fn):
        path = self.tmp / "content" / f"{name}.json"
        data = json.loads(path.read_text(encoding="utf-8"))
        fn(data)
        path.write_text(json.dumps(data), encoding="utf-8")

    def snapshot(self):
        return {p.relative_to(self.tmp).as_posix(): p.read_bytes() for p in self.tmp.rglob("*") if p.is_file()}

    def test_writes_four_pages(self):
        self.assertEqual(build_site.main([]), 0)
        for rel in build_site.PAGES:
            self.assertTrue((self.tmp / rel).exists(), rel)

    def test_invalid_content_writes_nothing(self):
        self.edit("site", lambda s: s["home"].update(text="Mogdha says hi"))
        before = self.snapshot()
        self.assertEqual(build_site.main([]), 1)
        self.assertEqual(self.snapshot(), before)

    def test_unused_images_deleted(self):
        img = self.tmp / "photos" / "img"
        for name in ("keep-1200.webp", "keep-600.webp", "old-600.webp"):
            (img / name).write_bytes(b"x")
        self.edit("photos", lambda ps: ps.append(photo(pid="keep")))
        self.assertEqual(build_site.main([]), 0)
        self.assertEqual(sorted(p.name for p in img.iterdir()), ["keep-1200.webp", "keep-600.webp"])
        self.assertIn("Paris, France", (self.tmp / "photos" / "index.html").read_text(encoding="utf-8"))

    def test_text_link_rendered(self):
        self.edit("site", lambda s: s["about"]["sections"][0].update(text="See my [photos page](/photos/)."))
        build_site.main([])
        about = (self.tmp / "about" / "index.html").read_text(encoding="utf-8")
        self.assertIn('<a href="/photos/">photos page</a>', about)

    def test_skills_before_projects(self):
        self.edit("site", lambda s: s.update(skills={"stack": ["JavaScript", "C & C++"], "tools": []}))
        build_site.main([])
        home = (self.tmp / "index.html").read_text(encoding="utf-8")
        self.assertLess(home.index('id="skills-title"'), home.index('id="projects-title"'))
        self.assertIn("<li>C &amp; C++</li>", home)
        self.assertIn("Tech stack", home)
        self.assertNotIn("<dt>Tools</dt>", home)  # empty group hidden

    def test_no_skills_no_section(self):
        self.edit("site", lambda s: s.update(skills={"stack": [], "tools": []}))
        build_site.main([])
        self.assertNotIn("skills-title", (self.tmp / "index.html").read_text(encoding="utf-8"))

    def test_new_profile_photo_gets_new_address(self):
        # Browsers and link previews cache the photo, so its address changes with its contents.
        (self.tmp / "mogdhopaul.jpeg").write_bytes(b"one")
        build_site.main([])
        first = (self.tmp / "index.html").read_text(encoding="utf-8")
        (self.tmp / "mogdhopaul.jpeg").write_bytes(b"two")
        build_site.main([])
        second = (self.tmp / "index.html").read_text(encoding="utf-8")
        v1 = re.search(r'/mogdhopaul\.jpeg\?v=(\w+)"', first).group(1)
        v2 = re.search(r'/mogdhopaul\.jpeg\?v=(\w+)"', second).group(1)
        self.assertNotEqual(v1, v2)
        for page in (first, second):
            self.assertEqual(len(re.findall(r'mogdhopaul\.jpeg"', page)), 0, "every photo link is versioned")

    def test_zero_photos_shows_empty_note(self):
        self.edit("photos", lambda ps: ps.clear())
        build_site.main([])
        self.assertIn("empty-note", (self.tmp / "photos" / "index.html").read_text(encoding="utf-8"))
        self.assertIn("empty-note", (self.tmp / "index.html").read_text(encoding="utf-8"))

    def test_photos_newest_first(self):
        self.edit("photos", lambda ps: ps.extend([photo(pid="old", date="2024-01-01", place="Sylhet"),
                                                  photo(pid="new", date="2025-06-01", place="Paris")]))
        build_site.main([])
        grid = (self.tmp / "photos" / "index.html").read_text(encoding="utf-8")
        self.assertLess(grid.index("Paris"), grid.index("Sylhet"))


if __name__ == "__main__":
    unittest.main()
