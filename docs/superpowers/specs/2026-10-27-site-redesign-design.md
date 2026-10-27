# mogdhopaul.com redesign — design

Date: 2026-10-27
Status: approved 2026-10-27. Amended 2026-10-27: owner dropped the Instagram feed; photos are added by hand (docs/adding-photos.md).

## Intent and why

mogdhopaul.com is Mogdho Paul's personal site. Its main job is to be the
top Google result for the name "Mogdho Paul" and to tell Google and
visitors clearly who he is. Getting hired (freelance work) is secondary.

Today the site is a single page with about 150 words, most of them in a
JavaScript typing effect. It looks like a typical AI-generated portfolio
(dark navy, purple/blue gradients, glowing cards, spinning photo ring,
pill tags). Searches for the name currently return nothing about him;
similar spellings (e.g. "Mugdho") are dominated by unrelated news
coverage, and his profiles describe him four different ways.

The redesign gives Google a lot of plain, consistent text about one
person, and gives visitors a site that feels made by a person with taste.

## Identity line (use everywhere)

> Mogdho Paul is a developer and SEO specialist from Bangladesh who
> builds small web tools and automations.

- Location is **Bangladesh**. Do not mention Bucharest as where he is based.
- "Video editor and motion designer" is **not** in the headline, page
  titles or meta descriptions as his main role. Video editing still
  appears on the site as a section (see Home).
- This line drives the `<title>`, meta descriptions, Open Graph tags and
  the JSON-LD `Person` data (`jobTitle`, `description`).
- The only spelling is **Mogdho Paul** (handle: `mogdhopaul`). Do not add
  "Mugdho", "Mogdha" or a Bengali spelling anywhere, including
  `alternateName`.

## Goals

1. Rank #1 for "Mogdho Paul" and "mogdhopaul".
2. Several indexable pages, each with real text containing the name.
3. One consistent identity across the site and every linked profile.
4. Show his travel photos from Instagram automatically.
5. Look personal and hand-made, not AI-generated.
6. Stay very fast and readable without JavaScript.

## Non-goals

- No Bengali version (English only).
- No redesign of video-showcase.mogdhopaul.com (separate site; its SEO
  problems are noted below but out of scope).
- No blog/CMS on this site; maggy2minutes.wordpress.com stays separate.
- No contact form or backend.

## Anti-goals (a failure even if it works)

- Looks like an AI template: dark navy, purple/blue/cyan gradients,
  gradient text, glow, glassmorphism, rows of pill tags, three identical
  cards, emoji icons, typing effects, spinning/floating elements.
- Marketing voice ("I bring your vision to life").
- Important text only visible after JavaScript runs.
- Third-party widget scripts for Instagram.

## Constraints

- Hosting stays GitHub Pages on the custom domain (CNAME `mogdhopaul.com`,
  served through Cloudflare). Static files only.
- Plain HTML, CSS, JavaScript. No framework, no build step for the pages.
- Keep the Google Analytics tag `G-LDY4Z5D7MW` on every page.
- GitHub Pages publishes every file in the repo. The local `.claude/`
  folder (the ui-ux-pro-max skill) must not be committed; add it to
  `.gitignore`.
- Instagram's Basic Display API was shut down in December 2024; the
  Instagram API now requires a Professional (Creator or Business) account
  and an access token, which cannot be exposed in client-side code.

## Approaches considered

### Instagram feed

1. **Nightly GitHub Action (chosen).** A scheduled workflow calls the
   Instagram API with a token stored in GitHub Secrets, downloads the
   latest photos into the repo, writes a data file and commits, which
   republishes the site. Free, fast, images self-hosted and indexable with
   alt text. Cost: up to ~24h delay; one-time setup of a Professional
   account and a Meta developer app.
2. **Third-party widget (Behold, LightWidget, etc.).** Five-minute setup,
   but loads an outside script and outside image hosting, is slower,
   gives little SEO value, has free-plan limits and is hard to style.

Owner picked 1 because ranking the name is the main goal and it keeps
everything on his own site.

### Site build

Only one sensible way: hand-written static pages, matching what exists.
A framework or static site generator adds a build step without helping
SEO or speed for four pages.

## Pages

All pages share a header (name + nav: Home, About, Photos, Projects) and a
footer with every profile link.

1. **Home** `/` — name, identity line, short intro in his own voice, a
   strip of the latest travel photos (links to Photos), two or three
   featured projects (links to Projects), a short video-editing section
   linking to video-showcase.mogdhopaul.com, profile links, WhatsApp
   contact.
