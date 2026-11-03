/** Run: node --test web/test_adaptive_fit.mjs (no browser or network needed) */
import test from 'node:test';
import assert from 'node:assert/strict';
import {createAdaptiveFit, FIT_AXES, FIT_BOUNDS, ADAPTIVE_FIT_CONFIG, adaptiveProbabilityA} from './dist/adaptive-fit.js';
import {defaults, ranges, toggles, normalize} from './dist/settings.js';

const near = (a, b, tolerance = 1e-10) => assert.ok(Math.abs(a - b) < tolerance, `${a} != ${b}`);
const axisValue = (axis, z) => FIT_BOUNDS[axis][0] + z * (FIT_BOUNDS[axis][1] - FIT_BOUNDS[axis][0]);
const normalized = (axis, value) => (value - FIT_BOUNDS[axis][0]) / (FIT_BOUNDS[axis][1] - FIT_BOUNDS[axis][0]);
const entropy = ps => -ps.reduce((sum, p) => sum + (p > 0 ? p * Math.log2(p) : 0), 0);
const canonical = q => [q.axis, q.canonical.low, q.canonical.high];
const independentProbability = (a, b, theta) => .05 + .9 / (1 + Math.exp(((a - theta) ** 2 - (b - theta) ** 2) / .08));

function candidates(axis) {
  const values = [...new Set(Array.from({length: 21}, (_, i) => Math.round(axisValue(axis, i / 20))))];
  const pairs = [];
  for (const a of values) for (const b of values) {
    const gap = normalized(axis, b) - normalized(axis, a);
    if (b - a >= 2 && gap >= .1 - 1e-12 && gap <= .5 + 1e-12) pairs.push([a, b]);
  }
  return pairs;
}

// Expected entropy reduction via both complete posteriors, independently of
// the engine's binary-entropy mutual-information calculation
function independentGain(axis, low, high, prior) {
  const a = normalized(axis, low), b = normalized(axis, high);
  const weightedA = prior.map((p, i) => p * independentProbability(a, b, i / 100));
  const weightedB = prior.map((p, i) => p - weightedA[i]);
  const evidenceA = weightedA.reduce((sum, p) => sum + p, 0);
  const evidenceB = weightedB.reduce((sum, p) => sum + p, 0);
  return entropy(prior) - evidenceA * entropy(weightedA.map(p => p / evidenceA)) - evidenceB * entropy(weightedB.map(p => p / evidenceB));
}

function finish(fit, response = 'equal') {
  while (fit.peek()) {
    const q = fit.peek();
    fit.answer(q.id, typeof response === 'function' ? response(q) : response);
  }
  return fit.result();
}

test('settings bounds, 101-bin uniform prior and fixed model are explicit', () => {
  assert.deepEqual(FIT_AXES, ['brightness', 'contrast', 'volume']);
  for (const axis of FIT_AXES) assert.deepEqual(FIT_BOUNDS[axis], ranges[axis]);
  const fit = createAdaptiveFit({seed: 0});
  const s = fit.snapshot();
  assert.equal(s.version, 'pariview-adaptive-fit-v1');
  assert.equal(ADAPTIVE_FIT_CONFIG.lapse, .1);
  assert.equal(ADAPTIVE_FIT_CONFIG.temperature, .08);
  assert.deepEqual(s.grid, Array.from({length: 101}, (_, i) => i / 100));
  for (const axis of FIT_AXES) {
    assert.deepEqual(s.prior[axis], Array(101).fill(1 / 101));
    assert.deepEqual(s.posterior[axis], s.prior[axis]);
    near(s.prior[axis].reduce((a, b) => a + b, 0), 1);
  }
  assert.equal(s.stopReason, null);
});

