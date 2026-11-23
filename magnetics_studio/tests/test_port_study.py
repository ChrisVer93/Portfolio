"""Actual geometry-preserving mesh/air matrix studies and failure-state guards."""
import copy  #: Preserve original source snapshots while generating detached numerical cases.
import unittest  #: Record physical geometry, actual field and transactional rejection contracts.
from test_port_reduction import three_ports  #: Reuse explicit nondegenerate preceding 2D/3D source fixtures.
from engine.port_study import plan_study,port_study  #: Exercise genuine shared preflight and matrix-study execution.
from engine.analysis import solve_project  #: Independently prescribe the calculated short currents on a translated field model.
from engine.connections import series_key  #: Map physical sections by stable electrical ownership, not equal names.
from engine.mesh import build_mesh  #: Inspect actual fitted physical-coordinate grids.
from engine.sparse import Cancelled  #: Require actual interruption without a partial success result.
from studio import Workspace  #: Check original accepted job/field retention under failed preflight.


def fixture(mode):  #: Keep regression work bounded while retaining complete physical 2D/3D sources.
    p=three_ports(mode);p['domain'].update(nx=2,ny=2)  #: Preserve original component geometry/materials/turns.
    if mode=='3d':p['domain']['nz']=2  #: Retain an actual spatial vector problem.
    keys=list(dict.fromkeys(series_key(w) for w in p['windings']))  #: Derive independent electrical IDs from the canonical grouping.
    return p,dict(input_id=keys[0],shorted_ids=keys[1:],mesh_factors=[1,2],air_factors=[1,2])  #: Request an explicit complete two-axis simultaneous-short study.


