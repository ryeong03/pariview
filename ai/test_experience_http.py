"""Local HTTP contract checks with dummy credentials and mocked Claude only."""
from contextlib import redirect_stderr, redirect_stdout
import http.client
import io
import json
import os
import threading
import unittest
from unittest.mock import patch

from ai import server


class ExperienceHTTPTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.httpd = server.ThreadingHTTPServer(('127.0.0.1', 0), server.Handler)
        cls.httpd.daemon_threads = True
        cls.worker = threading.Thread(target=cls.httpd.serve_forever, daemon=True)
        cls.worker.start()

    @classmethod
    def tearDownClass(cls):
        cls.httpd.shutdown()
        cls.httpd.server_close()
        cls.worker.join(timeout=2)

    def setUp(self):
        self.env = patch.dict(os.environ, {}, clear=True)
        self.env.start()
        server.AI_CALL_TIMES.clear()
        server.AI_COOLDOWN_UNTIL = 0

    def tearDown(self):
        self.env.stop()

    def request(self, payload):
        host, port = self.httpd.server_address
        connection = http.client.HTTPConnection(host, port, timeout=5)
        try:
            connection.request('POST', '/api/recommendation', body=json.dumps(payload).encode(),
                               headers={'Content-Type': 'application/json', 'Origin': f'http://{host}:{port}'})
            response = connection.getresponse()
            return response.status, response.getheader('Cache-Control'), json.loads(response.read())
        finally:
            connection.close()

    def test_experience_only_and_trimmed_maximum_use_default_answers(self):
        for text in ['폭발 장면에서 깜짝 놀라요', ' \n' + '🎬' * 300 + '\t ']:
            with patch.object(server, 'call_provider') as provider:
                status, cache, result = self.request({'experience': text})
            provider.assert_not_called()
            self.assertEqual(status, 200)
            self.assertEqual(cache, 'no-store')
            self.assertEqual((result['source'], result['status']), ('rules', 'unconfigured'))
            self.assertEqual(result['selection']['actionIds'], ['keep'])
            self.assertEqual(result['selection']['startingModeId'], 'keep')
            self.assertNotIn(text.strip(), json.dumps(result, ensure_ascii=False))

    def test_invalid_text_returns_generic_400_without_provider_or_body_log(self):
        invalid = [None, True, 7, [], {}, 'private-viewing-marker-' * 20, '🎬' * 301, '\ud800']
        for value in invalid:
            stdout, stderr = io.StringIO(), io.StringIO()
            with self.subTest(kind=type(value).__name__), patch.object(server, 'call_provider') as provider, \
                    redirect_stdout(stdout), redirect_stderr(stderr):
                status, cache, result = self.request({'experience': value})
            provider.assert_not_called()
            self.assertEqual((status, result), (400, {'error': 'invalid_request'}))
            self.assertEqual(cache, 'no-store')
            self.assertEqual(stdout.getvalue() + stderr.getvalue(), '')

    def test_mock_claude_experience_reaches_validated_mode_and_settings(self):
        selection = {'actionIds': ['sound_changes'], 'nextComparisonId': 'compression', 'startingModeId': 'gentle'}
        payload = {'experience': '  폭발 장면에서 깜짝 놀라요  ',
                   'currentSettings': {'volume': 28, 'compression': False, 'notices': False, 'captionYellow': True}}
        with patch.dict(os.environ, {'PARIVIEW_AI_ENABLED': '1', 'ANTHROPIC_API_KEY': 'unit-test-placeholder',
                                    'PARIVIEW_AI_MODEL': 'claude-test'}), \
                patch.object(server, 'call_provider', return_value=selection) as provider:
            status, cache, result = self.request(payload)
        self.assertEqual((status, cache), (200, 'no-store'))
        self.assertEqual(provider.call_args.args[0]['experience'], payload['experience'].strip())
        self.assertEqual((result['source'], result['status']), ('ai', 'ai_generated'))
        self.assertEqual(result['settings']['profileId'], 'gentle')
        self.assertEqual(result['settings']['volume'], 28)
        self.assertIs(result['settings']['captionYellow'], True)
        self.assertIs(result['settings']['compression'], True)
        self.assertIs(result['settings']['notices'], True)
        self.assertNotIn('experience', result)


if __name__ == '__main__':
    unittest.main()
