/* Run with node --test tools/tests/theme.test.cjs; no browser packages needed. */
const { test } = require('node:test');
const assert = require('node:assert/strict');
const { readFileSync } = require('node:fs');
const { runInNewContext } = require('node:vm');
const { resolve } = require('node:path');
const source = readFileSync(resolve(__dirname, '../../static/js/theme.js'), 'utf8');

function preview({ query = '', stored = null, attr = 'light', zone = 'public', hour = 12, blocked = false } = {}) {
  const root = { dataset: { theme: attr, siteZone: zone } };
  let timer;
  const clock = { hour };
  const state = { stored };
  runInNewContext(source, {
    document: { documentElement: root },
    window: { location: { search: query } }, URLSearchParams, Date,
    sessionStorage: {
      getItem() { if (blocked) throw Error('blocked'); return state.stored; },
      setItem(key, value) { if (blocked) throw Error('blocked'); state.stored = value; },
    },
    Intl: { DateTimeFormat: class { format() { return String(clock.hour); } } },
    setInterval(fn, delay) { assert.equal(delay, 60000); timer = fn; },
  });
  return { root, clock, state, tick() { timer(); } };
}

test('light is the default, including unknown values', () => {
  assert.equal(preview().root.dataset.theme, 'light');
  assert.equal(preview({attr: 'invalid', stored: 'invalid', query: '?theme=invalid'}).root.dataset.theme, 'light');
});
test('explicit preview persists for this tab and overrides a saved choice', () => {
  const p = preview({query: '?theme=dark', stored: 'light'});
  assert.equal(p.root.dataset.theme, 'dark');
  assert.equal(p.state.stored, 'dark');
  assert.equal(preview({stored: p.state.stored}).root.dataset.theme, 'dark');
});
test('an unknown query does not replace a valid saved choice', () => {
  assert.equal(preview({query: '?theme=invalid', stored: 'dark'}).root.dataset.theme, 'dark');
});
test('storage failures still allow explicit previews', () => {
  assert.equal(preview({query: '?theme=dark', blocked: true}).root.dataset.theme, 'dark');
});
test('auto switches at 06:00 and 22:00 in the Paris clock', () => {
  for (const [hour, expected] of [[5,'dark'],[6,'light'],[21,'light'],[22,'dark']]) {
    assert.equal(preview({query:'?theme=auto', hour}).root.dataset.theme, expected);
  }
});
test('automatic preview updates while open and respects manual overrides', () => {
  const p = preview({query:'?theme=auto', hour:21});
  p.clock.hour = 22; p.tick();
  assert.equal(p.root.dataset.theme,'dark');
  p.root.dataset.theme = 'light'; p.tick();
  assert.equal(p.root.dataset.theme,'light');
});
test('ops stays light without discarding the customer-page preview', () => {
  const p = preview({stored:'dark', zone:'ops'});
  assert.equal(p.root.dataset.theme, 'light');
  assert.equal(p.state.stored,'dark');
});
