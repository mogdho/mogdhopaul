import test from 'node:test';
import assert from 'node:assert/strict';
import { Repo, AuthError, ConflictError, GitHubError } from '../../admin/github.js';

function fakeFetch(responses) {
  const calls = [];
  const fn = async (url, opts = {}) => {
    calls.push({ method: opts.method || 'GET', url, headers: opts.headers || {}, body: opts.body ? JSON.parse(opts.body) : null });
    const [status, body] = responses.shift() ?? [500, { message: 'no response queued' }];
    return { ok: status >= 200 && status < 300, status, json: async () => body, text: async () => JSON.stringify(body) };
  };
  fn.calls = calls;
  return fn;
}
const API = 'https://api.github.com/repos/mogdho/mogdhopaul';

test('token sent as Bearer with API version', async () => {
  const fetch = fakeFetch([[200, { object: { sha: 'abc' } }]]);
  assert.equal(await new Repo({ token: 'T', fetch }).headSha(), 'abc');
  assert.equal(fetch.calls[0].url, `${API}/git/ref/heads/main`);
  assert.equal(fetch.calls[0].headers.Authorization, 'Bearer T');
  assert.equal(fetch.calls[0].headers['X-GitHub-Api-Version'], '2022-11-28');
});

test('401 raises AuthError', async () => {
  const repo = new Repo({ token: 'bad', fetch: fakeFetch([[401, { message: 'Bad credentials' }]]) });
  await assert.rejects(repo.headSha(), AuthError);
});

test('other errors raise GitHubError with status', async () => {
  const repo = new Repo({ token: 'T', fetch: fakeFetch([[500, { message: 'boom' }]]) });
  await assert.rejects(repo.headSha(), (e) => e instanceof GitHubError && /500/.test(e.message));
});

test('readJson asks for raw content at ref', async () => {
  const fetch = fakeFetch([[200, { identity: 'x' }]]);
  assert.deepEqual(await new Repo({ token: 'T', fetch }).readJson('content/site.json', 'abc'), { identity: 'x' });
  assert.equal(fetch.calls[0].url, `${API}/contents/content/site.json?ref=abc`);
  assert.equal(fetch.calls[0].headers.Accept, 'application/vnd.github.raw+json');
});

test('commitFiles makes one commit in order', async () => {
  const fetch = fakeFetch([
    [201, { sha: 'blob1' }],
    [200, { tree: { sha: 'tree0' } }],
    [201, { sha: 'tree1' }],
    [201, { sha: 'commit1' }],
    [200, { object: { sha: 'commit1' } }],
  ]);
  const sha = await new Repo({ token: 'T', fetch }).commitFiles('base', [
    { path: 'content/site.json', base64: 'e30K' },
    { path: 'photos/img/a-600.webp', delete: true },
  ], 'admin: update site');
  assert.equal(sha, 'commit1');
  assert.deepEqual(fetch.calls.map((c) => `${c.method} ${c.url.replace(API, '')}`), [
    'POST /git/blobs', 'GET /git/commits/base', 'POST /git/trees', 'POST /git/commits', 'PATCH /git/refs/heads/main',
  ]);
  assert.deepEqual(fetch.calls[0].body, { content: 'e30K', encoding: 'base64' });
  assert.deepEqual(fetch.calls[2].body, { base_tree: 'tree0', tree: [
    { path: 'content/site.json', mode: '100644', type: 'blob', sha: 'blob1' },
    { path: 'photos/img/a-600.webp', mode: '100644', type: 'blob', sha: null },
  ] });
  assert.deepEqual(fetch.calls[3].body, { message: 'admin: update site', tree: 'tree1', parents: ['base'] });
  assert.deepEqual(fetch.calls[4].body, { sha: 'commit1', force: false });
});

test('stale ref raises ConflictError', async () => {
  const fetch = fakeFetch([
    [200, { tree: { sha: 'tree0' } }], [201, { sha: 'tree1' }], [201, { sha: 'c1' }],
    [422, { message: 'Update is not a fast forward' }],
  ]);
  await assert.rejects(new Repo({ token: 'T', fetch }).commitFiles('base', [{ path: 'x', delete: true }], 'm'), ConflictError);
});

