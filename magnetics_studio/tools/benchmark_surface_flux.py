"""QA-only separated native h/p/source/domain pickup-flux study."""
import argparse  #: Require an explicit new evidence destination.
import json  #: Save actual selected frames, native fields and observations.
from pathlib import Path  #: Resolve exact source-bound inputs and engine.
import sys  #: Import this delivered checkout.
import time  #: Measure actual end-to-end native solve times.
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))  #: Bind numerical code and independent QA references to this source.
from engine.loop_native import solve_native_transfer  #: Perform genuine native solves with the new physical observable.
from tests.test_surface_flux import pickups  #: Reuse the explicit central 8 mm square definition.
from tests.test_closed_loop import independent_field  #: Use an independent smooth-current cylindrical integral.
ROOT=Path(__file__).resolve().parents[1]  #: Locate immutable historical mesh/current frames.


def smooth_flux(spec,z,outer_order,source_order):  #: Integrate a smooth-reference square independently of runtime clipping and quadrature.
    import numpy as np  #: Generate an independent tensor Gauss-Legendre square rule.
    x,w=np.polynomial.legendre.leggauss(outer_order);values=[]  #: Resolve physical observation-area quadrature separately from conductor quadrature.
    for a,wa in zip(x,w):  #: Cover the complete square width.
        for b,wb in zip(x,w):values.append(.004**2*wa*wb*independent_field(spec,[.004*a,.004*b,z],source_order)[2])  #: Integrate the independent cylindrical Biot-Savart normal field in SI weber units.
    return float(sum(values))  #: Return the actual whole-square reference flux.


def main():  #: Measure separate approximation, mesh, source and exterior-domain effects without claiming a certified bound.
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('output',type=Path);args=parser.parse_args();args.output.mkdir(parents=True,exist_ok=True)  #: Save complete actual evidence in an explicit destination.
    coarse=json.loads((ROOT/'sample_results/loop_adaptive/coarse_result.json').read_text());larger=json.loads((ROOT/'sample_results/loop_adaptive/larger_domain_result.json').read_text());fine=json.loads((ROOT/'sample_results/loop_adaptive/finer_source_result.json').read_text())  #: Reuse exact accepted historical meshes and original sources, re-solving all new native fields.
    surfaces=pickups()  #: Keep one physical observation definition for every compared solve.
    for s in pickups():  #: Add a second equal-area pickup thirty millimetres above the source.
        s['id']='remote_'+s['id'];s['vertices_m']=[[x,y,.03] for x,y,z in s['vertices_m']];surfaces.append(s)  #: Preserve positive-z orientation and explicit SI distance.
    (args.output/'surfaces.json').write_text(json.dumps(surfaces,indent=2)+'\n')  #: Persist exact observation geometry for the actual CLI.
    spec=coarse['frame']['source']['input'];references=[[smooth_flux(spec,z,4,12),smooth_flux(spec,z,8,20)] for z in (0.,.03)]  #: Independently check simultaneous smooth-source and square-quadrature sensitivity.
    refined=dict(coarse['frame'],mesh=coarse['history'][1]['mesh'])  #: Select the actual accepted second h mesh with the same original source.
    cases=[('coarse_h1_p0',coarse['initial_reference'],0),('coarse_h1_p2',coarse['initial_reference'],2),('coarse_h1_p3',coarse['initial_reference'],3),('coarse_h2_p0',refined,0),('coarse_h2_p2',refined,2),('larger_domain_h1_p2',larger['initial_reference'],2),('finer_source_h1_p2',fine['initial_reference'],2)]  #: Hold source/domain fixed for the first five cases and label each separate control change.
    records=[]  #: Retain every actual physical result and resource measurement.
    for name,frame,order in cases:  #: Execute all requested native fields rather than reuse saved field arrays.
        start=time.perf_counter();native=solve_native_transfer(frame,order=order,flux_surfaces=surfaces);seconds=time.perf_counter()-start  #: Integrate true native polynomial fields on each clipped pickup.
        (args.output/(name+'.json')).write_text(json.dumps(dict(format='magnetics-studio.loop-flux/1',frame=frame,native=native),allow_nan=False)+'\n')  #: Save the exact solved source/mesh and new native volume/flux results.
        source=frame['source'];ratio=source['terminal_current_into_conductor_A']['high']/source['analytic_cut_current_A'];flux=[sum(v['flux_Wb'] for v in native['surface_flux'][j:j+2]) for j in (0,2)]  #: Combine the two physical triangle halves and normalize the smooth source to the actual solved circulation.
        target=[r[1]*ratio for r in references];relative=[(a-b)/b for a,b in zip(flux,target)]  #: Retain signed smooth/current-matched differences for both pickups.
        record=dict(case=name,order=order,tetrahedra=len(frame['mesh']['elements']),source_tetrahedra=len(source['mesh']['tetrahedra']),mixed_dofs=native['mixed_dofs'],seconds=seconds,energy_J=native['energy_J'],square_flux_Wb=flux,current_matched_smooth_flux_Wb=target,signed_relative_flux_difference=relative,max_relative_area_error=max(s['relative_area_error'] for s in native['surface_flux']))  #: Preserve geometry, resource and signed accuracy data separately from residual success.
        records.append(record);print(json.dumps(record),flush=True)  #: Stream actual measured results including unfavorable comparisons.
    summary=dict(cases=records,smooth_reference_quadrature_flux_Wb=references,reference_relative_rule_change=[abs(a/b-1) for a,b in references],scope='Finite faceted DC source in homogeneous mu0; pickup flux is not winding linkage or a certified error bound')  #: Document independent reference quadrature sensitivity and physical scope.
    (args.output/'benchmark.json').write_text(json.dumps(summary,indent=2,allow_nan=False)+'\n')  #: Save complete actual measured convergence evidence.


if __name__=='__main__':main()  #: Keep imports free of field solves and file side effects.
