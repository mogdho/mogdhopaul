# mogdhopaul.com Redesign Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Rebuild mogdhopaul.com as a four-page "quiet travel notebook" site that ranks for "Mogdho Paul" and shows his Instagram travel photos, updated nightly.

**Architecture:** Hand-written static pages (`/`, `/about/`, `/projects/`, `/photos/`) sharing one stylesheet, served by GitHub Pages. A nightly GitHub Action runs a Python script that fetches Instagram posts, saves resized WebP images into the repo, and rewrites marked regions of the HTML so photos exist without JavaScript. Python `unittest` checks guard SEO rules, anti-AI-look rules and the photo pipeline.

**Tech Stack:** HTML, CSS, a little vanilla JS; Python 3.12 (stdlib + Pillow) for the photo pipeline and tests; GitHub Actions; Instagram API with Instagram Login (`graph.instagram.com`).

**Spec:** `docs/superpowers/specs/2026-10-27-site-redesign-design.md`

## Global Constraints

- Identity line, verbatim: "Mogdho Paul is a developer and SEO specialist from Bangladesh who builds small web tools and automations."
- Only spelling: "Mogdho Paul" / handle `mogdhopaul`. The strings "Mugdho", "Mogdha" and any Bengali script must not appear in any page or JSON-LD.
- Location is Bangladesh. "Bucharest" must not appear in titles, meta tags or JSON-LD.
- "Video editor" / "motion designer" must not appear in any `<title>`, meta description or `jobTitle`. Video editing appears as a section on Home and in About.
- English only.
- Plain HTML/CSS/JS, no framework, no build step for pages. Hosting: GitHub Pages, CNAME `mogdhopaul.com` (keep file).
- Google Analytics tag `G-LDY4Z5D7MW` on every page.
- `.claude/` is never committed (in `.gitignore`).
- All key text and photos are in the HTML; nothing important is injected by JS.
- Anti-AI-look: no `linear-gradient`/`radial-gradient`/`conic-gradient`, no `background-clip: text`, no `backdrop-filter`, no glow `box-shadow` with coloured blur, no typing effect, no emoji in HTML, no pill-tag rows, no infinite animations.
- Motion: gentle fade-in only; disabled under `prefers-reduced-motion: reduce`.
- Profile links (footer on every page and JSON-LD `sameAs`, exactly):
  `https://www.facebook.com/mogdhopaul`, `https://www.instagram.com/mogdhopaul/`, `https://www.linkedin.com/in/mogdho-paul/`, `https://github.com/mogdho`, `https://www.youtube.com/@mogdhoPAUL`, `https://t.me/MOGdhA`, `https://maggy2minutes.wordpress.com/`
- Footer contact: `mailto:mogdhapal@gmail.com` and `https://wa.me/+8801998955221`.
- Video showcase link: `https://video-showcase.mogdhopaul.com/`.
- About page excludes blood group, religion, marital status, mental health.
- Photos: show only extracted place and date, never the full caption. Image posts only; carousels use their first image child; videos/reels skipped. Exclude list supported.

## Review Focus

1. **Instagram fetch fails or token expired** → the job exits non-zero and leaves existing photos, JSON and HTML untouched (never wipes the gallery). Test in Task 6.
2. **Feed returns zero usable posts** → photo regions show a short, calm empty-state line, not a blank gap. Test in Task 6.
3. **Captions with `<`, `&`, quotes, or emoji-only text** → place text is HTML-escaped; emoji-only gives no place. Tests in Tasks 5 and 6.
4. **Carousel whose first child is a video** → use the first IMAGE child; skip if none. Test in Task 5.
5. **Visitor without JavaScript** → content is visible; fade-in hiding CSS applies only under `html.js`. Test in Task 1.

---

## File Structure

