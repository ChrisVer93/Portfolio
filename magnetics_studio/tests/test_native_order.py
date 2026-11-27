"""Native order selection, actual fields and accepted-state rejection."""
import copy,json,unittest  #: Preserve exact physical fixtures and distinct regression outcomes.
from pathlib import Path  #: Resolve this delivered checkout's original source models.
from engine.ngsolve_backend import check_native_order,solve_native  #: Exercise shared pure preflight and genuine native assembly.
from engine.backend_process import backend_status  #: Keep optional compiled execution explicitly detected.
from studio import Workspace  #: Verify real accepted-state behavior before worker launch.
ROOT=Path(__file__).resolve().parents[1]  #: Bind all fixtures to delivered source bytes.

def project():  #: Reuse the actual physical sheet model from the preceding independent verification.
    return json.loads((ROOT/'sample_results/local_field_s005/results.json').read_text())['rows'][0]['project']  #: Preserve exact source geometry, currents, materials and closed boundary.

class OrderBoundaryTests(unittest.TestCase):  #: Always qualify pure guards without requiring native imports.
    def test_reject_transactionally(self):  #: Unsupported numerical controls must not destroy a prior accepted job or field.
        p=project();state=Workspace();state.job={'id':'accepted','status':'done'};state.field_result={'accepted':True}  #: Establish actual prior server state before preflight.
        for o in [{'hcurl_order':True},{'hcurl_order':1},{'hcurl_order':2.0},{'hcurl_order':4},{'hcurl_order':2,'max_passes':2}]:  #: Include ambiguous types, duplicate space, unsupported degree and unqualified adaptation.
            with self.assertRaises(ValueError):state.start(dict(project=p,action='ngsolve',options=o))  #: Exercise the real production preflight before state mutation or native imports.
            self.assertEqual(state.job['id'],'accepted');self.assertEqual(state.field_result,{'accepted':True})  #: Keep accepted results and job identity after every rejected request.
        self.assertEqual(check_native_order(p,{}),0);self.assertEqual(check_native_order(p,{'hcurl_order':3}),3)  #: Preserve original default and accept explicit bounded higher order.
        p2=json.loads((ROOT/'examples/transformer_2d.json').read_text())  #: Retain original planar sources and formulation.
        with self.assertRaises(ValueError):check_native_order(p2,{'hcurl_order':2})  #: Reject changing the planar H1 space through a spatial-only control.

@unittest.skipUnless(backend_status()['ngsolve'],'Pinned native FEM unavailable')  #: Record unavailable compiled execution as skipped rather than passed numerics.
class NativeOrderTests(unittest.TestCase):  #: Compare actual production field results at explicitly selected orders.
    def test_real_higher_order_and_matrix(self):  #: Higher order must use actual native basis functions and retain physical source/matrix checks.
        p=project();before=copy.deepcopy(p);rows=[];truth=json.loads((ROOT/'sample_results/cell_projection_s006/results.json').read_text())['rows'][0]['observations'][1]['point_reference_B_T']  #: Bind source preservation and the off-axis comparison to independently generated free-space reference data.
        for order in [0,3]:  #: Exercise unchanged original and genuine higher native curl spaces.
            r=solve_native(p,dict(maxh_m=.2,max_passes=1,hcurl_order=order,probes_m=[[.53,.52,.54]]),True);rows.append(r)  #: Run real conforming native geometry, assembly, source solve and unit matrix.
            self.assertEqual(r['stats']['native_hcurl_order'],order);self.assertLess(r['stats']['energy_consistency'],1e-5);self.assertLess(r['stats']['reciprocity'],1e-7)  #: Preserve actual selected-space metadata and existing physical/algebraic guards.
            self.assertAlmostEqual(r['inductance_H'][0][0]/(2*r['stats']['energy_J']),1,places=6)  #: Require energy and the actually solved unit-current inductance to agree.
        error=lambda r:sum((x-y)**2 for x,y in zip(r['probes'][0]['B_T'],truth))**.5  #: Compare full vectors without discarding transverse components.
        self.assertLess(error(rows[1]),error(rows[0]));self.assertGreater(rows[1]['stats']['dofs'],rows[0]['stats']['dofs']);self.assertEqual(p,before)  #: Demonstrate real additional approximation capacity and preserved physical source for this fixture only.
        self.assertIn('centroid',' '.join(rows[1]['warnings']))  #: Keep the original display/export sampling limitation visible with higher-order output.

if __name__=='__main__':unittest.main()  #: Support reproducible focused qualification in both reference and native environments.
