// Admin page: log in with a GitHub key, edit content/*.json and photos, save as one commit, watch publishing.
import {
  DEFAULT_SKILL_ICONS, FEATURED_COUNT, ICON_SETS, dragFocus, filesToSave, iconQueries, isSupportedImage, newPhotoId, newestFirst,
  rankIcons, skillIconPath, validateContent, watchPublishing,
} from './core.js';
import { AuthError, ConflictError, Repo } from './github.js';
import { PORTRAIT_SIZE, cropImage, resizeImage } from './images.js';

const TOKEN_KEY = 'mp-admin-token';
const ACTIONS_URL = 'https://github.com/mogdho/mogdhopaul/actions';
const $ = (id) => document.getElementById(id);
const demo = new URLSearchParams(location.search).has('demo');

const state = {
  repo: null, sha: null, original: null,
  site: null, projects: [], photos: [],
  newImages: new Map(), // repo path -> Blob, for photos added since the last save
  previews: new Map(), // photo id -> object URL
  portrait: null, // a newly chosen profile photo, until it is saved
  dirty: false, saving: false,
  resumeSave: false, // a save stopped by a bad key: log in again and it continues, edits kept
};

// ---------- small DOM helpers ----------
function el(tag, attrs = {}, ...children) {
  const node = document.createElement(tag);
  for (const [k, v] of Object.entries(attrs)) {
    if (v === false || v == null) continue;
    if (k === 'class') node.className = v;
    else if (k.startsWith('on')) node.addEventListener(k.slice(2), v);
    else if (k === 'text') node.textContent = v;
    else node.setAttribute(k, v === true ? '' : v);
  }
  for (const c of children.flat()) if (c != null) node.append(c);
  return node;
}

let fieldCounter = 0;
function field({ label, value, field: name, onInput, type = 'text', multiline = false, hint, options, required = true }) {
  const id = `f${++fieldCounter}`;
  const input = options
    ? el('select', { id, 'data-field': name }, options.map(([v, t]) => el('option', { value: v, selected: v === value }, t)))
    : multiline
      ? el('textarea', { id, 'data-field': name, rows: 6 })
      : el('input', { id, type, 'data-field': name, required, autocomplete: 'off' });
  if (!options) input.value = value ?? '';
  input.addEventListener(options ? 'change' : 'input', () => { onInput(input.value); markDirty(); });
  if (multiline) {
    // Grow to fit the text so long paragraphs can be read without scrolling inside the box.
    input.addEventListener('input', () => fitTextarea(input));
    requestAnimationFrame(() => fitTextarea(input));
  }
  return el('div', { class: 'field' },
    el('label', { class: 'field__label', for: id, text: label }),
    hint ? el('p', { class: 'field__hint', text: hint }) : null,
    input,
    el('p', { class: 'field__error', 'data-error-for': name, role: 'alert' }));
}

function fitTextarea(area) {
  if (!area.offsetParent) return; // hidden tab: sized when the tab opens
  area.style.height = 'auto';
  area.style.height = `${area.scrollHeight + 2}px`;
}

const TEXT_HINT ='Blank line = new paragraph. Link: [text](https://…)';

function markDirty() {
  state.dirty = true;
  if (!state.saving) {
    $('save').disabled = false;
    setStatus('You have unsaved changes.');
  }
}

function setStatus(text, link) {
  const s = $('status');
  s.textContent = text;
  if (link) s.append(' ', el('a', { href: link.href, target: '_blank', rel: 'noopener' }, link.text));
}

// ---------- views ----------
function show(view) {
  for (const id of ['login', 'loading', 'editor']) $(id).hidden = id !== view;
  $('save-bar').hidden = view !== 'editor';
  $('user').hidden = view !== 'editor' || demo;
}

function selectTab(name) {
  for (const t of ['photos', 'projects', 'text']) {
    $(`tab-${t}`).setAttribute('aria-selected', String(t === name));
    $(`panel-${t}`).hidden = t !== name;
  }
  $(`panel-${name}`).querySelectorAll('textarea').forEach(fitTextarea);
}

function renderAll() {
  renderPhotos();
  renderProjects();
  renderText();
}

// ---------- photos ----------
function imgSrc(photo) {
  return state.previews.get(photo.id) || photo.thumb;
}

