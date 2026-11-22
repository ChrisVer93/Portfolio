"""QA-only actual tight/loose/budget flux-control studies with explicit accuracy limits."""
import argparse  #: Require an explicit evidence destination.
import json  #: Persist complete actual inputs, accepted meshes/fields and stopping criteria.
from pathlib import Path  #: Resolve this exact delivered engine and independent prior reference data.
import sys  #: Bind numerical imports to the delivered checkout.
import time  #: Record actual end-to-end one-host solve timings.
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))  #: Import the qualified local controller and explicit QA request.
from engine.flux_adaptive import solve_flux_adaptive  #: Execute real native source-preserving refinement and pickup monitoring.
from tests.test_flux_adaptive import spec  #: Keep every declared physical model and empirical threshold reproducible.
ROOT=Path(__file__).resolve().parents[1]  #: Resolve actual historical independent smooth-reference quadrature.


def main():  #: Compare real empirical stopping outcomes against separately retained physical reference values.
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('output',type=Path);args=parser.parse_args();args.output.mkdir(parents=True,exist_ok=True)  #: Save all observations in an explicit new evidence directory.
    reference=json.loads((ROOT/'sample_results/surface_flux/benchmark.json').read_text())  #: Reuse labelled E9 independent cylindrical/square reference integrals, not invented new reference solves.
    scenarios=[('tight',spec(4,.001,2)),('loose',spec(4,.2,2)),('budget',spec(4,.001,2))];scenarios[-1][1]['model']['source']['cells']=[16,1,1]  #: Separate strict, intentionally loose and actually DOF-limited physical runs.
    summaries=[]  #: Preserve every observed stop and unfavorable field comparison.
    for name,request in scenarios:  #: Actually solve each declared native sequence.
        start=time.perf_counter();result=solve_flux_adaptive(request);seconds=time.perf_counter()-start  #: Measure complete real source/refinement/flux execution.
        (args.output/(name+'_model.json')).write_text(json.dumps(request,indent=2)+'\n');(args.output/(name+'_result.json')).write_text(json.dumps(result,allow_nan=False)+'\n')  #: Retain actual requests, full accepted fields and original current provenance.
        source=result['frame']['source'];ratio=source['terminal_current_into_conductor_A']['high']/source['analytic_cut_current_A'];target=[v[1]*ratio for v in reference['smooth_reference_quadrature_flux_Wb']]  #: Match each reused smooth-reference integral to the actual solved circulation.
        history=[]  #: Keep compact measurements alongside full persisted native meshes and fields.
        for h in result['history']:  #: Report each genuinely accepted mesh and all pickup decisions.
            flux=[sum(o['flux_Wb'] for o in h['surface_flux'][j:j+2]) for j in (0,2)]  #: Compose the actual central and remote squares from their oriented triangle halves.
            history.append(dict(pass_number=h['pass_number'],tetrahedra=h['tetrahedra'],mixed_dofs=h['mixed_dofs'],energy_J=h['energy_J'],relative_residual_indicator=h['relative_residual_indicator'],relative_energy_change=h['relative_energy_change'],square_flux_Wb=flux,current_matched_smooth_flux_Wb=target,signed_relative_smooth_difference=[(a-b)/b for a,b in zip(flux,target)],flux_stability=h['flux_stability'],source_binding=h['source_binding']))  #: Keep empirical stability, physical reference differences and source preservation explicitly distinct.
        record=dict(scenario=name,seconds=seconds,stop_reason=result['stop_reason'],flux_control=request['flux_control'],history=history,accuracy_certified=result['accuracy_certified'])  #: Never turn a loose stable streak into a claimed true-error bound.
        summaries.append(record);print(json.dumps(record,allow_nan=False),flush=True)  #: Stream actual numerical history and stop decisions.
    summary=dict(scenarios=summaries,reference_source='Previously executed P002E9 independent cylindrical conductor/square Gauss quadrature; reused, not a new reference solve',reference_rule_sensitivity=reference['reference_relative_rule_change'],scope='Native order-zero fixed-source/domain empirical flux stopping; no source/p/domain accuracy certification')  #: Preserve exact reference provenance and limited physical scope.
    (args.output/'benchmark.json').write_text(json.dumps(summary,indent=2,allow_nan=False)+'\n')  #: Save only complete actual scenarios and their declared reference basis.


if __name__=='__main__':main()  #: Keep imports free of numerical and file-writing side effects.
