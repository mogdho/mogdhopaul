<div align="center">

<img src="favicon.png" width="72" alt="MP logo">

# mogdhopaul.com

**The personal site of Mogdho Paul**, a developer and SEO specialist from Bangladesh,<br>
designed like a passport notebook: a green cover, visa-page paper and violet entry stamps.

[**Visit the site →**](https://mogdhopaul.com) &nbsp;·&nbsp; [Admin guide](docs/admin-guide.md)

<br>

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="docs/readme/home-dark.jpg">
  <img src="docs/readme/home-light.jpg" width="900" alt="The home page of mogdhopaul.com: the name Mogdho Paul on a green cover, a passport-style profile photo, and travel photos printed with ink stamps">
</picture>

<sub>The screenshot follows your GitHub theme: switch to dark mode to see the night cover.</sub>

</div>

<br>

## Design

The whole site borrows from one object, a passport. The header and footer are the **cover**, the
page behind the content is the **visa paper**, photos are **prints** with a stamped place and date,
and the footer ends with a real **passport code line**.

### Colour palette

<img src="docs/readme/palette.png" width="100%" alt="Colour palette in light and dark mode: cover green, paper, print, ink, soft ink and stamp violet">

| | Role | Light | | Dark |
|:-:|:--|:--|:-:|:--|
| <img src="docs/readme/swatches/0f4d3a.svg" width="44"> | **Cover**: header and footer band | `#0F4D3A` | <img src="docs/readme/swatches/0a2e23.svg" width="44"> | `#0A2E23` |
| <img src="docs/readme/swatches/eef1e7.svg" width="44"> | **Text on the cover** | `#EEF1E7` | <img src="docs/readme/swatches/e3e8dd.svg" width="44"> | `#E3E8DD` |
| <img src="docs/readme/swatches/b7cbbf.svg" width="44"> | **Soft text on the cover**: menu links | `#B7CBBF` | <img src="docs/readme/swatches/9db5a8.svg" width="44"> | `#9DB5A8` |
| <img src="docs/readme/swatches/eef1e7.svg" width="44"> | **Paper**: page background | `#EEF1E7` | <img src="docs/readme/swatches/121a17.svg" width="44"> | `#121A17` |
| <img src="docs/readme/swatches/e2e7da.svg" width="44"> | **Deep paper**: image placeholders | `#E2E7DA` | <img src="docs/readme/swatches/18221e.svg" width="44"> | `#18221E` |
| <img src="docs/readme/swatches/f8faf4.svg" width="44"> | **Print**: photo cards | `#F8FAF4` | <img src="docs/readme/swatches/e9ece3.svg" width="44"> | `#E9ECE3` |
| <img src="docs/readme/swatches/17201c.svg" width="44"> | **Ink**: main text | `#17201C` | <img src="docs/readme/swatches/e3e8dd.svg" width="44"> | `#E3E8DD` |
| <img src="docs/readme/swatches/46534d.svg" width="44"> | **Soft ink**: secondary text | `#46534D` | <img src="docs/readme/swatches/a8b3ac.svg" width="44"> | `#A8B3AC` |
| <img src="docs/readme/swatches/c9d1c2.svg" width="44"> | **Rule**: divider lines | `#C9D1C2` | <img src="docs/readme/swatches/2c3833.svg" width="44"> | `#2C3833` |
| <img src="docs/readme/swatches/5b3e96.svg" width="44"> | **Stamp violet**: stamps, links, skill badges | `#5B3E96` | <img src="docs/readme/swatches/b9a3ea.svg" width="44"> | `#B9A3EA` |
| <img src="docs/readme/swatches/c9b6f2.svg" width="44"> | **Lilac**: logo underline | `#C9B6F2` | | same |

Prints stay light paper in both themes, like real photographs. In light mode the stamp ink is
blended into the paper (`multiply`) so it reads as pressed ink rather than a flat colour.

### Typography

<img src="docs/readme/type.png" width="100%" alt="Type specimen: Young Serif for the name and headings, Schibsted Grotesk for body text, Share Tech Mono for stamps and the passport line">

| Typeface | Used for | Sizes |
|:--|:--|:--|
| [**Young Serif**](https://fonts.google.com/specimen/Young+Serif) | The name, headings, project and skill group names | Name 52–96 px · sections 28–42 px · small headings ≈ 21 px |
| [**Schibsted Grotesk**](https://fonts.google.com/specimen/Schibsted+Grotesk) | Body text, menu, buttons (regular to bold, plus italic) | Body 17 px |
| [**Share Tech Mono**](https://fonts.google.com/specimen/Share+Tech+Mono) | Date stamps, skill names, the passport line and Morse code | 12–26 px |

All three are free Google Fonts, served from this site (`fonts/`) rather than from Google.
Sizes that say "52–96 px" grow smoothly with the screen width.

### Layout and spacing

| | |
|:--|:--|
| **Content width** | At most 72 rem (≈ 1150 px); paragraphs stop at 66 characters per line |
| **Side margins** | 16 px on phones, growing to 40 px on wide screens |
| **Spacing scale** | 4 · 8 · 12 · 16 · 24 · 32 · 48 · 72 · 112 px — every gap uses one of these |
| **Breakpoint** | 48 rem (768 px): one column below, wider grids above |

### Details

- **Photos** are paper prints with a soft shadow, each tilted a little (−1.2° to +1.4°), and a violet stamp with the place and date.
- **Skills** are round double-ring entry stamps, pressed slightly crooked, holding single-colour icons.
- **Profile photo** sits on the cover like a passport photo, tilted −1.5°.
- **Logo** is “MP” in Share Tech Mono, cream on cover green, with a lilac underline.
- **Motion** is kept small: prints fade in as you scroll, and nothing moves for visitors who ask for reduced motion.

<br>

## How it works

```mermaid
flowchart LR
  A["Admin page<br>/admin/"] -- "save: one commit" --> B["content/*.json<br>+ photos"]
  B --> C["GitHub Actions<br>build + tests"]
  C -- "tests pass" --> D["Rebuilt pages<br>committed"]
  D --> E["GitHub Pages<br>mogdhopaul.com"]
  C -. "tests fail" .-> F["Site keeps its<br>last good version"]
```

- **Content** lives in three files: `content/site.json` (text, links, skills), `content/projects.json` and `content/photos.json`.
- **The admin** (`/admin/`) edits them in the browser and saves straight to this repository with a GitHub key. Photos are resized and stripped of location data on the device before upload. See the [admin guide](docs/admin-guide.md).
- **The build** (`scripts/build_site.py`) turns content and `templates/` into the pages: home, about, projects, photos, the currency converter and one page per tool (AlwaysNumLock, NN-tab, How Many Times and the rest; listed in `TOOLS` in the build script). Links to files that change carry a content hash (`style.css?v=…`), so the hosting cache never serves an old copy.
- **The tests** check content rules, page structure, SEO basics and style rules before anything goes live.

### Project layout

```
content/        site text, projects and photo list (edited by the admin)
templates/      page templates the build fills in (tools/ holds one per tool page)
scripts/        the build: content checks, page rendering, photo markup
admin/          the browser admin (no server)
photos/img/     travel photos, resized by the admin
skill-icons/    single-colour skill icons saved by the admin
fonts/          self-hosted web fonts
tests/          Python and JavaScript tests
docs/           admin guide and these README images
currency-converter/  the converter's script (its page is built like the others)
<tool>/         built tool pages, e.g. alwaysnumlock/, nn-tab/, how-many-time/, with their images
```

### Run it locally

```bash
python -m scripts.build_site                 # rebuild the pages from content/
python -m unittest discover -s tests -t .    # Python tests
node --test "tests/js/*.test.mjs"            # admin logic tests
python -m http.server                        # then open http://localhost:8000
```

Open `http://localhost:8000/admin/?demo` to try the admin with your local content; demo mode never saves.

<br>

<div align="center">
<sub><code>P&lt;BGDPAUL&lt;&lt;MOGDHO&lt;&lt;&lt;&lt;&lt;&lt;&lt;&lt;&lt;&lt;&lt;&lt;&lt;&lt;&lt;&lt;&lt;&lt;&lt;&lt;&lt;&lt;&lt;&lt;&lt;&lt;&lt;</code></sub>
</div>