function renderPhotos() {
  const panel = $('panel-photos');
  panel.replaceChildren();
  const input = el('input', { type: 'file', accept: 'image/jpeg,image/png,image/webp,image/gif', multiple: true, onchange: (e) => addPhotos(e.target.files) });
  panel.append(
    el('h1', { text: 'Photos' }),
    renderPortrait(),
    el('h2', { text: 'Travel photos' }),
    el('p', { class: 'panel-intro', text: 'The three newest show on the home page; all of them on the Photos page. Photos are made smaller on this device, and their location data is removed before upload.' }),
    el('div', { class: 'photo-tools' },
      el('label', { class: 'button file-button' }, 'Add photos', input),
      el('p', { class: 'field__error', id: 'photo-error', role: 'alert' })),
  );
  const sorted = newestFirst(state.photos);
  if (!sorted.length) {
    panel.append(el('p', { class: 'empty-note empty-note--admin', text: 'No photos yet. Add some to get started.' }));
    return;
  }
  panel.append(el('ul', { class: 'admin-photos' }, sorted.map((photo) => {
    const index = state.photos.indexOf(photo);
    return el('li', { class: 'admin-photo' },
      cropControls(photo),
      state.newImages.has(photo.src.slice(1)) ? el('p', { class: 'new-tag', text: 'New · not saved yet' }) : null,
      field({ label: 'Place', value: photo.place, field: `photos[${index}].place`, required: false,
        onInput: (v) => { photo.place = v.trim() ? v : null; } }),
      field({ label: 'Date', type: 'date', value: photo.date, field: `photos[${index}].date`,
        onInput: (v) => { photo.date = v; } }),
      el('button', { type: 'button', class: 'link-button', onclick: () => removePhoto(photo) }, 'Delete photo'));
  })));
}

const CENTRE = { x: 50, y: 50 };

/**
 * A frame the photo fills; drag it (or use the arrow keys) to choose which part stays in view.
 * getFocus/setFocus read and store the position as {x, y} percentages.
 */
function cropFrame({ shape, label, src, alt, getFocus, setFocus, size }) {
  const img = el('img', { src, alt, draggable: 'false', loading: 'lazy' });
  const frame = el('div', { class: `crop crop--${shape}`, tabindex: '0', 'aria-label': `${label}. Drag the photo or use the arrow keys to move it.` }, img);
  let drag = null;
  frame.addEventListener('pointerdown', (e) => {
    frame.setPointerCapture(e.pointerId);
    drag = { x: e.clientX, y: e.clientY, focus: { ...getFocus() } };
    frame.classList.add('is-dragging');
  });
  frame.addEventListener('pointermove', (e) => {
    if (!drag) return;
    setFocus(dragFocus(drag.focus, e.clientX - drag.x, e.clientY - drag.y, {
      frameW: frame.clientWidth, frameH: frame.clientHeight,
      imageW: img.naturalWidth || size.width, imageH: img.naturalHeight || size.height,
    }));
  });
  const stop = () => { drag = null; frame.classList.remove('is-dragging'); };
  frame.addEventListener('pointerup', stop);
  frame.addEventListener('pointercancel', stop);
  frame.addEventListener('keydown', (e) => {
    const step = e.shiftKey ? 1 : 5;
    const move = { ArrowLeft: [-step, 0], ArrowRight: [step, 0], ArrowUp: [0, -step], ArrowDown: [0, step] }[e.key];
    if (!move) return;
    e.preventDefault();
    const f = getFocus();
    const clamp = (n) => Math.min(100, Math.max(0, n));
    setFocus({ x: clamp(f.x + move[0]), y: clamp(f.y + move[1]) });
  });
  return { frame, img };
}

/**
 * The photo in the two frame shapes the site uses (Photos page 4:5, home page 4:3).
 * Drag either one, or use the arrow keys, to choose which part stays in the frame.
 */
function cropControls(photo) {
  const frames = [];
  const getFocus = () => photo.focus || CENTRE;
  const apply = () => {
    const f = getFocus();
    for (const { img } of frames) img.style.objectPosition = `${f.x}% ${f.y}%`;
  };
  const setFocus = (f) => {
    const cur = getFocus();
    if (f.x === cur.x && f.y === cur.y) return;
    if (f.x === 50 && f.y === 50) delete photo.focus;
    else photo.focus = { x: f.x, y: f.y };
    apply();
    markDirty();
  };
  const common = {
    src: imgSrc(photo), alt: photo.place ? `Photo from ${photo.place}` : 'Travel photo',
    getFocus, setFocus, size: photo,
  };
  const card = cropFrame({ ...common, shape: 'card', label: 'Crop on the Photos page' });
  const home = cropFrame({ ...common, shape: 'home', label: 'Crop on the home page' });
  frames.push(card, home);
  apply();
  return el('div', { class: 'crop-controls' },
    card.frame,
    el('div', { class: 'crop-row' },
      home.frame,
      el('div', { class: 'crop-help' },
        el('p', { class: 'field__hint', text: 'Drag the photo to choose what stays in the frame. The small frame shows the home page.' }),
        el('button', { type: 'button', class: 'link-button', onclick: () => setFocus(CENTRE) }, 'Centre'))));
}