```
.gitignore                         # add .claude/
index.html                         # Home (rewrite)
about/index.html                   # About (new)
projects/index.html                # Projects (new)
photos/index.html                  # Photos (new)
photos/img/                        # generated WebP images (nightly job)
style.css                          # rewrite: tokens, type, layout, light/dark
script.js                          # rewrite: adds html.js + fade-in only
mogdhopaul.webp                    # profile photo, resized (keep .jpeg for og:image)
sitemap.xml, robots.txt, CNAME, favicon.png   # keep / update
DESIGN.md                          # design system record (Impeccable)
data/photos.json                   # generated photo data
data/photos-exclude.txt            # hand-edited exclude list
scripts/instagram.py               # API fetch, post selection, place extraction
scripts/build_photos.py            # images + JSON + HTML regions; CLI entry
scripts/requirements.txt           # Pillow
.github/workflows/photos.yml       # nightly photo update
.github/workflows/refresh-token.yml# monthly token refresh
docs/instagram-setup.md            # owner setup guide
tests/helpers.py                   # page loading + HTML parsing helpers
tests/test_style.py                # CSS / JS anti-pattern rules
tests/test_pages.py                # SEO + content rules for all pages
tests/test_instagram.py            # place extraction, selection, fetch
tests/test_build_photos.py         # rendering, markers, failure safety
tests/fixtures/media_page1.json, media_page2.json
```

Run all tests: `python -m unittest discover -s tests -v`

---

### Task 1: Branch, design system and stylesheet

**Files:**
- Create: `.gitignore`, `DESIGN.md`, `tests/helpers.py`, `tests/test_style.py`, `tests/__init__.py` (empty)
- Modify: `style.css` (full rewrite), `script.js` (full rewrite)
- Commit also: `docs/superpowers/specs/2026-10-27-site-redesign-design.md`, this plan

**Interfaces:**
- Produces: `tests/helpers.py`:
  - `ROOT: Path` (repo root)
  - `PAGES: dict[str, Path]` = `{"home": ROOT/"index.html", "about": ROOT/"about/index.html", "projects": ROOT/"projects/index.html", "photos": ROOT/"photos/index.html"}`
  - `parse(path: Path) -> Page` where `Page` has `.title: str`, `.meta: dict[str, str]` (keyed by `name` or `property`), `.links: list[tuple[str, str]]` (rel, href), `.h1_count: int`, `.text: str` (visible text), `.hrefs: list[str]`, `.jsonld: list[dict]`, `.html: str`, `.imgs: list[dict]` (attrs). Built on `html.parser.HTMLParser`.
- Produces: CSS class vocabulary later tasks use: `.site-header`, `.site-nav`, `.site-footer`, `.morse`, `.prose`, `.photo-strip`, `.photo-grid`, `.photo` (figure), `.photo__label`, `.project-list`, `.project`, `.fade` (fade-in target), `.empty-note`.

- [ ] **Step 1: Create branch and ignore the skill folder**

```bash
git checkout -b redesign
printf ".claude/\n__pycache__/\n" > .gitignore
git status --short   # .claude/ must no longer be listed
```

- [ ] **Step 2: Set the design direction with the skills**

Run `python .claude/skills/ui-ux-pro-max/scripts/search.py "personal travel journal photography" --design-system` and `... "editorial serif notebook" --domain typography`. Then invoke the `impeccable` skill with the spec's "Visual direction" section and the anti-AI constraints above, to choose: paper/ink/accent colours (accent earthy, from travel photos), one serif display face + one sans body face + one monospace label face, spacing scale, dark-mode palette. Contrast ≥ 4.5:1 for body text in both modes. Record the result in `DESIGN.md` (tokens, fonts, rules, banned patterns).

- [ ] **Step 3: Write failing style tests** in `tests/test_style.py`

```python
class StyleRules(unittest.TestCase):
    def setUp(self): self.css = (ROOT/"style.css").read_text(encoding="utf-8"); self.js = (ROOT/"script.js").read_text(encoding="utf-8")
    def test_no_gradients(self):
        for bad in ("linear-gradient", "radial-gradient", "conic-gradient", "background-clip: text", "backdrop-filter"):
            self.assertNotIn(bad, self.css)
    def test_no_infinite_animation(self): self.assertNotIn("infinite", self.css)
    def test_reduced_motion(self): self.assertIn("prefers-reduced-motion: reduce", self.css)
    def test_dark_mode(self): self.assertIn("prefers-color-scheme: dark", self.css)
    def test_fade_hidden_only_with_js(self):
        # any rule that hides .fade must be scoped under html.js / .js
        for m in re.finditer(r"([^{}]*\.fade[^{}]*)\{([^}]*)\}", self.css):
            if "opacity: 0" in m.group(2) or "opacity:0" in m.group(2):
                self.assertIn(".js", m.group(1))
    def test_no_typing_effect(self): self.assertNotIn("typeRole", self.js)
    def test_js_sets_js_class(self): self.assertIn("classList.add('js')", self.js)
    def test_gitignore_has_claude(self): self.assertIn(".claude/", (ROOT/".gitignore").read_text())
```

