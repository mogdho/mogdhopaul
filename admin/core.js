// Admin logic with no browser or network dependencies. Mirrors the rules in scripts/content.py,
// so problems are shown next to the field before anything is saved.

export const BANNED_NAMES = ['mugdho', 'mogdha'];
export const FEATURED_COUNT = 3;
export const GROUPS = ['windows', 'browser'];
export const SKILL_GROUPS = ['stack', 'tools'];
const LINK = /\[([^\]\n]+)\]\(([^)\s]+)\)/g;
const IMG_PATH = /^\/photos\/img\/[a-z0-9-]+\.(webp|jpg)$/;
const SUPPORTED = ['image/jpeg', 'image/png', 'image/webp', 'image/gif'];
const EMOJI = /[\u{1F300}-\u{1FAFF}\u{2600}-\u{27BF}]/u;
const HTML_TAG = /<\/?[a-z!]/i;
const BANNED_PHRASES = ['ai-assisted'];
const IDENTITY_NAME = 'Mogdho Paul';
const IDENTITY_BANNED = /video editor|motion designer|bucharest/i;

export function isAllowedUrl(url) {
  return /^(https?:\/\/[^\s"'<>]+|mailto:[^\s"'<>]+|\/[^\s"'<>]*)$/.test(url || '');
}

function nonLatin(text) {
  for (const ch of text) {
    if (/\p{L}/u.test(ch) && !/\p{Script=Latin}/u.test(ch)) return true;
    if (/\p{Nd}/u.test(ch) && !/[0-9]/.test(ch)) return true;
  }
  return false;
}

/** Problem with a text field, or null when it is fine. */
export function checkText(text, { required = true } = {}) {
  if (typeof text !== 'string' || (required && !text.trim())) return 'This can’t be empty.';
  if (nonLatin(text)) return 'Please write this in English letters.';
  const lower = text.toLowerCase();
  if (BANNED_NAMES.some((n) => lower.includes(n))) return 'This has another spelling of your name. Use “Mogdho Paul”.';
  if (EMOJI.test(text)) return 'Please leave out emoji.';
  if (BANNED_PHRASES.some((p) => lower.includes(p))) return 'Please leave out “AI-Assisted”.';
  if (HTML_TAG.test(text)) return 'HTML isn’t allowed here. Write plain text; for a link use [text](https://…).';
  for (const m of text.matchAll(LINK)) {
    if (!isAllowedUrl(m[2])) return `The link “${m[2]}” must start with https://, mailto: or /`;
  }
  return null;
}

function urlProblem(url) {
  return isAllowedUrl(url) ? null : 'Must be a link starting with https://, mailto: or /';
}

