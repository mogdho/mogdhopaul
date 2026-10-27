# Admin Panel Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** A private `/admin/` page that lets Mogdho manage photos, projects, and text & links from any device, publishing through GitHub.

**Architecture:** Site content moves into `content/*.json`; a stdlib-only Python generator renders the four pages from `templates/`. The admin is a static page that reads and writes those files (and browser-resized images) through the GitHub API as one commit; a push-triggered GitHub Action rebuilds, tests, and commits the pages.

**Tech Stack:** HTML/CSS/vanilla JS (ES modules, no build step); Python 3.12 stdlib (`json`, `string.Template`, `html`); Node 24 `node:test` for JS logic; GitHub REST API (Git Data + Actions); GitHub Actions.

**Spec:** `docs/superpowers/specs/2026-10-27-admin-panel-design.md` (builds on `docs/superpowers/specs/2026-10-27-site-redesign-design.md`)

## Global Constraints

- All redesign rules still hold: only spelling "Mogdho Paul"; no "Mugdho"/"Mogdha" (any case) and no Bengali script in any page; no "Bucharest" in titles/meta/JSON-LD; GA `G-LDY4Z5D7MW` on every page; one `<h1>` per page; key text in HTML.
- Generator is stdlib-only (no Pillow, no new Python deps). Admin has no build step and no third-party JS.
- Text link syntax exactly `[link text](address)`; allowed addresses: `https://…`, `http://…`, `mailto:…`, or a site path starting with `/`. Everything else, and all HTML, is escaped as plain text.
- Exactly three projects have `"featured": true`.
- Images resized in the browser to widths 1200 and 600; WebP when `canvas.toBlob` yields `image/webp`, else JPEG (quality 0.8). Originals never committed.
- Admin: `<meta name="robots" content="noindex, nofollow">`, `Disallow: /admin/` in robots.txt, not in sitemap.
- Token: GitHub fine-grained PAT, this repo only, Contents read/write + Actions read; stored in `localStorage` key `mp-admin-token`; "Log out" removes it.
- Repo: owner `mogdho`, repo `mogdhopaul`, branch `main`. Workflow name: `Build site`.
- Every save is one commit; if `main` moved since load → no overwrite, show "The site changed since you opened the admin. Reloading." and reload content.

## Review Focus

1. **Site changed elsewhere between load and save** → nothing overwritten, conflict message shown. Test in Task 4 (`commitFiles` raises `ConflictError` on 422).
2. **Typed HTML or a `javascript:` link in any text field** → shown as literal text, link not created; admin flags it before saving. Tests in Task 1 (`render_text`) and Task 3 (`checkText`).
3. **Odd photos: very large, sideways (EXIF-rotated), or a format the browser can't read (HEIC)** → resized within 1200px using the oriented size; unreadable file gives a clear per-file error and nothing is added. Tests in Task 3 (`targetSize`, `isSupportedImage`).
4. **Wrong or expired key** → "That key didn't work…" on login or save; nothing saved. Test in Task 4 (`AuthError` on 401/403).
5. **Deleting a photo / all photos** → its image files are removed in the same commit; zero photos shows the empty note. Tests in Task 2 (`unused_images`, empty render) and Task 3 (`photoChanges`).

---

## File Structure

```
content/site.json            # text & links (identity, home, about, video, contact, profiles)
content/projects.json        # projects list
content/photos.json          # photos list (paths + sizes)
templates/base.html          # shared shell: head (meta, GA, fonts), cover header, footer
templates/home.html  about.html  projects.html  photos.html   # page bodies
scripts/content.py           # load + validate content, render_text/inline links
scripts/render_photos.py     # print markup (moved from build_photos.py)
scripts/build_site.py        # render pages, prune unused images, CLI
admin/index.html  admin/admin.css
admin/core.js                # pure logic: validation, ids, sizes, change sets
admin/github.js              # GitHub API client
admin/images.js              # browser resize (canvas)
admin/app.js                 # UI wiring
tests/test_content.py  tests/test_build_site.py  (tests/test_pages.py, test_style.py updated)
tests/js/core.test.mjs  tests/js/github.test.mjs
.github/workflows/build.yml
docs/admin-guide.md
REMOVE: scripts/build_photos.py, tests/test_build_photos.py, scripts/requirements.txt,
        data/ (photos.csv, photos.json), docs/adding-photos.md
```

