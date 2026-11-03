"""Local PariView preview, including byte-range video requests. No deployment or Git actions."""
from http.server import SimpleHTTPRequestHandler,ThreadingHTTPServer
from pathlib import Path
import re,shutil
ROOT=Path(__file__).resolve().parent/'dist'
class Handler(SimpleHTTPRequestHandler):
 def __init__(self,*args,**kwargs):super().__init__(*args,directory=str(ROOT),**kwargs)
 def send_head(self):
  self.partial=None
  path=Path(self.translate_path(self.path))
  if not path.is_file():return super().send_head()
  size=path.stat().st_size;range_value=self.headers.get('Range')
  if not range_value:return super().send_head()
  match=re.fullmatch(r'bytes=(\d*)-(\d*)',range_value.strip())
  if not match:return super().send_head()
  a,b=match.groups();start=int(a) if a else max(0,size-int(b or 0));end=min(int(b),size-1) if b and a else size-1
  if start>=size or start>end:
   self.send_response(416);self.send_header('Content-Range',f'bytes */{size}');self.end_headers();return None
  f=path.open('rb');f.seek(start);self.partial=end-start+1
  self.send_response(206);self.send_header('Content-Type',self.guess_type(str(path)));self.send_header('Content-Length',str(self.partial));self.send_header('Content-Range',f'bytes {start}-{end}/{size}');self.end_headers();return f
 def end_headers(self):
  self.send_header('Accept-Ranges','bytes');self.send_header('Cache-Control','no-cache');super().end_headers()
 def copyfile(self,source,output):
  if self.partial is None:return super().copyfile(source,output)
  remaining=self.partial
  while remaining:
   block=source.read(min(65536,remaining))
   if not block:break
   output.write(block);remaining-=len(block)
 def log_message(self,*args):pass
print('PariView preview: http://127.0.0.1:4178',flush=True)
ThreadingHTTPServer(('127.0.0.1',4178),Handler).serve_forever()
