import test, { beforeEach } from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import ts from 'typescript';

const source = readFileSync(new URL('../src/api.ts', import.meta.url), 'utf8');
const { outputText } = ts.transpileModule(source, { compilerOptions: { module: ts.ModuleKind.ESNext, target: ts.ScriptTarget.ES2020 } });
const { api, login, AUTH_REQUIRED_EVENT } = await import(`data:text/javascript;base64,${Buffer.from(outputText).toString('base64')}`);
let store;
let signInEvents;
beforeEach(() => {
  store = new Map([['token', 'old-demo-token'], ['role', 'auditor'], ['display_name', 'Demo auditor']]);
  globalThis.localStorage = { getItem: key => store.get(key) ?? null, setItem: (key, value) => store.set(key, value), removeItem: key => store.delete(key) };
  globalThis.window = new EventTarget();
  signInEvents = 0;
  window.addEventListener(AUTH_REQUIRED_EVENT, () => signInEvents++);
});
const json = (body, status = 200) => new Response(JSON.stringify(body), { status, headers: { 'content-type': 'application/json' } });

test('a rejected session clears stored login and asks the app to show sign-in', async () => {
  globalThis.fetch = async () => json({ detail: 'Could not validate credentials' }, 401);
  await assert.rejects(api.listEngagements(), /Please sign in again/);
  assert.equal(store.size, 0);
  assert.equal(signInEvents, 1);
});

test('wrong login details show a helpful error without triggering a redirect loop', async () => {
  globalThis.fetch = async (url, options) => {
    assert.equal(url, '/api/auth/login');
    assert.equal(options.headers.Authorization, undefined);
    return json({ detail: 'Incorrect username or password' }, 401);
  };
  await assert.rejects(login('auditor', 'wrong'), /demo accounts shown below/);
  assert.equal(signInEvents, 0);
});

test('a delayed rejected request cannot clear a fresh sign-in', async () => {
  let respond;
  globalThis.fetch = () => new Promise(resolve => { respond = resolve; });
  const pending = api.listEngagements();
  localStorage.setItem('token', 'fresh-demo-token');
  respond(json({ detail: 'Expired' }, 401));
  await assert.rejects(pending);
  assert.equal(localStorage.getItem('token'), 'fresh-demo-token');
  assert.equal(signInEvents, 0);
});

test('a role restriction keeps the valid session', async () => {
  globalThis.fetch = async () => json({ detail: 'Reviewer access required' }, 403);
  await assert.rejects(api.actOnReview('sample-task', 'approve'), /Reviewer access required/);
  assert.equal(localStorage.getItem('token'), 'old-demo-token');
  assert.equal(signInEvents, 0);
});

test('successful sign-in replaces the stale token', async () => {
  globalThis.fetch = async () => json({ access_token: 'fresh-demo-token', role: 'reviewer', display_name: 'Demo reviewer' });
  await login('reviewer', 'reviewer123');
  assert.equal(localStorage.getItem('token'), 'fresh-demo-token');
  assert.equal(localStorage.getItem('role'), 'reviewer');
});

test('both report formats include authentication and return usable content', async () => {
  globalThis.fetch = async (url, options) => {
    assert.equal(options.headers.Authorization, 'Bearer old-demo-token');
    return url.endsWith('.json') ? json({ sample: true }) : new Response('<h1>Sample audit</h1>', { headers: { 'content-type': 'text/html' } });
  };
  assert.deepEqual(await api.exportReport('sample', 'json'), { sample: true });
  assert.equal(await api.exportReport('sample', 'html'), '<h1>Sample audit</h1>');
});
