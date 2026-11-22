"""QA-only matched finite-current H(curl), p-order and air-domain study."""
import argparse  #: Select an explicit new evidence destination.
from importlib import metadata  #: Record the native numerical dependencies actually executed.
import json  #: Save real source, fields, coefficients and qualification measurements.
import math  #: Normalize vector, energy and current-mode comparisons.
from pathlib import Path  #: Keep all actual evidence in one source-relative directory.
import platform  #: Record the actual development platform without implying Windows qualification.
import sys  #: Bind all test and engine imports to the delivered checkout.
import time  #: Measure actual solve time without claiming cross-machine performance.
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))  #: Use the exact delivered source and independent QA references.
from engine.loop_fem import solve_loop_fem  #: Execute the matching reference curl-curl formulation.
from engine.loop_native import solve_native_transfer  #: Execute the pinned established mixed-gauge formulation.
from engine.mesh import dot,sub  #: Compare full physical vector fields.
from tests.test_loop_fem import request  #: Use the explicit bounded matching source and magnetic air domain.
from tests.test_closed_loop import independent_field  #: Compute a separate smooth-annulus vector reference.


def save(path,value):  #: Persist actual complete numerical results with no NaN or infinity placeholders.
    path.write_text(json.dumps(value,allow_nan=False)+'\n',encoding='utf-8')  #: Keep JSON arrays and coefficients detached and reproducible.


def main():  #: Reproduce actual matched-source, gauge, p-refinement and air-domain measurements.
    parser = argparse.ArgumentParser(description=__doc__);parser.add_argument('output',type=Path);args = parser.parse_args()  #: Require an explicit QA destination before solving.
    args.output.mkdir(parents=True,exist_ok=True);spec = request();started = time.perf_counter();reference = solve_loop_fem(spec)  #: Run the actual conductor and conforming reference magnetic problem.
    reference_seconds = time.perf_counter()-started;save(args.output/'model.json',spec);save(args.output/'reference.json',reference)  #: Save the exact model and complete reference volume field.
    source = reference['source'];circulation = source['terminal_current_into_conductor_A']['high'];ratio = circulation/source['analytic_cut_current_A']  #: Match the independent smooth-geometry comparison to the actually solved current, not silently to a different voltage-driven current.
    smooth = [[v*ratio for v in independent_field(source['input'],p,24)] for p in source['input']['probes_m']]  #: Compute smooth-annulus fields at that exact actual current in separate cylindrical quadrature.
    sequence = [];native_results = {}  #: Retain actual approximation-order and gauge outputs.
    for order in (0,2,3):  #: Exercise the actual supported native approximation orders on the identical physical mesh and source.
        start = time.perf_counter();result = solve_native_transfer(reference,order);seconds = time.perf_counter()-start  #: Execute each native mixed solve independently.
        native_results[order] = result;save(args.output/f'native_order{order}.json',result)  #: Preserve actual native volume fields and finite-element coefficients.
        record = dict(order=order,mixed_dofs=result['mixed_dofs'],seconds=seconds,energy_J=result['energy_J'],energy_inductance_H=result['energy_inductance_H'],same_source_probe_relative_differences=[p['relative_vector_difference'] for p in result['probes']],matched_current_smooth_probe_relative_differences=[math.dist(p['B_T'],b)/math.sqrt(dot(b,b)) for p,b in zip(result['probes'],smooth)],source_gradient_compatibility=result['source_gradient_compatibility'],relative_residual=result['relative_residual'],relative_energy_identity_error=result['relative_energy_identity_error'])  #: Keep physical field error comparisons distinct from source, solver and energy identities.
        sequence.append(record);print(json.dumps(dict(p_refinement=record)),flush=True)  #: Retain genuine raw measurements for every actual approximation order.
    full = solve_native_transfer(reference,2,True);save(args.output/'native_full_gradients_order2.json',full)  #: Execute the independent complete-gradient mixed gauge on the same curl space.
    difference = math.fsum(dot(sub(a,b),sub(a,b)) for a,b in zip(full['B_at_cell_centroids_T'],native_results[2]['B_at_cell_centroids_T']));norm = math.fsum(dot(b,b) for b in full['B_at_cell_centroids_T'])  #: Measure full-volume physical gauge invariance without relying on selected probe agreement.
    gauge = dict(full_dofs=full['mixed_dofs'],reduced_dofs=native_results[2]['mixed_dofs'],relative_volume_vector_difference=math.sqrt(difference/norm),relative_energy_difference=abs(full['energy_J']/native_results[2]['energy_J']-1))  #: Record the actual DOF reduction and physical equivalence of both gauges.
    domains = []  #: Keep outer-domain sensitivity separate from the fixed-domain p study.
    for additions in ([],[.14],[.14,.26]):  #: Append only outer planes and retain every original inner cell.
        domain = request();domain['radial_air_m']+=additions;domain['axial_air_m']+=additions  #: Move the homogeneous tangential-A boundary while preserving the matched physical current.
        ref = reference if not additions else solve_loop_fem(domain);native = native_results[2] if not additions else solve_native_transfer(ref,2)  #: Resolve both actual magnetic formulations on each nested domain.
        record = dict(radial_boundary_m=domain['radial_air_m'][-1],axial_half_height_m=domain['axial_air_m'][-1],tetrahedra=len(ref['mesh']['elements']),mixed_dofs=native['mixed_dofs'],reference_energy_J=ref['energy_J'],native_energy_J=native['energy_J'],native_inductance_H=native['energy_inductance_H'],same_source_probe_relative_differences=[p['relative_vector_difference'] for p in native['probes']])  #: Preserve actual energy, inductance and field changes without asserting an infinite-domain error bound.
        domains.append(record);print(json.dumps(dict(nested_domain=record)),flush=True)  #: Keep raw observed sensitivity available for independent review.
    error = math.fsum(dot(sub(a,b),sub(a,b)) for a,b in zip(reference['B_T'],native_results[0]['B_at_cell_centroids_T']));norm = math.fsum(dot(b,b) for b in reference['B_T'])  #: Compare all lowest-order volume fields between independent assemblers and gauges.
    versions = {n:metadata.version(n) for n in ('numpy','scipy','ngsolve','ngsolve-openblas','netgen-mesher','netgen-occt')}  #: Record the exact actual development dependency combination.
    summary = dict(reference_seconds=reference_seconds,source_current_A=circulation,source_voltage_V=source['input']['voltage_V'],source_cells=len(source['mesh']['tetrahedra']),magnetic_cells=len(reference['mesh']['elements']),reference_edges=len(reference['edges']),reference_energy_J=reference['energy_J'],reference_inductance_H=reference['energy_inductance_H'],reference_source_gradient_compatibility=reference['source_gradient_compatibility'],reference_omitted_gauge_residual=reference['omitted_gauge_residual'],reference_native_lowest_order_relative_volume_vector_difference=math.sqrt(error/norm),reference_native_lowest_order_relative_energy_difference=abs(reference['energy_J']/native_results[0]['energy_J']-1),matched_current_smooth_B_T=smooth,p_refinement=sequence,gauge_comparison=gauge,nested_domains=domains,versions=versions,python=sys.version,platform=platform.platform())  #: Save complete actual numerical provenance and precise same-source versus smooth-current comparison conventions.
    save(args.output/'benchmark.json',summary);print(json.dumps(dict(gauge=gauge,versions=versions)),flush=True)  #: Publish finite complete QA results only after every selected solve succeeds.


if __name__=='__main__':  #: Keep imports free of native benchmark execution.
    main()  #: Run only through the explicit source QA command.