test('prior is independent of profile or starting settings; output preserves them until an A/B answer', () => {
  const settings = {...defaults, brightness: 98, contrast: 71, volume: 0, profileId: 'clarity', captionYellow: true};
  const low = createAdaptiveFit({seed: 42, settings});
  const high = createAdaptiveFit({seed: 42, settings: {...settings, brightness: 45, contrast: 110, volume: 70}});
  assert.deepEqual(low.snapshot().prior, high.snapshot().prior);
  assert.deepEqual(low.peek(), high.peek());
  assert.deepEqual(low.result().settings, settings);
  const q = low.peek(); low.answer(q.id, 'a');
  for (const key of Object.keys(defaults)) if (key !== q.axis) assert.equal(low.result().settings[key], settings[key]);
});

test('peek, result and snapshot never advance or expose mutable internal state', () => {
  const fit = createAdaptiveFit({seed: 23});
  const before = fit.snapshot();
  const q = fit.peek(); q.a = -1000; q.canonical.low = -900; q.bounds[0] = -30;
  const result = fit.result(); result.settings.volume = 999; result.uncertainty.volume.lower = -1;
  const s = fit.snapshot(); s.grid[0] = 88; s.posterior.volume[0] = 900; s.prior.brightness[0] = 900;
  for (let i = 0; i < 20; i++) { fit.peek(); fit.result(); }
  assert.deepEqual(fit.snapshot(), before);
});

test('all candidates are rounded actual integers and meet allowed gaps; no repeats through 20 nonanswers', () => {
  for (const policy of ['adaptive', 'fixed']) {
    const fit = createAdaptiveFit({seed: 81, budget: 20, policy});
    const seen = new Set();
    while (fit.peek()) {
      const q = fit.peek();
      const {low, high} = q.canonical, [min, max] = ranges[q.axis];
      assert.ok(Number.isInteger(low) && Number.isInteger(high));
      assert.ok(low >= min && high <= max && high - low >= 2);
      const gap = (high - low) / (max - min);
      assert.ok(gap >= .1 - 1e-12 && gap <= .5 + 1e-12);
      near(q.normalized.a, normalized(q.axis, q.a));
      near(q.normalized.b, normalized(q.axis, q.b));
      const key = canonical(q).join(':'); assert.ok(!seen.has(key)); seen.add(key);
      fit.answer(q.id, 'equal');
    }
    assert.equal(seen.size, 20);
    assert.equal(fit.result().stopReason, 'budget');
  }
});

test('first three questions cover each numeric axis; requested firstAxis only controls the first', () => {
  for (const firstAxis of [...FIT_AXES, null]) {
    const fit = createAdaptiveFit({seed: 3, firstAxis});
    const axes = [];
    for (let i = 0; i < 3; i++) {
      const q = fit.peek(); axes.push(q.axis); fit.answer(q.id, ['skip', 'unsure', 'equal'][i]);
    }
    assert.equal(new Set(axes).size, 3);
    if (firstAxis) assert.equal(axes[0], firstAxis);
  }
});

test('Bayes update uses displayed A/B and actual rounded values, independent calculation agrees', () => {
  for (const response of ['a', 'b']) {
    for (const firstAxis of FIT_AXES) {
      const fit = createAdaptiveFit({seed: 20261104, firstAxis});
      const q = fit.peek(), before = fit.snapshot();
      const values = before.posterior[q.axis].map((p, i) => {
        const pA = independentProbability(normalized(q.axis, q.a), normalized(q.axis, q.b), i / 100);
        return p * (response === 'a' ? pA : 1 - pA);
      });
      const evidence = values.reduce((a, b) => a + b, 0);
      fit.answer(q.id, response);
      const after = fit.snapshot();
      after.posterior[q.axis].forEach((p, i) => near(p, values[i] / evidence));
      for (const axis of FIT_AXES) if (axis !== q.axis) assert.deepEqual(after.posterior[axis], before.posterior[axis]);
      near(after.posterior[q.axis].reduce((a, b) => a + b, 0), 1);
      assert.ok(after.posterior[q.axis].every(p => p > 0 && Number.isFinite(p)));
      const median = after.uncertainty[q.axis].normalizedMedian;
      assert.equal(after.settings[q.axis], Math.round(axisValue(q.axis, median)));
    }
  }
});

