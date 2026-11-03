"""HTTP and cache regressions for static gzip; no external network or API calls."""
import gzip
import http.client
import json
import os
from pathlib import Path
import shutil
import tempfile
import threading
import unittest
from unittest.mock import patch

from ai import server


class StaticGzipTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory()
        cls.root = Path(cls.temp.name).resolve()
        cls.text = (b'const message = "PariView repeated static content";\n' * 1000)
        for name in ['index.html', 'app.js', 'style.css', 'data.json', 'image.svg']:
            (cls.root / name).write_bytes(cls.text)
        cls.binary = bytes(range(256)) * 100
        for name in ['movie.mp4', 'extension.zip', 'font.woff2', 'image.png']:
            (cls.root / name).write_bytes(cls.binary)
        (cls.root / 'vendor').mkdir()
        for name in ['three.module.js', 'three.core.js']:
            shutil.copyfile(server.STATIC_ROOT / 'vendor' / name, cls.root / 'vendor' / name)
        cls.root_patch = patch.object(server, 'STATIC_ROOT', cls.root)
        cls.root_patch.start()
        cls.httpd = server.ThreadingHTTPServer(('127.0.0.1', 0), server.Handler)
        cls.thread = threading.Thread(target=cls.httpd.serve_forever, daemon=True)
        cls.thread.start()

    @classmethod
    def tearDownClass(cls):
        cls.httpd.shutdown()
        cls.httpd.server_close()
        cls.thread.join()
        cls.root_patch.stop()
        cls.temp.cleanup()

    def setUp(self):
        self.cache_patch = patch.object(server, 'GZIP_CACHE', server.StaticGzipCache())
        self.cache_patch.start()

    def tearDown(self):
        self.cache_patch.stop()

    def request(self, path='/app.js', method='GET', headers=None, body=None):
        connection = http.client.HTTPConnection(*self.httpd.server_address, timeout=5)
        connection.putrequest(method, path, skip_accept_encoding=True)
        for name, value in (headers or {}).items():
            connection.putheader(name, value)
        if body is not None:
            connection.putheader('Content-Length', str(len(body)))
        connection.endheaders(body)
        response = connection.getresponse()
        result = response.status, dict(response.getheaders()), response.read()
        connection.close()
        return result

    def test_text_types_gzip_content_and_headers(self):
        for path, mime in [('/index.html','text/html'),('/app.js','application/javascript'),('/style.css','text/css'),('/data.json','application/json'),('/image.svg','image/svg+xml')]:
            with self.subTest(path=path):
                status, headers, body = self.request(path, headers={'Accept-Encoding': 'br, gzip, deflate'})
                self.assertEqual(status, 200)
                self.assertEqual(headers['Content-Encoding'], 'gzip')
                self.assertEqual(headers['Vary'], 'Accept-Encoding')
                self.assertEqual(headers['Cache-Control'], 'no-cache, no-transform')
                self.assertEqual(headers['Content-Type'], mime)
                self.assertEqual(int(headers['Content-Length']), len(body))
                self.assertEqual(gzip.decompress(body), self.text)
                self.assertLess(len(body), len(self.text))

    def test_encoding_quality_and_explicit_exclusions(self):
        cases = [(None,False),('',False),('br',False),('gzip;q=0',False),('gzip; q=0.000, *;q=1',False),
                 ('gzip;q=0, identity;q=1',False),('gzip;q=0.2, identity;q=0.8',False),
                 ('GZip ; Q=0.5',True),('*;q=0.8',True),('gzip;q=1, identity;q=0',True),
                 ('*;q=0, gzip;q=1',True),('gzip;q=0.8, identity;q=0.2',True),
                 ('gzip;q=bad',False),('gzip;q=nan',False),('gzip;q=0,gzip',False)]
        for encoding, compressed in cases:
            with self.subTest(encoding=encoding):
                status, headers, body = self.request(headers={} if encoding is None else {'Accept-Encoding': encoding})
                self.assertEqual(status, 200)
                self.assertEqual('Content-Encoding' in headers, compressed)
                self.assertEqual(gzip.decompress(body) if compressed else body, self.text)
                self.assertEqual(headers['Vary'], 'Accept-Encoding')

    def test_head_matches_selected_get_representation_without_body(self):
        for encoding in ['gzip', 'gzip;q=0', 'identity']:
            with self.subTest(encoding=encoding):
                status, headers, body = self.request(headers={'Accept-Encoding': encoding})
                head_status, head_headers, head_body = self.request(method='HEAD', headers={'Accept-Encoding': encoding})
                self.assertEqual((status, head_status), (200, 200))
                self.assertEqual(head_body, b'')
                for key in ['Content-Encoding','Content-Length','Content-Type','Vary','Cache-Control','Accept-Ranges']:
                    self.assertEqual(headers.get(key), head_headers.get(key))
                self.assertEqual(len(body), int(head_headers['Content-Length']))

    def test_edge_gzip_exclusions_have_no_transform_on_get_and_head(self):
        raw = (self.root / 'vendor/three.module.js').read_bytes()
        for encoding in ['gzip;q=0,*;q=1', 'gzip;q=0,identity;q=1,*;q=0']:
            for method in ['GET', 'HEAD']:
                with self.subTest(encoding=encoding, method=method):
                    status, headers, body = self.request('/vendor/three.module.js', method=method, headers={'Accept-Encoding':encoding})
                    self.assertEqual(status,200)
                    self.assertEqual(headers['Cache-Control'],'no-cache, no-transform')
                    self.assertEqual(headers['Vary'],'Accept-Encoding')
                    self.assertNotIn('Content-Encoding',headers)
                    self.assertEqual(int(headers['Content-Length']),len(raw))
                    self.assertEqual(body,raw if method=='GET' else b'')

    def test_range_and_head_range_keep_identity_bytes(self):
        for path, raw in [('/app.js',self.text),('/movie.mp4',self.binary),('/extension.zip',self.binary)]:
            for value, begin, end in [('bytes=0-19',0,19),('bytes=-20',len(raw)-20,len(raw)-1),('bytes=20-',20,len(raw)-1)]:
                with self.subTest(path=path, value=value):
                    status, headers, body = self.request(path, headers={'Accept-Encoding':'gzip','Range':value})
                    self.assertEqual(status,206)
                    self.assertEqual(headers['Cache-Control'],'no-cache, no-transform')
                    self.assertNotIn('Content-Encoding',headers)
                    self.assertEqual(headers['Content-Range'],f'bytes {begin}-{end}/{len(raw)}')
                    self.assertEqual(body,raw[begin:end+1])
                    self.assertEqual(int(headers['Content-Length']),len(body))
            status, headers, body = self.request(path,method='HEAD',headers={'Accept-Encoding':'gzip','Range':'bytes=0-19'})
            self.assertEqual(status,200)
            self.assertEqual(body,b'')
            self.assertNotIn('Content-Encoding',headers)
            self.assertEqual(int(headers['Content-Length']),len(raw))
            status, headers, body = self.request(path,headers={'Accept-Encoding':'gzip','Range':f'bytes={len(raw)}-'})
            self.assertEqual(status,416)
            self.assertEqual(headers['Content-Range'],f'bytes */{len(raw)}')
            self.assertEqual(body,b'')

    def test_already_compressed_assets_are_unchanged(self):
        for path in ['/movie.mp4','/extension.zip','/font.woff2','/image.png']:
            with self.subTest(path=path):
                status, headers, body = self.request(path,headers={'Accept-Encoding':'gzip'})
                self.assertEqual(status,200)
                self.assertNotIn('Content-Encoding',headers)
                self.assertEqual(body,self.binary)
                self.assertEqual(int(headers['Content-Length']),len(self.binary))

    def test_no_acceptable_representation_returns_empty_406(self):
        for encoding in ['gzip;q=0, identity;q=0','*;q=0']:
            for method in ['GET','HEAD']:
                status,headers,body=self.request(method=method,headers={'Accept-Encoding':encoding})
                self.assertEqual(status,406)
                self.assertEqual(headers['Content-Length'],'0')
                self.assertEqual(headers['Vary'],'Accept-Encoding')
                self.assertEqual(body,b'')

    def test_api_contract_stays_uncompressed(self):
        status,headers,body=self.request('/api/recommendation/status',headers={'Accept-Encoding':'gzip'})
        self.assertEqual(status,200)
        self.assertNotIn('Content-Encoding',headers)
        self.assertEqual(headers['Cache-Control'],'no-store')
        self.assertEqual(json.loads(body)['provider'],'anthropic')
        status,headers,body=self.request('/api/recommendation',method='POST',headers={'Content-Type':'application/json','Accept-Encoding':'gzip'},body=b'{"useAI":false}')
        self.assertEqual(status,200)
        self.assertNotIn('Content-Encoding',headers)
        self.assertEqual(json.loads(body)['source'],'rules')
        self.assertEqual(headers['Cache-Control'],'no-store')
        status,headers,body=self.request('/healthz',headers={'Accept-Encoding':'gzip'})
        self.assertEqual(status,200)
        self.assertEqual(headers['Cache-Control'],'no-cache')
        self.assertNotIn('Content-Encoding',headers)

    def test_cache_reuse_and_same_size_mtime_invalidation(self):
        path=self.root/'changing.js';path.write_bytes(b'a'*5000)
        with patch.object(server.gzip,'compress',wraps=gzip.compress) as compress:
            first=self.request('/changing.js',headers={'Accept-Encoding':'gzip'})[2]
            self.assertEqual(self.request('/changing.js',headers={'Accept-Encoding':'gzip'})[2],first)
            self.assertEqual(compress.call_count,1)
            before=path.stat();path.write_bytes(b'b'*5000)
            os.utime(path,ns=(before.st_atime_ns,before.st_mtime_ns+1_000_000))
            second=self.request('/changing.js',headers={'Accept-Encoding':'gzip'})[2]
            self.assertEqual(gzip.decompress(second),b'b'*5000)
            self.assertEqual(compress.call_count,2)

    def test_cache_byte_entry_and_source_limits(self):
        for limits in [{'max_bytes':50,'max_entries':10},{'max_bytes':1000,'max_entries':2}]:
            cache=server.StaticGzipCache(**limits)
            with patch.object(server,'GZIP_CACHE',cache):
                for index in range(4):
                    name=f'/small-{index}.js';(self.root/name.lstrip('/')).write_bytes(bytes([65+index])*1000)
                    self.request(name,headers={'Accept-Encoding':'gzip'})
                self.assertLessEqual(cache.bytes,limits['max_bytes'])
                self.assertLessEqual(len(cache.entries),limits['max_entries'])
                self.assertEqual(cache.bytes,sum(len(entry[1]) for entry in cache.entries.values()))
        with patch.object(server,'GZIP_CACHE',server.StaticGzipCache(max_source_bytes=10)):
            status,headers,body=self.request(headers={'Accept-Encoding':'gzip'})
            self.assertEqual(status,200)
            self.assertNotIn('Content-Encoding',headers)
            self.assertEqual(body,self.text)

    def test_three_js_transfer_reduction_and_lossless_payload(self):
        measurements=[]
        for name in ['three.module.js','three.core.js']:
            raw=(self.root/'vendor'/name).read_bytes()
            status,headers,body=self.request('/vendor/'+name,headers={'Accept-Encoding':'gzip'})
            self.assertEqual(status,200)
            self.assertEqual(gzip.decompress(body),raw)
            self.assertLess(len(body),len(raw)*0.4)
            measurements.append({'file':name,'originalBytes':len(raw),'gzipBytes':len(body),'reductionPercent':round(100*(1-len(body)/len(raw)),1)})
        print('\nThree.js transfer:',json.dumps(measurements))


if __name__=='__main__':
    unittest.main()