// ---------- profile photo ----------
// The photo beside your name on the home page. A new one is cropped to the frame on this device
// when you save, and replaces /mogdhopaul.webp and /mogdhopaul.jpeg.
function renderPortrait() {
  const p = state.portrait; // null, or { file, url, width, height, focus } for a newly chosen photo
  const input = el('input', { type: 'file', accept: 'image/jpeg,image/png,image/webp', onchange: (e) => choosePortrait(e.target.files[0]) });
  let frame;
  if (p) {
    frame = cropFrame({
      shape: 'portrait', label: 'Profile photo crop', src: p.url, alt: 'New profile photo', size: p,
      getFocus: () => p.focus,
      setFocus: (f) => {
        if (f.x === p.focus.x && f.y === p.focus.y) return;
        p.focus = f;
        frame.img.style.objectPosition = `${f.x}% ${f.y}%`;
        markDirty();
      },
    });
    frame.img.style.objectPosition = `${p.focus.x}% ${p.focus.y}%`;
  } else {
    // The live file; the commit id in the address skips a cached older photo after a save.
    const img = el('img', { src: `/mogdhopaul.jpeg?v=${state.sha || ''}`, alt: 'Current profile photo' });
    frame = { frame: el('div', { class: 'crop crop--portrait crop--still' }, img), img };
  }
  return el('section', { class: 'portrait-editor' },
    el('div', { class: 'portrait-editor__photo' }, frame.frame),
    el('div', { class: 'portrait-editor__text' },
      el('h2', { text: 'Profile photo' }),
      el('p', {
        class: 'field__hint',
        text: p
          ? 'Drag the photo to choose what shows in the frame, then save. It replaces the photo beside your name on the home page.'
          : 'The photo beside your name on the home page. It also shows when someone shares a link to your site.',
      }),
      p ? el('p', { class: 'new-tag', text: 'New · not saved yet' }) : null,
      el('div', { class: 'portrait-editor__actions' },
        el('label', { class: 'button file-button' }, p ? 'Choose another' : 'Change profile photo', input),
        p ? el('button', { type: 'button', class: 'link-button', onclick: () => setPortraitFocus(CENTRE) }, 'Centre') : null,
        p ? el('button', { type: 'button', class: 'link-button', onclick: cancelPortrait }, 'Keep the current photo') : null),
      el('p', { class: 'field__error', id: 'portrait-error', role: 'alert' })));
}

function setPortraitFocus(f) {
  state.portrait.focus = { ...f };
  renderPhotos();
  markDirty();
}

async function choosePortrait(file) {
  if (!file) return;
  if (!isSupportedImage(file)) {
    $('portrait-error').textContent = `${file.name}: this kind of file can't be used. Please use JPG or PNG.`;
    return;
  }
  try {
    const bitmap = await createImageBitmap(file, { imageOrientation: 'from-image' });
    const { width, height } = bitmap;
    bitmap.close();
    if (state.portrait) URL.revokeObjectURL(state.portrait.url);
    state.portrait = { file, url: URL.createObjectURL(file), width, height, focus: { ...CENTRE } };
  } catch {
    $('portrait-error').textContent = `${file.name}: couldn't open this photo.`;
    return;
  }
  renderPhotos();
  markDirty();
}

function cancelPortrait() {
  URL.revokeObjectURL(state.portrait.url);
  state.portrait = null;
  renderPhotos();
}

/** The two cropped files for a newly chosen profile photo, as [repo path, Blob]. */
async function portraitFiles() {
  const p = state.portrait;
  const small = await cropImage(p.file, p.focus, PORTRAIT_SIZE.small);
  const large = await cropImage(p.file, p.focus, PORTRAIT_SIZE.large, { jpeg: true });
  return [['mogdhopaul.webp', small], ['mogdhopaul.jpeg', large]];
}

async function addPhotos(files) {
  const problems = [];
  const today = new Date().toLocaleDateString('en-CA'); // YYYY-MM-DD in local time
  const taken = new Set(state.photos.map((p) => p.id));
  for (const file of files) {
    if (!isSupportedImage(file)) {
      problems.push(`${file.name}: this kind of file can't be used. Please use JPG or PNG.`);
      continue;
    }
    try {
      setStatus(`Preparing ${file.name}…`);
      const big = await resizeImage(file, 1200);
      const small = await resizeImage(file, 600);
      const id = newPhotoId(today, taken);
      taken.add(id);
      const src = `/photos/img/${id}-1200.${big.ext}`;
      const thumb = `/photos/img/${id}-600.${small.ext}`;
      state.newImages.set(src.slice(1), big.blob);
      state.newImages.set(thumb.slice(1), small.blob);
      state.previews.set(id, URL.createObjectURL(small.blob));
      state.photos.push({ id, place: null, date: today, src, thumb, width: big.width, height: big.height });
    } catch {
      problems.push(`${file.name}: couldn't open this photo.`);
    }
  }
  renderPhotos();
  if (problems.length) $('photo-error').textContent = problems.join(' ');
  markDirty();
}

