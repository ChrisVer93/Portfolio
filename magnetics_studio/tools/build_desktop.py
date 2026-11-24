"""Build a Windows one-folder development preview with installed native dependencies."""
import argparse  #: Keep the exact output and build platform explicit.
import importlib.metadata as metadata  #: Inventory actual distributions and preserve upstream licence files.
import json  #: Record exact packaged source and dependency provenance.
from pathlib import Path  #: Resolve trusted application resources and native wheel members.
import shutil  #: Copy exact runtime notices and deterministic source snapshots.
import subprocess  #: Invoke PyInstaller through the selected build interpreter.
import sys  #: Require a real Windows host and preserve its actual Python interpreter.
ROOT=Path(__file__).resolve().parents[1]  #: Bind the build to this exact delivered checkout.


def main():  #: Produce a complete one-folder Windows preview rather than cross-label a Linux executable.
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('output',type=Path);args=parser.parse_args()  #: Require an explicit distribution parent directory.
    if sys.platform!='win32':raise ValueError('Build this Windows package on a permitted Windows host')  #: Do not produce a platform-mislabeled application executable.
    notices=ROOT/'build/notices';notices.mkdir(parents=True,exist_ok=True);inventory=[]  #: Stage exact dependency notices separately from executable code.
    command=[sys.executable,'-m','PyInstaller','--noconfirm','--clean','--onedir','--console','--noupx','--name','MagneticsStudio','--distpath',str(args.output),'--workpath',str(ROOT/'build/pyinstaller'),'--specpath',str(ROOT/'build')]  #: Build the actual browser-launching Windows application with inspectable console errors.
    for folder in ['web','data','examples']:command.extend(['--add-data',str(ROOT/folder)+';'+folder])  #: Include original runtime assets, physical examples and builder/material catalogue data.
    for package in ['engine','tools']:command.extend(['--collect-submodules',package])  #: Retain all lazily imported original application and native worker modules.
    for package in ['numpy','scipy','cadquery','OCP','netgen','ngsolve','OpenMagneticsVirtualBuilder']:command.extend(['--collect-all',package])  #: Preserve required compiled libraries and package data used by original optional backends.
    command.extend(['--hidden-import','PyOpenMagnetics'])  #: Include the pinned extension module even though it is imported only by a native worker action.
    for distribution in metadata.distributions():  #: Inventory and preserve notices for the actual installed transitive environment, not guessed direct dependencies.
        name=distribution.metadata['Name'];record=dict(name=name,version=distribution.version,license=distribution.metadata.get('License-Expression') or distribution.metadata.get('License'),source=distribution.metadata.get('Home-page'),notices=[])  #: Retain actual upstream metadata and source attribution.
        command.extend(['--copy-metadata',name])  #: Keep version guards and original dist-info licence data available inside frozen workers.
        for member in distribution.files or []:  #: Inspect declared installed wheel members without importing native code.
            path=Path(distribution.locate_file(member));relative=str(member).replace('\\','/')  #: Resolve actual native/notice bytes from this Windows build environment.
            if path.is_file() and any(word in path.name.lower() for word in ['license','licence','copyright','notice']):  #: Preserve original legal notice contents rather than paraphrase them.
                target=notices/name/relative.replace('../','parent/');target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(path,target);record['notices'].append(relative)  #: Keep each upstream notice attributable to its owning distribution.
            if name.lower()=='pyopenmagnetics' and path.is_file() and path.suffix.lower()=='.dll':command.extend(['--add-binary',str(path)+';'+str(Path(relative).parent)])  #: Retain runtime-loaded Kirchhoff/native DLLs alongside the actual extension layout.
        inventory.append(record)  #: Preserve complete observed transitive metadata with explicit missing notice lists.
    (notices/'DEPENDENCIES.json').write_text(json.dumps(inventory,indent=2)+'\n',encoding='utf-8')  #: Make actual runtime dependencies and notice coverage inspectable in the preview.
    command.extend(['--add-data',str(notices)+';THIRD_PARTY_NOTICES',str(ROOT/'desktop_launcher.py')]);subprocess.run(command,cwd=ROOT,check=True)  #: Build only after complete resources/metadata/notices are staged.
    target=args.output/'MagneticsStudio';shutil.copyfile(ROOT/'requirements-desktop.txt',target/'requirements-desktop.txt')  #: Retain the exact direct build pins next to the executable.
    (target/'DEVELOPMENT_PREVIEW.txt').write_text('Magnetics Studio 0.9.35 development preview. Open MagneticsStudio.exe; keep the console open while using the browser. Native availability follows exact pinned backend diagnostics. Full commercial/physical/Windows release qualification remains pending.\n',encoding='utf-8')  #: Label preview scope without implying completed industrial parity or signed release status.
    print(json.dumps(dict(executable=str(target/'MagneticsStudio.exe'),dependencies=len(inventory))))  #: Report the concrete native Windows build output.


if __name__=='__main__':main()  #: Keep imports free of application executable generation.
