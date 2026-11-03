/**
 * Local, ideal-point Bayesian preference fitting
 * Contract: research/adaptive-fitting/CONTRACT.txt v1
 * The model and its uncertainty describe this session, not a medical threshold
 * No DOM, storage, network, audio playback, or automatic application of settings
 */
import {defaults, ranges, toggles, normalize} from './settings.js';

export const FIT_AXES = Object.freeze(['brightness', 'contrast', 'volume']);
export const FIT_BOUNDS = Object.freeze(Object.fromEntries(
  FIT_AXES.map(axis => [axis, Object.freeze([...ranges[axis]])])
));
export const ADAPTIVE_FIT_CONFIG = Object.freeze({
  version: 'pariview-adaptive-fit-v1',
  model: 'independent-quadratic-ideal-point',
  gridSize: 101,
  candidateGridSize: 21,
  lapse: .10,
  temperature: .08,
  minNormalizedGap: .10,
  maxNormalizedGap: .50,
  minActualGap: 2,
  initialBudget: 5,
  maxBudget: 20,
  intervalMass: .80,
  precisionWidth: .15,
  precisionMinAnswersPerAxis: 2,
  prior: 'uniform',
  fixedDistance: 'absolute-center-distance-plus-absolute-gap-distance',
});

const GRID = Object.freeze(Array.from({length: 101}, (_, i) => i / 100));
const OUTCOMES = Object.freeze(['a', 'b', 'equal', 'unsure', 'skip']);
const EPSILON = 1e-12;
const clone = value => structuredClone(value);
const uniform = () => GRID.map(() => 1 / GRID.length);
const directional = value => value === 'a' || value === 'b';
const unitValue = (axis, value) => (value - FIT_BOUNDS[axis][0]) / (FIT_BOUNDS[axis][1] - FIT_BOUNDS[axis][0]);
const actualValue = (axis, value) => FIT_BOUNDS[axis][0] + value * (FIT_BOUNDS[axis][1] - FIT_BOUNDS[axis][0]);
const binaryEntropy = p => p <= 0 || p >= 1 ? 0 : -p * Math.log2(p) - (1 - p) * Math.log2(1 - p);
const entropy = probabilities => -probabilities.reduce((sum, p) => sum + (p > 0 ? p * Math.log2(p) : 0), 0);

// a, b and theta are normalized values of the ACTUAL rounded candidates
export function adaptiveProbabilityA(a, b, theta) {
  const difference = (b - theta) ** 2 - (a - theta) ** 2;
  return ADAPTIVE_FIT_CONFIG.lapse / 2 + (1 - ADAPTIVE_FIT_CONFIG.lapse) /
    (1 + Math.exp(-difference / ADAPTIVE_FIT_CONFIG.temperature));
}

function makeCandidates(axis) {
  const values = [...new Set(Array.from({length: 21}, (_, i) => Math.round(actualValue(axis, i / 20))))];
  const pairs = [];
  for (let i = 0; i < values.length; i++) {
    for (let j = i + 1; j < values.length; j++) {
      const low = values[i], high = values[j], a = unitValue(axis, low), b = unitValue(axis, high);
      if (high - low < ADAPTIVE_FIT_CONFIG.minActualGap || b - a < .10 - EPSILON || b - a > .50 + EPSILON) continue;
      const likelihood = GRID.map(theta => adaptiveProbabilityA(a, b, theta));
      pairs.push({axis, low, high, a, b, likelihood, conditionalEntropy: likelihood.map(binaryEntropy), key: `${axis}:${low}:${high}`});
    }
  }
  return {values, pairs};
}

// Reused immutable kernels keep each next-question calculation small
const CANDIDATES = Object.fromEntries(FIT_AXES.map(axis => [axis, makeCandidates(axis)]));

function informationGain(prior, pair) {
  let pA = 0, conditional = 0;
  for (let i = 0; i < prior.length; i++) {
    pA += prior[i] * pair.likelihood[i];
    conditional += prior[i] * pair.conditionalEntropy[i];
  }
  return Math.max(0, binaryEntropy(pA) - conditional);
}

