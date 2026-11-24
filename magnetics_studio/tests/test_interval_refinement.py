"""Dyadic fitted-feature refinement: nested elements, preserved materials and actual fields."""
import bisect  #: Locate each fine simplex in its independently identified coarse Cartesian cell.
import copy  #: Preserve original physical sources while prescribing independently reduced currents.
import math  #: Aggregate physical measures without depending on element ordering.
import unittest  #: Qualify source, topology, actual fields and rejected-job state contracts.
from test_port_study import fixture  #: Reuse preceding real two-dimensional and spatial three-port models.
from engine.mesh import build_mesh,triangle_geometry,tetra_geometry,dot,sub  #: Inspect actual simplex geometry and original scalar/vector meshes.
from engine.port_study import plan_study,port_study,project_digest  #: Exercise shared genuine preflight, mesh identity and numerical study execution.
from engine.analysis import _solve_on_mesh  #: Independently solve the prescribed short-current field on the exact finer mesh.
from engine.connections import series_key  #: Assign currents through stable physical-series electrical keys.
from engine.sparse import Cancelled  #: Require actual cancellation instead of returning a partial successful study.
from studio import Workspace  #: Verify rejection before replacing an accepted job or magnetic field.


class IntervalRefinementTests(unittest.TestCase):  #: Cover the numerical refinement contract independently of UI labels.
    def test_nested_simplices_measures_and_quality(self):  #: Every fine simplex must lie inside a coarse simplex with the same material tag.
        for mode in ['2d','3d']:  #: Check both the scalar triangle and spatial edge-element discretizations.
            p,_=fixture(mode);coarse=build_mesh(p);fine=build_mesh(p,interval_factor=2);dim=coarse['dimension'];per_cell=2 if dim==2 else 6  #: Construct genuinely different fitted meshes of the exact same geometry.
            self.assertEqual(build_mesh(p,interval_factor=1),coarse);self.assertEqual(len(fine['elements']),len(coarse['elements'])*2**dim)  #: Keep the default path byte-value equivalent and require every interval to refine.
            for g,h in zip(coarse['grids'],fine['grids']):self.assertEqual(h[::2],g)  #: Preserve every original geometry/mesh plane exactly, not only within a plotting tolerance.
            self.assertAlmostEqual(fine['quality']['smallest_axis_interval_m']*2,coarse['quality']['smallest_axis_interval_m']);self.assertAlmostEqual(fine['quality']['largest_cell_axis_aspect_ratio'],coarse['quality']['largest_cell_axis_aspect_ratio'])  #: Require smaller physical resolution while explicitly detecting that aspect quality does not improve.
            widths=[len(g)-1 for g in coarse['grids']];measures=[]  #: Identify Cartesian parent cells without searching all coarse elements.
            for j,e in enumerate(fine['elements']):  #: Inspect every actual fine triangle or tetrahedron.
                points=[fine['nodes'][n] for n in e];center=[sum(v[i] for v in points)/len(points) for i in range(dim)];indices=[bisect.bisect_right(g,x)-1 for g,x in zip(coarse['grids'],center)]  #: Locate the containing coarse Cartesian cell by its interior centroid.
                cell=indices[0]+widths[0]*(indices[1]+(widths[1]*indices[2] if dim==3 else 0));parents=range(cell*per_cell,(cell+1)*per_cell);contained=[]  #: Restrict possible parents to the original globally conforming simplex split.
                for k in parents:  #: Test containment geometrically rather than assume a matching tetrahedral diagonal.
                    vertices=[coarse['nodes'][n] for n in coarse['elements'][k]];_,grads=(triangle_geometry if dim==2 else tetra_geometry)(vertices)  #: Obtain exact affine barycentric gradients on the coarse element.
                    if all(all((1 if n==0 else 0)+dot(g,sub(x,vertices[0]))>=-1e-10 for n,g in enumerate(grads)) for x in points):contained.append(k)  #: Require all fine vertices to lie in one original simplex, including shared boundaries.
                self.assertTrue(contained);self.assertTrue(any(coarse['tags'][k]==fine['tags'][j] for k in contained))  #: Preserve both nested FE spaces and original last-region-wins material/source assignment.
            for mesh in [coarse,fine]:  #: Independently integrate every tagged physical region and the surrounding air.
                by_tag={}  #: Keep material-region measures separate instead of only checking total domain volume.
                for e,tag in zip(mesh['elements'],mesh['tags']):by_tag.setdefault(tag,[]).append((triangle_geometry if dim==2 else tetra_geometry)([mesh['nodes'][n] for n in e])[0])  #: Integrate positive simplex areas or volumes from actual vertices.
                measures.append({k:math.fsum(v) for k,v in by_tag.items()})  #: Reduce accumulated roundoff without silently changing region ownership.
            self.assertEqual(set(measures[0]),set(measures[1]))  #: Keep every original material/air region represented.
            for tag,value in measures[0].items():self.assertAlmostEqual(measures[1][tag]/value,1,places=12)  #: Preserve exact physical area/volume under refinement.

    def test_actual_nested_fields_and_independent_short_energy(self):  #: Each new matrix must correspond to the exported mesh and real short-current field.
        for mode in ['2d','3d']:  #: Exercise real separate planar H1 and spatial Nedelec field systems.
            p,o=fixture(mode);o.update(mesh_mode='interval',air_factors=[1]);original=copy.deepcopy(p);study=port_study(p,o);first,last=study['rows'];self.assertEqual(p,original)  #: Execute actual dyadic matrix solves without changing user data.
            self.assertEqual(first['project_sha256'],last['project_sha256']);self.assertNotEqual(first['mesh_sha256'],last['mesh_sha256']);self.assertFalse(last['identical_previous_mesh'])  #: Show why exact mesh-mode/factor metadata is required in addition to project JSON.
            self.assertEqual(last['actual_elements'],first['actual_elements']*(4 if mode=='2d' else 8));self.assertIsNotNone(last['mesh_change'])  #: Require actual refinement of the physical geometry at the declared dimension.
            q=copy.deepcopy(last['project']);m=build_mesh(q,interval_factor=2);self.assertEqual(project_digest({k:m[k] for k in ['nodes','elements','tags']}),last['mesh_sha256'])  #: Independently reproduce the exact preflight and solved mesh identity.
            r=last['measurement'];ids=r['source_matrix']['group_ids']  #: Keep selected electrical constraints and all simultaneous mutual couplings explicit.
            for w in q['windings']:w['current']=r['current_A_per_input_A'][ids.index(series_key(w))]  #: Prescribe the genuinely calculated cancellation currents on all physical sections.
            solved=_solve_on_mesh(q,m,False);self.assertGreater(solved['stats']['peak_B_T'],0);self.assertAlmostEqual(2*solved['stats']['energy_J']/r['input_inductance_H'],1,places=6)  #: Compare actual nonzero-field energy with the reduced full-matrix prediction.
            for key in o['shorted_ids']:  #: Check actual re-solved shorted linkage after summing every physical same-current section.
                value=sum(w['linkage_Wb_turn'] for w,physical in zip(solved['windings'],q['windings']) if series_key(physical)==key);self.assertLess(abs(value)/r['input_inductance_H'],1e-6)  #: Enforce zero shorted linkage relative to the driven1A port response using actual independently solved fields.


    def test_resource_mode_and_transactional_rejection(self):  #: Unsupported or excessive refinement must fail before replacing accepted data.
        p,o=fixture('3d');o.update(mesh_mode='interval',air_factors=[1]);state=Workspace();state.job={'id':'accepted','status':'done'};state.field_result={'accepted':True}  #: Establish an actual original workspace state before preflight rejection.
        for bad in [{**o,'mesh_mode':'unknown'},{**o,'mesh_factors':[1,3]},{**o,'mesh_factors':[1,True]},{**o,'mesh_factors':[1,2,4],'air_factors':[1,2]}]:  #: Include wrong definitions, non-dyadic/boolean factors and actual over-budget fitted meshes.
            with self.assertRaises(ValueError):state.start(dict(project=p,action='port_study',options=bad))  #: Invoke the shared server preflight before job mutation.
            self.assertEqual(state.job['id'],'accepted');self.assertEqual(state.field_result,{'accepted':True})  #: Retain the original accepted job and field for every invalid request.
        stopped=[False]  #: Trigger interruption only after the first real interval-mode matrix has completed.
        def log(message):  #: Observe original numerical progress rather than inject a fabricated field result.
            if message.startswith('Reference port study: mesh×2'):stopped[0]=True  #: Cancel while reconstructing the second genuine refined mesh.
        with self.assertRaises(Cancelled):port_study(p,o,log,lambda:stopped[0])  #: A cancelled interval study must return no completed result.
        for value in [0,True,3,8,1.5]:  #: Bound the internal mesh API itself, including allocation multipliers.
            with self.assertRaises(ValueError):build_mesh(p,interval_factor=value)  #: Reject invalid subdivision before building elements.
        p2,o2=fixture('2d');o2.update(mesh_mode='interval',mesh_factors=[1,2,4],air_factors=[1]);cases=plan_study(p2,o2)['cases']  #: Permit all three bounded dyadic planar levels.
        self.assertEqual([r['actual_elements'] for r in cases],[286,1144,4576])  #: Verify actual all-feature refinement rather than nominal subdivision targets.


if __name__=='__main__':unittest.main()  #: Support reproducible focused qualification of the delivered source.