test('mutual information matches expected posterior entropy, and next pair is globally maximal among eligible pairs', () => {
  const fit = createAdaptiveFit({seed: 7});
  for (let step = 0; step < 5; step++) {
    const q = fit.peek(), snapshot = fit.snapshot();
    const used = new Set(snapshot.history.map(item => item.pairKey));
    const unseen = FIT_AXES.filter(axis => !snapshot.history.some(item => item.question.axis === axis));
    let best = -Infinity;
    for (const axis of (unseen.length ? unseen : FIT_AXES)) {
      for (const [low, high] of candidates(axis)) {
        if (used.has(`${axis}:${low}:${high}`)) continue;
        best = Math.max(best, independentGain(axis, low, high, snapshot.posterior[axis]));
      }
    }
    near(q.expectedInformationGain, independentGain(q.axis, q.canonical.low, q.canonical.high, snapshot.posterior[q.axis]));
    near(q.expectedInformationGain, best);
    fit.answer(q.id, step % 2 ? 'b' : 'a');
  }
});

test('equal, unsure and skip keep posterior and output unchanged but have distinct logs and counts', () => {
  const settings = {...defaults, brightness: 91, contrast: 74, volume: 17, captionYellow: true};
  const fit = createAdaptiveFit({seed: 12, settings});
  const start = fit.snapshot();
  const responses = ['equal', 'unsure', 'skip', 'unsure', 'equal'];
  for (const response of responses) {
    const q = fit.peek(); fit.answer(q.id, response);
    assert.deepEqual(fit.snapshot().posterior, start.posterior);
    assert.deepEqual(fit.result().settings, settings);
  }
  assert.equal(fit.peek(), null);
  assert.equal(fit.result().answered, 5);
  assert.equal(fit.result().stopReason, 'budget');
  assert.deepEqual(fit.result().counts, {a: 0, b: 0, equal: 2, unsure: 2, skip: 1, effective: 0});
  assert.deepEqual(fit.snapshot().history.map(item => item.outcome), responses);
});

test('skip defers that axis for the next adaptive question; it adds no evidence', () => {
  const fit = createAdaptiveFit({seed: 2, budget: 10});
  for (let i = 0; i < 3; i++) { const q = fit.peek(); fit.answer(q.id, 'a'); }
  const skipped = fit.peek(), before = fit.snapshot().posterior;
  fit.answer(skipped.id, 'skip');
  assert.notEqual(fit.peek().axis, skipped.axis);
  assert.deepEqual(fit.snapshot().posterior, before);
});

test('changing a preference changes a later adaptive candidate pair, not just a label', () => {
  const low = createAdaptiveFit({seed: 41}), high = createAdaptiveFit({seed: 41});
  for (let i = 0; i < 3; i++) {
    for (const [fit, side] of [[low, 'low'], [high, 'high']]) {
      const q = fit.peek(); fit.answer(q.id, q.placement.a === side ? 'a' : 'b');
    }
  }
  assert.notDeepEqual(canonical(low.peek()), canonical(high.peek()));
  assert.notDeepEqual(low.snapshot().posterior, high.snapshot().posterior);
});

test('left/right randomization is reproducible; choosing the same numeric candidate produces the same inference', () => {
  const pairs = [];
  for (let seed = 0; seed < 20; seed++) {
    const fit = createAdaptiveFit({seed, firstAxis: 'brightness'});
    const q = fit.peek(); fit.answer(q.id, q.placement.a === 'low' ? 'a' : 'b');
    pairs.push({q, posterior: fit.snapshot().posterior});
  }
  assert.ok(pairs.some(p => p.q.a < p.q.b));
  assert.ok(pairs.some(p => p.q.a > p.q.b));
  for (const {q, posterior} of pairs) {
    assert.deepEqual(canonical(q), canonical(pairs[0].q));
    posterior.brightness.forEach((p, i) => near(p, pairs[0].posterior.brightness[i]));
  }
  const a = createAdaptiveFit({seed: 93}), b = createAdaptiveFit({seed: 93});
  finish(a, 'b'); finish(b, 'b');
  assert.deepEqual(a.snapshot(), b.snapshot());
});