function quantile(probabilities, q) {
  let sum = 0;
  for (let i = 0; i < probabilities.length; i++) {
    sum += probabilities[i];
    if (sum >= q - EPSILON) return GRID[i];
  }
  return 1;
}

function summarize(axis, probabilities, effectiveAnswers) {
  const normalizedLower = quantile(probabilities, .10);
  const normalizedUpper = quantile(probabilities, .90);
  const normalizedMedian = quantile(probabilities, .50);
  return {
    lower: actualValue(axis, normalizedLower),
    upper: actualValue(axis, normalizedUpper),
    median: Math.round(actualValue(axis, normalizedMedian)),
    normalizedLower, normalizedUpper, normalizedMedian,
    normalizedWidth: normalizedUpper - normalizedLower,
    entropyBits: entropy(probabilities),
    intervalMass: .80,
    effectiveAnswers,
    hasEvidence: effectiveAnswers > 0,
  };
}

function cleanContext(value = {}) {
  if (!value || typeof value !== 'object' || Array.isArray(value)) throw new TypeError('context must be an object');
  const result = {};
  // Only experiment conditions belong in the local log, not identity or diagnosis
  if (typeof value.clipId === 'string') result.clipId = value.clipId.slice(0, 120);
  if (Number.isFinite(value.playbackRate) && value.playbackRate > 0 && value.playbackRate <= 4) result.playbackRate = value.playbackRate;
  if (value.segment) {
    const start = Array.isArray(value.segment) ? value.segment[0] : value.segment.start;
    const end = Array.isArray(value.segment) ? value.segment[1] : value.segment.end;
    if (Number.isFinite(start) && Number.isFinite(end) && start >= 0 && end >= start) result.segment = {start, end};
  }
  if (value.fixedOptions && typeof value.fixedOptions === 'object') {
    result.fixedOptions = {};
    const normalized = normalize(value.fixedOptions);
    for (const key of [...Object.keys(ranges), ...toggles]) {
      if (!FIT_AXES.includes(key) && Object.hasOwn(value.fixedOptions, key)) result.fixedOptions[key] = normalized[key];
    }
  }
  return result;
}

function newSeed() {
  if (globalThis.crypto?.getRandomValues) return globalThis.crypto.getRandomValues(new Uint32Array(1))[0];
  return Date.now() >>> 0;
}

// Breadth-first dyadic centers: .5, .25, .75, .125, .375, .625, .875, ...
function fixedCenter(ordinal) {
  const level = Math.floor(Math.log2(ordinal + 1));
  const offset = ordinal - (2 ** level - 1);
  return (2 * offset + 1) / 2 ** (level + 1);
}

/**
 * Mutations are explicit: answer, undo, extend and stop
 * peek/result/snapshot return detached values and never select another question
 * All outcome labels refer to the displayed A/B positions, including swapped pairs
 */