- [ ] **Step 4: Run** `python -m unittest tests.test_style -v` — Expected: FAIL (old CSS has gradients, old JS has `typeRole`).

- [ ] **Step 5: Rewrite `style.css` and `script.js`**

`style.css`: tokens from `DESIGN.md` as custom properties on `:root`, dark overrides under `@media (prefers-color-scheme: dark)`, base type (body ≥ 16px, line-height ~1.6), the class vocabulary above, album-like `.photo-grid` with varied spans (CSS grid, some items span 2 rows/cols by `:nth-child` pattern), `.morse` styled as a quiet monospace divider, focus-visible rings, mobile-first with no horizontal scroll. Fonts loaded via `<link>` in each page (not `@import`) with `display=swap`.
`script.js`: `document.documentElement.classList.add('js')` first line; IntersectionObserver adds `.is-visible` to `.fade` elements once; skip entirely when `matchMedia('(prefers-reduced-motion: reduce)')` matches. Nothing else.

- [ ] **Step 6: Run** `python -m unittest tests.test_style -v` — Expected: PASS.

- [ ] **Step 7: Commit**

```bash
git add .gitignore DESIGN.md style.css script.js tests docs
git commit -m "feat: notebook design system and base stylesheet"
```

---

### Task 2: Home page

**Files:**
- Modify: `index.html` (full rewrite)
- Create: `mogdhopaul.webp`, `tests/test_pages.py`

**Interfaces:**
- Consumes: `parse`, `PAGES` from `tests/helpers.py`; CSS classes from Task 1.
- Produces: the shared header and footer markup (copied verbatim into Tasks 3–5); photo markers in `index.html`:
  `<!-- photos:strip:start -->` … `<!-- photos:strip:end -->` inside `<div class="photo-strip">`.
- Produces in `tests/test_pages.py`: `SAME_AS: list[str]` (the seven profile URLs), `class CommonPageRules` mixin with `page_key` attribute, reused by Tasks 3–5.

- [ ] **Step 1: Write failing tests** in `tests/test_pages.py`

