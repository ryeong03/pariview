"""Build the two identical, reproducible install archives (no test artifacts)."""
from pathlib import Path
import shutil
import zipfile

root = Path(__file__).resolve().parent
repo = root.parent
files = ['manifest.json', 'settings.js', 'content.js', 'popup.html', 'popup.js', 'install.html', 'README.md']
files += [str(p.relative_to(root)) for p in sorted((root / 'icons').glob('*.png'))]
target = repo / 'pariview-extension.zip'
with zipfile.ZipFile(target, 'w', zipfile.ZIP_DEFLATED) as archive:
    for name in files:
        info = zipfile.ZipInfo(f'pariview-extension/{name}', (2026, 1, 1, 0, 0, 0))
        info.compress_type = zipfile.ZIP_DEFLATED
        info.external_attr = 0o644 << 16
        archive.writestr(info, (root / name).read_bytes())
shutil.copyfile(target, repo / 'web' / 'dist' / target.name)
print(f'Built two identical archives with {len(files)} files')
