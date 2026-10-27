---
name: Mogdho Paul
description: A personal site kept like a passport notebook. Cover green, visa-page paper and violet entry stamps.
colors:
  cover: "#0f4d3a"
  on-cover: "#eef1e7"
  on-cover-soft: "#b7cbbf"
  paper: "#eef1e7"
  paper-deep: "#e2e7da"
  print: "#f8faf4"
  ink: "#17201c"
  ink-soft: "#46534d"
  rule: "#c9d1c2"
  stamp: "#5b3e96"
  stamp-on-print: "#5b3e96"
  cover-dark: "#0a2e23"
  on-cover-dark: "#e3e8dd"
  on-cover-soft-dark: "#9db5a8"
  paper-dark: "#121a17"
  paper-deep-dark: "#18221e"
  print-dark: "#e9ece3"
  ink-dark: "#e3e8dd"
  ink-soft-dark: "#a8b3ac"
  rule-dark: "#2c3833"
  stamp-dark: "#b9a3ea"
typography:
  display:
    fontFamily: "Young Serif, Georgia, Times New Roman, serif"
    fontSize: "clamp(3.25rem, 1.5rem + 9vw, 6rem)"
    fontWeight: 400
    lineHeight: 0.95
    letterSpacing: "-0.02em"
  display-short:
    fontFamily: "Young Serif, Georgia, Times New Roman, serif"
    fontSize: "clamp(2.5rem, 1.4rem + 5vw, 4.5rem)"
    fontWeight: 400
    lineHeight: 0.95
    letterSpacing: "-0.02em"
  headline:
    fontFamily: "Young Serif, Georgia, Times New Roman, serif"
    fontSize: "clamp(1.75rem, 1.2rem + 2vw, 2.6rem)"
    fontWeight: 400
    lineHeight: 1.1
    letterSpacing: "-0.01em"
  title:
    fontFamily: "Young Serif, Georgia, Times New Roman, serif"
    fontSize: "1.35rem"
    fontWeight: 400
    lineHeight: 1.1
    letterSpacing: "-0.01em"
  lead:
    fontFamily: "Schibsted Grotesk, Segoe UI, system-ui, sans-serif"
    fontSize: "clamp(1.15rem, 1rem + 0.6vw, 1.4rem)"
    fontWeight: 400
    lineHeight: 1.45
  body:
    fontFamily: "Schibsted Grotesk, Segoe UI, system-ui, sans-serif"
    fontSize: "1.0625rem"
    fontWeight: 400
    lineHeight: 1.6
  nav:
    fontFamily: "Schibsted Grotesk, Segoe UI, system-ui, sans-serif"
    fontSize: "0.95rem"
    fontWeight: 400
  label-stamp:
    fontFamily: "Share Tech Mono, ui-monospace, Consolas, monospace"
    fontSize: "0.72rem"
    fontWeight: 400
    lineHeight: 1.25
    letterSpacing: "0.08em"
  mono-data:
    fontFamily: "Share Tech Mono, ui-monospace, Consolas, monospace"
    fontSize: "clamp(0.95rem, 0.8rem + 0.6vw, 1.2rem)"
    fontWeight: 400
    letterSpacing: "0.18em"
rounded:
  none: "0px"
  stamp: "2px"
spacing:
  s1: "0.25rem"
  s2: "0.5rem"
  s3: "0.75rem"
  s4: "1rem"
  s5: "1.5rem"
  s6: "2rem"
  s7: "3rem"
  s8: "4.5rem"
  s9: "7rem"
  gutter: "clamp(1rem, 4vw, 2.5rem)"