```python
IDENTITY = "Mogdho Paul is a developer and SEO specialist from Bangladesh who builds small web tools and automations."
SAME_AS = [ ...seven URLs from Global Constraints... ]
BANNED = ("Mugdho", "Mogdha", "AI-Assisted")
class CommonPageRules:
    page_key = None
    def setUp(self): self.p = parse(PAGES[self.page_key])
    def test_title_has_name(self): self.assertIn("Mogdho Paul", self.p.title)
    def test_title_meta_no_video_role(self):
        for s in (self.p.title, self.p.meta["description"]): self.assertNotRegex(s.lower(), "video editor|motion designer")
    def test_meta_description(self): self.assertIn("Mogdho Paul", self.p.meta["description"]); self.assertLessEqual(len(self.p.meta["description"]), 160)
    def test_canonical(self): self.assertIn(("canonical", f"https://mogdhopaul.com{URLS[self.page_key]}"), self.p.links)
    def test_og_twitter(self):
        for k in ("og:title", "og:description", "og:url", "og:image", "twitter:card"): self.assertIn(k, self.p.meta)
    def test_one_h1(self): self.assertEqual(self.p.h1_count, 1)
    def test_analytics(self): self.assertIn("G-LDY4Z5D7MW", self.p.html)
    def test_banned_strings(self):
        for b in BANNED: self.assertNotIn(b, self.p.html)
        self.assertIsNone(re.search(r"[ঀ-৿]", self.p.html))   # Bengali script
        self.assertNotIn("Bucharest", self.p.title + self.p.meta["description"] + json.dumps(self.p.jsonld))
    def test_no_emoji(self): self.assertIsNone(re.search(r"[\U0001F300-\U0001FAFF☀-➿]", self.p.html))
    def test_footer_links(self):
        for u in SAME_AS + ["mailto:mogdhapal@gmail.com", "https://wa.me/+8801998955221"]: self.assertIn(u, self.p.hrefs)
    def test_nav(self):
        for u in ("/", "/about/", "/projects/", "/photos/"): self.assertIn(u, self.p.hrefs)
    def test_images_have_alt_and_size(self):
        for img in self.p.imgs: self.assertTrue(img.get("alt")); self.assertIn("width", img); self.assertIn("height", img)
URLS = {"home": "/", "about": "/about/", "projects": "/projects/", "photos": "/photos/"}

class HomePage(CommonPageRules, unittest.TestCase):
    page_key = "home"
    def test_identity_line(self): self.assertIn(IDENTITY, self.p.text)
    def test_person_jsonld(self):
        person = next(d for d in self.p.jsonld if d.get("@type") == "Person")
        self.assertEqual(person["name"], "Mogdho Paul"); self.assertEqual(person["sameAs"], SAME_AS)
        self.assertEqual(person["description"], IDENTITY); self.assertEqual(person["nationality"]["name"], "Bangladesh")
        self.assertEqual(person["url"], "https://mogdhopaul.com/"); self.assertNotIn("alternateName", person)
    def test_video_section(self): self.assertIn("https://video-showcase.mogdhopaul.com/", self.p.hrefs); self.assertIn("video editing", self.p.text.lower())
    def test_morse_name(self): self.assertIn("-- --- --. -.. .... --- / .--. .- ..- .-..", self.p.text)
    def test_photo_markers(self): self.assertIn("<!-- photos:strip:start -->", self.p.html); self.assertIn("<!-- photos:strip:end -->", self.p.html)
```

- [ ] **Step 2: Run** `python -m unittest tests.test_pages -v` — Expected: FAIL (old page lacks identity line, nav, markers; has "AI-Assisted").

- [ ] **Step 3: Write `index.html`**

Sections in order: header (name as wordmark + nav Home/About/Photos/Projects), `<h1>Mogdho Paul</h1>` with the identity line as the lead paragraph, short intro (2–3 sentences in his plain voice, from the spec facts), Morse divider (`<p class="morse" aria-label="Mogdho Paul in Morse code">-- --- --. -.. .... --- / .--. .- ..- .-..</p>`), latest photos strip with markers (initially contains `<p class="empty-note">Photos from the road are on their way.</p>`) and a link to `/photos/`, three featured projects (Copilot2Gemini, Hotspot-Auto-Connect, leaflet) linking to `/projects/`, a "Video editing" section (one short paragraph: Premiere Pro, After Effects, podcast shorts, YouTube; link to showcase), contact line with WhatsApp, footer with the seven profile links + email. Head: title `Mogdho Paul — Developer & SEO Specialist from Bangladesh`, meta description from the identity line, canonical, OG/Twitter (`og:image` stays `https://mogdhopaul.com/mogdhopaul.jpeg`), GA snippet, font links, JSON-LD `Person` (`jobTitle: "Developer & SEO Specialist"`, `image`, `nationality: {"@type":"Country","name":"Bangladesh"}`, `sameAs`). Profile photo: create `mogdhopaul.webp` (max 640px wide, Pillow) and use `<picture>` with the jpeg fallback.

- [ ] **Step 4: Run** `python -m unittest tests.test_pages -v` — Expected: PASS for `HomePage`.

- [ ] **Step 5: Commit** — `git add index.html mogdhopaul.webp tests/test_pages.py && git commit -m "feat: rebuild home page around identity line"`

---

### Task 3: About page

**Files:** Create `about/index.html`; Modify `tests/test_pages.py`

**Interfaces:** Consumes `CommonPageRules`, shared header/footer from Task 2.

- [ ] **Step 1: Add failing tests**