test('duplicate/stale IDs and invalid outcomes are rejected without any state change', () => {
  const fit = createAdaptiveFit({seed: 4}), q = fit.peek();
  const initial = fit.snapshot();
  assert.throws(() => fit.answer(q.id, 'tie'), /unknown answer/);
  assert.throws(() => fit.answer('old-id', 'a'), /not current/);
  assert.deepEqual(fit.snapshot(), initial);
  fit.answer(q.id, 'a');
  const once = fit.snapshot();
  assert.throws(() => fit.answer(q.id, 'b'), /not current/);
  assert.deepEqual(fit.snapshot(), once);
  finish(fit);
  assert.throws(() => fit.answer(q.id, 'a'), /not current/);
});

test('undo restores the same query/placement and all estimates; abandoned future IDs remain invalid', () => {
  const fit = createAdaptiveFit({seed: 17});
  const first = fit.peek(), before = fit.snapshot();
  fit.answer(first.id, 'a');
  const discarded = fit.peek();
  assert.deepEqual(fit.undo(), first);
  assert.deepEqual(fit.snapshot().posterior, before.posterior);
  assert.deepEqual(fit.result().settings, before.settings);
  assert.equal(fit.snapshot().history.length, 0);
  fit.answer(first.id, 'b');
  assert.notEqual(fit.peek().id, discarded.id);
  assert.throws(() => fit.answer(discarded.id, 'a'), /not current/);
  finish(fit, 'b');
  for (let i = 5; i > 0; i--) {
    const last = fit.snapshot().history.at(-1);
    assert.deepEqual(fit.undo(), last.question);
    assert.equal(fit.result().answered, i - 1);
  }
  assert.deepEqual(fit.result().settings, before.settings);
  assert.deepEqual(fit.snapshot().posterior, before.posterior);
});

test('five is a budget end, never a precision claim; extend is explicit and capped at twenty', () => {
  const fit = createAdaptiveFit({seed: 3});
  finish(fit, 'a');
  assert.equal(fit.result().stopReason, 'budget');
  assert.equal(fit.result().answered, 5);
  const before = fit.snapshot();
  assert.throws(() => fit.extend(100), /five/);
  assert.deepEqual(fit.snapshot(), before);
  for (const budget of [10, 15, 20]) {
    assert.ok(fit.extend(5));
    assert.equal(fit.result().budget, budget);
    finish(fit, 'unsure');
    assert.equal(fit.result().answered, budget);
  }
  assert.equal(fit.extend(5), null);
  assert.equal(fit.result().budget, 20);
  assert.equal(fit.result().canExtend, false);
});

test('user stop ends immediately, never applies values, and explicit extension can resume', () => {
  const original = {...defaults, captionYellow: true};
  const fit = createAdaptiveFit({seed: 1, settings: original});
  const q = fit.peek();
  const end = fit.stop();
  assert.equal(fit.peek(), null);
  assert.equal(end.stopReason, 'user');
  assert.equal(end.answered, 0);
  assert.deepEqual(end.settings, original);
  assert.throws(() => fit.answer(q.id, 'a'), /not current/);
  assert.deepEqual(original, {...defaults, captionYellow: true});
  assert.ok(fit.extend(5));
  assert.equal(fit.result().stopReason, null);
  assert.equal(fit.result().budget, 10);
});

