"""Physical reference equivalence and honest static/frozen release adapters."""
import json  #: Load actual shipped physical projects and generated static source packets.
import os  #: Select genuine standard-library reference execution.
from pathlib import Path  #: Resolve exact source fixtures and generated browser assets.
import tempfile  #: Keep publication checks separate from delivered historical evidence.
import unittest  #: Record distinct physical and resource/capability contracts.
from engine import browser_bridge as bridge  #: Exercise actual browser model/metadata dispatch.
from engine.analysis import solve_project  #: Compare against the untouched direct original reference formulation.
from engine.connections import require_static_sources  #: Preserve original declared AC/static source separation.
from tools.build_browser import build  #: Generate the exact original browser assets and source-bound packet.
ROOT=Path(__file__).resolve().parents[1]  #: Bind models and resource checks to this delivered checkout.


class ReleaseAdapterTests(unittest.TestCase):  #: Verify real physical reuse and publication without new solver formulas.
    def test_actual_reference_vector_fields_equivalent_in_two_dimensions(self):  #: Compare actual original direct and browser-adapter B fields in 2D and 3D.
        for name in ['transformer_2d','air_coil_3d']:  #: Use genuine nonzero original winding/source fixtures.
            project=json.loads((ROOT/'examples'/(name+'.json')).read_text());project['domain'].update(nx=6,ny=6)  #: Keep bounded real meshes, not manufactured saved numerical output.
            if project['mode']=='3d':project['domain']['nz']=6  #: Solve an actual volume model in the spatial case.
            direct=solve_project(project,False);adapted=bridge.run(dict(action='solve',project=project,matrix=False))  #: Execute both independent public entry paths on the same unchanged kernel.
            self.assertEqual(adapted['fields']['B'],direct['fields']['B']);self.assertGreater(adapted['stats']['energy_J'],0)  #: Require exact physical vector-B equivalence and nonzero actual energy.

    def test_actual_ac_and_static_rejection(self):  #: Preserve dedicated AC physics and reject incompatible static actions.
        project=json.loads((ROOT/'examples/ac_square_2d.json').read_text());project['domain'].update(nx=6,ny=6)  #: Use a genuine finite-conductor diffusion fixture.
        result=bridge.run(dict(action='ac',project=project,options={'frequency_Hz':10000}));self.assertGreater(result['stats']['ohmic_loss_W'],0)  #: Require an actual positive resolved AC loss.
        for action in ['solve','adaptive','convergence','sweep']:  #: Retain every original static-action source gate.
            with self.assertRaises(ValueError):bridge.preflight(dict(action=action,project=project))  #: Reject declared AC solids before a browser job is accepted.

    def test_original_metadata_and_unsupported_native_boundary(self):  #: Preserve original builder data and explicitly report missing browser-native backends.
        catalogue=bridge.rpc('/api/builder/catalog');self.assertIn('defaults',catalogue)  #: Read actual shipped original catalogue/default data.
        spec=bridge.rpc('/api/builder/upgrade',dict(specification=catalogue['defaults']))['specification'];built=bridge.rpc('/api/builder/build',dict(specification=spec));self.assertIn('project',built)  #: Exercise the genuine original hierarchy and dimensional builder.
        self.assertFalse(bridge.rpc('/api/backends')['design_transformer'])  #: Never advertise an unavailable native adviser on GitHub Pages.
        with self.assertRaises(ValueError):bridge.preflight(dict(action='design_transformer',design_request={}))  #: Reject native requests rather than fabricate browser designs.

    def test_static_output_binds_source_and_relative_assets(self):  #: Check generated application resource paths and exact original engine identity.
        with tempfile.TemporaryDirectory() as directory:  #: Preserve historical source/evidence files during publication checks.
            manifest=build(directory);out=Path(directory);packet=json.loads((out/'magnetics-core.json').read_text());page=(out/'index.html').read_text()  #: Generate the actual static tool from this exact checkout.
            self.assertEqual(packet['files']['engine/analysis.py'],(ROOT/'engine/analysis.py').read_text());self.assertNotIn('src="/',page);self.assertIn('browser-runtime.js',page)  #: Preserve original PDE code and make every original script base-path safe.
            self.assertFalse(manifest['native_backends_available']);self.assertTrue((out/'digitiser-example.png').is_file())  #: Keep explicit capability limits and original digitiser runtime data available.


if __name__=='__main__':unittest.main()  #: Support actual focused adapter qualification.
