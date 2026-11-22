#!/usr/bin/env python3
"""Build a deterministic offline Loss Lab manual bundle from current documentation.

The bundle contains the manual plus any external UI captures it references.
Self-contained manuals already carry their screenshots as embedded image data.
Deterministic ZIP metadata prevents repeated GitHub Actions self-triggered pushes.
"""
from pathlib import Path
from zipfile import ZipFile, ZipInfo, ZIP_DEFLATED
from html.parser import HTMLParser
import re

ROOT = Path(__file__).resolve().parents[2]
DIR = ROOT / "dist" / "tools" / "loss-lab"
MANUAL = DIR / "manual.html"
ZIP = DIR / "Loss_Lab_Manual_Offline.zip"
html = MANUAL.read_text(encoding="utf-8")
images = sorted(set(re.findall(r'src="(screenshots/[a-z0-9_-]+\.png)"', html)))

class EmbeddedImages(HTMLParser):
    count = 0

    def handle_starttag(self, tag, attrs):
        if tag == 'img' and dict(attrs).get('src', '').startswith('data:image/'):
            self.count += 1

embedded = EmbeddedImages()
embedded.feed(html)
if not images and not embedded.count:
    raise SystemExit("No real screenshots referenced by manual; refusing empty offline bundle.")

members = [("manual.html", MANUAL)]
for rel in images:
    path = DIR / rel
    if not path.is_file():
        raise SystemExit(f"Missing screenshot referenced by manual: {rel}")
    members.append((rel, path))

with ZipFile(ZIP, "w", compression=ZIP_DEFLATED, compresslevel=8) as zipfile:
    for name, path in members:
        info = ZipInfo(name, date_time=(2026, 1, 1, 0, 0, 0))
        info.compress_type = ZIP_DEFLATED
        info.external_attr = 0o644 << 16
        zipfile.writestr(info, path.read_bytes(), compress_type=ZIP_DEFLATED, compresslevel=8)

print(f"Updated {ZIP.name}: {len(images)} external and {embedded.count} embedded images; {ZIP.stat().st_size} bytes.")