class PortStudyTests(unittest.TestCase):  #: Verify physics and source identity rather than simply repeat reduction formulas.
    def test_translation_spacing_and_unchanged_model(self):  #: Expanding exterior air must preserve feature sizes and source/material order.
        for mode in ['2d','3d']:  #: Enforce the same contract for planar and spatial field problems.
            p,o=fixture(mode);before=copy.deepcopy(p);plan=plan_study(p,o);self.assertEqual(p,before);a,b=plan['cases'][0],plan['cases'][2];q=b['project']  #: Compare equal mesh factors at different exterior extents without editing the source.
            self.assertEqual(q['materials'],p['materials']);self.assertEqual([w['turns'] for w in q['windings']],[w['turns'] for w in p['windings']])  #: Preserve magnetic laws and electrical turns exactly.
            objects=p['regions']+([w['window'] for w in p['windings']] if mode=='3d' else []);moved=q['regions']+([w['window'] for w in q['windings']] if mode=='3d' else [])  #: Compare every original core/conductor and source support in original order.
            for old,new in zip(objects,moved):  #: Check rigid translation rather than geometric scaling.
                for i,axis in enumerate('xyz'[:2 if mode=='2d' else 3]):  #: Keep planar depth outside the expanded exterior coordinates.
                    for end in ['0','1']:self.assertAlmostEqual(new[axis+end]-b['translation_m'][i],old[axis+end],places=14)  #: Require identical physical dimensions and separations in the original coordinate frame.
            if mode=='2d':self.assertEqual(q['domain']['depth'],p['domain']['depth'])  #: Prevent accidental planar linkage/energy scaling through changed extrusion depth.
            ga=build_mesh(a['project'])['grids'];gb=build_mesh(q)['grids']  #: Independently inspect actual interface-fitted meshes.
            for i,axis in enumerate('xyz'[:len(ga)]):  #: Compare all subdivisions within the physical component bounds.
                lo=min(v[axis+'0'] for v in objects);hi=max(v[axis+'1'] for v in objects);old=[v for v in ga[i] if lo-1e-12<=v<=hi+1e-12];new=[v-b['translation_m'][i] for v in gb[i] if lo-1e-12<=v-b['translation_m'][i]<=hi+1e-12]  #: Place both numerical grids in the same source-relative coordinate frame.
                self.assertEqual(len(old),len(new));self.assertLess(max(abs(x-y) for x,y in zip(old,new)),1e-12)  #: Catch unintended interior coarsening during air-only comparisons.

    def test_actual_two_axis_fields_and_short_energy(self):  #: Study entries must come from real original FEM matrices on the declared cases.
        for mode in ['2d','3d']:  #: Exercise separate actual H1 and edge-element magnetic formulations.
            p,o=fixture(mode);study=port_study(p,o);rows=study['rows'];self.assertEqual(len(rows),4)  #: Execute the full explicit mesh/air grid.
            self.assertIsNone(rows[0]['mesh_change']);self.assertIsNone(rows[0]['air_change']);self.assertIsNotNone(rows[-1]['mesh_change']);self.assertIsNotNone(rows[-1]['air_change'])  #: Retain independent axes and undefined initial comparisons.
            if mode=='2d':self.assertTrue(rows[1]['identical_previous_mesh']);self.assertIsNone(rows[1]['mesh_change'])  #: Fitted geometry may dominate a coarse grid; identical meshes must not count as zero-error refinement evidence.
            for row in rows:self.assertGreater(row['measurement']['input_inductance_H'],0);self.assertEqual(row['actual_elements'],row['stats_at_original_currents']['elements'])  #: Require positive actual port energy and identical preflight/solved mesh sizes.
            final=rows[-1];q=copy.deepcopy(final['project']);c=final['measurement']['source_matrix'];currents=final['measurement']['current_A_per_input_A']  #: Prepare an independent field solve on the translated/refined model.
            for w in q['windings']:w['current']=currents[c['group_ids'].index(series_key(w))]  #: Prescribe the reduced short-current mode on every original physical section.
            check=solve_project(q,False);self.assertAlmostEqual(2*check['stats']['energy_J']/final['measurement']['input_inductance_H'],1,places=6);self.assertGreater(check['stats']['peak_B_T'],0)  #: Compare actual nonzero magnetic field energy against the selected matrix prediction.
            self.assertIn('not certified',study['note'])  #: Preserve the limit that empirical changes do not certify physical accuracy.

    def test_transactional_rejection_and_actual_cancellation(self):  #: Invalid or interrupted studies cannot replace accepted fields/results.
        p,o=fixture('2d');state=Workspace();state.job=dict(id='accepted',status='done');state.field_result={'accepted':True}  #: Establish explicit prior accepted workspace data.
        for bad in [{**o,'mesh_factors':[1,1.5]},{**o,'air_factors':[1,True]},{**o,'shorted_ids':['missing']},{**o,'mesh_factors':[1,2,3],'air_factors':[1,2,3]}]:  #: Include malformed factors, wrong IDs and excessive case grids.
            with self.assertRaises(ValueError):state.start(dict(project=p,action='port_study',options=bad))  #: Reject through real workspace preflight before creating a job.
            self.assertEqual(state.job['id'],'accepted');self.assertEqual(state.field_result,{'accepted':True})  #: Preserve the original accepted job/field after every rejection.
        ac=copy.deepcopy(p);ac['ac_conductors']=[dict(id='solid',conductivity_Spm=58e6,current_A=0)]  #: Declare incompatible solid AC sources without relying on region assignment.
        with self.assertRaises(ValueError):plan_study(ac,o)  #: Reject silently ignored AC physics.
        nonlinear=copy.deepcopy(p);nonlinear['materials'][2]['bh']=[[0,0],[1000,.1]]  #: Supply a valid reversible nonlinear material instead of a constant linear matrix.
        with self.assertRaises(ValueError):plan_study(nonlinear,o)  #: Reject unsupported nonlinear characterization explicitly.
        huge=copy.deepcopy(p);huge['domain'].update(nx=90,ny=90)  #: Exceed the shared actual fitted-work ceiling.
        with self.assertRaises(ValueError):plan_study(huge,o)  #: Reject excess work before any study field is solved.
        stopped=[False]  #: Trigger real cancellation only after the first numerical case has run.
        def log(message):  #: Detect the next actual matrix-study case through genuine progress callbacks.
            if message.startswith('Reference port study: mesh×2'):stopped[0]=True  #: Cancel before completing the second field solve.
        with self.assertRaises(Cancelled):port_study(p,o,log,lambda:stopped[0])  #: Interrupted work must return no completed study result.


if __name__=='__main__':unittest.main()  #: Support reproducible focused source-form numerical qualification.
