"""Build reproducible development and Chrome Web Store archives."""
from pathlib import Path
import shutil
import zipfile

root = Path(__file__).resolve().parent
repo = root.parent
files = ['manifest.json', 'settings.js', 'content.js', 'popup.html', 'popup.js', 'install.html', 'privacy.html', 'README.md']
files += [str(p.relative_to(root)) for p in sorted((root / 'icons').glob('*.png'))]
files += ['LICENSE']
def build(target, prefix):
    with zipfile.ZipFile(target, 'w', zipfile.ZIP_DEFLATED) as archive:
        for name in files:
            info = zipfile.ZipInfo(f'{prefix}{name}', (2026, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o644 << 16
            source = repo / name if name == 'LICENSE' else root / name
            archive.writestr(info, source.read_bytes())

target = repo / 'pariview-extension.zip'
build(target, 'pariview-extension/')
shutil.copyfile(target, repo / 'web' / 'dist' / target.name)
build(repo / 'pariview-webstore.zip', '')
print(f'Built two identical development archives and one root-manifest Web Store archive, {len(files)} files each')
