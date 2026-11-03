"""Render the PariView A1 poster to PDF and PNG.

Usage: uv run --with playwright python poster/render.py
Requires Google Chrome and Poppler (pdfinfo/pdftoppm) on PATH.
Serves the repo root locally so the poster can read web/dist data.
"""
import functools, http.server, json, subprocess, sys, threading
from pathlib import Path
from playwright.sync_api import sync_playwright

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
CHROME = '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome'


def main():
    handler = functools.partial(http.server.SimpleHTTPRequestHandler, directory=str(ROOT))
    server = http.server.ThreadingHTTPServer(('127.0.0.1', 0), handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    # Optional: render another copy, e.g. a versions/ snapshot — python3 poster/render.py poster/versions/v5/PariView_A1.html
    html = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else HERE / 'PariView_A1.html'
    out = html.parent
    url = f'http://127.0.0.1:{server.server_port}/{html.relative_to(ROOT).as_posix()}'
    pdf = out / 'PariView_A1.pdf'
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(executable_path=CHROME)
            page = browser.new_page(viewport={'width': 2245, 'height': 3179})
            page.goto(url)
            page.wait_for_function('document.body.dataset.layoutErrors !== undefined', timeout=60000)
            errors = json.loads(page.evaluate('document.body.dataset.layoutErrors'))
            if errors:
                raise SystemExit(f'Poster layout check failed: {errors}')
            page.pdf(path=str(pdf), width='594mm', height='841mm', print_background=True, prefer_css_page_size=True)
            browser.close()
    finally:
        server.shutdown()
    subprocess.run(['pdftoppm', '-singlefile', '-png', '-r', '300', '-scale-to-x', '7016', '-scale-to-y', '9933', str(pdf), str(out / 'PariView_A1_300dpi')], check=True)
    subprocess.run(['pdftoppm', '-singlefile', '-png', '-scale-to', '2000', str(pdf), str(out / 'PariView_A1_preview')], check=True)
    info = subprocess.run(['pdfinfo', str(pdf)], capture_output=True, text=True).stdout
    print('Created', pdf.name, 'PariView_A1_300dpi.png PariView_A1_preview.png')
    print('\n'.join(l for l in info.splitlines() if l.startswith(('Pages', 'Page size'))))


if __name__ == '__main__':
    main()
