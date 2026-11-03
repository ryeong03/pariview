"""Drive the real PariView fitting UI with AI personas and measure how close the result gets.

Each persona has a hidden target setting. The simulator opens the fit dialog, picks the
persona's starting mode, answers every A/B step by choosing the option closer to the target
("비슷해요" when both are about equally close), applies the result and reads the saved settings.

This is a simulation of the elicitation flow, not user data.

Usage: python3 analysis/simulation/simulate.py http://127.0.0.1:4178/ analysis/simulation/results.json
"""
import json
import sys
import tempfile
from pathlib import Path
from playwright.sync_api import sync_playwright

HERE = Path(__file__).resolve().parent
NUMERIC = {'brightness': (45, 100), 'contrast': (65, 110), 'volume': (0, 70)}
BOOLEAN = ['compression', 'easyCaptions']


def norm_error(settings, target):
    errs = {k: abs(settings[k] - target[k]) / (hi - lo) for k, (lo, hi) in NUMERIC.items()}
    errs['mean'] = sum(errs.values()) / len(NUMERIC)
    errs['booleanMatch'] = sum(settings[k] == target[k] for k in BOOLEAN) / len(BOOLEAN)
    return errs


def check_steps():
    app = (HERE.parent.parent / 'web/dist/app.js').read_text(encoding='utf-8')
    for spec in STEPS:
        a = str(spec['a']).lower(); b = str(spec['b']).lower()
        assert f"key:'{spec['key']}'" in app and f"a:{a},b:{b}" in app, f'step changed in app.js: {spec}'


def run(url, out):
    check_steps()
    cfg = json.loads((HERE / 'personas.json').read_text())
    tol = cfg['behavior']['equalTolerance']
    results = []
    with sync_playwright() as p:
        browser = p.chromium.launch(executable_path='/Applications/Google Chrome.app/Contents/MacOS/Google Chrome')
        for persona in cfg['personas']:
            ctx = browser.new_context(viewport={'width': 1440, 'height': 900}, storage_state=None)
            page = ctx.new_page()
            errors = []
            page.on('pageerror', lambda e: errors.append(str(e)))
            page.goto(url, wait_until='domcontentloaded')
            page.wait_for_function('!!(window.__pariview && window.__pariview.openFit)', timeout=90000)
            defaults = page.evaluate('window.__pariview.settings')
            clicks = 0
            page.evaluate('window.__pariview.openFit()')
            page.wait_for_selector('[data-mode]')
            modes = page.evaluate('window.__pariview.modes.map(m=>m.id)')
            page.click(f'[data-mode="{modes.index(persona["mode"])}"]'); clicks += 1
            page.click('#start-comparison'); clicks += 1
            answers = []
            for idx, spec in enumerate(STEPS):
                page.wait_for_selector('[data-choose="a"]')
                want = persona['target'][spec['key']]
                if isinstance(spec['a'], bool):
                    choice = 'a' if spec['a'] == want else 'b'
                else:
                    da, db = abs(spec['a'] - want), abs(spec['b'] - want)
                    choice = 'equal' if abs(da - db) < tol else ('a' if da < db else 'b')
                if choice == 'equal':
                    page.click('#choose-equal')
                else:
                    page.click(f'[data-choose="{choice}"]')
                clicks += 1
                answers.append({'key': spec['key'], 'choice': choice, 'a': spec['a'], 'b': spec['b'], 'want': want})
                page.click('#fit-next'); clicks += 1
            page.wait_for_selector('#apply-fit')
            page.click('#apply-fit'); clicks += 1
            page.wait_for_timeout(200)
            fitted = page.evaluate('window.__pariview.settings')
            saved = page.evaluate("JSON.parse(localStorage.getItem('pariview-fit-v1')||'null')")
            target = persona['target']
            results.append({
                'id': persona['id'], 'segment': persona['segment'], 'age': persona['age'], 'mode': persona['mode'],
                'target': target,
                'fitted': {k: fitted[k] for k in list(NUMERIC) + BOOLEAN},
                'default': {k: defaults[k] for k in list(NUMERIC) + BOOLEAN},
                'errorDefault': norm_error(defaults, target),
                'errorFitted': norm_error(fitted, target),
                'answers': answers, 'clicks': clicks, 'savedToStorage': bool(saved), 'pageErrors': errors,
            })
            ctx.close()
        browser.close()

    def mean(xs):
        return round(sum(xs) / len(xs), 4)
    fitted_sets = {json.dumps(r['fitted'], sort_keys=True) for r in results}
    summary = {
        'label': cfg['label'],
        'personas': len(results),
        'meanErrorDefault': mean([r['errorDefault']['mean'] for r in results]),
        'meanErrorFitted': mean([r['errorFitted']['mean'] for r in results]),
        'booleanMatchDefault': mean([r['errorDefault']['booleanMatch'] for r in results]),
        'booleanMatchFitted': mean([r['errorFitted']['booleanMatch'] for r in results]),
        'improvedPersonas': sum(r['errorFitted']['mean'] < r['errorDefault']['mean'] for r in results),
        'worsenedPersonas': sum(r['errorFitted']['mean'] > r['errorDefault']['mean'] for r in results),
        'distinctFittedSettings': len(fitted_sets),
        'meanClicks': mean([r['clicks'] for r in results]),
        'allSaved': all(r['savedToStorage'] for r in results),
        'pageErrors': sum(len(r['pageErrors']) for r in results),
        'perKeyResidual': {k: mean([abs(r['fitted'][k] - r['target'][k]) for r in results]) for k in NUMERIC},
    }
    Path(out).write_text(json.dumps({'summary': summary, 'results': results}, ensure_ascii=False, indent=1))
    print(json.dumps(summary, ensure_ascii=False, indent=1))


# A/B values mirror the fitting steps in web/dist/app.js (const steps)
STEPS = [
    {'key': 'brightness', 'a': 65, 'b': 90},
    {'key': 'contrast', 'a': 78, 'b': 105},
    {'key': 'volume', 'a': 22, 'b': 45},
    {'key': 'compression', 'a': True, 'b': False},
    {'key': 'easyCaptions', 'a': False, 'b': True},
]

if __name__ == '__main__':
    run(sys.argv[1], sys.argv[2])