function removePhoto(photo) {
  if (!confirm('Delete this photo from the site?')) return;
  state.photos = state.photos.filter((p) => p !== photo);
  state.newImages.delete(photo.src.slice(1));
  state.newImages.delete(photo.thumb.slice(1));
  renderPhotos();
  markDirty();
}

// ---------- skills ----------
// Each skill has a name and an icon from Iconify (a free icon library; single-colour sets only).
// The chosen icon's SVG is saved into skill-icons/ with the next save, so the site never loads it from Iconify.
const ICONIFY = 'https://api.iconify.design';
const SKILL_GROUP_LABELS = [['stack', 'Tech stack'], ['tools', 'Tools']];
const skillUi = {
  previews: new Map(), // icon id -> object URL, for icons picked since the page opened
  manual: new WeakSet(), // skills whose icon was chosen by hand: renaming keeps it
  added: new WeakSet(), // skills added since the page opened: their icon follows the name
  stamps: new WeakMap(), // skill -> its preview element, updated in place while typing
  timers: new WeakMap(),
  picker: null, // the skill whose icon picker is open
};

const iconFileUrl = (id) => { const [p, n] = id.split(':'); return `${ICONIFY}/${p}/${n}.svg`; };
const iconSrc = (id) => skillUi.previews.get(id) || `/${skillIconPath(id)}`;

async function searchIcons(query) {
  const res = await fetch(`${ICONIFY}/search?query=${encodeURIComponent(query)}&limit=64&prefixes=${ICON_SETS.join(',')}`);
  if (!res.ok) throw new Error(`icon search failed (${res.status})`);
  return rankIcons((await res.json()).icons || []);
}

async function findIcon(name) {
  for (const q of iconQueries(name)) {
    const found = await searchIcons(q);
    if (found.length) return found[0];
  }
  return null;
}

/** Download the icon so it is saved with the site, then use it. null = the group's default icon. */
async function useIcon(item, id) {
  if (id) {
    const res = await fetch(iconFileUrl(id));
    const svg = res.ok ? await res.text() : '';
    if (!svg.trim().startsWith('<svg')) throw new Error('icon download failed');
    const blob = new Blob([svg], { type: 'image/svg+xml' });
    state.newImages.set(skillIconPath(id), blob);
    if (!skillUi.previews.has(id)) skillUi.previews.set(id, URL.createObjectURL(blob));
  }
  item.icon = id;
  markDirty();
}

function skillStamp(item, group) {
  const id = item.icon || DEFAULT_SKILL_ICONS[group];
  return el('span', { class: 'skill__stamp skill-entry__stamp', 'aria-hidden': 'true' },
    el('span', { class: 'skill__icon', style: `--icon: url("${iconSrc(id)}")` }));
}

function refreshStamp(item, group) {
  const old = skillUi.stamps.get(item);
  if (!old) return;
  const fresh = skillStamp(item, group);
  old.replaceWith(fresh);
  skillUi.stamps.set(item, fresh);
}

/** New skills (and ones without an icon) get the best matching icon a moment after you stop typing. */
function autoIcon(item, group) {
  if (skillUi.manual.has(item) || !(skillUi.added.has(item) || item.icon == null)) return;
  clearTimeout(skillUi.timers.get(item));
  skillUi.timers.set(item, setTimeout(async () => {
    const name = item.name;
    try {
      const id = name.trim() ? await findIcon(name) : null;
      if (item.name !== name || skillUi.manual.has(item)) return; // typed on, or chosen by hand meanwhile
      await useIcon(item, id);
      refreshStamp(item, group);
    } catch { /* offline or the library is down: the default icon stays */ }
  }, 700));
}