components:
  cover-field:
    backgroundColor: "{colors.cover}"
    textColor: "{colors.on-cover}"
  nav-link:
    textColor: "{colors.on-cover-soft}"
    typography: "{typography.nav}"
    padding: "0.5rem 0"
  nav-link-current:
    textColor: "{colors.on-cover}"
  text-link:
    textColor: "{colors.stamp}"
  passport-photo:
    backgroundColor: "{colors.print}"
    rounded: "{rounded.none}"
    padding: "0.35rem"
    width: "clamp(7.5rem, 22vw, 11rem)"
  print:
    backgroundColor: "{colors.print}"
    rounded: "{rounded.none}"
    padding: "0.4rem 0.4rem 0.7rem"
  entry-stamp:
    textColor: "{colors.stamp-on-print}"
    typography: "{typography.label-stamp}"
    rounded: "{rounded.stamp}"
    padding: "0.3rem 0.55rem 0.25rem"
  project-entry:
    textColor: "{colors.ink}"
    padding: "1.5rem 0"
  project-entry-hover:
    textColor: "{colors.stamp}"
---

# Design System: Mogdho Paul

## Overview

**Creative North Star: "The Passport Notebook"**

The site is built from the physical materials of a Bangladeshi passport. A deep cover green holds the header and the footer like the front and back boards; between them lies the visa page, a pale grey-green paper carrying a faint 28px security grid. Content is ink on that paper. The only colour that is not paper, ink or cover is violet entry-stamp ink, and it marks the places a reader can act or a journey was recorded.

Density is calm and generous: one reading column, wide vertical breaths between sections, and photographs presented as small physical prints with a white border, a soft lift and a slight hand-placed tilt. Machine-readable passport conventions (Morse line, MRZ line, stamp dates) are set in a monospace face, so data reads as data and voice reads as voice.

Motion is nearly absent. Prints are always visible and still; the single moment of movement is each entry stamp landing on its print once, as it scrolls in.

**Key Characteristics:**
- Cover-green boards top and bottom, visa-paper field in between.
- One accent, violet stamp ink, for links, stamps, focus and selection.
- Prints as objects: light border, soft shadow, small rotation.
- Three faces with fixed jobs: serif for names, grotesk for reading, mono for data.
- One motion: the stamp landing.
- Full light and dark mode through `prefers-color-scheme`; prints stay light paper in both.

## Colors

A restrained, earthy passport palette: green boards, grey-green paper, green-black ink, one violet ink.

### Primary
- **Entry-Stamp Violet** (stamp): every text link, the entry stamps on prints, the focus ring, text selection and the caret. In dark mode it lifts to a pale lavender (stamp-dark) to hold contrast on dark paper.
- **Stamp Ink on Print** (stamp-on-print): the stamp colour fixed at the light-mode violet in both modes, because prints remain light paper in dark mode.

### Secondary
- **Passport Cover Green** (cover): the full-bleed header field and the footer. Also the `theme-color`. Darkens to cover-dark in dark mode.

### Neutral
- **Visa Paper** (paper): the page background under the security grid.
- **Deep Paper** (paper-deep): image placeholder behind loading prints; scrollbar track.
- **Print White** (print): the border of every print and the passport photo. Stays light in dark mode (print-dark).
- **Green-Black Ink** (ink): body text and headings on paper.
- **Faded Ink** (ink-soft): secondary text, the Morse line, project language tags, empty notes.
- **Ruling Line** (rule): the 1px hairlines between project entries.
- **Cover Paper Text** (on-cover) and **Cover Soft Text** (on-cover-soft): text on the cover field; the soft value is used for inactive nav links, the MRZ line and the copyright.

### Named Rules
**The One Ink Rule.** Violet is the only chromatic accent. It appears on links, stamps, focus rings, selection and caret, and nowhere else. No fills, no buttons, no backgrounds in violet.

**The Boards and Pages Rule.** Cover green belongs to the header field and the footer only. Content sections sit on paper; never put a green panel mid-page.

**The Prints Stay Paper Rule.** Prints and the passport photo stay light in dark mode, and the stamp on them keeps its light-mode violet with multiply blending turned off.

## Typography

**Display Font:** Young Serif (with Georgia, Times New Roman, serif)
**Body Font:** Schibsted Grotesk (with Segoe UI, system-ui, sans-serif)
**Label/Mono Font:** Share Tech Mono (with ui-monospace, Consolas, monospace)

**Character:** A soft, slightly old-fashioned serif for names and headings over a plain, sturdy grotesk for reading, with a technical mono that feels like the printed machine fields of a travel document. All three are self-hosted woff2 with `font-display: swap`.

