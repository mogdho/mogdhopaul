import test from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import {
  checkText, isAllowedUrl, validateContent, targetSize, isSupportedImage,
  newPhotoId, photoChanges, toJson,
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
test('targetSize scales down', () => assert.deepEqual(targetSize(6000, 4000, 1200), { width: 1200, height: 800 }));
test('targetSize never upscales', () => assert.deepEqual(targetSize(800, 600, 1200), { width: 800, height: 600 }));
test('isSupportedImage refuses HEIC', () => {
  assert.equal(isSupportedImage({ type: 'image/heic' }), false);
  assert.equal(isSupportedImage({ type: 'image/jpeg' }), true);
});
test('newPhotoId is unique', () => {
  const taken = new Set(['2025-05-14-0000']);
  assert.equal(newPhotoId('2025-05-14', taken, seq(0, 0.5)), '2025-05-14-8000');
});
test('photoChanges lists files of removed photos', () =>
  assert.deepEqual(photoChanges([p('a'), p('b')], [p('b')]).deletePaths,
    ['photos/img/a-1200.webp', 'photos/img/a-600.webp']));
test('toJson matches the repo format', () => assert.equal(toJson({ a: 1 }), '{\n  "a": 1\n}\n'));