function iconPicker(item, group) {
  const results = el('ul', { class: 'icon-picker__results' });
  const status = el('p', { class: 'field__hint', role: 'status' });
  const query = el('input', { type: 'search', id: 'icon-search', autocomplete: 'off', 'aria-label': 'Search icons' });
  query.value = item.name;
  const choose = async (id) => {
    status.textContent = 'Saving this icon…';
    try {
      await useIcon(item, id);
      skillUi.manual.add(item);
      skillUi.picker = null;
      renderSkills();
    } catch {
      status.textContent = 'Couldn’t download that icon. Check your connection and try again.';
    }
  };
  const run = async () => {
    results.replaceChildren();
    if (!query.value.trim()) return;
    status.textContent = 'Searching…';
    try {
      const found = await searchIcons(query.value.trim());
      status.textContent = found.length ? 'Pick the icon you like.' : 'No icons found. Try another word, for example the company name.';
      results.replaceChildren(...found.slice(0, 24).map((id) => el('li', {},
        el('button', { type: 'button', class: 'icon-picker__choice', title: id, 'aria-label': `Use icon ${id}`, onclick: () => choose(id) },
          el('span', { class: 'skill__icon', style: `--icon: url("${iconFileUrl(id)}")` })))));
    } catch {
      status.textContent = 'Couldn’t reach the icon library. Check your connection and try again.';
    }
  };
  const form = el('form', { class: 'icon-picker__search', onsubmit: (e) => { e.preventDefault(); run(); } },
    query, el('button', { type: 'submit', class: 'button button--quiet' }, 'Search'));
  requestAnimationFrame(() => { query.focus(); run(); });
  return el('div', { class: 'icon-picker' }, form, status, results,
    el('div', { class: 'entry__actions' },
      el('button', { type: 'button', class: 'link-button', onclick: () => choose(null) }, 'Use the plain default icon'),
      el('button', { type: 'button', class: 'link-button', onclick: () => { skillUi.picker = null; renderSkills(); } }, 'Close')));
}

function renderSkills() {
  const box = $('skills-editor');
  if (!box) return;
  const skills = state.site.skills;
  box.replaceChildren(...SKILL_GROUP_LABELS.map(([group, label]) => {
    const list = skills[group];
    return el('div', { class: 'skill-group' },
      el('h3', { text: label }),
      list.length ? null : el('p', { class: 'field__hint', text: 'Empty: this row is hidden on the site.' }),
      el('ol', { class: 'skill-list' }, list.map((item, i) => {
        const stamp = skillStamp(item, group);
        skillUi.stamps.set(item, stamp);
        return el('li', { class: 'skill-entry' },
          el('div', { class: 'skill-entry__main' },
            stamp,
            field({ label: 'Skill', value: item.name, field: `site.skills.${group}[${i}].name`,
              onInput: (v) => { item.name = v; autoIcon(item, group); } }),
            el('div', { class: 'entry__actions' },
              el('button', { type: 'button', class: 'button button--quiet', onclick: () => { skillUi.picker = skillUi.picker === item ? null : item; renderSkills(); } }, 'Change icon'),
              el('button', { type: 'button', class: 'button button--quiet', disabled: i === 0, onclick: () => moveItem(list, i, -1, renderSkills) }, 'Move up'),
              el('button', { type: 'button', class: 'button button--quiet', disabled: i === list.length - 1, onclick: () => moveItem(list, i, 1, renderSkills) }, 'Move down'),
              el('button', { type: 'button', class: 'button button--quiet danger', onclick: () => { list.splice(i, 1); markDirty(); renderSkills(); } }, 'Delete'))),
          el('p', { class: 'field__error', 'data-error-for': `site.skills.${group}[${i}].icon`, role: 'alert' }),
          skillUi.picker === item ? iconPicker(item, group) : null);
      })),
      el('button', { type: 'button', class: 'button', onclick: () => {
        const item = { name: '', icon: null };
        list.push(item);
        skillUi.added.add(item);
        markDirty();
        renderSkills();
        box.querySelectorAll(`[data-field="site.skills.${group}[${list.length - 1}].name"]`).forEach((n) => n.focus());
      } }, `Add to ${label.toLowerCase()}`));
  }));
}

