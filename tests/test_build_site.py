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

    def test_committed_admin_page_is_fresh(self):
        self.assertEqual((ROOT / "admin" / "index.html").read_text(encoding="utf-8"), build_site._admin_page())

    def test_changed_files_get_new_addresses(self):
        # The site sits behind a cache that keeps files for hours: every changing file is linked with a version.
        home = self.pages["index.html"]
        self.assertRegex(home, r'href="/style\.css\?v=\w+"')
        self.assertRegex(home, r'src="/script\.js\?v=\w+"')
        admin = build_site._admin_page()
        for name in ("/style.css", "/admin/admin.css", "/admin/app.js"):
            self.assertRegex(admin, re.escape(name) + r'\?v=\w+"')
        imports = json.loads(re.search(r'<script type="importmap">(.*?)</script>', admin).group(1))["imports"]
        found = {Path(m.group(1)).name for f in (ROOT / "admin").glob("*.js")
                 for m in re.finditer(r"from '\./([\w.]+)'", f.read_text(encoding="utf-8"))}
        self.assertEqual({k.rsplit("/", 1)[1] for k in imports}, found, "every imported admin module is versioned")

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

    def skill(self, name, icon=None):
        return {"name": name, "icon": icon}

    def icon_file(self, icon_id):
        path = self.tmp / build_site.skill_icon_path(icon_id)
        path.parent.mkdir(exist_ok=True)
        path.write_text("<svg/>", encoding="utf-8")
        return path

    def test_skills_before_projects(self):
        self.edit("site", lambda s: s.update(skills={"stack": [self.skill("JavaScript"), self.skill("C & C++")], "tools": []}))
        build_site.main([])
        home = (self.tmp / "index.html").read_text(encoding="utf-8")
        self.assertLess(home.index('id="skills-title"'), home.index('id="projects-title"'))
        self.assertIn('<span class="skill__name">C &amp; C++</span>', home)
        self.assertIn("Tech stack", home)
        self.assertNotIn("<dt>Tools</dt>", home)  # empty group hidden

    def test_skill_icon_from_its_file(self):
        self.icon_file("simple-icons:python")
        self.edit("site", lambda s: s.update(skills={"stack": [self.skill("Python", "simple-icons:python")], "tools": []}))
        build_site.main([])
        home = (self.tmp / "index.html").read_text(encoding="utf-8")
        self.assertIn("--icon: url(/skill-icons/simple-icons--python.svg)", home)

    def test_skill_without_icon_gets_group_default(self):
        self.icon_file("tabler:tools")
        self.edit("site", lambda s: s.update(skills={"stack": [], "tools": [self.skill("CapCut"), self.skill("Gone", "x:missing")]}))
        build_site.main([])
        home = (self.tmp / "index.html").read_text(encoding="utf-8")
        self.assertEqual(home.count("url(/skill-icons/tabler--tools.svg)"), 2)

    def test_skill_initials_when_no_icon_files(self):
        self.assertEqual(build_site.skill_mark("Final Cut Pro"), "FCP")
        self.assertEqual(build_site.skill_mark("Blender"), "Bl")
        self.edit("site", lambda s: s.update(skills={"stack": [self.skill("Blender")], "tools": []}))
        build_site.main([])
        self.assertIn('aria-hidden="true">Bl</span>', (self.tmp / "index.html").read_text(encoding="utf-8"))

    def test_unused_skill_icons_deleted(self):
        keep, gone, default = self.icon_file("cib:figma"), self.icon_file("cib:old"), self.icon_file("tabler:code")
        self.edit("site", lambda s: s.update(skills={"stack": [self.skill("Figma", "cib:figma")], "tools": []}))
        self.assertEqual(build_site.main([]), 0)
        self.assertTrue(keep.exists())
        self.assertTrue(default.exists())
        self.assertFalse(gone.exists())

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

    def test_home_shows_three_newest_linked_to_photos_page(self):
        self.edit("photos", lambda ps: (ps.clear(), ps.extend(
            photo(pid=f"p{i}", date=f"2025-05-1{i}") for i in range(5))))
        build_site.main([])
        home = (self.tmp / "index.html").read_text(encoding="utf-8")
        photos_page = (self.tmp / "photos" / "index.html").read_text(encoding="utf-8")
        strip = home[home.index('class="photo-strip"'):home.index("</section>", home.index('class="photo-strip"'))]
        self.assertEqual(strip.count("<figure"), 3)
        self.assertEqual(re.findall(r'href="/photos/#photo-(\w+)"', strip), ["p4", "p3", "p2"])  # newest first
        for pid in ("p4", "p3", "p2"):
            self.assertIn(f'id="photo-{pid}"', photos_page)
        self.assertEqual(photos_page.count("<figure"), 5)
        self.assertNotIn("photo__link", photos_page)

    def test_same_day_uploads_newest_first(self):
        # Uploads are added at the end of the list; on the same date the last upload is the newest.
        self.edit("photos", lambda ps: (ps.clear(), ps.extend([
            photo(pid="old", date="2025-05-01"), photo(pid="a", date="2025-06-01"),
            photo(pid="b", date="2025-06-01"), photo(pid="c", date="2025-06-01"), photo(pid="d", date="2025-06-01")])))
        build_site.main([])
        home = (self.tmp / "index.html").read_text(encoding="utf-8")
        self.assertEqual(re.findall(r'href="/photos/#photo-(\w+)"', home), ["d", "c", "b"])
        photos_page = (self.tmp / "photos" / "index.html").read_text(encoding="utf-8")
        self.assertEqual(re.findall(r'id="photo-(\w+)"', photos_page), ["d", "c", "b", "a", "old"])

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
