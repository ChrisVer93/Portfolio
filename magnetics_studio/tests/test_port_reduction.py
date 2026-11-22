"""Explicit simultaneous shorts: analytical algebra, actual 2D/3D fields and HTTP state."""
import copy  #: Preserve original winding identities while constructing independent physical secondary sources.
import json  #: Retain reproducible exact matrices, solved fields and characterization evidence.
import math  #: Independently evaluate energy and current/flux normalization checks.
from pathlib import Path  #: Resolve actual shipped physical models.
import threading  #: Run the genuine protected HTTP server for state-retention checks.
import unittest  #: Record distinct physical and rejection contracts.
from urllib.request import Request,urlopen  #: Exercise real loopback routes rather than a mocked request handler.
from engine.analysis import solve_project  #: Re-solve independently prescribed cancellation currents on the actual field mesh.
from engine.browser_bridge import rpc  #: Verify genuine online/desktop shared postprocessing.
from engine.port_reduction import reduce_ports  #: Exercise the actual declared electrical-port reduction.
from studio import make_server  #: Check API integration without changing accepted jobs/results.
ROOT=Path(__file__).resolve().parents[1]  #: Keep fixture lookup rooted in the delivered checkout.


def three_ports(mode):  #: Build distinct secondary geometry while keeping equal display names electrically independent.
    p=json.loads((ROOT/'examples'/('transformer_2d.json' if mode=='2d' else 'air_coil_3d.json')).read_text());p['domain'].update(nx=5,ny=5)  #: Use genuine fitted field models and bounded but nontrivial meshes.
    if mode=='2d':  #: Split the original secondary window into two separately driven physical conductors.
        p['windings'].append(dict(id='tertiary',name='Secondary',turns=13,current=0))  #: Preserve equal labels with distinct stable electrical IDs.
        for region in list(p['regions']):  #: Give both new secondary source halves their own fitted geometry.
            if region.get('winding')=='secondary':  #: Keep the original positive and return source directions.
                region['y1']=.062;third=copy.deepcopy(region);third.update(id=region['id']+'_third',winding='tertiary',y0=.065,y1=.072);p['regions'].append(third)  #: Create spatially distinct paired conductors instead of identical redundant source modes.
    else:  #: Use three actual closed rectangular sheet sources with different axial support.
        p['domain']['nz']=5;first=p['windings'][0];first.update(current=1,series_group='primary')  #: Retain the original main 3D winding and an explicit grouped electrical key.
        for i,(z0,z1) in enumerate([(.025,.042),(.078,.095)]):  #: Position the two secondary sheets at different heights.
            w=copy.deepcopy(first);w.update(id='secondary'+str(i),name='Secondary',series_group='secondary'+str(i),turns=17+i,current=0);w['window'].update(z0=z0,z1=z1);p['windings'].append(w)  #: Preserve physical source identity, polarity and independent current assignment.
    return p  #: Return a detached complete physical source project.