// ---------- projects ----------
function renderProjects() {
  const panel = $('panel-projects');
  panel.replaceChildren(
    el('h1', { text: 'Projects' }),
    el('p', { class: 'panel-intro', text: `Tick “Show on home page” for exactly ${FEATURED_COUNT} projects.` }),
    el('p', { class: 'field__error', 'data-error-for': 'projects', role: 'alert' }),
  );
  const featuredCount = state.projects.filter((p) => p.featured).length;
  panel.append(el('ol', { class: 'entry-list' }, state.projects.map((p, i) => {
    const f = `projects[${i}]`;
    const box = el('input', { type: 'checkbox', id: `feat${i}`, checked: p.featured,
      disabled: !p.featured && featuredCount >= FEATURED_COUNT,
      onchange: (e) => { p.featured = e.target.checked; markDirty(); renderProjects(); } });
    return el('li', { class: 'entry' },
      el('div', { class: 'entry__head' },
        el('h3', { text: p.name || 'New project' }),
        el('div', { class: 'entry__actions' },
          el('button', { type: 'button', class: 'button button--quiet', disabled: i === 0, onclick: () => moveItem(state.projects, i, -1, renderProjects) }, 'Move up'),
          el('button', { type: 'button', class: 'button button--quiet', disabled: i === state.projects.length - 1, onclick: () => moveItem(state.projects, i, 1, renderProjects) }, 'Move down'),
          el('button', { type: 'button', class: 'button button--quiet danger', onclick: () => {
            if (confirm(`Delete ${p.name || 'this project'}?`)) { state.projects.splice(i, 1); markDirty(); renderProjects(); }
          } }, 'Delete'))),
      el('div', { class: 'entry__row' },
        field({ label: 'Name', value: p.name, field: `${f}.name`, onInput: (v) => { p.name = v; } }),
        field({ label: 'Link', type: 'url', value: p.url, field: `${f}.url`, onInput: (v) => { p.url = v.trim(); } })),
      field({ label: 'Description (Projects page)', value: p.description, field: `${f}.description`, multiline: true, onInput: (v) => { p.description = v; } }),
      field({ label: 'Short version for the home page (optional)', value: p.home_blurb, field: `${f}.home_blurb`, required: false, onInput: (v) => { p.home_blurb = v; } }),
      el('div', { class: 'entry__row' },
        field({ label: 'Language', value: p.language, field: `${f}.language`, onInput: (v) => { p.language = v; } }),
        field({ label: 'Section', value: p.group, field: `${f}.group`, options: [['windows', 'Windows, made calmer'], ['extensions', 'Chrome extensions'], ['browser', 'In the browser']], onInput: (v) => { p.group = v; } })),
      el('label', { class: 'field--check', for: `feat${i}` }, box, 'Show on home page'));
  })));
  panel.append(el('button', { type: 'button', class: 'button', onclick: () => {
    state.projects.push({ name: '', url: 'https://github.com/mogdho/', description: '', home_blurb: '', language: '', group: 'windows', featured: false });
    markDirty(); renderProjects();
  } }, 'Add project'));
}

function moveItem(list, i, step, rerender) {
  const j = i + step;
  [list[i], list[j]] = [list[j], list[i]];
  markDirty();
  rerender();
}

// ---------- text & links ----------
function renderText() {
  const s = state.site;
  const panel = $('panel-text');
  panel.replaceChildren(
    el('h1', { text: 'Text & links' }),
    el('div', { class: 'field-stack' },
      field({ label: 'Who you are (top of the home page, and Google’s description)', value: s.identity, field: 'site.identity', multiline: true, hint: 'Keep it under 160 characters.', onInput: (v) => { s.identity = v; } }),
      field({ label: 'Home: first line', value: s.home.lead, field: 'site.home.lead', multiline: true, onInput: (v) => { s.home.lead = v; } }),
      field({ label: 'Home: intro', value: s.home.text, field: 'site.home.text', multiline: true, hint: TEXT_HINT, onInput: (v) => { s.home.text = v; } }),
      field({ label: 'Home: video editing', value: s.home.video, field: 'site.home.video', multiline: true, hint: TEXT_HINT, onInput: (v) => { s.home.video = v; } })),
    el('h2', { text: 'Skills' }),
    el('p', { class: 'panel-intro', text: 'Shown on the home page above “Things I’ve built”. Each skill gets a matching icon automatically; use “Change icon” to pick another.' }),
    el('div', { id: 'skills-editor' }),
    el('h2', { text: 'About page' }),
    field({ label: 'Opening line', value: s.about.lead, field: 'site.about.lead', multiline: true, onInput: (v) => { s.about.lead = v; } }),
    el('ol', { class: 'entry-list' }, s.about.sections.map((sec, i) => el('li', { class: 'entry' },
      el('div', { class: 'entry__head' },
        el('h3', { text: sec.heading || 'New section' }),
        el('div', { class: 'entry__actions' },
          el('button', { type: 'button', class: 'button button--quiet', disabled: i === 0, onclick: () => moveItem(s.about.sections, i, -1, renderText) }, 'Move up'),
          el('button', { type: 'button', class: 'button button--quiet', disabled: i === s.about.sections.length - 1, onclick: () => moveItem(s.about.sections, i, 1, renderText) }, 'Move down'),
          el('button', { type: 'button', class: 'button button--quiet danger', onclick: () => {
            if (confirm(`Delete the section “${sec.heading}”?`)) { s.about.sections.splice(i, 1); markDirty(); renderText(); }
          } }, 'Delete'))),
      field({ label: 'Heading', value: sec.heading, field: `site.about.sections[${i}].heading`, onInput: (v) => { sec.heading = v; } }),
      field({ label: 'Text', value: sec.text, field: `site.about.sections[${i}].text`, multiline: true, hint: TEXT_HINT, onInput: (v) => { sec.text = v; } }))),
    ),
    el('button', { type: 'button', class: 'button', onclick: () => { s.about.sections.push({ heading: '', text: '' }); markDirty(); renderText(); } }, 'Add section'),
    el('h2', { text: 'Contact' }),
    el('div', { class: 'field-stack' },
      field({ label: 'WhatsApp link', type: 'url', value: s.contact.whatsapp, field: 'site.contact.whatsapp', hint: 'Looks like https://wa.me/+8801…', onInput: (v) => { s.contact.whatsapp = v.trim(); } }),
      field({ label: 'Email', type: 'email', value: s.contact.email, field: 'site.contact.email', onInput: (v) => { s.contact.email = v.trim(); } })),
    el('h2', { text: 'Profile links' }),
    el('ol', { class: 'entry-list' }, s.profiles.map((p, i) => el('li', { class: 'entry' },
      el('div', { class: 'entry__row' },
        field({ label: 'Name', value: p.label, field: `site.profiles[${i}].label`, onInput: (v) => { p.label = v; } }),
        field({ label: 'Link', type: 'url', value: p.url, field: `site.profiles[${i}].url`, onInput: (v) => { p.url = v.trim(); } })),
      el('div', { class: 'entry__actions' },
        el('button', { type: 'button', class: 'button button--quiet', disabled: i === 0, onclick: () => moveItem(s.profiles, i, -1, renderText) }, 'Move up'),
        el('button', { type: 'button', class: 'button button--quiet danger', onclick: () => { s.profiles.splice(i, 1); markDirty(); renderText(); } }, 'Delete'))))),
    el('button', { type: 'button', class: 'button', onclick: () => { s.profiles.push({ label: '', url: 'https://' }); markDirty(); renderText(); } }, 'Add link'),
  );
  renderSkills();
}