```python
class AboutPage(CommonPageRules, unittest.TestCase):
    page_key = "about"
    def test_story_facts(self):
        t = self.p.text
        for s in ("Brahmanbaria", "Dhaka", "Bangladesh", "Tagore", "Morse code", "SEO", "video editing"): self.assertIn(s.lower(), t.lower())
        self.assertGreaterEqual(len(t.split()), 500)
    def test_no_sensitive(self):
        for s in ("blood group", "religion", "marital", "mental health", "Hindu"): self.assertNotIn(s.lower(), self.p.text.lower())
    def test_jsonld(self):
        page = next(d for d in self.p.jsonld if d.get("@type") in ("AboutPage", "ProfilePage"))
        self.assertEqual(page["mainEntity"]["name"], "Mogdho Paul")
```

- [ ] **Step 2: Run** `python -m unittest tests.test_pages.AboutPage -v` — Expected: FAIL (file missing).

- [ ] **Step 3: Write `about/index.html`** — title `About Mogdho Paul — Developer from Bangladesh`. A first-person story (≥ 500 words, short paragraphs, `.prose`) rewritten in English from https://maggy2minutes.wordpress.com/about/ facts listed in the spec: grew up in Brahmanbaria and Dhaka; introvert who loves learning, "talk at least two minutes on any topic"; quiet places close to nature; Tagore songs; learning Morse code; tried calligraphy; documentaries; the farmhouse dream; how he works (SEO learned from Khalid Farhan, web tools and automations, video editing for creators). Plain voice, no marketing phrases. May mention university studies abroad but not as where he is based. Links to the blog and to `/projects/`. JSON-LD `ProfilePage` with `mainEntity` Person (name, url).

- [ ] **Step 4: Run** the AboutPage tests — Expected: PASS.

- [ ] **Step 5: Commit** — `git add about tests/test_pages.py && git commit -m "feat: add about page"`

---

### Task 4: Projects page

**Files:** Create `projects/index.html`; Modify `tests/test_pages.py`

- [ ] **Step 1: Add failing tests**

```python
class ProjectsPage(CommonPageRules, unittest.TestCase):
    page_key = "projects"
    def test_projects_listed(self):
        for name in ("Hotspot-Auto-Connect", "Copilot2Gemini", "Capslock-CopyPaste", "NN-tab", "leaflet", "video-showcase-paul"):
            self.assertIn(name, self.p.text); self.assertIn(f"https://github.com/mogdho/{name}", self.p.hrefs)
```

- [ ] **Step 2: Run** `python -m unittest tests.test_pages.ProjectsPage -v` — Expected: FAIL.

- [ ] **Step 3: Write `projects/index.html`** — title `Projects by Mogdho Paul — Small Web Tools & Automations`. `.project-list` of `<article class="project">` entries: name, one sentence on the problem it solves (from the GitHub descriptions in the spec), language, repo link. No tag pills; language as plain small text. Verify each repo URL returns 200 with `curl -sI` before committing.

- [ ] **Step 4: Run** tests — Expected: PASS.

- [ ] **Step 5: Commit** — `git add projects tests/test_pages.py && git commit -m "feat: add projects page"`

---

### Task 5: Instagram client and place extraction

**Files:** Create `scripts/instagram.py`, `scripts/__init__.py` (empty), `tests/test_instagram.py`, `tests/fixtures/media_page1.json`, `tests/fixtures/media_page2.json`

**Interfaces:**
- Produces:
  - `@dataclass Post: id: str; permalink: str; timestamp: str; image_url: str; place: str | None`
  - `extract_place(caption: str | None) -> str | None`
  - `select_posts(media: list[dict], exclude: set[str], limit: int = 60) -> list[Post]` (newest first, as returned by API; `exclude` matches id or permalink)
  - `fetch_media(token: str, urlopen=urllib.request.urlopen) -> list[dict]` — GET `https://graph.instagram.com/me/media?fields=id,caption,media_type,media_url,permalink,timestamp,children{media_type,media_url}&limit=50&access_token=…`, follows `paging.next` until absent or 100 items; raises `InstagramError` on HTTP error or JSON with `"error"`.
  - `refresh_token(token: str, urlopen=...) -> str` — GET `https://graph.instagram.com/refresh_access_token?grant_type=ig_refresh_token&access_token=…`, returns `access_token`.
  - `class InstagramError(Exception)`

