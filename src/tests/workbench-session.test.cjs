'use strict';
const {test} = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const path = require('node:path');

const source = fs.readFileSync(path.join(__dirname, '../workbench/ui/app.js'), 'utf8');
const key = 'blueprint.workbench.session.v1';

// Execute the actual UI script in fresh page contexts with the same tab storage.
// This is a DOM/API unit harness, not a real browser or live-provider test.
class Element {
  constructor() {
    this.value = ''; this.hidden = false; this.children = []; this.handlers = {};
    this.classList = {toggle() {}, add() {}, remove() {}};
  }
  append(...items) { this.children.push(...items); }
  replaceChildren(...items) { this.children = items; }
  setAttribute() {}
  removeAttribute() {}
  addEventListener(name, fn) { this.handlers[name] = fn; }
  querySelector() { return new Element(); }
  focus() {}
}
function storage() {
  const values = new Map();
  return {values, getItem: k => values.get(k) || null, setItem: (k, v) => values.set(k, v), removeItem: k => values.delete(k)};
}
async function boot(store, {expired = false, offline = false} = {}) {
  const elements = new Map();
  const $ = id => {
    if (!elements.has(id)) elements.set(id, new Element());
    return elements.get(id);
  };
  $('max-tokens').value = '8192'; $('context-window').value = '65536';
  const calls = [];
  const context = vm.createContext({
    document: {getElementById: $, createElement: () => new Element(), querySelectorAll: () => []},
    sessionStorage: store,
    fetch: async (url, options) => {
      calls.push({url, options});
      if (offline) throw new Error('Offline');
      if (expired && url === '/api/session') return {ok: false, status: 401, text: async () => JSON.stringify({detail: 'Pair again'})};
      const payloads = {
        '/api/session': {connected: true, provider: 'gemini', model: 'test-gemini', csrf: 'server-csrf'},
        '/api/solutions': [{name: 'example-solution', title: 'Example', tasks: 0, completed: 0}],
        '/api/solutions/example-solution': {solution: 'example-solution', files: [], tasks: []},
        '/api/catalog': {items: [], modules: []},
        '/api/jobs': [],
        '/api/jobs/run-1': {id: 'run-1', kind: 'advice', state: 'succeeded', events: [], result: {}},
        '/api/system': {os: 'Windows', cpu: 'test CPU', logical_cpus: 8, architecture: 'AMD64', ram_gb: 32, available_ram_gb: 16, gpu: 'test GPU', disk_free_gb: 100, tools: {docker: true, docker_ready: true, runner_ready: false, ollama: true, ollama_ready: true}, installed_models: [], local_models: [{id: 'qwen3:4b', download_gb: 2.5, working_gb: 6, purpose: 'Local test model', fits_estimate: true, available_now_estimate: true}]},
      };
      if (!(url in payloads)) throw new Error('Unexpected request: ' + url);
      return {ok: true, status: 200, text: async () => JSON.stringify(payloads[url])};
    },
    setTimeout: () => 1, clearTimeout() {}, console, URL,
  });
  await vm.runInContext(source, context);
  const ui = vm.runInContext('({state, unlock, show, selectSolution, syncConnection, rememberSession, lock, setupState})', context);
  return {ui, $, calls};
}

test('refresh restores the same authenticated Gemini session, solution and page without re-pairing', async () => {
  const store = storage();
  const first = await boot(store);
  await first.ui.unlock({session_token: 'short-lived-session', csrf: 'server-csrf', connected: true, provider: 'gemini', model: 'test-gemini'});
  first.$('api-key').value = 'test-provider-secret-must-not-be-saved';
  first.$('pair-token').value = 'initial-pairing-token-must-not-be-saved';
  first.$('max-tokens').value = '12000';
  await first.ui.selectSolution('example-solution');
  await first.ui.show('setup');
  const second = await boot(store);
  assert.equal(second.ui.state.connected, true);
  assert.equal(second.ui.state.selected, 'example-solution');
  assert.equal(second.ui.state.view, 'setup');
  assert.equal(second.$('provider').value, 'gemini');
  assert.equal(second.$('model').value, 'test-gemini');
  assert.equal(second.$('max-tokens').value, 12000);
  assert.equal(second.$('workspace').hidden, false);
  assert.equal(second.calls[0].options.headers.Authorization, 'Bearer short-lived-session');
  assert.ok(second.calls.every(call => !call.options.method || call.options.method === 'GET'));
  assert.ok(second.calls.every(call => call.options.credentials === 'omit'));
  assert.ok(!store.getItem(key).includes('must-not-be-saved'));
  assert.ok(!store.getItem(key).includes('server-csrf'));
});

test('run selection is restored from server history after refresh', async () => {
  const store = storage();
  store.setItem(key, JSON.stringify({token: 'short-lived-session', view: 'runs', activeRun: 'run-1'}));
  const page = await boot(store);
  assert.equal(page.ui.state.activeRun, 'run-1');
  assert.ok(page.calls.some(call => call.url === '/api/jobs/run-1'));
});

test('expired sessions clear browser credentials and show pairing', async () => {
  const store = storage();
  store.setItem(key, JSON.stringify({token: 'expired-session', view: 'setup'}));
  const page = await boot(store, {expired: true});
  assert.equal(store.getItem(key), null);
  assert.equal(page.ui.state.sessionToken, '');
  assert.equal(page.$('pairing').hidden, false);
  assert.equal(page.$('workspace').hidden, true);
});

test('temporary network failures preserve the session for a later refresh', async () => {
  const store = storage();
  store.setItem(key, JSON.stringify({token: 'short-lived-session', view: 'setup'}));
  await boot(store, {offline: true});
  assert.ok(store.getItem(key));
  const recovered = await boot(store);
  assert.equal(recovered.ui.state.connected, true);
  assert.equal(recovered.ui.state.view, 'setup');
});

test('lock clears saved credentials and selected state', async () => {
  const store = storage();
  store.setItem(key, JSON.stringify({token: 'short-lived-session', view: 'setup'}));
  const page = await boot(store);
  page.ui.lock();
  assert.equal(store.getItem(key), null);
  assert.equal(page.ui.state.selected, null);
  assert.equal(page.ui.state.activeRun, null);
  const reloaded = await boot(store);
  assert.equal(reloaded.calls.length, 0);
});

test('unavailable or malformed tab storage falls back to pairing', async () => {
  const unavailable = {getItem() {throw new Error('Disabled');}, setItem() {throw new Error('Disabled');}, removeItem() {throw new Error('Disabled');}};
  const page = await boot(unavailable);
  assert.equal(page.$('pairing').hidden, false);
  await page.ui.unlock({session_token: 'short-lived-session', csrf: 'csrf'});
  assert.equal(page.$('workspace').hidden, false);
  const corrupt = storage();
  corrupt.setItem(key, '{not json');
  assert.equal((await boot(corrupt)).calls.length, 0);
});

test('detected prerequisite state replaces installation actions with current readiness', async () => {
  const page = await boot(storage());
  page.ui.setupState({tools: {ollama: true, ollama_ready: true, docker: true, docker_ready: true, runner_ready: true}, installed_models: ['qwen3:4b']});
  assert.equal(page.$('ollama-state').textContent, 'Running');
  assert.equal(page.$('install-ollama').hidden, true);
  assert.equal(page.$('start-ollama').hidden, true);
  assert.equal(page.$('docker-state').textContent, 'Ready');
  assert.equal(page.$('build-runner').hidden, true);
});