// ---------- errors ----------
function showErrors(errors) {
  for (const p of document.querySelectorAll('[data-error-for]')) p.textContent = '';
  for (const f of document.querySelectorAll('.has-error')) f.classList.remove('has-error');
  let first = null;
  for (const { field: name, message } of errors) {
    const slot = document.querySelector(`[data-error-for="${CSS.escape(name)}"]`);
    if (slot) {
      slot.textContent = message;
      slot.closest('.field')?.classList.add('has-error');
      first ??= slot;
    }
  }
  if (first) {
    const tab = first.closest('[role="tabpanel"]').id.replace('panel-', '');
    selectTab(tab);
    first.closest('.field, p')?.scrollIntoView({ behavior: 'smooth', block: 'center' });
  }
}

// ---------- save ----------
function base64FromText(text) {
  return base64FromBytes(new TextEncoder().encode(text));
}

function base64FromBytes(bytes) {
  let binary = '';
  for (let i = 0; i < bytes.length; i += 0x8000) binary += String.fromCharCode(...bytes.subarray(i, i + 0x8000));
  return btoa(binary);
}

async function save() {
  const content = { site: state.site, projects: state.projects, photos: state.photos };
  const errors = validateContent(content);
  showErrors(errors);
  if (errors.length) {
    setStatus(`Please fix ${errors.length === 1 ? 'the highlighted field' : `${errors.length} highlighted fields`} before saving.`);
    return;
  }
  state.saving = true;
  $('save').disabled = true;
  setStatus('Saving…');
  let sha = null;
  try {
    const files = filesToSave(content).map(({ path, text }) => ({ path, base64: base64FromText(text) }));
    const images = [...state.newImages];
    if (state.portrait) images.push(...await portraitFiles());
    for (const [path, blob] of images) {
      files.push({ path, base64: base64FromBytes(new Uint8Array(await blob.arrayBuffer())) });
    }
    sha = await state.repo.saveFiles(state.sha, files, 'admin: update site');
    state.sha = sha;
    state.original = structuredClone(content);
    state.newImages.clear();
    if (state.portrait) URL.revokeObjectURL(state.portrait.url);
    state.portrait = null;
    state.dirty = false;
    renderPhotos();
  } catch (err) {
    handleError(err);
  } finally {
    state.saving = false;
    $('save').disabled = !state.dirty;
  }
  // Outside the try: once the commit exists, nothing that goes wrong while checking can undo the save.
  if (sha) {
    const watch = ++publishWatch;
    await watchPublishing(state.repo, sha, {
      intervalMs: demo ? 1000 : 5000,
      onStatus: (s) => { if (watch === publishWatch) showPublishStatus(s); },
    });
  }
}