test('an unanswered question abandoned on stop is not silently repeated after resuming', () => {
  const fit = createAdaptiveFit({seed: 14, firstAxis: 'brightness'});
  const abandoned = fit.peek();
  fit.stop(); fit.extend(5);
  assert.notDeepEqual(canonical(fit.peek()), canonical(abandoned));
  assert.equal(fit.result().answered, 0);
  assert.deepEqual(fit.result().settings, defaults);
  const second = fit.peek(); fit.answer(second.id, 'a');
  const discarded = fit.peek();
  assert.deepEqual(fit.undo(), second);
  assert.ok(!fit.snapshot().issued.some(q => q.id === discarded.id));
  assert.ok(fit.snapshot().issued.some(q => q.id === abandoned.id));
});

test('a user can resume remaining comparisons even after the allocated budget reaches twenty', () => {
  const fit = createAdaptiveFit({seed: 12, budget: 20});
  fit.answer(fit.peek().id, 'skip');
  fit.stop();
  assert.equal(fit.result().canExtend, true);
  assert.ok(fit.extend(5));
  assert.equal(fit.result().budget, 20);
  assert.equal(fit.result().answered, 1);
  finish(fit, 'equal');
  assert.equal(fit.result().answered, 20);
  assert.equal(fit.result().canExtend, false);
  assert.equal(fit.extend(5), null);
});

test('fixed schedule is response independent and uses the same Bayesian estimator', () => {
  const traces = [];
  for (const response of ['a', 'b', 'skip', 'equal', 'unsure']) {
    const fit = createAdaptiveFit({seed: 91, budget: 20, policy: 'fixed', firstAxis: 'volume'});
    const trace = [];
    while (fit.peek()) {
      const q = fit.peek(); trace.push(canonical(q)); fit.answer(q.id, response);
    }
    traces.push(trace);
    assert.deepEqual(trace.map(q => q[0]), Array.from({length: trace.length}, (_, i) => FIT_AXES[i % 3]));
  }
  for (const trace of traces) assert.deepEqual(trace, traces[0]);
  const adaptive = createAdaptiveFit({seed: 14, firstAxis: 'brightness'});
  const fixed = createAdaptiveFit({seed: 14, policy: 'fixed'});
  assert.deepEqual(canonical(adaptive.peek()), canonical(fixed.peek()));
  adaptive.answer(adaptive.peek().id, 'a'); fixed.answer(fixed.peek().id, 'a');
  assert.deepEqual(adaptive.snapshot().posterior.brightness, fixed.snapshot().posterior.brightness);
});

test('fixed candidates minimize the declared center/gap distance in contract order', () => {
  const fit = createAdaptiveFit({seed: 6, budget: 20, policy: 'fixed'});
  const centers = [.5, .25, .75, .125, .375, .625, .875];
  const seen = new Set();
  for (let i = 0; i < 20; i++) {
    const q = fit.peek(), axis = FIT_AXES[i % 3];
    const shiftedLow = Math.max(0, Math.min(.5, centers[Math.floor(i / 3)] - .25));
    const pool = candidates(axis).filter(([lo, hi]) => !seen.has(`${axis}:${lo}:${hi}`));
    const score = ([lo, hi]) => Math.abs((normalized(axis, lo) + normalized(axis, hi)) / 2 - shiftedLow - .25) + Math.abs((hi - lo) / (ranges[axis][1] - ranges[axis][0]) - .5);
    let best = pool[0];
    for (const pair of pool) if (score(pair) < score(best) - 1e-12) best = pair;
    assert.deepEqual([q.canonical.low, q.canonical.high], best);
    seen.add(canonical(q).join(':')); fit.answer(q.id, 'equal');
  }
});