### Hierarchy
- **Display** (400, clamp(3.25rem, 1.5rem + 9vw, 6rem), 0.95): his name on the home cover. Inner pages use **Display Short** (clamp(2.5rem, 1.4rem + 5vw, 4.5rem)).
- **Headline** (400, clamp(1.75rem, 1.2rem + 2vw, 2.6rem), 1.1): section headings, balanced wrapping, 4.5rem above. The footer heading drops to 1.6rem.
- **Title** (400, 1.35rem, 1.1): sub-headings; project names at 1.3rem.
- **Lead** (400, clamp(1.15rem, 1rem + 0.6vw, 1.4rem), 1.45): the opening paragraph; the cover identity line is a near twin at up to 1.45rem, held to 34ch.
- **Body** (400, 1.0625rem, 1.6): all reading text, held to a 66ch measure.
- **Label / Stamp** (Share Tech Mono 400, 0.72rem, 0.08em, uppercase): dates inside entry stamps. The place name above the date switches to Schibsted Grotesk 700 at 0.06em.
- **Mono data** (Share Tech Mono 400): the Morse line (up to 1.2rem, 0.18em tracking), the MRZ line (clamp(0.7rem, 0.55rem + 0.6vw, 1rem), 0.12em), project language tags (0.85rem).

### Named Rules
**The Three Jobs Rule.** Serif names things, grotesk says things, mono records things. Mono is for data a machine could read (dates, codes, Morse, MRZ, language tags), never for prose or headings.

**The Single Weight Rule.** Headings are always Young Serif at 400. Hierarchy comes from size, not weight; bold appears only in a stamp's place name.

## Layout

A single centred column, `min(100% - 2 × gutter, 72rem)`, with a fluid gutter of clamp(1rem, 4vw, 2.5rem). Prose is capped at 66ch inside it. The spacing scale runs s1–s9 (0.25rem to 7rem); headings take s8 above and s4 below, sections breathe at s7–s8, and `main` closes with s9.

One breakpoint, 48rem, does all responsive work:
- **Home cover:** a two-column grid. On phones the passport photo sits beside the name with the identity line spanning beneath; from 48rem the photo stands beside the whole name-and-line block.
- **Photo strip (home):** 2 columns, 3 from 48rem (prints crop to 4:3 there).
- **Photo grid (photos page):** 2 columns, 4 from 48rem, dense flow; when there are five or more prints the first spans 2×2.
- **Project entries:** stacked, then a three-column row (17rem name, flexible description, auto language tag) on a baseline.
- **Split sections:** stacked, then 1fr / 1.4fr with s7 gap.

Section heads put the heading and its "see all" link on one baseline, wrapping when tight. The body background carries a 28px grid at 7% cover-green (5% paper-light in dark mode).

## Elevation & Depth

Surfaces are flat paper. Depth exists only for physical objects laid on the page: prints and the passport photo. They carry one soft, two-layer shadow and a small rotation, which together read as a photograph resting on a page rather than a floating card.

### Shadow Vocabulary
- **Print lift** (`box-shadow: 0 1px 2px rgb(23 32 28 / 0.12), 0 6px 16px -6px rgb(23 32 28 / 0.22)`; dark mode `0 1px 2px rgb(0 0 0 / 0.4), 0 8px 20px -8px rgb(0 0 0 / 0.6)`): prints and the passport photo only.

### Named Rules
**The Objects Only Rule.** Only physical objects (prints, the passport photo) lift. Text blocks, lists, headers and the footer stay flat.

## Shapes

Square-cornered by default: prints, the passport photo, the cover field and the project list have no radius. The one curve is the entry stamp's 2px corner, which the focus ring shares. Borders are 1px hairlines in rule colour between project entries, and a 4px double rule in violet around each stamp.

Rotation is part of the form language. The passport photo rests at -1.5deg. Prints cycle through -1.2, 0.8, -0.4 and 1.4deg; stamps cycle through -4, 3 and -2.5deg and alternate between the print's right and left margin, so no two neighbours repeat.

