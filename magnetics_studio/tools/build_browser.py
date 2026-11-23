"""Publish the exact original interface/reference Python as a static GitHub Pages tool."""
import argparse  #: Require one explicit static output destination.
import hashlib  #: Bind every shipped engine/input asset to exact source bytes.
import json  #: Package trusted Python/data for the browser virtual filesystem.
from pathlib import Path  #: Resolve source and static output independently.
import shutil  #: Copy original browser assets without reimplementing their behavior.
ROOT=Path(__file__).resolve().parents[1]  #: Anchor all publication content to this source release.


def build(destination):  #: Generate a complete, source-bound browser preview without a Python server.
    destination=Path(destination);destination.mkdir(parents=True,exist_ok=True);files={}  #: Preserve an explicit static output and trusted virtual source packet.
    for folder in ['engine','examples','data']:  #: Include exact original reference kernels, physical examples and builder/material inputs.
        for path in sorted((ROOT/folder).rglob('*')):  #: Traverse only declared source/data roots, excluding caches/native binaries.
            if path.is_file() and '__pycache__' not in path.parts and path.suffix in ['.py','.json']:files[str(path.relative_to(ROOT))]=path.read_text(encoding='utf-8')  #: Retain actual UTF-8 source/data with original virtual paths.
    for name in ['report.html','cad-view.js','field-view.js']:files['web/'+name]=(ROOT/'web'/name).read_text(encoding='utf-8')  #: Preserve the original offline report template and embedded view scripts inside the virtual source tree.
    for path in (ROOT/'web').iterdir():  #: Preserve original interface scripts/styles rather than create a mock UI.
        if path.is_file():shutil.copyfile(path,destination/path.name)  #: Keep exact original bytes for every reused browser asset.
    page=(ROOT/'web/index.html').read_text().replace('src="/','src="').replace('href="/','href="').replace('<head>','<head><script src="browser-runtime.js"></script>')  #: Make assets subdirectory-safe and install the worker API transport before original startup.
    (destination/'index.html').write_text(page,encoding='utf-8')  #: Publish the genuine original interface with only its transport/base-path integration changed.
    digitiser=destination/'digitiser.js';digitiser.write_text(digitiser.read_text().replace('/digitiser-example.png','digitiser-example.png'),encoding='utf-8')  #: Make the original digitiser image URL relative to the published tool subdirectory.
    shutil.copyfile(ROOT/'data/digitiser-example.png',destination/'digitiser-example.png')  #: Keep the existing digitiser example available beside other static assets.
    (destination/'magnetics-core.json').write_text(json.dumps({'files':files},ensure_ascii=False),encoding='utf-8')  #: Ship trusted original Python and inputs without any saved field pretending to be a new solve.
    manifest={'release':'0.9.34','runtime':'Pyodide 0.27.7 standard-library reference','native_backends_available':False,'source_sha256':{n:hashlib.sha256(text.encode()).hexdigest() for n,text in files.items()}}  #: Make exact engine/source identity and the native capability boundary inspectable.
    (destination/'version.json').write_text(json.dumps(manifest,indent=2)+'\n');return manifest  #: Preserve reproducible per-release browser provenance.


if __name__=='__main__':  #: Keep imports free of publication writes.
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('output',type=Path);args=parser.parse_args();print(json.dumps(build(args.output),indent=2))  #: Build the requested static preview from this exact source checkout.
