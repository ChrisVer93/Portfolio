"""Independent rectangular-conductor Fourier reference and reproducible AC cases."""
import json  #: Read and write portable benchmark models/evidence.
import math  #: Evaluate the independent double-sine diffusion solution.
from pathlib import Path  #: Locate delivered examples relative to the release root.
import sys  #: Import the delivered engine during direct script execution.
ROOT = Path(__file__).resolve().parents[1]  #: Resolve the release directory independently of the current working directory.
sys.path.insert(0, str(ROOT))  #: Prefer this release's engine over unrelated installed modules.
from engine.ac import solve_ac, frequency_sweep  #: Run actual AC fields rather than deriving losses from static snapshots.
from engine.materials import MU0  #: Match the SI vacuum permeability constant in the independent analytic equations.
from engine.export import write_report  #: Save an inspectable offline view of solved fields.


def rectangular_impedance(width, height, depth, sigma, frequency, terms=160):  #: Evaluate E0*d/I for a uniform solid rectangle with Az=0 on its entire perimeter.
    omega, nu = 2 * math.pi * frequency, 1 / MU0  #: This independent reference uses μr=1 and exp(+jωt).
    area = width * height  #: The source constraint integrates current over the whole conductor cross-section.
    integral = 0j  #: Accumulate ∫Az dS divided by σE0.
    for m in range(1, 2 * terms, 2):  #: A constant source excites only odd sine harmonics in x.
        for n in range(1, 2 * terms, 2):  #: The same odd-harmonic restriction applies in y.
            eigenvalue = nu * math.pi ** 2 * ((m / width) ** 2 + (n / height) ** 2)  #: Eigenvalue of the independent Dirichlet diffusion stiffness operator.
            integral += 64 * area / (math.pi ** 4 * m * m * n * n * (eigenvalue + 1j * omega * sigma))  #: Integrate each double-sine response analytically over the rectangle.
    gradient_per_amp = 1 / (sigma * (area - 1j * omega * sigma * integral))  #: Enforce I=σ(E0*S−jω∫Az) instead of prescribing an incorrect fixed electric gradient.
    return depth * gradient_per_amp  #: Convert the axial gradient ratio into the defined finite-depth field-port impedance.


def main():  #: Reproduce all Task 002 numerical evidence in one explicit command.
    output = ROOT / 'sample_results' / 'ac'  #: Keep solved AC examples separate from static and adaptive samples.
    output.mkdir(parents=True, exist_ok=True)  #: Preserve earlier outputs while making the directory available.
    model = json.loads((ROOT / 'examples' / 'ac_square_2d.json').read_text())  #: Use the documented analytic-reference geometry.
    rows = []  #: Retain every tested mesh rather than selecting a favourable one.
    reference = rectangular_impedance(.004, .004, .1, 58e6, 10000.)  #: Compute an independent Fourier reference at 10 kHz.
    check = rectangular_impedance(.004, .004, .1, 58e6, 10000., terms=240)  #: Check series truncation independently of FEM mesh refinement.
    for subdivisions in [8, 16, 32, 48]:  #: Refine physical element size relative to skin depth.
        model['domain'].update(nx=subdivisions, ny=subdivisions)  #: Change only mesh subdivisions for this sequence.
        result = solve_ac(model, progress=print)  #: Solve the true complex conductor-current problem.
        z = complex(*result['ac']['ports'][0]['impedance_ohm'])  #: Decode the explicit real/imaginary port convention.
        rows.append(dict(subdivisions=subdivisions, elements=result['stats']['elements'], impedance_ohm=[z.real, z.imag], relative_complex_error=abs(z-reference)/abs(reference), ohmic_loss_W=result['ac']['ohmic_loss_W'], power_balance=result['ac']['complex_power_balance']))  #: Record accuracy and independent power evidence together.
    write_report(result, output / 'square_fields.html')  #: Export the final reference-model field snapshot and complete phasors.
    (output / 'square_fields.json').write_text(json.dumps(result, allow_nan=False))  #: Retain the exact final mesh and complex field data.
    foil = json.loads((ROOT / 'examples' / 'ac_foil_pair_2d.json').read_text())  #: Use a forward/return pair plus a passive isolated shield as a representative stationary conductor case.
    solved = solve_ac(foil, progress=print)  #: Verify actual induced currents and loss in the passive shield.
    write_report(solved, output / 'foil_fields.html')  #: Provide the complete inspectable physical example.
    (output / 'foil_fields.json').write_text(json.dumps(solved, allow_nan=False))  #: Preserve source/return constraints and all solved phasors.
    sweep = frequency_sweep(foil, [1000., 10000., 100000.], progress=print)  #: Recompute fields at three frequencies on the same initial mesh.
    evidence = dict(analytic_impedance_ohm=[reference.real, reference.imag], series_relative_change=abs(check-reference)/abs(check), square_rows=rows, foil_stats=solved['stats'], foil_ports=solved['ac']['ports'], frequency_sweep=sweep, note='Fourier reference matches the finite Dirichlet square, not an unbounded isolated wire. Foil examples are demonstration meshes and require further skin-depth/domain refinement.')  #: Preserve explicit applicability limits beside the numerical results.
    (output / 'benchmark.json').write_text(json.dumps(evidence, indent=2, allow_nan=False))  #: Reject nonfinite results during evidence serialisation.
    print(json.dumps(evidence, indent=2))  #: Make the exact evidence available to captured execution logs.


if __name__ == '__main__':  #: Avoid launching numerical jobs when tests import the analytic reference.
    main()  #: Run the reproducible benchmark only on direct invocation.