## Components

### Navigation
Quiet paper-coloured links along the top of the cover.
- **Style:** Schibsted Grotesk 0.95rem in cover soft text, no underline, s2 vertical padding, s5 gap, wrapping.
- **Hover / Current:** full cover text colour with a 1px underline; `aria-current="page"` marks the current page.
- **Name mark:** his name at the left in Young Serif 1.15rem, no underline.
- **Focus:** on the cover the focus ring switches to cover text colour.

### Text Links
- **Style:** violet, 1px underline offset 0.2em.
- **Hover:** underline thickens to 2px over 150ms (no transition with reduced motion).
- **Focus:** 2px solid violet outline, 3px offset, 2px corners. On cover-green fields, links and focus rings use cover text colour.

### Passport Photo
A small square-cornered portrait inset on the cover: print-white border (0.35rem), print lift, -1.5deg tilt, 4:5 crop focused near the top.

### Print and Entry Stamp (signature)
Each travel photo is a print with a violet entry stamp in its margin, generated as a `figure` with a linked image and a `figcaption` stamp.
- **Print:** print-white frame (0.4rem sides, 0.7rem bottom), print lift, cycled tilt; 4:5 image crop on a deep-paper placeholder.
- **Stamp:** sits in the print's bottom margin with a 4px double violet border, 2px corners, uppercase mono date at 0.72rem, and the place name above it in bold grotesk. It is tilted, uses multiply blending in light mode, and is masked with the raster ink grain (`stamp-ink.png`, 160px tile, offset on every fourth print) so the ink looks pressed, not drawn.
- **Content:** place and date only ("Paris" / "14 February 2025"), never a caption.
- **Motion:** with JS, the stamp starts hidden and, once its print is 15% in view, lands once over 420ms after a 260ms delay: from 1.35× scale and 6deg extra rotation, overshooting to 0.96×, settling at its resting tilt (ease-out `cubic-bezier(0.16, 1, 0.3, 1)`). Without JS or with reduced motion, stamps are simply present.

### Project Entry
An entry on a visa page: a list ruled by 1px hairlines above and between items.
- **Name:** Young Serif 1.3rem in ink, no underline; on hover, violet with underline.
- **Description:** body text, capped at 66ch.
- **Language tag:** mono 0.85rem in faded ink, aligned to the baseline at the far right from 48rem.

### Cover and Footer Boards
- **Cover:** full-bleed cover green holding the header, the display name, the identity line and the passport photo.
- **Footer:** the same green, s7/s6 padding, a 1.6rem serif heading, the profile links in a wrapping row, the MRZ line in mono cover soft text that may break anywhere, and a 0.85rem copyright.

## Do's and Don'ts

### Do:
- **Do** keep violet (stamp) for links, stamps, focus, selection and caret only.
- **Do** frame every photograph as a print: print-white border, the print lift shadow, a small tilt from the -1.2 / 0.8 / -0.4 / 1.4deg cycle.
- **Do** label prints with an entry stamp of place and date only, in mono uppercase inside a 4px double violet border with the ink mask.
- **Do** set names and headings in Young Serif 400, reading text in Schibsted Grotesk at 1.0625rem / 1.6, and machine-readable data in Share Tech Mono.
- **Do** keep cover green to the header field and the footer, with paper and its 28px security grid everywhere between.
- **Do** keep the stamp landing as the site's only animation (beyond the 150ms link underline), and turn both off under reduced motion.
- **Do** check each new colour pair in both light and dark mode; prints stay light paper in both.

### Don't:
- **Don't** put violet on fills, buttons, panels or backgrounds.
- **Don't** add a second accent colour or gradients.
- **Don't** use mono for prose, headings or navigation.
- **Don't** add shadows to text blocks, lists, headers or the footer; only prints and the passport photo lift.
- **Don't** round the corners of prints, the passport photo or containers; the 2px corner belongs to stamps and focus rings.
- **Don't** animate prints or add scroll-triggered movement beyond the stamp landing.
- **Don't** add captions to prints beyond place and date.