Place rules (builder's call, pinned here):
1. If a line contains `📍`, use the text after it on that line.
2. Otherwise use the first non-empty line.
3. Clean: drop `#hashtags` and `@mentions`; keep only letters, digits, spaces, `,` `.` `-` `'`; collapse spaces; strip `,.- ` from ends.
4. Return `None` if empty, longer than 40 characters, more than 5 words, or containing non-Latin letters.

- [ ] **Step 1: Write failing tests**

```python
class ExtractPlace(unittest.TestCase):
    def test_pin(self): self.assertEqual(extract_place("lovely day\n📍 Paris, France #travel"), "Paris, France")
    def test_first_line(self): self.assertEqual(extract_place("Eiffel Tower, Paris 🇫🇷 #paris\nmore"), "Eiffel Tower, Paris")
    def test_hashtags_only(self): self.assertIsNone(extract_place("#travel #snow"))
    def test_none(self): self.assertIsNone(extract_place(None))
    def test_emoji_only(self): self.assertIsNone(extract_place("❄️❄️"))
    def test_bengali(self): self.assertIsNone(extract_place("প্যারিস"))
    def test_sentence(self): self.assertIsNone(extract_place("What a wonderful day walking around the old town with friends"))
    def test_html_chars_kept_out(self): self.assertEqual(extract_place("Rock & <Roll> Café"), "Rock Roll Café")
class SelectPosts(unittest.TestCase):
    # fixtures: IMAGE, VIDEO, CAROUSEL_ALBUM(first child VIDEO, second IMAGE), CAROUSEL_ALBUM(all VIDEO), excluded IMAGE
    def test_skips_video(self): ...           # VIDEO id not in result
    def test_carousel_first_image(self): ...  # image_url == second child's media_url
    def test_carousel_no_image_skipped(self): ...
    def test_exclude_by_id_and_permalink(self): ...
    def test_limit(self): ...                 # limit=1 -> 1 post
class Fetch(unittest.TestCase):
    def test_follows_paging(self): ...        # fake urlopen returns page1 (with paging.next) then page2; total = sum
    def test_api_error_raises(self): ...      # {"error": {...}} -> InstagramError
    def test_refresh_returns_token(self): ... # {"access_token": "NEW"} -> "NEW"
```

Fixtures are hand-written JSON in the API's shape (`{"data": [...], "paging": {"next": "..."}}`).

- [ ] **Step 2: Run** `python -m unittest tests.test_instagram -v` — Expected: FAIL (module missing).

- [ ] **Step 3: Implement `scripts/instagram.py`** to the interfaces above (stdlib only: `urllib`, `json`, `re`, `unicodedata`; "non-Latin letter" = any `ch.isalpha()` whose `unicodedata.name` does not start with `LATIN`).

- [ ] **Step 4: Run** tests — Expected: PASS.

- [ ] **Step 5: Commit** — `git add scripts tests && git commit -m "feat: instagram client and place extraction"`

---

### Task 6: Photo builder (images, JSON, HTML regions) and Photos page

**Files:** Create `scripts/build_photos.py`, `scripts/requirements.txt` (`Pillow>=10`), `photos/index.html`, `data/photos-exclude.txt`, `data/photos.json` (`[]`), `tests/test_build_photos.py`; Modify `tests/test_pages.py`

**Interfaces:**
- Consumes: `fetch_media`, `select_posts`, `Post`, `InstagramError` from Task 5.
- Produces:
  - `photos.json` entries: `{"id", "permalink", "date": "YYYY-MM-DD", "place": str|null, "src": "/photos/img/<id>-1200.webp", "thumb": "/photos/img/<id>-600.webp", "width": int, "height": int}` (width/height of the 1200 image)
  - `alt_text(photo: dict) -> str` → `"Travel photo by Mogdho Paul in {place}, {Month YYYY}"`, or `"Travel photo by Mogdho Paul, {Month YYYY}"` when no place
  - `render_items(photos: list[dict], limit: int | None) -> str` — `<figure class="photo fade">` with `<a href=permalink>`, `<img src=thumb srcset="thumb 600w, src 1200w" alt width height loading="lazy">`, `<figcaption class="photo__label">{place · }{D Month YYYY}</figcaption>`; all text HTML-escaped; empty list → `<p class="empty-note">Photos from the road are on their way.</p>`
  - `replace_region(html: str, name: str, content: str) -> str` — replaces between `<!-- photos:{name}:start -->` and `<!-- photos:{name}:end -->`; raises `ValueError` if markers missing
  - `save_images(post: Post, out_dir: Path, download) -> tuple[int, int]` — downloads, writes 1200w and 600w WebP (quality 80, EXIF dropped), returns 1200 size
  - `main(argv: list[str] | None = None) -> int` — reads `IG_TOKEN` env; `--fixture PATH` uses a local JSON instead of the API (for tests/local preview); fetch → select (exclude from `data/photos-exclude.txt`, `#` comments) → save new images → delete images in `photos/img/` not in the kept set → write `data/photos.json` → rewrite `strip` region in `index.html` (6 newest) and `grid` region in `photos/index.html` (all). Returns 0 on success, 1 on `InstagramError` **before writing anything**.

- [ ] **Step 1: Write failing tests** in `tests/test_build_photos.py`

```python
class Render(unittest.TestCase):
    def test_alt_with_place(self): self.assertEqual(alt_text({"place": "Paris, France", "date": "2025-05-14"}), "Travel photo by Mogdho Paul in Paris, France, May 2025")
    def test_alt_without_place(self): self.assertEqual(alt_text({"place": None, "date": "2025-05-14"}), "Travel photo by Mogdho Paul, May 2025")
    def test_escapes(self): self.assertIn("A &amp; B", render_items([photo(place="A & B")], None))
    def test_empty_state(self): self.assertIn("empty-note", render_items([], None))
    def test_limit(self): self.assertEqual(render_items([photo()]*8, 6).count("<figure"), 6)
    def test_label_date_only(self): self.assertIn(">14 May 2025<", render_items([photo(place=None)], None))
class Regions(unittest.TestCase):
    def test_replace(self): ...         # content between markers replaced, markers kept, rest identical
    def test_missing_markers(self): ... # ValueError
class MainSafety(unittest.TestCase):
    # runs main() against a temp copy of the repo layout (patch module-level ROOT)
    def test_api_failure_changes_nothing(self): ...  # fetch raises InstagramError -> returns 1, index.html/photos.json/img bytes unchanged
    def test_fixture_run_writes_everything(self): ... # --fixture with 2 image posts (download patched to return a small Pillow image) -> 2 entries, 4 webp files, both regions filled
    def test_removed_post_image_deleted(self): ...
```

Add to `tests/test_pages.py`:

```python
class PhotosPage(CommonPageRules, unittest.TestCase):
    page_key = "photos"
    def test_markers(self): self.assertIn("<!-- photos:grid:start -->", self.p.html); self.assertIn("<!-- photos:grid:end -->", self.p.html)
    def test_intro_mentions_name(self): self.assertIn("Mogdho Paul", self.p.text)
```

- [ ] **Step 2: Run** `python -m unittest tests.test_build_photos tests.test_pages.PhotosPage -v` — Expected: FAIL.

- [ ] **Step 3: Install Pillow locally** — `python -m pip install -r scripts/requirements.txt`

- [ ] **Step 4: Implement `scripts/build_photos.py`** to the interfaces above; write `photos/index.html` (title `Travel Photos by Mogdho Paul`, short intro paragraph, Instagram profile link, `<div class="photo-grid">` with grid markers containing the empty note); `data/photos-exclude.txt` with a one-line comment explaining the format.

- [ ] **Step 5: Run** all tests `python -m unittest discover -s tests -v` — Expected: PASS.

- [ ] **Step 6: Commit** — `git add scripts photos data tests && git commit -m "feat: photo builder and photos page"`

---

### Task 7: GitHub workflows and owner setup guide

**Files:** Create `.github/workflows/photos.yml`, `.github/workflows/refresh-token.yml`, `docs/instagram-setup.md`

**Interfaces:** Consumes `python -m scripts.build_photos` (Task 6) and `refresh_token` (Task 5). Secrets: `IG_TOKEN` (long-lived Instagram token), `GH_PAT` (fine-grained token, this repo only, "Secrets: Read and write").

- [ ] **Step 1: `photos.yml`** — triggers: `schedule: cron "30 21 * * *"` (03:30 Bangladesh time) and `workflow_dispatch`. `permissions: contents: write`. Steps: checkout, setup-python 3.12, `pip install -r scripts/requirements.txt`, `python -m unittest discover -s tests` (stop if tests fail), `python -m scripts.build_photos` with `IG_TOKEN: ${{ secrets.IG_TOKEN }}`, then commit and push only if `git status --porcelain` is non-empty, message `chore: update instagram photos`, author `github-actions[bot]`.

- [ ] **Step 2: `refresh-token.yml`** — `schedule: cron "0 3 1 * *"` (monthly; tokens last 60 days) and `workflow_dispatch`. Runs `python -c` calling `scripts.instagram.refresh_token`, masks the result with `echo "::add-mask::$NEW"`, then `gh secret set IG_TOKEN --body "$NEW"` with `GH_TOKEN: ${{ secrets.GH_PAT }}`. Fails loudly if refresh fails (GitHub emails the owner).

- [ ] **Step 3: Write `docs/instagram-setup.md`** — plain numbered steps for the owner: switch @mogdhopaul to a Creator account; create a Meta developer app (type Business) and add "Instagram API with Instagram Login" (no Facebook page needed for this variant); add his account as a tester and generate a token in the app dashboard; add it as repo secret `IG_TOKEN`; create the fine-grained `GH_PAT` and add it as a secret; run "Update photos" once from the Actions tab; how to hide a post (add its link to `data/photos-exclude.txt`).

- [ ] **Step 4: Verify** — run `python -m unittest discover -s tests -v` (Expected: PASS; the end-to-end builder run is covered by `MainSafety.test_fixture_run_writes_everything`). Check both workflow files reference exactly `IG_TOKEN`, `GH_PAT` and `python -m scripts.build_photos`. YAML syntax is confirmed when the branch is pushed in Task 8 (the Actions tab shows no workflow errors).

- [ ] **Step 5: Commit** — `git add .github docs/instagram-setup.md && git commit -m "feat: nightly instagram workflow and setup guide"`

---

### Task 8: Sitemap, review and launch

**Files:** Modify `sitemap.xml`, `tests/test_pages.py`; remove nothing else (`CNAME`, `robots.txt`, `favicon.png`, `mogdhopaul.jpeg` stay).

- [ ] **Step 1: Add failing test**

```python
class Sitemap(unittest.TestCase):
    def test_all_pages(self):
        xml = (ROOT/"sitemap.xml").read_text()
        for u in URLS.values(): self.assertIn(f"<loc>https://mogdhopaul.com{u}</loc>", xml)
```

- [ ] **Step 2: Run** — Expected: FAIL. **Step 3:** update `sitemap.xml` (four URLs, `lastmod` = launch date). **Step 4:** Run all tests — Expected: PASS.

- [ ] **Step 5: Visual review** — serve with `python -m http.server 8000`, open each page at 375px and 1280px wide, light and dark mode, and with JavaScript disabled. Check: no horizontal scroll, text readable, focus rings visible, photos look like album prints. Then invoke the `impeccable` skill's critique/finish review against `DESIGN.md` and the anti-AI list; apply material fixes; re-run tests.

- [ ] **Step 6: Commit** — `git add -A && git commit -m "feat: sitemap and design polish"` (confirm `.claude/` is not staged).

- [ ] **Step 7: Instagram setup before launch** (spec: site goes live with the feed working) — owner completes `docs/instagram-setup.md` and adds both secrets. Then fill the photos on the branch by running the builder locally with his token (owner sets it himself in his terminal, never pasted into chat or committed): `$env:IG_TOKEN = '<token>'; python -m scripts.build_photos`. Expected: exit 0, `data/photos.json` non-empty, both photo regions filled. Commit `chore: first instagram photos`.

- [ ] **Step 8: Owner sign-off, then launch** — show the owner the pages locally. With approval: push `redesign`, open a PR, merge to `main`; GitHub Pages publishes and the nightly workflow takes over. Owner then submits `https://mogdhopaul.com/sitemap.xml` in Google Search Console and updates profile bios (GitHub location → Bangladesh; LinkedIn, Instagram, Facebook bios use the identity line).
