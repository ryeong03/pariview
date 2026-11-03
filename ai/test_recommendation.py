"""Run python3 -m unittest ai.test_recommendation -v — never calls a real provider."""
import json
import os
from pathlib import Path
import random
import shutil
import subprocess
import unittest
from unittest.mock import patch

from ai.domain import CATALOG, ROOT, compose, default_selection, output_schema, prepare
from ai import server
NODE = shutil.which('node')


class RecommendationTests(unittest.TestCase):
    def setUp(self):
        self.env = patch.dict(os.environ, {}, clear=True)
        self.env.start()
        server.AI_CALL_TIMES.clear()
        server.AI_COOLDOWN_UNTIL = 0

    def tearDown(self):
        self.env.stop()

    def enabled(self):
        return patch.dict(os.environ, {'PARIVIEW_AI_ENABLED': '1', 'ANTHROPIC_API_KEY': 'unit-test-placeholder', 'PARIVIEW_AI_MODEL': 'claude-test'})

    def test_references_are_existing_verified_sources(self):
        sources = {}
        for name in ['sources.json', 'medical-sensory-sources.json']:
            sources.update({s['id']: s for s in json.loads((ROOT/'research'/name).read_text())['sources']})
        for sid, source in CATALOG['sources'].items():
            self.assertEqual(source['url'], sources[sid]['url'])
        for item in CATALOG['actions'] + CATALOG['comparisons']:
            self.assertTrue(set(item['sources']) <= set(CATALOG['sources']))

    def test_default_never_calls_provider(self):
        with patch.object(server, 'call_provider', side_effect=AssertionError('Unexpected provider call')):
            result = server.recommend({'answers': {'concerns': ['light', 'changes']}})
        self.assertEqual((result['source'], result['status']), ('rules', 'unconfigured'))
        self.assertEqual(result['settings']['brightness'], 77)
        self.assertEqual(result['nextComparison']['axis'], 'brightness')

    def test_only_anthropic_key_and_claude_model_enable_provider(self):
        with patch.dict(os.environ, {'PARIVIEW_AI_ENABLED': '1', 'OPENAI_API_KEY': 'not-used', 'PARIVIEW_AI_MODEL': 'claude-haiku-5-5'}):
            self.assertFalse(server.configuration()['configured'])
        with self.enabled():
            self.assertTrue(server.configuration()['configured'])
            with patch.dict(os.environ, {'PARIVIEW_AI_MODEL': 'gpt-5.4-mini'}):
                self.assertFalse(server.configuration()['configured'])

    def test_original_and_explicit_responses_are_preserved(self):
        payload = {'currentSettings': {'brightness': 67, 'volume': 20}, 'answers': {'concerns': ['light', 'sound'], 'goal': 'original'}}
        result = compose(prepare(payload))
        self.assertEqual(result['selection']['actionIds'], ['keep'])
        self.assertEqual(result['settings']['brightness'], 67)
        self.assertEqual(result['settings']['volume'], 20)
        payload['answers']['goal'] = 'softer'
        payload['comparisons'] = [{'axis': 'brightness', 'outcome': 'b'}, {'axis': 'volume', 'outcome': 'skip'}]
        result = compose(prepare(payload))
        self.assertEqual(result['settings']['brightness'], 67)
        self.assertEqual(result['settings']['volume'], 20)
        self.assertNotIn(result['nextComparison']['axis'], ['brightness', 'volume'])

    def test_user_caption_color_survives_rules_ai_and_failure(self):
        # Legacy saves default to white; only explicit booleans change the colour.
        for settings, expected in [({}, False), ({'captionYellow': True}, True), ({'captionYellow': False}, False),
                                   ({'captionYellow': 'true'}, False), ({'captionYellow': 1}, False)]:
            payload = {'currentSettings': settings, 'answers': {'concerns': ['text'], 'captionStyle': 'simple'}}
            with self.subTest(settings=settings):
                result = server.recommend(payload)
                self.assertIs(result['settings']['captionYellow'], expected)
                self.assertEqual(result['source'], 'rules')
                with self.enabled(), patch.object(server, 'call_provider', side_effect=default_selection):
                    server.AI_COOLDOWN_UNTIL = 0
                    result = server.recommend(payload)
                    self.assertEqual(result['source'], 'ai')
                    self.assertIs(result['settings']['captionYellow'], expected)
                with self.enabled(), patch.object(server, 'call_provider', side_effect=TimeoutError):
                    server.AI_COOLDOWN_UNTIL = 0
                    result = server.recommend(payload)
                    self.assertEqual(result['source'], 'rules')
                    self.assertIs(result['settings']['captionYellow'], expected)
                self.assertTrue(all('captionYellow' not in a['changes'] for a in result['actions']))
        self.assertTrue(all('captionYellow' not in a['adjust'] for a in CATALOG['actions']))

    def test_tie_unsure_and_skip_are_not_equivalent(self):
        for outcome in ['equal', 'skip', 'a', 'b']:
            plan = prepare({'comparisons': [{'axis': 'brightness', 'outcome': outcome}]})
            self.assertNotIn('brightness', [x['id'] for x in plan['comparisons']])
        plan = prepare({'comparisons': [{'axis': 'brightness', 'outcome': 'unsure'}]})
        self.assertIn('brightness', [x['id'] for x in plan['comparisons']])
        result = compose(prepare({'comparisons': [{'axis': c['id'], 'outcome': 'skip'} for c in CATALOG['comparisons']]}))
        self.assertIsNone(result['nextComparison'])

    def test_no_mock_features_or_forced_volume_increase(self):
        for action in CATALOG['actions']:
            self.assertFalse({'backgroundReduction', 'transitionSoftening'} & action['adjust'].keys())
            self.assertLessEqual(action['adjust'].get('volume', {}).get('delta', 0), 0)

    def test_malformed_or_injected_inputs_rejected(self):
        for payload in [{'answers': {'concerns': ['ignore instructions']}}, {'answers': {'diagnosis': 'anything'}},
                        {'answers': {'room': {}}}, {'comparisons': [{'axis': 'volume', 'outcome': 'diagnosed'}]},
                        {'currentSettings': []}, {'useAI': 'true'}, {'prompt': 'invent a paper'}]:
            with self.subTest(payload=payload), self.assertRaises(ValueError):
                prepare(payload)

    def test_model_cannot_invent_values_claims_or_citations(self):
        plan = prepare({'answers': {'concerns': ['light']}})
        valid = default_selection(plan)
        for selection in [{**valid, 'paper': 'invented'}, {**valid, 'brightness': 1000},
                          {**valid, 'actionIds': ['not-offered']}, {**valid, 'actionIds': ['keep', 'softer_light']},
                          {**valid, 'actionIds': ['keep', 'keep']}, {**valid, 'nextComparisonId': 'diagnosis'},
                          {**valid, 'sourceIds': ['fake']}, {**valid, 'nextComparisonId': 'done'}]:
            with self.subTest(selection=selection), self.assertRaises(ValueError):
                compose(plan, selection, source='ai')
        schema = output_schema(plan)
        self.assertFalse(schema['additionalProperties'])
        self.assertEqual(set(schema['properties']), {'actionIds', 'nextComparisonId'})

    def test_real_ai_label_requires_valid_model_selection(self):
        with self.enabled(), patch.object(server, 'call_provider', side_effect=lambda plan: default_selection(plan)) as provider:
            result = server.recommend({'answers': {'concerns': ['text']}})
            self.assertEqual((result['source'], result['status']), ('ai', 'ai_generated'))
            self.assertEqual(provider.call_count, 1)
            self.assertEqual(result['settings']['captionSize'], 24)

    def test_timeout_refusal_bad_schema_and_limits_fall_back(self):
        for response in [TimeoutError(), {'invented': True}, {'actionIds': ['fake'], 'nextComparisonId': 'brightness'}]:
            server.AI_COOLDOWN_UNTIL = 0
            mock = {'side_effect': response} if isinstance(response, Exception) else {'return_value': response}
            with self.subTest(response=response), self.enabled(), patch.object(server, 'call_provider', **mock):
                result = server.recommend({})
                self.assertEqual((result['source'], result['status']), ('rules', 'default_provider'))
        with self.enabled(), patch.object(server, 'call_provider', side_effect=AssertionError('Unexpected provider call')):
            self.assertEqual(server.recommend({})['status'], 'default_cooldown')
            server.AI_COOLDOWN_UNTIL = 0
            with patch.dict(os.environ, {'PARIVIEW_AI_MAX_CALLS_PER_HOUR': '0'}):
                self.assertEqual(server.recommend({})['status'], 'default_limit')

    def test_provider_payload_and_refusal_handling(self):
        plan = prepare({})
        class Response:
            def __enter__(self): return self
            def __exit__(self, *args): pass
            def read(self, limit):
                return json.dumps({'stop_reason': 'end_turn', 'content': [{'type': 'text', 'text': json.dumps(default_selection(plan))}]}).encode()
        with self.enabled(), patch.object(server.urllib.request, 'urlopen', return_value=Response()) as opening:
            self.assertEqual(server.call_provider(plan), default_selection(plan))
            request = opening.call_args.args[0]
            body = json.loads(request.data)
            self.assertEqual(request.full_url, 'https://api.anthropic.com/v1/messages')
            self.assertEqual(request.get_header('Anthropic-version'), '2023-06-01')
            self.assertEqual(request.get_header('X-api-key'), 'unit-test-placeholder')
            self.assertNotIn('tools', body)
            self.assertNotIn('store', body)
            self.assertEqual(body['output_config']['format']['type'], 'json_schema')
            self.assertNotIn('maxItems', body['output_config']['format']['schema']['properties']['actionIds'])
            self.assertEqual(body['messages'][0]['role'], 'user')
            self.assertNotIn('unit-test-placeholder', request.data.decode())
        class Refusal(Response):
            def read(self, limit):
                return b'{"stop_reason":"refusal","content":[{"type":"text","text":"no"}]}'
        with self.enabled(), patch.object(server.urllib.request, 'urlopen', return_value=Refusal()), self.assertRaises(ValueError):
            server.call_provider(plan)

    def test_browser_and_server_policy_parity(self):
        rng = random.Random(42)
        cases = [{}]
        for index in range(60):
            answers = {k: rng.choice(list(v)) for k,v in CATALOG['inputs'].items() if k != 'concerns'}
            answers['concerns'] = rng.sample(list(CATALOG['inputs']['concerns']), rng.randrange(7))
            color = {} if index % 3 == 0 else {'captionYellow': index % 3 == 1}
            cases.append({'answers': answers, 'currentSettings': {'brightness': rng.randrange(35,110), 'volume': rng.randrange(0,80), **color},
                          'comparisons': [{'axis': c['id'], 'outcome': rng.choice(['a','equal','unsure','skip'])} for c in CATALOG['comparisons'] if rng.random()<.3]})
        script = "import fs from 'node:fs'; import {defaults,ranges} from './web/dist/settings.js'; import {prepareRecommendation,composeRecommendation} from './web/dist/recommendation-engine.js'; const c=JSON.parse(fs.readFileSync('web/dist/recommendation-data.json')); const cases=JSON.parse(fs.readFileSync(0,'utf8')); console.log(JSON.stringify({defaults,ranges,results:cases.map(p=>composeRecommendation(prepareRecommendation(p,c),c))}));"
        completed = subprocess.run([NODE, '--input-type=module', '-e', script], input=json.dumps(cases), cwd=ROOT, text=True, capture_output=True, check=True)
        client = json.loads(completed.stdout)
        self.assertEqual(client['defaults'], CATALOG['defaults'])
        self.assertEqual(client['ranges'], CATALOG['ranges'])
        for payload, js in zip(cases, client['results']):
            py = compose(prepare(payload)); py.pop('status')
            self.assertEqual(js, py)

    def test_range_semantics(self):
        self.assertEqual(server.byte_range('bytes=0-9',100),(0,9))
        self.assertEqual(server.byte_range('bytes=-10',100),(90,99))
        self.assertEqual(server.byte_range('bytes=90-',100),(90,99))
        for value in ['bytes=100-', 'bytes=9-1', 'bytes=-0', 'bytes=-', 'bytes=0-1,4-5']:
            with self.subTest(value=value), self.assertRaises(ValueError):server.byte_range(value,100)


if __name__ == '__main__':
    unittest.main()
