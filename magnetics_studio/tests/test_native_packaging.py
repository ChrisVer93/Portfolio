"""S007: frozen Netgen OCCT metadata resolves exact bundled DLLs; no executable built."""
import importlib.metadata as metadata  #: Exercise the same standard-library file lookup used by the upstream loader.
from pathlib import Path  #: Build explicit temporary installed and frozen directory layouts.
import tempfile  #: Keep synthetic packaging fixtures outside runtime source and historical evidence.
import unittest  #: Require real relocation and fail-closed incomplete-inventory behavior.
from tools.build_desktop import stage_netgen_occt  #: Test the actual production build function without generating an application executable.


class NativePackagingTests(unittest.TestCase):  #: Verify packaging semantics independently of unavailable Windows execution.
    def test_relocated_record_resolves_exact_dll_bytes(self):  #: Model installed-prefix DLL records that cannot be reused inside a frozen root.
        with tempfile.TemporaryDirectory() as temporary:  #: Isolate exact synthetic wheel and bundle fixture bytes.
            root=Path(temporary);site=root/'installed/site';info=site/'netgen_occt-7.8.1.dist-info';info.mkdir(parents=True);(root/'installed/bin').mkdir();bundle=root/'bundle'  #: Separate installation prefix, original metadata and actual frozen resources.
            (info/'METADATA').write_text('Name: netgen-occt\nVersion: 7.8.1\n');(info/'RECORD').write_text('../bin/TKernel.dll,,\n../bin/TKMath.dll,,\nnetgen_occt-7.8.1.dist-info/METADATA,,\n')  #: Retain genuine relative-prefix metadata lookup semantics in the fixture.
            for name in ['TKernel.dll','TKMath.dll']:(root/'installed/bin'/name).write_bytes(name.encode())  #: Make source identity checks independent of filenames alone.
            flags=stage_netgen_occt(metadata.PathDistribution(info),root/'staged');bundle.mkdir();staged=Path(flags[1].split(';')[0]);import shutil;shutil.copytree(staged,bundle/staged.name);(bundle/'netgen_occt_libs').mkdir()  #: Run actual production staging and materialize its declared frozen destinations without freezing code.
            for i in range(2,len(flags),2):source,destination=flags[i+1].split(';');shutil.copyfile(source,bundle/destination/Path(source).name)  #: Interpret exact production binary flags rather than recreating its lookup record in the test.
            frozen=metadata.PathDistribution(bundle/info.name);files=frozen.files;self.assertEqual({f.name for f in files},{'TKernel.dll','TKMath.dll'})  #: Require upstream file enumeration to discover every packaged OCCT library.
            for member in files:self.assertTrue(member.locate().resolve().is_relative_to(bundle));self.assertEqual(member.locate().read_bytes(),member.name.encode())  #: Require actual bundle-local file resolution and exact original DLL bytes.
            self.assertEqual(frozen.version,'7.8.1')  #: Preserve upstream version identity through relocation.

    def test_missing_dll_rejected(self):  #: Do not generate a package whose metadata advertises absent native binaries.
        with tempfile.TemporaryDirectory() as temporary:  #: Keep the malformed synthetic distribution isolated.
            root=Path(temporary);info=root/'netgen_occt-7.8.1.dist-info';info.mkdir();(info/'METADATA').write_text('Name: netgen-occt\nVersion: 7.8.1\n');(info/'RECORD').write_text('TKernel.dll,,\n')  #: Declare an actually missing required upstream kernel.
            with self.assertRaisesRegex(ValueError,'incomplete'):stage_netgen_occt(metadata.PathDistribution(info),root/'stage')  #: Require a build failure before PyInstaller or runtime native execution.


if __name__=='__main__':unittest.main()  #: Expose reproducible standalone packaging checks.