Python tests: `python -m unittest discover -s tests -t .` · JS tests: `node --test tests/js/`

---

### Task 1: Content files and content module

**Files:** Create `content/site.json`, `content/projects.json`, `content/photos.json`, `scripts/content.py`, `tests/test_content.py`

**Interfaces — Produces (`scripts/content.py`):**
- `class ContentError(ValueError)` — message names the field, e.g. `"projects[2].url: …"`.
- `load_content(root: Path) -> dict` → `{"site": …, "projects": […], "photos": […]}` (raises `ContentError` on bad JSON or rule break).
- `validate(content: dict) -> None`
- `inline(text: str) -> str` — escape, then turn allowed `[t](u)` into `<a href="u">t</a>`.
- `render_text(text: str) -> str` — blank-line-separated paragraphs → `<p>…</p>` joined by `\n`, each via `inline`.
- `is_allowed_url(url: str) -> bool`

**Schemas (exact keys):**
- site: `identity`, `home.lead`, `home.text`, `home.video`, `about.lead`, `about.sections[] {heading, text}`, `contact.whatsapp` (URL), `contact.email` (address), `profiles[] {label, url}`.
- project: `name`, `url`, `description`, `home_blurb` (may be ""), `language`, `group` (`"windows"`|`"browser"`), `featured` (bool).
- photo: `id`, `place` (str|null), `date` (`YYYY-MM-DD`), `src`, `thumb`, `width`, `height`.

- [ ] **Step 1: Write content files** by moving today's exact text from `index.html`, `about/index.html`, `projects/index.html` (keep every sentence; links become `[text](url)`, e.g. `my [photos page](/photos/)`, `my [video showcase](https://video-showcase.mogdhopaul.com/)`, blog `[maggy2minutes](https://maggy2minutes.wordpress.com/)`). Projects keep both texts: home blurb = the home-page sentence, description = projects-page sentence. Featured: Copilot2Gemini, Hotspot-Auto-Connect, leaflet. `photos.json` = `[]`.

- [ ] **Step 2: Write failing tests** `tests/test_content.py`

```python
class Inline(unittest.TestCase):
    def test_link(self): self.assertEqual(inline("my [photos page](/photos/)."), 'my <a href="/photos/">photos page</a>.')
    def test_html_escaped(self): self.assertEqual(inline("<b>hi</b> & co"), "&lt;b&gt;hi&lt;/b&gt; &amp; co")
    def test_bad_scheme_left_as_text(self): self.assertEqual(inline("[x](javascript:alert(1))"), "[x](javascript:alert(1))")
    def test_quote_in_url_escaped(self): self.assertNotIn('"onmouseover', inline('[x](https://a.b/"onmouseover=1)'))
    def test_mailto(self): self.assertIn('href="mailto:a@b.c"', inline("[mail](mailto:a@b.c)"))
class RenderText(unittest.TestCase):
    def test_paragraphs(self): self.assertEqual(render_text("One.\n\nTwo\nlines."), "<p>One.</p>\n<p>Two\nlines.</p>")
    def test_empty(self): self.assertEqual(render_text("  "), "")
class Validate(unittest.TestCase):   # uses a deep copy of load_content(ROOT)
    def test_repo_content_valid(self): validate(load_content(ROOT))
    def test_banned_spelling(self): ... site["home"]["text"] = "Mogdha says hi" -> ContentError naming "site.home.text"
    def test_bengali(self): ... about.sections[0].text with "\u09aa" -> ContentError
    def test_featured_must_be_three(self): ... two featured -> ContentError "featured"
    def test_bad_profile_url(self): ... profiles[0].url = "ftp://x" -> ContentError "site.profiles[0].url"
    def test_bad_photo_date(self): ... photos=[{...,"date":"14/05/2025"}] -> ContentError "photos[0].date"
    def test_photo_paths_inside_img(self): ... src "/../x.webp" or not starting "/photos/img/" -> ContentError
    def test_missing_field(self): ... del projects[0]["url"] -> ContentError "projects[0].url"
    def test_project_name_not_banned(self): ... name "Mugdho tool" -> ContentError
```