let publishWatch = 0;
function showPublishStatus(status) {
  const check = { href: ACTIONS_URL, text: 'Check progress' };
  if (status === 'publishing') setStatus('Saved. Publishing… (about two minutes)');
  else if (status === 'success') setStatus('Live — your changes are on mogdhopaul.com.');
  else if (status === 'failure') {
    setStatus('Saved, but publishing failed. The site still shows the previous version.', { href: ACTIONS_URL, text: 'See what went wrong' });
  } else if (status === 'unchecked') setStatus('Saved. Couldn’t check publishing; it usually takes about two minutes.', check);
  else setStatus('Saved. Publishing is taking longer than usual.', check);
}

function handleError(err) {
  if (err instanceof AuthError) {
    // Keep every edit: ask for the key again, then finish this save.
    forgetToken();
    state.resumeSave = true;
    show('login');
    $('login-error').textContent = `${err.message} Your changes are kept: log in again and they will be saved.`;
    return;
  }
  if (err instanceof ConflictError) {
    setStatus(err.message);
    setTimeout(() => load(), 2500);
    return;
  }
  setStatus(`Something went wrong: ${err.message}`);
}

// ---------- loading & login ----------
function demoRepo() {
  return {
    headSha: async () => 'demo',
    readJson: async (path) => (await fetch(`/${path}`)).json(),
    saveFiles: async () => new Promise((r) => setTimeout(() => r('demo-2'), 800)),
    buildStatus: async () => 'success',
  };
}

async function load() {
  show('loading');
  try {
    state.sha = await state.repo.headSha();
    const [site, projects, photos] = await Promise.all(
      ['site', 'projects', 'photos'].map((n) => state.repo.readJson(`content/${n}.json`, state.sha)));
    Object.assign(state, { site, projects, photos, dirty: false });
    state.original = structuredClone({ site, projects, photos });
    state.newImages.clear();
    state.portrait = null;
    renderAll();
    show('editor');
    const tab = new URLSearchParams(location.search).get('tab');
    if (['photos', 'projects', 'text'].includes(tab)) selectTab(tab);
    document.fonts?.ready.then(() => document.querySelectorAll('textarea').forEach(fitTextarea));
    setStatus('No changes yet.');
    $('save').disabled = true;
  } catch (err) {
    if (err instanceof AuthError) {
      logout();
      $('login-error').textContent = err.message;
    } else {
      show('login');
      $('login-error').textContent = `Couldn't load the site: ${err.message}`;
    }
  }
}

function forgetToken() {
  try { localStorage.removeItem(TOKEN_KEY); } catch { /* storage unavailable */ }
  state.repo = null;
  $('token').value = '';
}

function logout() {
  forgetToken();
  state.resumeSave = false;
  show('login');
}

function start() {
  for (const t of ['photos', 'projects', 'text']) $(`tab-${t}`).addEventListener('click', () => selectTab(t));
  document.querySelector('.tabs').addEventListener('keydown', (e) => {
    if (!['ArrowLeft', 'ArrowRight'].includes(e.key)) return;
    const tabs = [...document.querySelectorAll('[role="tab"]')];
    const i = tabs.indexOf(document.activeElement);
    const next = tabs[(i + (e.key === 'ArrowRight' ? 1 : tabs.length - 1)) % tabs.length];
    next.focus();
    next.click();
  });
  const refit = () => document.querySelectorAll('textarea').forEach(fitTextarea);
  document.fonts?.ready.then(refit);
  window.addEventListener('resize', refit);
  $('save').addEventListener('click', save);
  $('logout').addEventListener('click', () => {
    if (state.dirty && !confirm('You have unsaved changes. Log out anyway?')) return;
    logout();
  });
  $('login-form').addEventListener('submit', (e) => {
    e.preventDefault();
    const token = $('token').value.trim();
    if (!token) return;
    $('login-error').textContent = '';
    try { localStorage.setItem(TOKEN_KEY, token); } catch { /* storage unavailable: works for this visit */ }
    state.repo = new Repo({ token });
    if (state.resumeSave) {
      state.resumeSave = false;
      show('editor');
      save();
    } else {
      load();
    }
  });
  window.addEventListener('beforeunload', (e) => {
    if (state.dirty) e.preventDefault();
  });

  if (demo) {
    $('demo-banner').hidden = false;
    state.repo = demoRepo();
    load();
    return;
  }
  let token = null;
  try { token = localStorage.getItem(TOKEN_KEY); } catch { /* storage unavailable */ }
  if (token) {
    state.repo = new Repo({ token });
    load();
  } else {
    show('login');
  }
}

start();