class PortReductionTests(unittest.TestCase):  #: Verify circuit semantics through actual magnetic energy/linkage, not only formula repetition.
    def test_analytical_three_port_simultaneous_and_orientation(self):  #: Compare against a hand-solvable coupled 3×3 matrix and signed source reversal.
        c=dict(group_ids=['p','s','t'],names=['P','same','same'],inductance_H=[[v*1e-6 for v in row] for row in [[10,3,2],[3,4,1],[2,1,2]]]);original=copy.deepcopy(c)  #: Preserve an explicit positive-energy analytical fixture with two equal labels.
        r=reduce_ports(c,'p',['s','t']);self.assertAlmostEqual(r['input_inductance_H']/1e-6,48/7);self.assertAlmostEqual(r['current_A_per_input_A'][1],-4/7);self.assertAlmostEqual(r['current_A_per_input_A'][2],-5/7)  #: Check simultaneous coupling against exact rational cancellation currents and Lsc.
        self.assertLess(r['input_inductance_H'],reduce_ports(c,'p',['s'])['input_inductance_H']);self.assertLess(r['input_inductance_H'],reduce_ports(c,'p',['t'])['input_inductance_H'])  #: Demonstrate why separate pairwise measurements cannot replace simultaneous shorts.
        c['inductance_H']=[[x*(-1 if (i==1)!=(j==1) else 1) for j,x in enumerate(row)] for i,row in enumerate(c['inductance_H'])];reversed_port=reduce_ports(c,'p',['t','s'])  #: Reverse one physical port orientation and reorder the declared short list.
        self.assertAlmostEqual(reversed_port['input_inductance_H']/r['input_inductance_H'],1);self.assertAlmostEqual(reversed_port['current_A_per_input_A'][1],4/7);self.assertEqual(original, r['source_matrix'])  #: Preserve invariant input inductance, signed current reversal and exact original-matrix export.

    def test_reject_bad_and_dependent_modes_without_mutation(self):  #: Fail closed for invalid, nonpassive and nearly dependent electrical matrices.
        c=dict(group_ids=['a','b'],names=['same','same'],inductance_H=[[1.,.3],[.3,.5]])  #: Use independent positive-energy ports with equal display names.
        for matrix in [[[1,2],[2,1]],[[1,1],[1,1]],[[1,1-1e-12],[1-1e-12,1]],[[1,.2],[.3,1]],[[1,True],[True,1]],[[1,float('nan')],[0,1]],[[0,0],[0,1]]]:  #: Exercise indefiniteness, exact/near singularity, nonreciprocity, types, finiteness and zero source energy.
            with self.assertRaises(ValueError):reduce_ports({**c,'inductance_H':matrix},'a',['b'])  #: Never produce fabricated cancellation currents from an unqualified matrix.
        for selected in [['a'],['b','b'],['missing'],'b']:  #: Include input shorting, duplicate and malformed selections.
            with self.assertRaises(ValueError):reduce_ports(c,'a',selected)  #: Retain explicit ID-based constraints.
        saved=copy.deepcopy(c);r=reduce_ports(c,'a',[]);self.assertEqual(r['input_inductance_H'],1);self.assertEqual(c,saved);self.assertEqual(r['open_ids'],['b'])  #: An empty short set means open input; postprocessing never edits source JSON.
        scaled={**c,'inductance_H':[[1e-12,3e-7],[3e-7,.5]]};self.assertAlmostEqual(reduce_ports(scaled,'a',['b'])['input_inductance_H']/1e-12,.82)  #: Diagonal normalization handles extreme legitimate turn/unit scales without an absolute-henry pivot threshold.

    def test_actual_planar_and_spatial_cancellation_energy(self):  #: Compare predicted currents with independently re-solved actual vector fields and source work in both dimensions.
        for mode in ['2d','3d']:  #: Exercise distinct planar H1 and spatial edge-element formulations.
            p=three_ports(mode);source=copy.deepcopy(p);solved=solve_project(p);c=solved['circuits'];report=reduce_ports(c,c['group_ids'][0],c['group_ids'][1:])  #: Compute a full genuine unit-excitation matrix before any reduction.
            q=copy.deepcopy(solved['project'])  #: Prescribe the independently calculated cancellation currents on the exact accepted physical project.
            from engine.connections import series_key  #: Map currents back through the authoritative canonical electrical grouping.
            for w in q['windings']:w['current']=report['current_A_per_input_A'][c['group_ids'].index(series_key(w))]  #: Assign every physical section of an electrical winding the same calculated current.
            check=solve_project(q,False);links=[sum(w['linkage_Wb_turn'] for w,physical in zip(check['windings'],q['windings']) if series_key(physical)==key) for key in c['group_ids']]  #: Recompute actual field linkages with no matrix solve and regroup independently.
            scale=report['input_open_H'];self.assertLess(max(abs(x) for x in links[1:])/scale,2e-7);self.assertAlmostEqual(links[0]/report['input_inductance_H'],1,places=6)  #: Require actual zero short linkage and the predicted driven-input flux/current.
            self.assertAlmostEqual(2*check['stats']['energy_J']/report['input_inductance_H'],1,places=6);self.assertGreater(check['stats']['peak_B_T'],0);self.assertEqual(p,source)  #: Check independent physical field energy, nonzero B and source immutability.
            self.assertEqual(rpc('/api/port-reduction',dict(circuits=c,input_id=c['group_ids'][0],shorted_ids=c['group_ids'][1:])),report)  #: Keep the real browser bridge identical to direct characterization.

    def test_real_protected_http_preserves_accepted_state(self):  #: Characterization must not replace or mutate a prior accepted field/job.
        server=make_server();state=server.studio_state;thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()  #: Exercise an actual protected loopback server on an allocated port.
        try:  #: Always release real HTTP resources after success or rejection.
            state.job=dict(id='accepted',status='done');state.field_result={'sentinel':'unchanged'};state.result_job='accepted'  #: Establish explicit accepted workspace state independently of characterization.
            data=dict(circuits=dict(group_ids=['a','b'],names=['same','same'],inductance_H=[[1.,.3],[.3,.5]]),input_id='a',shorted_ids=['b'])  #: Submit an explicit supplied matrix; the API does not claim to authenticate arbitrary matrices as FEM evidence.
            request=Request('http://127.0.0.1:'+str(server.server_port)+'/api/port-reduction',data=json.dumps(data).encode(),headers={'X-Studio-Token':state.token,'Content-Type':'application/json'})  #: Retain genuine session/body/host guards.
            with urlopen(request) as response:r=json.load(response)  #: Read actual finite JSON returned by the server.
            self.assertAlmostEqual(r['input_inductance_H'],.82);self.assertEqual(state.result_job,'accepted');self.assertEqual(state.field_result,{'sentinel':'unchanged'});self.assertEqual(state.job['status'],'done')  #: Check physical reduction and unchanged accepted job/result.
        finally:server.shutdown();server.server_close();thread.join()  #: Close the genuine server and supervision thread.


if __name__=='__main__':unittest.main()  #: Support a reproducible focused source-form numerical run.