2. **About** `/about/` — longer personal story, rewritten in English from
   https://maggy2minutes.wordpress.com/about/ : grew up in Brahmanbaria and
   Dhaka, introvert who loves learning ("talk at least 2 min on any
   topic"), prefers quiet places close to nature, Tagore songs, learning
   Morse code, calligraphy, documentaries, farmhouse dream; skills in SEO,
   web development, video editing. Leave out sensitive personal details
   from the blog (blood group, religion, marital status, mental health).
3. **Photos** `/photos/` — full travel feed from Instagram, updated
   nightly, with the place and date as real text.

### Instagram photo details

- **Launch order (owner):** photos come only from Instagram. The
  Instagram setup is done as part of the launch, so the site goes live
  with the automatic feed working. No hand-picked starter set.
- **Places (owner):** he usually writes the place name in the caption.
  The workflow extracts the place from the caption and uses it for the
  label and alt text. When none is found, show the date only.
- **Captions (builder's call):** show only the extracted place and the
  date, not the full caption. This avoids hashtags and any Bengali text
  on an English-only site.
- **Which posts (builder's call):** include all image posts (carousel
  posts use their first image; skip videos/reels). Provide a small
  hand-edited exclude list for posts that should not appear.
4. **Projects** `/projects/` — GitHub tools, each with one sentence on the
   problem it solves: Hotspot-Auto-Connect, Copilot2Gemini,
   Capslock-CopyPaste, NN-tab, leaflet (invoice generator),
   video-showcase-paul.

## Profile links (site footer and JSON-LD `sameAs`)

- https://www.facebook.com/mogdhopaul
- https://www.instagram.com/mogdhopaul/
- https://www.linkedin.com/in/mogdho-paul/ (the current JSON-LD uses an
  older URL; use this one everywhere)
- https://github.com/mogdho
- https://www.youtube.com/@mogdhoPAUL
- https://t.me/MOGdhA
- https://maggy2minutes.wordpress.com/
- Footer also keeps email (mailto:mogdhapal@gmail.com, as on the current
  site; builder's call, owner may switch to the yahoo address) and
  WhatsApp (https://wa.me/+8801998955221).

## Visual direction: "a quiet travel notebook"

- Calm, personal, slightly hand-made, like a field journal.
- Warm off-white paper background, dark ink text, one earthy accent
  colour drawn from his photos. A dark mode in the same calm tones.
- A characterful serif for name and headings, a plain readable sans for
  body text, small typewriter/monospace labels for photo place and date.
- Photos laid out like album prints at varied sizes, not a uniform grid.
- His name in Morse code as a small decorative divider.
- Motion: only gentle fade-ins; respect `prefers-reduced-motion`.
- Copy in his own plain voice.

Exact palette, fonts and spacing are refined during the build with the
ui-ux-pro-max skill (design-system search) and the Impeccable skill (to
avoid AI-looking patterns).

## SEO requirements

- Unique `<title>` and meta description per page, each containing
  "Mogdho Paul".
- One `<h1>` per page; all key text in the HTML, not injected by JS.
- JSON-LD `Person` on Home (identity line, `sameAs` above, `image`,
  `nationality` Bangladesh); `ProfilePage`/`AboutPage` on About.
- Descriptive image `alt` text including the place.
- Update `sitemap.xml` with all four pages; keep `robots.txt`.
- Canonical URLs, Open Graph and Twitter tags on every page.
- Images resized and served as WebP/AVIF with width/height set.

## Owner tasks outside the code

- Switch Instagram to a Creator or Business account, connect it to a
  Facebook page, create a Meta developer app, and add the access token as
  a GitHub secret (the builder provides step-by-step instructions).
- Update bios on GitHub (location → Bangladesh), LinkedIn and other
  profiles to match the identity line.
- After launch, submit the sitemap in Google Search Console.

## Left to the builder

- Exact colours, fonts, spacing and layout details (via the two skills).
- Wording of page copy, following the voice and facts above.
- Instagram workflow details: schedule time, number of photos kept,
  image sizes, token refresh (long-lived tokens expire after 60 days and
  must be refreshed by the workflow).
- How the photo data reaches the HTML so photos are present without JS
  (e.g. the workflow regenerates the photo sections of the HTML).

## Noted, out of scope

video-showcase.mogdhopaul.com has the title "Pauls Video Showcase", the
description "Lovable Generated Project", and shows "Access Denied" without
JavaScript, so search engines see almost nothing there.