export function createAdaptiveFit(options = {}) {
  if (!options || typeof options !== 'object' || Array.isArray(options)) throw new TypeError('options must be an object');
  const initialSettings = normalize(options.settings ?? defaults);
  const context = cleanContext(options.context);
  const seed = options.seed ?? newSeed();
  const policy = options.policy ?? 'adaptive';
  const firstAxis = options.firstAxis ?? null;
  let budget = options.budget ?? ADAPTIVE_FIT_CONFIG.initialBudget;
  if (!Number.isInteger(seed) || seed < 0 || seed > 0xffffffff) throw new RangeError('seed must be a uint32');
  if (!Number.isInteger(budget) || budget < 1 || budget > 20) throw new RangeError('budget must be an integer from 1 to 20');
  if (!['adaptive', 'fixed'].includes(policy)) throw new RangeError('unknown policy');
  if (firstAxis !== null && !FIT_AXES.includes(firstAxis)) throw new RangeError('firstAxis must be a numeric fit axis');
  const prior = Object.fromEntries(FIT_AXES.map(axis => [axis, uniform()]));
  const posterior = clone(prior);
  const history = [], frames = [], events = [], issued = [], discarded = [];
  let randomState = seed, serial = 0, pending = null, pendingRngAfter = seed, stopReason = null;

  function random() {
    randomState = (randomState + 0x6d2b79f5) >>> 0;
    let t = randomState;
    t = Math.imul(t ^ t >>> 15, t | 1);
    t ^= t + Math.imul(t ^ t >>> 7, t | 61);
    return ((t ^ t >>> 14) >>> 0) / 4294967296;
  }

  function result() {
    const counts = {a: 0, b: 0, equal: 0, unsure: 0, skip: 0, effective: 0};
    const perAxis = Object.fromEntries(FIT_AXES.map(axis => [axis, 0]));
    for (const item of history) {
      counts[item.outcome]++;
      if (directional(item.outcome)) { counts.effective++; perAxis[item.question.axis]++; }
    }
    const settings = {...initialSettings}, uncertainty = {};
    for (const axis of FIT_AXES) {
      uncertainty[axis] = summarize(axis, posterior[axis], perAxis[axis]);
      if (perAxis[axis]) settings[axis] = uncertainty[axis].median;
    }
    return {
      settings, answered: history.length, issuedCount: issued.length, discardedCount: discarded.length,
      budget, remaining: Math.max(0, budget - history.length),
      stopReason, counts, uncertainty, policy,
      canExtend: !['precision', 'no_candidates'].includes(stopReason) &&
        (budget < 20 || (stopReason === 'user' && history.length < budget)),
    };
  }

  function precise() {
    const {uncertainty} = result();
    return FIT_AXES.every(axis => uncertainty[axis].effectiveAnswers >= 2 && uncertainty[axis].normalizedWidth <= .15 + EPSILON);
  }

  function choosePair() {
    const used = new Set(issued.map(q => `${q.axis}:${q.canonical.low}:${q.canonical.high}`));
    if (policy === 'fixed') {
      // This schedule is independent of all response values, including skip
      const axis = FIT_AXES[history.length % FIT_AXES.length];
      const ordinal = Math.floor(history.length / FIT_AXES.length);
      const low = Math.max(0, Math.min(.5, fixedCenter(ordinal) - .25));
      const center = low + .25;
      let best = null, distance = Infinity;
      for (const pair of CANDIDATES[axis].pairs) {
        if (used.has(pair.key)) continue;
        const next = Math.abs((pair.a + pair.b) / 2 - center) + Math.abs(pair.b - pair.a - .5);
        if (next < distance - EPSILON) { best = pair; distance = next; }
      }
      return best;
    }
    let eligible = FIT_AXES;
    const unseen = FIT_AXES.filter(axis => !issued.some(q => q.axis === axis));
    if (unseen.length) eligible = unseen;
    if (!issued.length && firstAxis) eligible = [firstAxis];
    const last = history.at(-1);
    if (last?.outcome === 'skip' && issued.at(-1)?.id === last.question.id) {
      const deferred = eligible.filter(axis => axis !== last.question.axis);
      if (deferred.some(axis => CANDIDATES[axis].pairs.some(pair => !used.has(pair.key)))) eligible = deferred;
    }
    let best = null, bestGain = -Infinity;
    // Iteration order implements the contract's stable tie breaks
    for (const axis of eligible) {
      for (const pair of CANDIDATES[axis].pairs) {
        if (used.has(pair.key)) continue;
        const gain = informationGain(posterior[axis], pair);
        if (gain > bestGain + EPSILON) { best = pair; bestGain = gain; }
      }
    }
    return best;
  }

  function prepare() {
    pending = null;
    if (precise()) { stopReason = 'precision'; return; }
    if (history.length >= budget) { stopReason = 'budget'; return; }
    const pair = choosePair();
    if (!pair) { stopReason = 'no_candidates'; return; }
    const swapped = random() < .5;
    pendingRngAfter = randomState;
    stopReason = null;
    pending = {
      id: `pv-fit-${seed.toString(16)}-${++serial}`,
      axis: pair.axis,
      a: swapped ? pair.high : pair.low,
      b: swapped ? pair.low : pair.high,
      queryIndex: history.length + 1,
      canonical: {low: pair.low, high: pair.high},
      placement: {a: swapped ? 'high' : 'low', b: swapped ? 'low' : 'high', left: 'a', right: 'b'},
      normalized: {a: swapped ? pair.b : pair.a, b: swapped ? pair.a : pair.b},
      bounds: [...FIT_BOUNDS[pair.axis]],
      expectedInformationGain: informationGain(posterior[pair.axis], pair),
      priorEntropyBits: entropy(posterior[pair.axis]),
      policy,
    };
    issued.push({...clone(pending), status: 'pending'});
  }

  function peek() { return clone(pending); }

  function answer(questionId, outcome) {
    if (!OUTCOMES.includes(outcome)) throw new RangeError('unknown answer');
    if (!pending || pending.id !== questionId) throw new Error('question is not current');
    const question = clone(pending), axis = question.axis;
    const before = [...posterior[axis]];
    const resultBefore = result();
    if (directional(outcome)) {
      const weighted = before.map((p, i) => {
        const likelihoodA = adaptiveProbabilityA(question.normalized.a, question.normalized.b, GRID[i]);
        return p * (outcome === 'a' ? likelihoodA : 1 - likelihoodA);
      });
      const evidence = weighted.reduce((sum, value) => sum + value, 0);
      posterior[axis] = weighted.map(value => value / evidence);
    }
    const item = {
      question, pairKey: `${axis}:${question.canonical.low}:${question.canonical.high}`,
      outcome, directional: directional(outcome),
      posteriorBefore: before, posteriorAfter: [...posterior[axis]],
      settingsBefore: resultBefore.settings,
    };
    history.push(item);
    frames.push({rngAfterQuestion: pendingRngAfter});
    Object.assign(issued.find(q => q.id === questionId), {status: 'answered', outcome});
    const after = result();
    item.settingsAfter = after.settings;
    item.uncertaintyAfter = after.uncertainty;
    events.push({type: 'answer', questionId, outcome});
    prepare();
    return peek();
  }

  function undo() {
    if (!history.length) return peek();
    const item = history.pop(), frame = frames.pop();
    posterior[item.question.axis] = [...item.posteriorBefore];
    pending = clone(item.question);
    const index = issued.findIndex(q => q.id === pending.id);
    discarded.push(...issued.splice(index + 1).map(q => ({...q, status: 'discarded', reason: 'undo'})));
    issued[index].status = 'pending';
    delete issued[index].outcome;
    randomState = frame.rngAfterQuestion;
    pendingRngAfter = randomState;
    // Keep serial monotonic so an old discarded question ID cannot answer a new pair
    stopReason = null;
    events.push({type: 'undo', questionId: pending.id});
    return peek();
  }

  function extend(amount = 5) {
    if (amount !== 5) throw new RangeError('extend adds five comparisons');
    if (!result().canExtend) return peek();
    budget = Math.min(20, budget + amount);
    events.push({type: 'extend', budget});
    if (!pending) prepare();
    return peek();
  }

  function stop() {
    if (!pending) return result();
    events.push({type: 'stop', question: clone(pending)});
    issued.find(q => q.id === pending.id).status = 'abandoned';
    pending = null;
    stopReason = 'user';
    return result();
  }

  function snapshot() {
    return clone({
      version: ADAPTIVE_FIT_CONFIG.version, config: ADAPTIVE_FIT_CONFIG,
      seed, policy, firstAxis, context, bounds: FIT_BOUNDS, grid: GRID, prior,
      candidateValues: Object.fromEntries(FIT_AXES.map(axis => [axis, CANDIDATES[axis].values])),
      initialSettings, posterior, history, issued, discarded, events, question: pending, ...result(),
    });
  }

  prepare();
  return Object.freeze({peek, answer, undo, extend, stop, result, snapshot});
}
