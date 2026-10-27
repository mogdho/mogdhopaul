# mogdhopaul.com admin panel — design

Date: 2026-10-27
Status: draft, awaiting owner approval
Builds on: docs/superpowers/specs/2026-10-27-site-redesign-design.md (branch `redesign`)

## Intent and why

Mogdho wants to manage his site from anywhere (phone or PC) without touching code: travel photos
(with place and date), the projects list, and his text and links. He chose a custom page on his own
domain over a third-party CMS.

## Goals

1. A private editor at `https://mogdhopaul.com/admin/`, usable on a phone.
2. Manage **photos**: upload one or many, edit place and date, delete.
3. Manage **projects**: add, edit, delete, choose which three appear on the home page.
4. Manage **text and links**: identity line, home intro, About story, video-editing text,
   WhatsApp and email, profile links.
5. Saving publishes: the live site updates within about two minutes.
6. Google sees exactly what it sees today: plain HTML pages, same SEO.

## Non-goals

- No user accounts beyond Mogdho; no roles, no comments, no drafts or scheduling.
- No editing of page design, colours or layout from the admin.
- No Bengali version; no Instagram import.

## Anti-goals (a failure even if it works)

- Original photos (with GPS location in their EXIF data) ever reaching the public repo.
- A bad save breaking the live site (empty pages, broken HTML, banned name spellings).
- Admin page showing up in Google.
- A generic, template-looking admin that doesn't match the site.

## Constraints

- Hosting stays GitHub Pages (static files only, no server). The repo is public.
- All site rules from the redesign spec still hold (one spelling "Mogdho Paul", English only,
  no Bengali script, no "Bucharest" in titles/meta/JSON-LD, Google Analytics tag, etc.).
- No outside services beyond GitHub itself.

## Approaches considered

1. **Custom /admin page using the GitHub API with a personal key (chosen).** On his domain, styled
   like the site, tailored to his content. Cost: most code to build; a key is stored in the browser
   of each device he logs in on.
2. **Decap CMS at /admin.** Ready-made editor with real GitHub login. Needs an OAuth helper on
   Cloudflare; generic look.
3. **Pages CMS (hosted).** Least setup; not on his domain; depends on a third party.

Owner picked 1: it is what he asked for, on his domain, usable from his phone, matching the site.

## How it works

### Content becomes data

The hand-written content moves into three files in the repo:

- `content/site.json` — identity line, home intro, About sections (heading + paragraphs),
  video-editing text, WhatsApp number, email, profile links (label + URL).
- `content/projects.json` — projects: name, URL, one-line description, language, group
  ("Windows" / "Browser"), and whether it is featured on the home page (exactly three).
- `content/photos.json` — photos: id, place (optional), date, image paths and size.

A Python generator (`scripts/build_site.py`) renders the four pages from small HTML templates plus
these files. Its output is the same plain HTML as today, committed to the repo, so Google and
visitors see no difference. The generator refuses to build (and changes nothing) if content breaks
a site rule: banned spellings, Bengali script, missing required fields, bad dates, or URLs that are
not http(s)/mailto.

### Admin page

- Static page at `/admin/` (HTML + one JS file + CSS), styled with the site's own tokens.
  `noindex, nofollow`, disallowed in robots.txt, absent from the sitemap.
- **Login:** Mogdho creates a GitHub fine-grained personal access token once (this repo only;
  Contents read/write, Actions read), pastes it in, and the browser remembers it on that device.
  A "Log out" button forgets it. The guide explains how to revoke it.
- **Photos tab:** grid of prints with place/date fields; "Add photos" accepts several images.
  Each image is resized **in the browser** to 1200px and 600px wide and re-encoded (WebP, or JPEG
  where the browser cannot make WebP). Re-encoding strips EXIF, so originals and their GPS data never
  leave the device.
- **Projects tab:** editable list; "Show on home page" checkboxes limited to three.
- **Text & links tab:** form fields for every item in `site.json`; About story as sections with
  plain paragraphs (blank line = new paragraph; no HTML accepted).
- **Save:** one button sends every change as **one commit** (images + JSON) through the GitHub API.
  If the site changed elsewhere since the admin loaded, it says so and reloads instead of overwriting.
- **Status:** after saving, the admin shows "Publishing…" and then "Live" or "Failed: <reason>",
  read from the GitHub Actions run.

### Publishing

A GitHub Actions workflow runs on every push to `main` that touches `content/` or `photos/img/`:
install Pillow → run `build_site.py` → run the test suite → commit the regenerated HTML (and
remove images no photo uses) → Pages publishes. If the build or tests fail, nothing is committed and
the live site keeps its last good version; the admin shows the failure.

## Decided by the owner

- Custom /admin page on his domain, usable from anywhere (phone or PC).
- Manages photos, projects, and text & links.
- Links hover like the menu (already built).

## Builder's calls (owner may change)

- GitHub personal key stored in the browser, not a login service.
- Images resized in the browser; no originals in the repo; the old `photo-originals/` +
  `data/photos.csv` flow is retired in favour of the admin.
- Exactly three featured projects on the home page.
- Text fields are plain paragraphs (blank line = new paragraph) with one small link syntax:
  `[link text](address)`. Addresses must be `https://…`, `mailto:…` or a page on the site (`/photos/`).
  Anything else, and any HTML, is shown as plain text (escaped), never as markup. The current links
  ("photos page", "projects page", "video showcase", "maggy2minutes") are migrated into this syntax,
  so no link is lost.
- Each project has a description for the Projects page and an optional shorter **home blurb**; if the
  blurb is empty the description is used. Migration keeps today's two texts exactly. Descriptions may
  use the same link syntax (video-showcase-paul links to the showcase).
- No undo inside the admin; every save is a git commit, so any version can be restored from GitHub.
- **Release:** the redesign and the admin go live together in one merge of `redesign` into `main`,
  when Mogdho says so. Checked 2026-10-27: Pages publishes from the `main` branch (classic
  "pages build and deployment"), and `main` is not protected, so the workflow can push its rebuilt
  pages; it also asks Pages to rebuild after its push, in case a bot push does not trigger one.

## Left to the builder

- Template mechanism for the generator (stdlib `string.Template` or similar; no new dependencies).
- Admin layout details within the site's design system (DESIGN.md).
- JS test approach (Node is available locally; tests must also run in GitHub Actions).