- [ ] **Step 3: Run** `python -m unittest tests.test_content -v` — Expected: FAIL (module missing).
- [ ] **Step 4: Implement `scripts/content.py`.** Text fields checked for banned names (case-insensitive), non-Latin letters/digits (same rule as `_check_place` in today's `build_photos.py`), and non-empty where required. Link regex: `\[([^\]\n]+)\]\(([^)\s]+)\)` applied to the already-escaped text; `href` re-escaped with `html.escape(url, quote=True)` on the original URL.
- [ ] **Step 5: Run** tests — Expected: PASS.
- [ ] **Step 6: Commit** `git add content scripts/content.py tests/test_content.py && git commit -m "feat: site content as data with validation"`

---

### Task 2: Templates and site generator

**Files:** Create `templates/*.html`, `scripts/render_photos.py`, `scripts/build_site.py`, `tests/test_build_site.py`. Modify `tests/test_pages.py` (IDENTITY/SAME_AS from `content/site.json`). Regenerate `index.html`, `about/index.html`, `projects/index.html`, `photos/index.html`. Delete `scripts/build_photos.py`, `tests/test_build_photos.py`, `scripts/requirements.txt`, `data/`, `docs/adding-photos.md`.

**Interfaces:**
- Consumes: `load_content`, `render_text`, `inline`, `ContentError` (Task 1).
- Produces:
  - `scripts/render_photos.py`: `alt_text(photo) -> str`, `render_items(photos, limit, eager=0) -> str` (moved unchanged from `build_photos.py` incl. its tests).
  - `scripts/build_site.py`: `PAGES = {"index.html": "home", "about/index.html": "about", "projects/index.html": "projects", "photos/index.html": "photos"}`; `build(root: Path) -> dict[str, str]` (relative path → HTML); `unused_images(root: Path, photos: list) -> list[Path]`; `main(argv=None) -> int` (writes pages, deletes unused images, prints summary; returns 1 and writes nothing on `ContentError`).

- [ ] **Step 1: Write failing tests** `tests/test_build_site.py` (moved render tests from `test_build_photos.py` → `RenderPhotos` class importing `scripts.render_photos`), plus:

```python
class Build(unittest.TestCase):
    def test_committed_pages_are_fresh(self):
        for rel, html in build(ROOT).items():
            self.assertEqual((ROOT / rel).read_text(encoding="utf-8"), html, rel)
    def test_featured_on_home(self): home = build(ROOT)["index.html"]; for name in ("Copilot2Gemini", "Hotspot-Auto-Connect", "leaflet"): self.assertIn(name, home)
    def test_home_blurb_used_on_home_description_on_projects(self): ...  # Copilot2Gemini texts from projects.json appear on the right page
    def test_profiles_drive_footer_and_jsonld(self): ...  # every profiles[].url in each page's hrefs and in Person.sameAs
    def test_text_link_rendered(self): self.assertIn('<a href="/photos/">photos page</a>', build(ROOT)["about/index.html"])
class Main(unittest.TestCase):  # temp copy of root (content/, templates/, photos/img/) with build_site.ROOT patched
    def test_invalid_content_writes_nothing(self): ...  # banned spelling -> main returns 1, files unchanged
    def test_unused_images_deleted(self): ...  # photos/img/old-600.webp not in photos.json -> removed; listed ones kept
    def test_zero_photos_shows_empty_note(self): ...
```

- [ ] **Step 2: Run** `python -m unittest tests.test_build_site -v` — Expected: FAIL (module missing).
- [ ] **Step 3: Write templates.** `base.html` holds the shared head/cover header/footer with `string.Template` placeholders `$title`, `$description`, `$canonical`, `$og_type`, `$jsonld`, `$nav`, `$cover`, `$main`, `$footer_profiles`, `$whatsapp`, `$email`. Page templates hold their fixed markup (MRZ line, Morse line, section headings, `<!-- photos:… -->` markers no longer needed). Output must keep every rule `tests/test_pages.py` checks.
- [ ] **Step 4: Implement `scripts/render_photos.py`** (move) **and `scripts/build_site.py`.**
- [ ] **Step 5: Regenerate pages** `python -m scripts.build_site`; delete retired files; update `test_pages.py` to read IDENTITY and SAME_AS from `content/site.json`.
- [ ] **Step 6: Run** both suites — Expected: PASS (`test_pages` unchanged in substance, freshness test passes).
- [ ] **Step 7: Commit** `git add -A && git commit -m "feat: generate pages from content files"` (check `.claude/` not staged).

---

### Task 3: Admin core logic (pure JS)

**Files:** Create `admin/core.js`, `tests/js/core.test.mjs`

**Interfaces — Produces (ES module exports):**
- `BANNED_NAMES = ["mugdho", "mogdha"]`
- `checkText(text: string) -> string|null` — error message or null (banned name, non-Latin letter/digit via `/\p{L}|\p{N}/u` + Latin test `/\p{Script=Latin}/u`, link with disallowed address).
- `isAllowedUrl(url: string) -> boolean` (same rule as Python).
- `validateContent({site, projects, photos}) -> Array<{field: string, message: string}>` (mirrors Python field names).
- `targetSize(width: number, height: number, max: number) -> {width, height}` (never upscale; rounds).
- `isSupportedImage(file: {type: string}) -> boolean` — `image/jpeg|png|webp|gif`.
- `newPhotoId(date: string, taken: Set<string>, rand = Math.random) -> string` — `"<date>-<4 hex>"`, unique.
- `photoChanges(before: Photo[], after: Photo[]) -> {deletePaths: string[]}` — `src` and `thumb` of removed photos.
- `toJson(value) -> string` — `JSON.stringify(value, null, 2) + "\n"`.

- [ ] **Step 1: Write failing tests** `tests/js/core.test.mjs` with `node:test` + `node:assert/strict`:

```js
test('checkText rejects banned spelling', () => assert.match(checkText('Mogdha here'), /name/i));
test('checkText rejects Bengali', () => assert.match(checkText('প্যারিস'), /English/));
test('checkText rejects javascript link', () => assert.match(checkText('[x](javascript:alert(1))'), /link/i));
test('checkText accepts plain and site links', () => assert.equal(checkText('my [photos](/photos/) and [mail](mailto:a@b.c)'), null));
test('validateContent needs exactly three featured', () => assert.ok(validateContent(withFeatured(2)).some(e => e.field === 'projects' )));
test('validateContent names the field', () => assert.deepEqual(validateContent(withProfileUrl('ftp://x')).map(e => e.field), ['site.profiles[0].url']));
test('targetSize scales down', () => assert.deepEqual(targetSize(6000, 4000, 1200), {width: 1200, height: 800}));
test('targetSize never upscales', () => assert.deepEqual(targetSize(800, 600, 1200), {width: 800, height: 600}));
test('isSupportedImage refuses HEIC', () => assert.equal(isSupportedImage({type: 'image/heic'}), false));
test('newPhotoId is unique', () => { const taken = new Set(['2025-05-14-0000']); const id = newPhotoId('2025-05-14', taken, seq(0, 0.5)); assert.equal(id, '2025-05-14-8000'); });
test('photoChanges lists files of removed photos', () => assert.deepEqual(photoChanges([p('a'), p('b')], [p('b')]).deletePaths, ['/photos/img/a-1200.webp', '/photos/img/a-600.webp']));
```

(`withFeatured`, `withProfileUrl`, `p`, `seq` are small helpers in the test file built from `content/*.json` read with `fs`.)

- [ ] **Step 2: Run** `node --test tests/js/` — Expected: FAIL (module missing).
- [ ] **Step 3: Implement `admin/core.js`.**
- [ ] **Step 4: Run** — Expected: PASS.
- [ ] **Step 5: Commit** `git add admin/core.js tests/js && git commit -m "feat: admin core logic"`

---

### Task 4: GitHub API client

**Files:** Create `admin/github.js`, `tests/js/github.test.mjs`

**Interfaces — Produces:**
- `class AuthError extends Error`, `class ConflictError extends Error`, `class GitHubError extends Error`
- `class Repo { constructor({token, owner = 'mogdho', repo = 'mogdhopaul', branch = 'main', fetch = globalThis.fetch}) }`
  - `async headSha() -> string` — `GET /repos/{o}/{r}/git/ref/heads/{branch}`.
  - `async readJson(path, ref) -> any` — `GET /repos/{o}/{r}/contents/{path}?ref=` with `Accept: application/vnd.github.raw+json`.
  - `async commitFiles(baseSha, files, message) -> string` — files: `[{path, base64}]` or `[{path, delete: true}]`; blobs (`POST git/blobs`, encoding base64) → `GET git/commits/{baseSha}` tree → `POST git/trees` (`base_tree`, deletions as `sha: null`) → `POST git/commits` (parents `[baseSha]`) → `PATCH git/refs/heads/{branch}` `{sha, force: false}`; returns new commit sha.
  - `async buildStatus(sha) -> 'pending'|'success'|'failure'|'none'` — `GET actions/runs?head_sha={sha}`, filter `name === 'Build site'`.
- Errors: 401/403 → `AuthError("That key didn't work. Check it hasn't expired and has access to mogdhopaul.")`; 422 on PATCH ref → `ConflictError`; other non-2xx → `GitHubError(status + message)`. All requests send `Authorization: Bearer <token>`, `X-GitHub-Api-Version: 2022-11-28`.

- [ ] **Step 1: Write failing tests** with a fake `fetch` recording `(method, url, body)` and returning queued responses:

```js
test('commitFiles makes one commit in order', async () => { /* expect methods/urls: POST blobs, GET commits/base, POST trees, POST commits, PATCH refs; tree has deleted path with sha null; returns new sha */ });
test('stale ref raises ConflictError', async () => { /* PATCH returns 422 */ await assert.rejects(repo.commitFiles('base', files, 'm'), ConflictError); });
test('401 raises AuthError', async () => { await assert.rejects(repo.headSha(), AuthError); });
test('readJson asks for raw content at ref', async () => { /* url contains contents/content/site.json?ref=abc and Accept raw */ });
test('buildStatus maps run state', async () => { /* in_progress -> pending; completed+success -> success; completed+failure -> failure; no runs -> none */ });
test('token sent as Bearer', async () => { /* header check */ });
```

- [ ] **Step 2: Run** `node --test tests/js/` — Expected: FAIL.
- [ ] **Step 3: Implement `admin/github.js`.**
- [ ] **Step 4: Run** — Expected: PASS.
- [ ] **Step 5: Commit** `git add admin/github.js tests/js/github.test.mjs && git commit -m "feat: github client for the admin"`

---

### Task 5: Admin page UI

**Files:** Create `admin/index.html`, `admin/admin.css`, `admin/images.js`, `admin/app.js`

**Interfaces:**
- Consumes: Task 3 exports, Task 4 `Repo`/errors.
- Produces: `admin/images.js` `async resizeImage(file: File, maxWidth: number) -> {blob, width, height, ext: 'webp'|'jpg'}` (`createImageBitmap(file, {imageOrientation: 'from-image'})` → canvas at `targetSize` → `toBlob('image/webp', 0.8)`, falling back to `image/jpeg` when the blob type isn't webp).

Behaviour (owner-facing copy is plain and short):
- **Login view:** one password field "GitHub key", button "Log in", link to `/admin` guide section in `docs/admin-guide.md` on GitHub. On success store token, load `content/*.json` at `headSha()`.
- **Tabs:** Photos · Projects · Text & links (buttons with `aria-selected`, keyboard reachable). Header shows "Logged in · Log out".
- **Photos:** prints grid (same `.photo` look), each with Place input, Date input (`type=date`), Delete button. "Add photos" (`<input type=file accept="image/jpeg,image/png,image/webp,image/gif" multiple>`): each file resized to 1200 and 600, given `newPhotoId(today)`; default date today; unsupported file → message naming it, not added. New photos listed newest first.
- **Projects:** list of editable rows (name, link, description, home blurb, language, group select, "Show on home page" checkbox; at most three can be checked at once — extra checkbox disabled with hint). Add / Delete buttons.
- **Text & links:** identity line, home intro (lead + text), video text, About lead + sections (heading + text; add/remove/reorder up-down), WhatsApp link, email, profiles (label + URL; add/remove). Help line under text areas: "Blank line = new paragraph. Link: [text](https://…)".
- **Save bar** (sticky bottom): "Save and publish" disabled until something changed; runs `validateContent` + per-field `checkText` and shows errors next to fields; then `commitFiles(loadedSha, [...json files, ...new images, ...deletes], "admin: update site")`. Then status line: "Publishing…" polling `buildStatus` every 5 s up to 5 min → "Live — changes are on mogdhopaul.com" / "Publishing failed. The site still shows the previous version. (link to the Actions run)". `ConflictError` → reload message from Global Constraints. `AuthError` → back to login with its message.
- **Unsaved changes:** `beforeunload` warning when dirty.
- **Demo mode** for local review: `?demo` loads `/content/*.json` via `fetch` from the same origin, uses a fake Repo whose `commitFiles` resolves after 1 s and `buildStatus` returns `success`; banner "Demo — nothing is saved".
- Styling: link `/style.css` then `admin.css`; reuse tokens; Operate surface — clear labels, 44px targets, visible focus, works at 390px wide. `index.html` has the robots meta and no GA.

- [ ] **Step 1: Build the page** (files above).
- [ ] **Step 2: Verify in demo mode** — `python -m http.server 8765` in the repo, open `http://127.0.0.1:8765/admin/?demo` (headless screenshots at 1280×900 and 390×844 of each tab with the Playwright headless shell at `C:\Users\Lenovo\AppData\Local\ms-playwright\chromium_headless_shell-1200\chrome-headless-shell-win64\chrome-headless-shell.exe`). Expected: three tabs render content from `content/*.json`; layout holds at 390px.
- [ ] **Step 3: Run** `node --test tests/js/` and the Python suite — Expected: PASS.
- [ ] **Step 4: Commit** `git add admin && git commit -m "feat: admin page"`

---

### Task 6: Publishing workflow, robots, guide, cleanup

**Files:** Create `.github/workflows/build.yml`, `docs/admin-guide.md`. Modify `robots.txt`, `_config.yml`, `.gitignore`, `tests/test_pages.py`.

- [ ] **Step 1: Write failing tests** in `tests/test_pages.py`:

```python
class AdminPrivacy(unittest.TestCase):
    def test_robots_disallows_admin(self): self.assertIn("Disallow: /admin/", (ROOT/"robots.txt").read_text())
    def test_admin_noindex(self): self.assertIn('content="noindex, nofollow"', (ROOT/"admin/index.html").read_text(encoding="utf-8"))
    def test_admin_not_in_sitemap(self): self.assertNotIn("/admin", (ROOT/"sitemap.xml").read_text())
    def test_tooling_not_published(self):
        cfg = (ROOT/"_config.yml").read_text()
        for name in ("content", "templates", "scripts", "tests", "docs", "PRODUCT.md", "DESIGN.md"): self.assertIn(f"- {name}", cfg)
```

- [ ] **Step 2: Run** — Expected: FAIL. **Step 3:** update robots/_config (remove `data`, `photo-originals` entries; add `content`, `templates`); `.gitignore` drop `photo-originals/`.
- [ ] **Step 4: Write `build.yml`:** name `Build site`; on `push` to `main` with paths `content/**`, `photos/img/**`, `templates/**`, `scripts/**`, `admin/**`, plus `workflow_dispatch`; permissions `contents: write`, `pages: write`; steps: checkout → setup-python 3.12 → setup-node 24 → `python -m scripts.build_site` → `python -m unittest discover -s tests -t .` → `node --test tests/js/` → if `git status --porcelain` non-empty: commit `chore: rebuild pages` as github-actions[bot], `git pull --rebase`, `git push` → `gh api -X POST repos/${{ github.repository }}/pages/builds || true`. The bot's own push changes only generated pages, which are not in the trigger paths, so it does not loop.
- [ ] **Step 5: Write `docs/admin-guide.md`:** create the key (Settings → Developer settings → Fine-grained tokens; only `mogdho/mogdhopaul`; Contents read & write, Actions read; longest expiry), log in at `/admin/`, adding photos, projects, text & link syntax, what "Publishing failed" means, logging out, revoking the key if a device is lost.
- [ ] **Step 6: Run** all tests + YAML parse (`python -c "import yaml; yaml.safe_load(open('.github/workflows/build.yml'))"`) — Expected: PASS.
- [ ] **Step 7: Commit** `git add -A && git commit -m "feat: publishing workflow and admin guide"`

---

### Task 7: Final checks

- [ ] **Step 1:** Full suites green: `python -m unittest discover -s tests -t .` and `node --test tests/js/`.
- [ ] **Step 2:** Rebuild preview and screenshot the four public pages at 1280 and 390 — Expected: identical to before the content move except intended changes.
- [ ] **Step 3:** Commit any fixes; record rulings; final whole-branch review per executing-plans.
