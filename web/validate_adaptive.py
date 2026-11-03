"""Browser checks for adaptive fitting; all recommendation provider responses are mocked.

uv run --with playwright python web/validate_adaptive.py --base-url http://127.0.0.1:4207
"""
import argparse
import json
from pathlib import Path
from playwright.sync_api import sync_playwright


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--base-url', default='http://127.0.0.1:4207')
    args = parser.parse_args()
    checks = []
    with sync_playwright() as p:
        browser = p.chromium.launch(executable_path='/Applications/Google Chrome.app/Contents/MacOS/Google Chrome', args=['--autoplay-policy=no-user-gesture-required'])
        page = browser.new_page(viewport={'width': 1280, 'height': 720}, accept_downloads=True)
        errors = []
        page.on('pageerror', lambda e: errors.append(str(e)))
        page.add_init_script("sessionStorage.setItem('pariview-scene-adapt-off','1')")
        page.route('**/api/recommendation/status', lambda r: r.fulfill(json={'configured': False}))
        unexpected = []
        page.route('**/api/recommendation', lambda r: (unexpected.append(r.request.url), r.abort()))
        page.goto(args.base_url, wait_until='networkidle')
        page.wait_for_function('window.__pariview')
        state = lambda: page.evaluate('window.__pariview.fitState')
        question = lambda: page.evaluate('window.__pariview.fitQuestion')
        settings = lambda: page.evaluate('window.__pariview.settings')
        stored = lambda: page.evaluate("localStorage.getItem('pariview-fit-v1')")

        def start():
            page.evaluate('window.__pariview.openFit()')
            page.locator('#mode-current').click()

        def answer(outcome):
            if outcome == 'skip':
                page.locator('#skip-step').click()
            else:
                selector = f'[data-choose="{outcome}"]' if outcome in ('a', 'b') else '#choose-' + outcome
                page.locator(selector).click()
                page.locator('#fit-next').click()

        def download():
            page.locator('.fit-records summary').click()
            with page.expect_download() as info:
                page.locator('#download-fit-records').click()
            assert info.value.suggested_filename == 'pariview-comparison-record.json'
            return json.loads(Path(info.value.path()).read_text())

        base, storage = settings(), stored()
        start()
        first = question()
        for choice in ['a', 'b', 'a']:
            page.locator(f'[data-choose="{choice}"]').click()
            assert state()['answered'] == 0
        page.locator('#finish-fitting').click()
        assert state()['answered'] == 0 and state()['settings'] == base
        assert not page.evaluate('window.__pariview.fitSnapshot.history.length')
        page.keyboard.press('Escape')
        assert settings() == base and stored() == storage
        checks.append('pending choice is neither counted nor saved on early finish or cancel')

        start()
        low_questions = []
        for _ in range(3):
            q = question(); low_questions.append(q)
            answer('a' if q['a'] < q['b'] else 'b')
        low_next = question()
        for _ in range(3):
            page.locator('#fit-back').click()
        assert question()['id'] == low_questions[0]['id']
        assert question()['a'] == low_questions[0]['a'] and state()['answered'] == 0
        for _ in range(3):
            q = question(); answer('a' if q['a'] > q['b'] else 'b')
        high_next = question()
        assert (low_next['axis'], low_next['canonical']) != (high_next['axis'], high_next['canonical'])
        assert len({q['axis'] for q in low_questions}) == 3
        answer('equal'); answer('unsure')
        assert state()['answered'] == 5 and state()['counts']['effective'] == 3
        assert state()['counts']['equal'] == 1 and state()['counts']['unsure'] == 1
        report = download()
        assert len(report['history']) == 5 and len(report['comparisons']) == 5
        assert report['context']['clipId'] == 'tears-lab' and report['context']['playbackRate'] == .75
        assert not any(key in json.dumps(report) for key in ['experience', 'participantName', 'email'])
        assert stored() == storage
        checks.append('undo restores the pair; opposite preferences change the fourth pair; download includes actual choices and context')

        before = page.evaluate('window.__pariview.fitSnapshot.posterior')
        page.locator('#continue-fit').click()
        assert state()['budget'] == 10 and state()['answered'] == 5
        assert page.evaluate('window.__pariview.fitSnapshot.posterior') == before
        for _ in range(5): answer('skip')
        assert state()['counts']['skip'] == 5
        for expected in [15, 20]:
            page.locator('#continue-fit').click()
            assert state()['budget'] == expected
            for _ in range(5): answer('skip')
        assert state()['answered'] == 20 and not state()['canExtend']
        assert page.locator('#continue-fit').is_hidden()
        page.keyboard.press('Escape')
        assert settings() == base and stored() == storage
        checks.append('additional comparisons preserve estimates and stop at twenty; cancel never writes settings')

        start()
        for _ in range(5): answer('a')
        old = page.evaluate('window.__pariview.fitSnapshot')
        page.locator('#result-compression').click()
        changed = not old['initialSettings']['compression']
        assert '다시 비교' in page.locator('#continue-fit').inner_text()
        page.locator('#continue-fit').click()
        assert state()['answered'] == 0 and state()['budget'] == 5
        assert state()['settings']['compression'] == changed
        assert page.evaluate('window.__pariview.fitSnapshot.context.fixedOptions.compression') == changed
        q = question()
        assert q['axis'] == 'volume'
        lower = 'a' if q['a'] < q['b'] else 'b'
        page.locator(f'[data-listen="{lower}"]').click()
        page.wait_for_function('window.__pariview.comparisonPlaying')
        assert page.evaluate('window.__pariview.audioRoute') == ('compressed' if changed else 'original')
        page.locator('#finish-fitting').click()
        report = download()
        assert len(report['previousSessions']) == 1
        assert report['previousSessions'][0]['context']['fixedOptions']['compression'] != changed
        assert len(report['previousSessions'][0]['history']) == 5
        assert len(report['history']) == 0
        page.locator('#apply-fit').click()
        assert settings()['compression'] == changed and stored() != storage
        page.reload(wait_until='networkidle')
        assert settings()['compression'] == changed
        checks.append('option changes start a new estimate and audible route; old conditions remain in the export; only apply persists')

        # A recommendation can still enter an explicit boolean A/B comparison.
        version = page.evaluate("fetch('/recommendation-data.json').then(r=>r.json()).then(d=>d.version)")
        page.unroute('**/api/recommendation/status')
        page.route('**/api/recommendation/status', lambda r: r.fulfill(json={'configured': True}))
        page.unroute('**/api/recommendation')
        page.route('**/api/recommendation', lambda r: r.fulfill(json={'source': 'ai', 'status': 'ai_generated', 'evidenceVersion': version, 'selection': {'actionIds': ['sound_changes'], 'nextComparisonId': 'compression', 'startingModeId': 'gentle'}}))
        page.evaluate('window.__pariview.recommendationUI.open()')
        page.locator('#pv-rec-experience').fill('폭발 장면에서 깜짝 놀라요')
        page.locator('.pv-rec-form [type=submit]').click()
        page.locator('[data-compare]').click()
        assert question()['key'] == 'compression' and state() is None
        answer('b')
        page.locator('#continue-fit').click()
        assert state()['settings']['compression'] is False
        answer('skip'); page.locator('#finish-fitting').click()
        report = download()
        assert [r['axis'] for r in report['comparisons']] == ['compression', 'volume']
        assert report['comparisons'][0]['outcome'] == 'b'
        assert len(report['history']) == 1
        page.keyboard.press('Escape')
        checks.append('mock recommendation boolean comparison carries its choice into numeric fitting and exported UI records')

        assert not unexpected and not errors
        browser.close()
    print(json.dumps({'checks': checks, 'passed': len(checks), 'errors': errors, 'provider': 'mock only'}, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
