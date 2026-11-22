"""Real optional-backend verification; no mocks and no Maxwell reference claim."""
import copy  #: Vary one physical parameter per reproducible native calculation.
import json  #: Persist actual measurements and the exact dependency environment.
import math  #: Evaluate independent SI wire resistance arithmetic.
import pathlib  #: Resolve input models and selected output directories.
import platform  #: Record the platform on which native code was actually exercised.
import sys  #: Import this source tree when launched from tools/.
import tempfile  #: Isolate and remove deliberately invalid native CAD output from the negative control.
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))  #: Select this delivered bridge implementation.
from engine.openmagnetics_bridge import calculate, create_case, winding_contract  #: Call real external calculations and CAD through the production bridge.


def run(output):  #: Produce reproducible measurements rather than a hand-written validation table.
    root = pathlib.Path(__file__).resolve().parents[1]  #: Find shipped source models independently of the working directory.
    request = json.loads((root / 'examples/openmagnetics_core_screening.json').read_text())  #: Use the public equal-turn E-core screening case.
    output = pathlib.Path(output)  #: Respect the caller's chosen writable benchmark location.
    baseline = create_case(request, output / 'core_24turn')  #: Generate and reimport actual baseline core CAD and calculate native L/R.
    measurements = {'platform': platform.platform(), 'python': sys.version, 'baseline_values': baseline['values'], 'cad': baseline['cad'], 'checks': [], 'reference_scope': 'analytic geometry/DC wire arithmetic and parameter scaling only; Maxwell/hardware pending'}  #: Label what these measurements establish and what they do not.
    from OpenMagneticsVirtualBuilder.builder import Builder  #: Exercise the actual native generator without our compatibility translation as a negative control.
    import cadquery as cq  #: Inspect the actual failed native exchange file rather than mocking an empty result.
    with tempfile.TemporaryDirectory() as temporary:  #: Do not ship the deliberately empty native CAD file as a usable deliverable.
        raw_files = Builder('CadQuery').get_core('negative_control', baseline['core']['geometricalDescription'], output_path=temporary, save_files=False, export_files=True)  #: Reproduce the halfSet/half-set incompatibility using real MKF output.
        count = len(cq.importers.importStep(raw_files[0]).val().Solids())  #: Measure how many actual solids the unadapted native export contains.
        assert count == 0, count  #: Freeze the observed compatibility failure for these pinned package versions.
        measurements['checks'].append({'check': 'unadapted_native_negative_control', 'actual_solids': count, 'adapted_solids': baseline['cad']['solid_count']})  #: Demonstrate why checking export filenames alone would be inadequate.
    for turns in [12, 24, 48]:  #: Exercise native magnetising-inductance turn scaling at fixed gap/model.
        case = copy.deepcopy(request)  #: Keep each test input independent.
        case['turns'] = turns  #: Change only the electrical turn count.
        actual = calculate(case)['values']['magnetizing_inductance_H']  #: Obtain the actual MKF result rather than a copied expected value.
        expected = baseline['values']['magnetizing_inductance_H'] * (turns / 24) ** 2  #: Use the fixed-reluctance N-squared law as a structural consistency reference.
        relative = abs(actual - expected) / expected  #: Measure the actual turn-scaling disagreement.
        assert relative < 1e-10, (turns, actual, expected)  #: Stop qualification if basic reluctance scaling fails.
        measurements['checks'].append({'check': 'turn_scaling', 'turns': turns, 'actual_H': actual, 'expected_H': expected, 'relative_error': relative})  #: Preserve numerical evidence for every turn-count case.
    previous = None  #: Compare increasing gap at fixed turns without assuming a particular empirical fringing formula.
    alternate = copy.deepcopy(request)  #: Keep the model-selection sensitivity case independent of turn/gap variations.
    alternate['reluctance_model'] = 'ZHANG'  #: Exercise the second supported real native gap model explicitly.
    alternate_inductance = calculate(alternate)['values']['magnetizing_inductance_H']  #: Recompute with upstream fringing assumptions instead of changing our own formula.
    assert alternate_inductance > 0 and alternate_inductance != baseline['values']['magnetizing_inductance_H']  #: Check actual model selection changes the finite-gap prediction in this case.
    measurements['checks'].append({'check': 'model_selection_sensitivity', 'model': 'ZHANG', 'actual_H': alternate_inductance, 'note': 'model sensitivity, not independent accuracy validation'})  #: Preserve the assumption-dependent difference without declaring either model ground truth.
    for gap in [0.0005, 0.001, 0.002]:  #: Check the physical monotonic trend across a fourfold gap range.
        case = copy.deepcopy(request)  #: Isolate this gap variation from earlier turn changes.
        case['gap_m'] = gap  #: Specify each actual central subtractive gap in SI metres.
        actual = calculate(case)['values']['magnetizing_inductance_H']  #: Recompute native magnetising inductance for this physical gap.
        assert actual > 0 and (previous is None or actual < previous), (gap, actual)  #: Reject nonphysical or nonmonotonic fixed-model gap results.
        previous = actual  #: Advance the actual comparison value for the next larger gap.
        measurements['checks'].append({'check': 'gap_monotonicity', 'gap_m': gap, 'actual_H': actual})  #: Keep trend evidence distinct from an absolute external-accuracy claim.
    for temperature in [25, 100]:  #: Exercise native temperature-dependent DC wire resistance at two actual material conditions.
        case = copy.deepcopy(request)  #: Keep the gap and turns fixed while changing temperature.
        case['temperature_C'] = temperature  #: Apply the explicit copper-temperature setting.
        result = calculate(case)  #: Call the actual external wire model.
        rho = result['wire_material']['resistivity']  #: Use the same documented input material parameters, not a hidden fitted reference.
        diameter = result['wire']['conductingDiameter']['nominal']  #: Use the resolved conducting diameter rather than the insulated outer diameter.
        expected = rho['referenceValue'] * (1 + rho['temperatureCoefficient'] * (temperature - rho['referenceTemperature'])) / (math.pi * diameter ** 2 / 4)  #: Independently evaluate rho(T)/copper-area in ohms per metre.
        actual = result['values']['wire_dc_resistance_ohm_per_m']  #: Read the actual external result being checked.
        relative = abs(actual - expected) / expected  #: Quantify disagreement with the explicit DC physical model.
        assert relative < 1e-10, (temperature, actual, expected)  #: Fail if material-temperature or diameter-unit arithmetic disagrees.
        measurements['checks'].append({'check': 'dc_wire_arithmetic', 'temperature_C': temperature, 'actual_ohm_per_m': actual, 'expected_ohm_per_m': expected, 'relative_error': relative})  #: Retain reproducible scalar reference values.
    variant = copy.deepcopy(request)  #: Prepare a second actual CAD export with different removed material.
    variant['gap_m'] = 0.0005  #: Halve the central gap without changing the outer core dimensions.
    smaller = create_case(variant, output / 'core_half_gap')  #: Exercise native CAD geometry and verification on the second gap case.
    area = 0.01195 * 0.01495  #: Use the explicit nominal central-leg dimensions of the delivered E42 example in metres.
    delta = smaller['cad']['volume_m3'] - baseline['cad']['volume_m3']  #: Measure the actual STEP material-volume difference.
    expected_delta = area * 0.0005  #: Independently predict the removed central rectangular volume difference.
    assert abs(delta - expected_delta) < 1e-12, (delta, expected_delta)  #: Check machining volume changes rather than only static bounding boxes.
    measurements['checks'].append({'check': 'cad_gap_volume_change', 'actual_m3': delta, 'expected_m3': expected_delta, 'absolute_error_m3': abs(delta - expected_delta)})  #: Record real gap-machining evidence.
    for mode in ['2d', '3d']:  #: Preserve both existing dimensional workflows in the integration sidecar.
        project = json.loads((root / 'examples' / ('builder_saved_circuits_' + mode + '.json')).read_text())  #: Load the real saved six-winding fourteen-layer project.
        contract = winding_contract(project['builder'])  #: Produce the actual validated electrical hierarchy sidecar.
        (output / ('winding_contract_' + mode + '.json')).write_text(json.dumps(contract, indent=2, allow_nan=False) + '\n')  #: Save exact identity/layer data for adapter review.
        measurements['checks'].append({'check': 'winding_preservation', 'mode': mode, 'windings': len(contract['windings']), 'layers': len(contract['layers']), 'mas_mapping': contract['mas_mapping']})  #: Keep completed sidecar preservation separate from pending MAS conversion.
    measurements['passed'] = True  #: Set success only after every real native and contract check above passes.
    (output / 'benchmark.json').write_text(json.dumps(measurements, indent=2, allow_nan=False) + '\n')  #: Persist the complete measured evidence inside the selected result directory.
    return measurements  #: Enable a concise terminal summary without discarding exact results.


if __name__ == '__main__':  #: Avoid running native calculations when the module is imported for documentation.
    destination = sys.argv[1] if len(sys.argv) > 1 else pathlib.Path(__file__).resolve().parents[1] / 'sample_results/openmagnetics'  #: Supply a reproducible default output and optional caller override.
    print(json.dumps(run(destination), indent=2))  #: Print only actual completed benchmark results.
