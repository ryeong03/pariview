// Keep these defaults/ranges aligned with web/dist/settings.js
globalThis.PariViewSettings = (() => {
  const defaults = { brightness: 85, contrast: 90, saturation: 100, warmth: 0, volume: 35, highCut: 0, compression: true, dialogueBoost: false, notices: true };
  const ranges = { brightness: [45, 100], contrast: [65, 110], saturation: [40, 110], warmth: [0, 60], volume: [0, 70], highCut: [0, 100] };
  function normalize(input) {
    if (!input || typeof input !== 'object' || Array.isArray(input)) return null;
    const result = { ...defaults };
    for (const [key, [min, max]] of Object.entries(ranges)) {
      if (Number.isFinite(input[key])) result[key] = Math.min(max, Math.max(min, input[key]));
    }
    for (const key of ['compression', 'dialogueBoost', 'notices']) {
      if (typeof input[key] === 'boolean') result[key] = input[key];
    }
    return result;
  }
  return { normalize, home: 'https://pariview-production.up.railway.app/' };
})();
