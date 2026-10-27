// Small GitHub REST client for the admin: read content, save changes as one commit, check publishing.

export class AuthError extends Error {}
export class ConflictError extends Error {}
export class GitHubError extends Error {}

const API = 'https://api.github.com';

export class Repo {
  constructor({ token, owner = 'mogdho', repo = 'mogdhopaul', branch = 'main', fetch = globalThis.fetch }) {
    this.token = token;
    this.base = `${API}/repos/${owner}/${repo}`;
    this.branch = branch;
    this.fetch = fetch;
  }

  async request(method, path, { body, accept = 'application/vnd.github+json', conflictOn422 = false } = {}) {
    const res = await this.fetch(`${this.base}${path}`, {
      method,
      headers: {
        Authorization: `Bearer ${this.token}`,
        Accept: accept,
        'X-GitHub-Api-Version': '2022-11-28',
        ...(body ? { 'Content-Type': 'application/json' } : {}),
      },
      body: body ? JSON.stringify(body) : undefined,
    });
    if (res.status === 401 || res.status === 403) {
      throw new AuthError("That key didn't work. Check it hasn't expired and has access to mogdhopaul.");
    }
    if (conflictOn422 && res.status === 422) {
      throw new ConflictError('The site changed since you opened the admin. Reloading.');
    }
    if (!res.ok) {
      let message = '';
      try { message = (await res.json()).message || ''; } catch { /* body was not JSON */ }
      throw new GitHubError(`GitHub said ${res.status}${message ? `: ${message}` : ''}`);
    }
    return res.json();
  }

  async headSha() {
    return (await this.request('GET', `/git/ref/heads/${this.branch}`)).object.sha;
  }

  async readJson(path, ref) {
    return this.request('GET', `/contents/${path}?ref=${encodeURIComponent(ref)}`, {
      accept: 'application/vnd.github.raw+json',
    });
  }

  /** files: [{path, base64}] to add/replace, [{path, delete: true}] to remove. Returns the new commit sha. */
  async commitFiles(baseSha, files, message) {
    const entries = [];
    for (const f of files) {
      if (f.delete) {
        entries.push({ path: f.path, mode: '100644', type: 'blob', sha: null });
      } else {
        const blob = await this.request('POST', '/git/blobs', { body: { content: f.base64, encoding: 'base64' } });
        entries.push({ path: f.path, mode: '100644', type: 'blob', sha: blob.sha });
      }
    }
    const baseCommit = await this.request('GET', `/git/commits/${baseSha}`);
    const tree = await this.request('POST', '/git/trees', { body: { base_tree: baseCommit.tree.sha, tree: entries } });
    const commit = await this.request('POST', '/git/commits', {
      body: { message, tree: tree.sha, parents: [baseSha] },
    });
    await this.request('PATCH', `/git/refs/heads/${this.branch}`, {
      body: { sha: commit.sha, force: false }, conflictOn422: true,
    });
    return commit.sha;
  }

  /** 'pending' | 'success' | 'failure' | 'none' for the "Build site" run on this commit. */
  async buildStatus(sha) {
    const { workflow_runs: runs = [] } = await this.request('GET', `/actions/runs?head_sha=${encodeURIComponent(sha)}`);
    const run = runs.find((r) => r.name === 'Build site');
    if (!run) return 'none';
    if (run.status !== 'completed') return 'pending';
    return run.conclusion === 'success' ? 'success' : 'failure';
  }
}