test('every response record keeps candidates, actual placement, both distributions and resulting settings', () => {
  const fit = createAdaptiveFit({seed: 20261104, context: {clipId: 'tears-lab', segment: [4, 12], playbackRate: .75, fixedOptions: {captionYellow: true, compression: true}, identity: 'must not be logged'}});
  finish(fit, q => q.queryIndex % 2 ? 'a' : 'unsure');
  const s = fit.snapshot();
  assert.deepEqual(s.context, {clipId: 'tears-lab', segment: {start: 4, end: 12}, playbackRate: .75, fixedOptions: {compression: true, captionYellow: true}});
  assert.equal(s.history.length, 5);
  for (const record of s.history) {
    assert.equal(record.posteriorBefore.length, 101); assert.equal(record.posteriorAfter.length, 101);
    near(record.posteriorAfter.reduce((a, b) => a + b, 0), 1);
    assert.equal(record.question.queryIndex, s.history.indexOf(record) + 1);
    assert.equal(record.question.a, record.question.canonical[record.question.placement.a]);
    assert.equal(record.question.b, record.question.canonical[record.question.placement.b]);
    assert.deepEqual(Object.keys(record.uncertaintyAfter), FIT_AXES);
    assert.equal(record.settingsAfter.captionYellow, defaults.captionYellow);
    if (!record.directional) assert.deepEqual(record.posteriorBefore, record.posteriorAfter);
  }
  assert.doesNotThrow(() => JSON.stringify(s));
});

test('boolean axes, colours and other controls are never fitted or dropped', () => {
  for (const boolean of [false, true]) {
    const input = {...defaults, ...Object.fromEntries(toggles.map(key => [key, boolean])), highCut: 63, saturation: 43, warmth: 52, captionSize: 28};
    const fit = createAdaptiveFit({seed: 5, settings: input});
    finish(fit, 'a');
    for (const key of Object.keys(defaults)) if (!FIT_AXES.includes(key)) assert.equal(fit.result().settings[key], input[key], key);
    assert.ok(fit.snapshot().history.every(item => FIT_AXES.includes(item.question.axis)));
  }
  const bounded = createAdaptiveFit({seed: 7, settings: {brightness: -500, contrast: 900, volume: Infinity, captionYellow: 'true'}});
  assert.deepEqual(bounded.result().settings, normalize({brightness: -500, contrast: 900, volume: Infinity, captionYellow: 'true'}));
});

test('long deterministic runs retain valid posteriors and only stop for precision if every axis meets it', () => {
  for (const target of [0, .25, .5, .75, 1]) {
    const fit = createAdaptiveFit({seed: 15, budget: 20});
    finish(fit, q => Math.abs(q.normalized.a - target) <= Math.abs(q.normalized.b - target) ? 'a' : 'b');
    const result = fit.result();
    assert.ok(['precision', 'budget'].includes(result.stopReason));
    assert.ok(result.answered <= 20);
    for (const axis of FIT_AXES) {
      near(fit.snapshot().posterior[axis].reduce((a, b) => a + b, 0), 1);
      assert.ok(fit.snapshot().posterior[axis].every(p => Number.isFinite(p) && p > 0));
      const u = result.uncertainty[axis];
      assert.ok(u.normalizedLower <= u.normalizedMedian && u.normalizedMedian <= u.normalizedUpper);
      assert.ok(result.settings[axis] >= ranges[axis][0] && result.settings[axis] <= ranges[axis][1]);
      if (result.stopReason === 'precision') {
        assert.ok(u.effectiveAnswers >= 2);
        assert.ok(u.normalizedWidth <= .15 + 1e-12);
      }
    }
  }
});

test('invalid configuration does not silently change the protocol', () => {
  for (const options of [{budget: 0}, {budget: 21}, {budget: 1.5}, {seed: -1}, {seed: NaN}, {seed: 2 ** 32}, {firstAxis: 'compression'}, {policy: 'staircase'}]) {
    assert.throws(() => createAdaptiveFit(options));
  }
  for (const a of [0, .1, .4, 1]) for (const b of [0, .5, .9, 1]) for (const theta of [0, .5, 1]) {
    near(adaptiveProbabilityA(a, b, theta) + adaptiveProbabilityA(b, a, theta), 1);
    near(adaptiveProbabilityA(a, b, theta), independentProbability(a, b, theta));
  }
});