test('buildStatus maps the Build site run', async () => {
  const runs = (r) => [200, { workflow_runs: r }];
  const cases = [
    [[{ name: 'Build site', status: 'in_progress', conclusion: null }], 'pending'],
    [[{ name: 'Build site', status: 'completed', conclusion: 'success' }], 'success'],
    [[{ name: 'Build site', status: 'completed', conclusion: 'failure' }], 'failure'],
    [[{ name: 'pages build and deployment', status: 'completed', conclusion: 'success' }], 'none'],
    [[], 'none'],
  ];
  for (const [r, expected] of cases) {
    const fetch = fakeFetch([runs(r)]);
    assert.equal(await new Repo({ token: 'T', fetch }).buildStatus('abc'), expected);
    assert.equal(fetch.calls[0].url, `${API}/actions/runs?head_sha=abc`);
  }
});

test('requests skip the browser cache so a fresh head is always seen', async () => {
  let seen;
  const fetch = async (url, opts) => { seen = opts; return { ok: true, status: 200, json: async () => ({ object: { sha: 'a' } }) }; };
  await new Repo({ token: 'T', fetch }).headSha();
  assert.equal(seen.cache, 'no-store');
});

const commitChain = (sha) => [
  [201, { sha: 'blob1' }], [200, { tree: { sha: 'tree0' } }], [201, { sha: 'tree1' }],
  [201, { sha }], [200, { object: { sha } }],
];
const FILES = [{ path: 'content/site.json', base64: 'e30K' }];
const route = (calls) => calls.map((c) => `${c.method} ${c.url.replace(API, '')}`);

test('saveFiles commits on the loaded commit when nothing moved', async () => {
  const fetch = fakeFetch([[200, { object: { sha: 'loaded' } }], ...commitChain('c1')]);
  assert.equal(await new Repo({ token: 'T', fetch }).saveFiles('loaded', FILES, 'm'), 'c1');
  assert.deepEqual(fetch.calls[4].body.parents, ['loaded']);
});

test('saveFiles builds on the bot page rebuild instead of conflicting', async () => {
  const fetch = fakeFetch([
    [200, { object: { sha: 'bot' } }],
    [200, { status: 'ahead', files: [{ filename: 'index.html' }, { filename: 'photos/img/old-600.webp' }] }],
    ...commitChain('c2'),
  ]);
  assert.equal(await new Repo({ token: 'T', fetch }).saveFiles('mine', FILES, 'm'), 'c2');
  assert.equal(route(fetch.calls)[1], 'GET /compare/mine...bot');
  assert.deepEqual(fetch.calls[5].body.parents, ['bot']);
});

test('saveFiles stops when content changed elsewhere', async () => {
  const fetch = fakeFetch([
    [200, { object: { sha: 'other' } }],
    [200, { status: 'ahead', files: [{ filename: 'content/site.json' }] }],
  ]);
  await assert.rejects(new Repo({ token: 'T', fetch }).saveFiles('mine', FILES, 'm'), ConflictError);
  assert.equal(fetch.calls.length, 2);
});

test('saveFiles stops when history was rewritten', async () => {
  const fetch = fakeFetch([[200, { object: { sha: 'other' } }], [200, { status: 'diverged', files: [] }]]);
  await assert.rejects(new Repo({ token: 'T', fetch }).saveFiles('mine', FILES, 'm'), ConflictError);
});

test('saveFiles retries when the bot lands during the save', async () => {
  const fetch = fakeFetch([
    [200, { object: { sha: 'mine' } }],
    [201, { sha: 'blob1' }], [200, { tree: { sha: 'tree0' } }], [201, { sha: 'tree1' }], [201, { sha: 'lost' }],
    [422, { message: 'Update is not a fast forward' }],
    [200, { object: { sha: 'bot' } }],
    [200, { status: 'ahead', files: [{ filename: 'about/index.html' }] }],
    ...commitChain('c3'),
  ]);
  assert.equal(await new Repo({ token: 'T', fetch }).saveFiles('mine', FILES, 'm'), 'c3');
});
