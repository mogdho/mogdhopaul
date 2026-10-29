import test from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import {
  checkText, isAllowedUrl, validateContent, targetSize, isSupportedImage,
  newPhotoId, toJson, filesToSave, watchPublishing, isFocus, dragFocus,
} from '../../admin/core.js';

const load = (name) => JSON.parse(readFileSync(new URL(`../../content/${name}.json`, import.meta.url), 'utf8'));
const content = () => ({ site: load('site'), projects: load('projects'), photos: load('photos') });
const withFeatured = (n) => { const c = content(); c.projects.forEach((p, i) => { p.featured = i < n; }); return c; };
const withProfileUrl = (url) => { const c = content(); c.site.profiles[0].url = url; return c; };
const p = (id) => ({ id, place: null, date: '2025-05-14', src: `/photos/img/${id}-1200.webp`, thumb: `/photos/img/${id}-600.webp`, width: 1200, height: 900 });
const seq = (...values) => { let i = 0; return () => values[i++ % values.length]; };

test('checkText rejects banned spelling', () => assert.match(checkText('Mogdha here'), /name/i));
test('checkText rejects Bengali letters and digits', () => {
  assert.match(checkText('প্যারিস'), /English/);
  assert.match(checkText("Cox's Bazar ২০২৪"), /English/);
});
test('checkText rejects javascript link', () => assert.match(checkText('[x](javascript:alert(1))'), /link/i));
test('checkText accepts plain text and allowed links', () => {
  assert.equal(checkText('my [photos](/photos/) and [mail](mailto:a@b.c) and [site](https://x.y/)'), null);
  assert.equal(checkText('Café in Paris'), null);
});
test('isAllowedUrl', () => {
  assert.equal(isAllowedUrl('https://github.com/mogdho'), true);
  assert.equal(isAllowedUrl('/photos/'), true);
  assert.equal(isAllowedUrl('javascript:alert(1)'), false);
  assert.equal(isAllowedUrl('https://a.b/"x'), false);
});
test('repo content is valid', () => assert.deepEqual(validateContent(content()), []));
test('validateContent needs exactly three featured', () =>
  assert.ok(validateContent(withFeatured(2)).some((e) => e.field === 'projects')));
test('validateContent names the field', () =>
  assert.deepEqual(validateContent(withProfileUrl('ftp://x')).map((e) => e.field), ['site.profiles[0].url']));
test('validateContent flags long identity line', () => {
  const c = content(); c.site.identity = 'x'.repeat(161);
  assert.deepEqual(validateContent(c).map((e) => e.field), ['site.identity']);
});
test('validateContent checks photo date and place', () => {
  const c = content(); c.photos = [{ ...p('a'), date: '14/05/2025' }, { ...p('b'), place: 'Mugdho house' }];
  assert.deepEqual(validateContent(c).map((e) => e.field), ['photos[0].date', 'photos[1].place']);
});
test('isFocus accepts whole percentages only', () => {
  assert.equal(isFocus({ x: 0, y: 100 }), true);
  for (const bad of [null, { x: 101, y: 0 }, { x: 1.5, y: 0 }, { x: 50 }, { x: 1, y: 2, z: 3 }, '50% 50%']) {
    assert.equal(isFocus(bad), false, JSON.stringify(bad));
  }
});
test('validateContent flags a broken crop position', () => {
  const c = content(); c.photos = [{ ...p('a'), focus: { x: 120, y: 50 } }, { ...p('b'), focus: { x: 20, y: 70 } }];
  assert.deepEqual(validateContent(c).map((e) => e.field), ['photos[0].focus']);
});
test('dragFocus moves only the side that overflows', () => {
  // Landscape photo in a tall frame: it overflows left/right only.
  const box = { frameW: 400, frameH: 500, imageW: 1200, imageH: 900 };
  // Scaled to 500 high -> 667 wide, 267px to spare. Dragging right 133px shows more of the left.
  assert.deepEqual(dragFocus({ x: 50, y: 50 }, 133.5, 40, box), { x: 0, y: 50 });
  assert.deepEqual(dragFocus({ x: 50, y: 50 }, -1000, 0, box), { x: 100, y: 50 });
});
test('targetSize scales down',() => assert.deepEqual(targetSize(6000, 4000, 1200), { width: 1200, height: 800 }));
test('targetSize never upscales', () => assert.deepEqual(targetSize(800, 600, 1200), { width: 800, height: 600 }));
test('isSupportedImage refuses HEIC', () => {
  assert.equal(isSupportedImage({ type: 'image/heic' }), false);
  assert.equal(isSupportedImage({ type: 'image/jpeg' }), true);
});
test('newPhotoId is unique', () => {
  const taken = new Set(['2025-05-14-0000']);
  assert.equal(newPhotoId('2025-05-14', taken, seq(0, 0.5)), '2025-05-14-8000');
});
test('toJson matches the repo format', () => assert.equal(toJson({ a: 1 }), '{\n  "a": 1\n}\n'));

test('identity must contain the owner name', () => {
  const c = content(); c.site.identity = 'A developer from Bangladesh who builds small web tools.';
  assert.ok(validateContent(c).some((e) => e.field === 'site.identity'));
});
test('identity must not name a video role', () => {
  const c = content(); c.site.identity = 'Mogdho Paul is a video editor from Bangladesh.';
  assert.ok(validateContent(c).some((e) => e.field === 'site.identity'));
});
test('checkText rejects emoji', () => assert.match(checkText('Hello \u{1F600}'), /emoji/i));
test('checkText rejects AI-Assisted', () => assert.match(checkText('An AI-Assisted tool'), /AI-Assisted/));
test('checkText flags typed HTML', () => assert.match(checkText('I am <b>bold</b>'), /HTML/));
test('checkText allows a plain less-than sign', () => assert.equal(checkText('Loads in < 1 second, 3<4.'), null));

test('filesToSave writes the three content files and never deletes images', () => {
  const c = content();
  c.photos = [];
  const files = filesToSave(c);
  assert.deepEqual(files.map((f) => f.path), ['content/site.json', 'content/projects.json', 'content/photos.json']);
  assert.ok(files.every((f) => !f.delete && typeof f.text === 'string'));
  assert.equal(files[2].text, '[]\n');
});

const clock = () => { let t = 0; return { now: () => t, sleep: async (ms) => { t += ms; } }; };
const repoWith = (...results) => ({
  buildStatus: async () => { const r = results.shift(); if (r instanceof Error) throw r; return r; },
});

test('watchPublishing reports live once the build succeeds', async () => {
  const seen = [];
  const out = await watchPublishing(repoWith('none', 'pending', 'success'), 'sha', { ...clock(), onStatus: (s) => seen.push(s) });
  assert.equal(out, 'success');
  assert.deepEqual(seen, ['publishing', 'success']);
});

test('watchPublishing reports failure', async () => {
  assert.equal(await watchPublishing(repoWith('failure'), 'sha', { ...clock(), onStatus() {} }), 'failure');
});

test('watchPublishing never throws: a key without Actions access means unchecked, not a failed save', async () => {
  const seen = [];
  const out = await watchPublishing(repoWith(new Error('403')), 'sha', { ...clock(), onStatus: (s) => seen.push(s) });
  assert.equal(out, 'unchecked');
  assert.deepEqual(seen, ['publishing', 'unchecked']);
});

test('watchPublishing gives up after five minutes', async () => {
  const forever = { buildStatus: async () => 'pending' };
  assert.equal(await watchPublishing(forever, 'sha', { ...clock(), onStatus() {} }), 'timeout');
});
