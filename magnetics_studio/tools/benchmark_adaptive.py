"""Reproduce Task 001 evidence using standard-library Python and the shipped FEM.

Run from the release root: python tools/benchmark_adaptive.py
"""
import json  #: Read models and save machine-readable numerical evidence.
import pathlib  #: Resolve release-relative input and output paths portably.
import sys  #: Make the release's engine importable when invoking this script directly.
ROOT = pathlib.Path(__file__).resolve().parents[1]  #: Find the release root from this script's installed location.
sys.path.insert(0, str(ROOT))  #: Prefer the delivered engine over an unrelated Python module.
from engine.adaptive import adaptive_solve, refine_mesh  #: Run local adaptation and a separate uniformly subdivided reference sequence.
from engine.analysis import solve_project, _solve_on_mesh  #: Compare global remeshing and nested uniform refinement with the same physical solver.
from engine.mesh import build_mesh  #: Construct the common initial mesh for the nested comparison.
from engine.project import validate  #: Apply the ordinary model validation before using the internal mesh solve entry point.
from engine.export import write_report  #: Export a self-contained viewer of the final solved fields.


def main():  #: Keep execution explicit so importing this script does not launch solves.
    output = ROOT / 'sample_results' / 'adaptive'  #: Keep reproducible evidence beside the existing sample results.
    output.mkdir(parents=True, exist_ok=True)  #: Create the evidence directory without removing existing files.
    original = json.loads((ROOT / 'examples' / 'transformer_2d.json').read_text())  #: Use the delivered gapped transformer geometry and excitations.
    project = json.loads(json.dumps(original))  #: Make an independent JSON-compatible working copy.
    project['domain'].update(nx=10, ny=10)  #: Begin with a deliberately coarse interface-fitted mesh.
    result = adaptive_solve(project, dict(max_passes=6), matrix=True, progress=print)  #: Run up to six accepted passes and extract the final winding matrix.
    global_rows = []  #: Collect a separate global refinement sequence for comparison.
    for target in [10, 18, 26, 50, 80]:  #: Span coarse meshes through a substantially finer reference.
        p = json.loads(json.dumps(original))  #: Reset geometry and source definitions for each comparison.
        p['domain'].update(nx=target, ny=target)  #: Change only the global mesh target.
        r = solve_project(p, matrix=False, progress=print)  #: Solve without unnecessary unit-excitation matrix jobs.
        row = {k: r['stats'][k] for k in ['nodes', 'elements', 'energy_J', 'peak_B_T', 'seconds']}  #: Record measurable computational and field outputs.
        row['target'] = target  #: Retain the input subdivision control for reproducibility.
        row['linkages_Wb_turn'] = [w['linkage_Wb_turn'] for w in r['windings']]  #: Record every winding's response at the same operating point.
        global_rows.append(row)  #: Preserve the full trend rather than only a selected favourable point.
    validated = validate(project)  #: Reuse the exact coarse operating-point source definition for nested comparisons.
    mesh = build_mesh(validated)  #: Start the uniform reference from the same fitted triangles as adaptation.
    uniform_rows = []  #: Record every uniform level rather than treating the finest one as exact truth.
    for level in range(4):  #: Three complete refinements create 64 times as many triangles as the initial mesh.
        r = _solve_on_mesh(validated, mesh, matrix=False, progress=print)  #: Solve the same physical equations on each explicitly subdivided mesh.
        row = {k: r['stats'][k] for k in ['nodes', 'elements', 'energy_J', 'peak_B_T', 'seconds']}  #: Store directly measured outputs for each reference level.
        row['uniform_level'] = level  #: Make the repeated-red-refinement history reproducible.
        uniform_rows.append(row)  #: Preserve the approach to the finite reference energy.
        if level < 3:  #: Avoid constructing an unused mesh beyond the documented memory budget.
            mesh = refine_mesh(mesh, range(len(mesh['elements'])))  #: Refine every cell uniformly through the same conforming splitter.
    reference_energy = uniform_rows[-1]['energy_J']  #: Use the finest nested uniform run as a numerical comparison, not exact truth.
    for row in result['adaptive']['rows'] + global_rows + uniform_rows:  #: Apply the same comparison convention to every sequence.
        row['energy_difference_to_fine_uniform'] = abs(row['energy_J'] - reference_energy) / abs(reference_energy)  #: This is finite-mesh agreement rather than a certified physical error.
    evidence = dict(model=project, adaptive=result['adaptive'], final_stats=result['stats'], final_inductance_H=result['inductance_H'], global_rows=global_rows, uniform_rows=uniform_rows, reference_note='Finest nested uniform mesh is a numerical comparator, not an analytic, measured or Maxwell reference; it still requires further convergence assessment.')  #: Bind every reported quantity to actual inputs and solver output.
    (output / 'benchmark.json').write_text(json.dumps(evidence, indent=2, allow_nan=False))  #: Reject nonfinite values during evidence serialisation.
    (output / 'adaptive_fields.json').write_text(json.dumps(result, allow_nan=False))  #: Store the exact final mesh, fields, project and adaptive history.
    write_report(result, output / 'adaptive_fields.html')  #: Provide an offline viewer for inspecting the final physical solution.
    print(json.dumps(evidence, indent=2))  #: Make the same evidence visible in a captured execution log.


if __name__ == '__main__':  #: Launch only for direct command-line execution.
    main()  #: Reproduce the complete benchmark and all its output files.