/** Every problem in the content, as {field, message}; field names match scripts/content.py. */
export function validateContent({ site, projects, photos }) {
  const errors = [];
  const add = (field, message) => { if (message) errors.push({ field, message }); };
  const text = (field, value, opts) => add(field, checkText(value, opts));

  text('site.identity', site.identity);
  if ((site.identity || '').length > 160) add('site.identity', 'Keep it under 160 characters (Google shows it as the page description).');
  else if (!(site.identity || '').includes(IDENTITY_NAME)) add('site.identity', `Include your name, “${IDENTITY_NAME}”, so Google connects this line to you.`);
  else if (IDENTITY_BANNED.test(site.identity)) add('site.identity', 'Leave out “video editor”, “motion designer” and “Bucharest” here; video editing has its own section.');
  for (const key of ['lead', 'text', 'video']) text(`site.home.${key}`, site.home[key]);
  for (const key of SKILL_GROUPS) {
    const items = site.skills?.[key];
    if (!Array.isArray(items)) add(`site.skills.${key}`, 'This list is missing.');
    else add(`site.skills.${key}`, items.map((t) => checkText(t)).find(Boolean) || null);
  }
  text('site.about.lead', site.about.lead);
  site.about.sections.forEach((s, i) => {
    text(`site.about.sections[${i}].heading`, s.heading);
    text(`site.about.sections[${i}].text`, s.text);
  });
  add('site.contact.whatsapp', urlProblem(site.contact.whatsapp));
  if (!/^[^\s@<>"']+@[^\s@<>"']+\.[a-z]{2,}$/i.test(site.contact.email || '')) add('site.contact.email', 'Not an email address.');
  site.profiles.forEach((p, i) => {
    text(`site.profiles[${i}].label`, p.label);
    add(`site.profiles[${i}].url`, urlProblem(p.url));
  });

  projects.forEach((p, i) => {
    const f = `projects[${i}]`;
    for (const key of ['name', 'description', 'language']) text(`${f}.${key}`, p[key]);
    text(`${f}.home_blurb`, p.home_blurb, { required: false });
    add(`${f}.url`, urlProblem(p.url));
    if (!GROUPS.includes(p.group)) add(`${f}.group`, 'Choose Windows or Browser.');
  });
  if (projects.filter((p) => p.featured).length !== FEATURED_COUNT) {
    add('projects', `Choose exactly ${FEATURED_COUNT} projects for the home page.`);
  }

  photos.forEach((ph, i) => {
    const f = `photos[${i}]`;
    if (!/^\d{4}-\d{2}-\d{2}$/.test(ph.date || '') || Number.isNaN(Date.parse(ph.date))) add(`${f}.date`, 'Pick a date.');
    if (ph.place != null && ph.place !== '') text(`${f}.place`, ph.place);
    for (const key of ['src', 'thumb']) if (!IMG_PATH.test(ph[key] || '')) add(`${f}.${key}`, 'Image path is broken.');
    if (ph.focus !== undefined && !isFocus(ph.focus)) add(`${f}.focus`, 'Crop position is broken. Press “Centre” to reset it.');
  });
  return errors;
}

/** Crop position: {x, y} whole percentages from 0 to 100. */
export function isFocus(focus) {
  return focus !== null && typeof focus === 'object'
    && Object.keys(focus).sort().join() === 'x,y'
    && [focus.x, focus.y].every((n) => Number.isInteger(n) && n >= 0 && n <= 100);
}

/**
 * New crop position after dragging the photo by (dx, dy) pixels inside a frame.
 * The photo covers the frame, so only the overflowing side can move; dragging right shows more of the left.
 */
export function dragFocus(start, dx, dy, { frameW, frameH, imageW, imageH }) {
  const scale = Math.max(frameW / imageW, frameH / imageH);
  const overX = imageW * scale - frameW;
  const overY = imageH * scale - frameH;
  const clamp = (n) => Math.min(100, Math.max(0, Math.round(n)));
  return {
    x: overX > 0.5 ? clamp(start.x - (dx / overX) * 100) : start.x,
    y: overY > 0.5 ? clamp(start.y - (dy / overY) * 100) : start.y,
  };
}

/**
 * Part of a srcW x srcH image to cut for an outW x outH frame, placed by `focus` ({x, y} percentages),
 * like object-fit: cover with object-position. The output never enlarges the source.
 */
export function cropRect(srcW, srcH, outW, outH, focus) {
  const ratio = outW / outH;
  let sw = srcW;
  let sh = srcH;
  if (srcW / srcH > ratio) sw = Math.round(srcH * ratio);
  else sh = Math.round(srcW / ratio);
  const sx = Math.round(((srcW - sw) * focus.x) / 100);
  const sy = Math.round(((srcH - sh) * focus.y) / 100);
  const w = Math.min(outW, sw);
  return { sx, sy, sw, sh, outW: w, outH: Math.round(w / ratio) };
}

/** Size that fits within `max` pixels wide, never enlarging. */
export function targetSize(width, height, max) {
  if (width <= max) return { width, height };
  return { width: max, height: Math.round((height * max) / width) };
}

export function isSupportedImage(file) {
  return SUPPORTED.includes(file && file.type);
}

/** "<date>-<4 hex>", not already in `taken`. */
export function newPhotoId(date, taken, rand = Math.random) {
  for (;;) {
    const hex = Math.floor(rand() * 0x10000).toString(16).padStart(4, '0');
    const id = `${date}-${hex}`;
    if (!taken.has(id)) return id;
  }
}

/**
 * The content files a save writes. Images of removed photos are not deleted here: the build
 * deletes them in the same commit as the new pages, so the live site never links to a missing file.
 */
export function filesToSave({ site, projects, photos }) {
  return [
    { path: 'content/site.json', text: toJson(site) },
    { path: 'content/projects.json', text: toJson(projects) },
    { path: 'content/photos.json', text: toJson(photos) },
  ];
}

/**
 * Wait for the "Build site" run of `sha`. Never throws: the save already succeeded, so a failed
 * check (key without Actions access, network blip) is reported as 'unchecked'.
 * Calls onStatus with 'publishing' first, then the outcome: 'success' | 'failure' | 'timeout' | 'unchecked'.
 */
export async function watchPublishing(repo, sha, {
  onStatus, sleep = (ms) => new Promise((r) => setTimeout(r, ms)), now = Date.now,
  intervalMs = 5000, timeoutMs = 5 * 60 * 1000,
}) {
  onStatus('publishing');
  const started = now();
  let outcome = 'timeout';
  try {
    while (now() - started < timeoutMs) {
      await sleep(intervalMs);
      const status = await repo.buildStatus(sha);
      if (status === 'success' || status === 'failure') { outcome = status; break; }
    }
  } catch {
    outcome = 'unchecked';
  }
  onStatus(outcome);
  return outcome;
}

export function toJson(value) {
  return JSON.stringify(value, null, 2) + '\n';
}
