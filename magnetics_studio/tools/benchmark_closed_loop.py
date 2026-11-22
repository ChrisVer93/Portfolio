"""QA-only finite-loop refinement and independent smooth-current comparison."""
import argparse  #: Select an explicit evidence output directory.
import json  #: Save exact model, fields and finite measured benchmark values.
import math  #: Measure physical current-field and dipole-moment differences.
from pathlib import Path  #: Resolve source-relative test references and output files.
import sys  #: Import the exact source checkout used for this benchmark.
import time  #: Record observed elapsed solve time without claiming cross-machine performance.
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))  #: Keep QA imports local to this delivered source.
from engine.closed_loop import solve_loop  #: Run actual scalar, conservative-current and magnetic field calculations.
from engine.mesh import dot, sub, tetra_geometry  #: Evaluate independent physical cell measures and source errors.
from tests.test_closed_loop import independent_field, model  #: Use the separately derived cylindrical quadrature reference.


def main():  #: Reproduce one complete refinement study from explicit SI data.
    parser = argparse.ArgumentParser(description=__doc__)  #: Describe the QA-only study command.
    parser.add_argument('output',type=Path)  #: Select the actual evidence destination.
    args = parser.parse_args()  #: Resolve command arguments before solving.
    args.output.mkdir(parents=True,exist_ok=True)  #: Keep all new evidence together.
    spec = model()  #: Fix the physical conductor and probe coordinates across all mesh levels.
    references = [independent_field(spec,p,24) for p in spec['probes_m']]  #: Compute independent smooth-annulus B vectors.
    reference_checks = [independent_field(spec,p,16) for p in spec['probes_m']]  #: Measure separate cylindrical quadrature sensitivity.
    levels = []  #: Preserve actual measured mesh/source/field behavior in refinement order.
    for counts in ([16,1,1],[32,2,2],[64,4,4],[128,8,4]):  #: Refine angular geometry and finite cross-section resolution.
        start = time.perf_counter()  #: Time the complete actual solve including source projection and probe integration.
        solved = solve_loop(dict(spec,cells=counts))  #: Solve each mesh independently.
        seconds = time.perf_counter()-start  #: Retain observed wall time on this exact environment only.
        recovered = solved['conservative_current']  #: Inspect the finite current used to create the field.
        denominator, raw_error, projected_error, projected_power = [], [], [], []  #: Collect independent source and dissipation integrals.
        coefficient = spec['conductivity_S_m']*spec['voltage_V']/(2*math.pi)  #: Derive the exact smooth J_theta=C/r coefficient.
        for cell, raw, current in zip(solved['mesh']['tetrahedra'],solved['current_density_A_m2'],recovered['current_density_at_cell_centroid_A_m2']):  #: Compare both discontinuous and recovered currents on the same actual cells.
            points = [solved['mesh']['nodes_m'][n] for n in cell]  #: Use actual mapped copper geometry.
            volume, _ = tetra_geometry(points)  #: Obtain an independent physical volume measure.
            x, y = (sum(p[d] for p in points)/4 for d in (0,1))  #: Evaluate the analytical current at each physical cell centroid.
            exact = (-coefficient*y/(x*x+y*y),coefficient*x/(x*x+y*y),0.)  #: Preserve the exact vector direction and radial current variation.
            denominator.append(volume*dot(exact,exact))  #: Form the physical volume-weighted reference norm.
            raw_error.append(volume*dot(sub(raw,exact),sub(raw,exact)))  #: Measure the original scalar-gradient source error.
            projected_error.append(volume*dot(sub(current,exact),sub(current,exact)))  #: Measure the recovered source error independently of conservation.
            projected_power.append(volume*dot(current,current)/spec['conductivity_S_m'])  #: Record the recovered centroid dissipation separately from the original P1 Joule loss.
        moment = spec['conductivity_S_m']*spec['voltage_V']*spec['thickness_m']*(spec['outer_radius_m']**2-spec['inner_radius_m']**2)/4  #: Derive an independent smooth-loop dipole moment in A m².
        record = dict(cells=counts,tetrahedra=len(solved['mesh']['tetrahedra']),nodes=len(solved['mesh']['nodes_m']),seconds=seconds,
                      resistance_ohm=solved['resistance_ohm'],resistance_relative_error=solved['resistance_ohm']/solved['analytic_resistance_ohm']-1,
                      probe_relative_vector_errors=[math.dist(f['B_T'],v)/math.sqrt(dot(v,v)) for f,v in zip(solved['magnetic_field'],references)],
                      raw_relative_centroid_error=math.sqrt(math.fsum(raw_error)/math.fsum(denominator)),projected_relative_centroid_error=math.sqrt(math.fsum(projected_error)/math.fsum(denominator)),
                      projection_correction=recovered['relative_centroid_field_correction'],max_relative_balance_defect=recovered['max_relative_balance_defect'],max_cell_current_defect_A=recovered['max_cell_current_defect_A'],
                      original_joule_power_W=solved['joule_power_W'],projected_centroid_joule_power_W=math.fsum(projected_power),
                      source_integrals=solved['source_integrals'],moment_relative_error=solved['source_integrals']['magnetic_moment_A_m2'][2]/moment-1,
                      magnetic_field=solved['magnetic_field'])  #: Retain actual timing, geometry/source/field errors and constitutive sensitivity without turning balance into an error estimate.
        levels.append(record)  #: Preserve every independently solved refinement result.
        print(json.dumps(record,allow_nan=False),flush=True)  #: Stream genuine measurements for the raw benchmark log.
    (args.output/'model.json').write_text(json.dumps(dict(spec,cells=counts),indent=2)+'\n')  #: Save the exact final source request.
    (args.output/'loop_result.json').write_text(json.dumps(solved,allow_nan=False)+'\n')  #: Preserve the final actual tetrahedral source and solved field arrays.
    summary = dict(levels=levels,smooth_reference_B_T=references,reference_quadrature_relative_changes=[math.dist(a,b)/math.sqrt(dot(a,a)) for a,b in zip(references,reference_checks)],analytic_resistance_ohm=solved['analytic_resistance_ohm'],analytic_center_Bz_T=solved['analytic_center_Bz_T'])  #: Keep exact reference provenance and actual numerical quadrature stability.
    (args.output/'benchmark.json').write_text(json.dumps(summary,indent=2,allow_nan=False)+'\n')  #: Persist finite reviewable study data.


if __name__ == '__main__':  #: Keep imports free of benchmark side effects.
    main()  #: Execute only through the explicit source QA command.
