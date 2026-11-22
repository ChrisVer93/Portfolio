"""F001 report-only numerical reproduction of canonical electrical grouping."""
import hashlib  #: Bind exact input/output files to the delivered code.
import json  #: Preserve actual model, matrix, sweep and rejection evidence.
from pathlib import Path  #: Resolve examples and the caller-selected output directory.
import sys  #: Import this release's source engine during direct invocation.
ROOT = Path(__file__).resolve().parents[1]  #: Keep the runtime imports tied to this delivered source tree.
sys.path.insert(0, str(ROOT))  #: Prefer the actual release's engine over unrelated installed code.
from engine.analysis import solve_project, current_sweep  #: Run actual spatial matrix and current-sweep fields.
from engine.ac import solve_ac  #: Confirm compatible harmonic current/loss solving remains available.
from engine.project import validate  #: Inspect canonical migration through the public project boundary.


def run(output):  #: Generate evidence explicitly, rather than modifying fixtures during import.
    output = Path(output); output.mkdir(parents=True, exist_ok=True)  #: Keep report evidence separate from runtime data.
    source = ROOT/'examples/cllc_nominal_flux_peak_3d.json'  #: Use the unchanged actual CLLC-labelled linear snapshot fixture.
    p = json.loads(source.read_text()); p['domain'].update(nx=4, ny=4, nz=4)  #: Change only reference mesh targets for a bounded reproducible field case.
    canonical = validate(p)  #: Convert the old series map without changing geometry, turns, current or material.
    solved = solve_project(p, progress=print)  #: Compute the real 3D field and all three section-level unit excitations.
    sweep = current_sweep(p, 'primary_inner', [0, 1], progress=print)  #: Selecting the inner source must sweep and measure both primary sections.
    primary = solved['circuits']['inductance_H'][0][0]  #: Use the exported grouped primary coefficient as the linear comparator.
    measured = sweep['rows'][1]['chord_inductance_H']  #: Read linkage-derived inductance from the independently recomputed field.
    if abs(measured/primary-1) > 1e-7:  #: Gate the actual electrical interpretation before saving accepted evidence.
        raise RuntimeError('Grouped matrix and swept primary linkage disagree')  #: Do not publish a failed connection correction.
    foil = json.loads((ROOT/'examples/ac_square_2d.json').read_text())  #: Use a separately defined valid conducting AC problem.
    try:  #: Record the explicit incompatibility instead of treating a thrown error as a field solution.
        solve_project(foil)  #: The ordinary static path previously returned a misleading zero field here.
    except ValueError as error:  #: Expect the new physics-selection guard.
        rejection = str(error)  #: Retain the actual diagnostic in reproducible JSON.
    else:  #: A silently accepted static result is a benchmark failure.
        raise RuntimeError('AC solid source was silently ignored by static solve')  #: Prevent a false successful release.
    ac = solve_ac(foil)  #: Run the same unchanged fixture through the actual harmonic solver.
    result = {'passed': True, 'source_fixture_sha256': hashlib.sha256(source.read_bytes()).hexdigest(), 'canonical_project': canonical, 'stats': solved['stats'], 'section_inductance_H': solved['inductance_H'], 'electrical_ports': solved['circuits'], 'sweep': sweep, 'grouped_to_sweep_relative_difference': abs(measured/primary-1), 'static_ac_rejection': rejection, 'ac_stats': ac['stats'], 'ac_ports': ac['ac']['ports'], 'limits': 'Same-model linear static consistency only; CLLC uses ideal sheets and illustrative linear core, no loaded resonant circuit, no mesh convergence or Maxwell/hardware validation. Native FEM code was not executed by this benchmark.'}  #: Keep complete numerical inputs, definitions and limits with actual outputs.
    (output/'benchmark.json').write_text(json.dumps(result, indent=2, allow_nan=False)+'\n')  #: Save finite completed evidence only after all gates pass.
    print(json.dumps({'passed': True, 'elements': solved['stats']['elements'], 'grouped_primary_H': primary, 'sweep_primary_H': measured, 'difference': result['grouped_to_sweep_relative_difference']}))  #: Summarise actual completed numerical values.
    return result  #: Allow report generation without launching a second solve.


if __name__ == '__main__':  #: Importing this report-only tool must never start a field job.
    run(sys.argv[1] if len(sys.argv)>1 else ROOT/'sample_results/source_integrity')  #: Accept an explicit output directory or the documented evidence location.
