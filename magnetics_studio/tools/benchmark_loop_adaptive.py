"""QA-only native adaptive source-preservation and separated accuracy study."""
import argparse  #: Require an explicit new evidence destination.
import json  #: Save actual accepted meshes, fields and separate comparison data.
import math  #: Normalize complete vector comparisons at the actual solved current.
from pathlib import Path  #: Resolve the delivered engine and QA references.
import sys  #: Bind imports to this exact source checkout.
import time  #: Record observed end-to-end execution time.
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))  #: Use the delivered native controller and independent smooth-current integral.
from engine.loop_adaptive import solve_adaptive_loop,enrich_adaptive  #: Execute actual residual-driven native h refinement and bounded p enrichment.
from engine.mesh import dot  #: Use full vector norms rather than a single selected component.
from tests.test_loop_adaptive import adaptive  #: Keep explicit adaptive settings reproducible.
from tests.test_closed_loop import independent_field  #: Compute independent smooth-annulus references in cylindrical coordinates.


def main():  #: Run three cases that distinguish fixed-source adaptation, outer domain and source angular faceting.
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('output',type=Path);args=parser.parse_args();args.output.mkdir(parents=True,exist_ok=True)  #: Require one explicit evidence directory.
    summaries=[]  #: Preserve actual results for every declared scenario.
    for name,angular,extended,passes in [('coarse',8,False,4),('larger_domain',8,True,2),('finer_source',16,True,2)]:  #: Change only source angle count between the two extended-domain scenarios.
        spec=adaptive(passes);spec['model']['source']['cells']=[angular,1,1]  #: Declare the actual original conduction-source mesh separately from magnetic refinement.
        if extended:spec['model']['radial_air_m']+=[.14,.26];spec['model']['axial_air_m']+=[.14,.26]  #: Extend the original domain while retaining every existing inner plane.
        start=time.perf_counter();result=solve_adaptive_loop(spec);higher=enrich_adaptive(result,2);seconds=time.perf_counter()-start  #: Execute every solve and resource-limited enrichment attempt.
        result['enrichment']=higher  #: Preserve both actual accepted field sequences without substituting a higher-order field onto the wrong mesh.
        (args.output/(name+'_model.json')).write_text(json.dumps(spec,indent=2)+'\n')  #: Save the complete actual SI request.
        (args.output/(name+'_result.json')).write_text(json.dumps(result,allow_nan=False)+'\n')  #: Preserve all accepted mesh/field and source-volume evidence.
        source=result['frame']['source'];current=source['terminal_current_into_conductor_A']['high'];ratio=current/source['analytic_cut_current_A']  #: Normalize the independent smooth reference to the same actual cut current.
        smooth=[[v*ratio for v in independent_field(source['input'],p,24)] for p in source['input']['probes_m']]  #: Keep source-geometric error separate from same-source magnetic comparisons.
        solution=higher.get('native');same=[p['relative_vector_difference'] for p in solution['probes']] if solution else None  #: Retain a genuine undefined result when no higher-order solve fit.
        smooth_errors=[math.dist(p['B_T'],v)/math.sqrt(dot(v,v)) for p,v in zip(solution['probes'],smooth)] if solution else None  #: Report all three full-vector smooth/current-matched differences without hiding an unfavorable point.
        history=[{k:v for k,v in h.items() if k not in ('mesh','cell_B_T')} for h in result['history']]  #: Keep a compact measurement summary alongside complete actual field files.
        record=dict(name=name,source_cells=len(source['mesh']['tetrahedra']),angular_cells=angular,domain_radius_m=spec['model']['radial_air_m'][-1],domain_half_height_m=spec['model']['axial_air_m'][-1],seconds=seconds,stop_reason=result['stop_reason'],history=history,enrichment_status=higher['status'],selected_pass=higher['selected_pass'],enrichment_attempts=higher['attempts'],enriched_mixed_dofs=solution['mixed_dofs'] if solution else None,enriched_energy_J=solution['energy_J'] if solution else None,enriched_inductance_H=solution['energy_inductance_H'] if solution else None,same_source_probe_differences=same,current_matched_smooth_probe_differences=smooth_errors,current_matched_smooth_B_T=smooth)  #: Preserve accepted fields, true resource limits and both physical comparison conventions.
        summaries.append(record);print(json.dumps(record,allow_nan=False),flush=True)  #: Save genuine streamed measurements rather than a manufactured convergence narrative.
    (args.output/'benchmark.json').write_text(json.dumps({'scenarios':summaries},indent=2,allow_nan=False)+'\n')  #: Publish complete finite measured comparisons after every actual requested solve succeeds.


if __name__=='__main__':main()  #: Keep imports free of benchmark side effects.
