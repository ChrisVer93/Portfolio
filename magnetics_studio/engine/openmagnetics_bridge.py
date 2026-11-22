"""Optional, pinned OpenMagnetics core-screening bridge; not a field solver."""
import copy  #: Protect caller-owned requests from mutations by external geometry code.
import hashlib  #: Tie exported files and requests to their exact byte content.
import importlib.metadata as metadata  #: Detect optional dependencies without importing their native libraries.
import json  #: Encode finite, deterministic provenance records.
import math  #: Validate finite physical inputs and construct RMS sine descriptors.
import pathlib  #: Keep output paths explicit and portable.
import shutil  #: Publish verified CAD files after all geometry checks succeed.
import tempfile  #: Stage native CAD output before replacing any existing deliverable.
from .workflow import expand, upgrade  #: Reuse the existing circuit/winding/layer validation contract.

PINS = {'PyOpenMagnetics': '1.7.35', 'OpenMagneticsVirtualBuilder': '0.6.12', 'cadquery': '2.6.1'}  #: Limit this initial bridge to versions actually exercised together.
FORMAT = 'magnetics-studio.openmagnetics-core/1'  #: Version our request envelope separately from upstream MAS.


def dependency_status():  #: Report package availability without installing or downloading anything.
    result = {}  #: Preserve one independent status per dependency.
    for package, expected in PINS.items():  #: Audit every runtime package required by the CAD proof.
        try:  #: Missing packages are an expected optional-backend condition.
            installed = metadata.version(package)  #: Read the local distribution version only.
        except metadata.PackageNotFoundError:  #: Keep the ordinary pure-Python application usable without this backend.
            installed = None  #: Represent absence explicitly instead of substituting a fake version.
        result[package] = {'expected': expected, 'installed': installed, 'supported': installed == expected}  #: Distinguish installed from qualified versions.
    return result  #: Return JSON-compatible diagnostics to the CLI and future desktop integration.


def winding_contract(specification):  #: Preserve the existing electrical hierarchy for future MAS mapping.
    _, saved, lookup = expand(upgrade(specification))  #: Validate turns, limbs, IDs and layer ordering with the existing builder.
    windings = []  #: Keep independent electrical windings separate from their circuit containers.
    for (cid, wid), (container, winding) in lookup.items():  #: Preserve the original stable circuit/winding identity pairs.
        windings.append({'id': cid + '__' + wid, 'circuit_id': cid, 'winding_id': wid, 'circuit_name': container['name'], 'name': winding['name'], 'turns': winding['turns'], 'source_definition': copy.deepcopy(winding)})  #: Retain complete excitation and wire metadata without reinterpreting it.
    if len({w['id'] for w in windings}) != len(windings):  #: Detect ambiguous composite IDs before exposing them to any backend.
        raise ValueError('Composite winding IDs collide; rename the circuit or winding IDs')  #: Preserve electrical independence instead of merging two windings silently.
    return {'format': 'magnetics-studio.winding-contract/1', 'windings': windings, 'layers': copy.deepcopy(saved['layout']), 'source_specification': saved, 'mas_mapping': 'pending', 'geometry_equivalence': 'not_established'}  #: This lossless sidecar is explicitly not a completed MAS or FEM-geometry conversion.


def finite(value, label, lower, upper):  #: Validate physical scalar inputs before entering native code.
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or not lower <= value <= upper:  #: Reject booleans, nonnumbers, infinities and values outside the bounded demonstration scope.
        raise ValueError(label + ' is outside the supported finite range')  #: Produce an actionable error instead of a native-library failure.
    return float(value)  #: Give native bindings a predictable scalar type.


def validate_request(request):  #: Define the narrow initial external-core calculation that has real verification.
    r = copy.deepcopy(request)  #: Keep native-library mutations out of the user's source request.
    if not isinstance(r, dict) or r.get('format') != FORMAT:  #: Refuse ambiguous request and upstream-schema interpretations.
        raise ValueError('Use request format ' + FORMAT)  #: Name the supported version explicitly.
    for key in ['shape', 'material', 'bobbin', 'wire']:  #: These names resolve through OpenMagnetics catalogues rather than our own approximations.
        if not isinstance(r.get(key), str) or not 1 <= len(r[key]) <= 200:  #: Bound identifiers passed to the external database.
            raise ValueError('Supply a bounded catalogue name for ' + key)  #: Explain which external identifier is missing.
    r['gap_m'] = finite(r.get('gap_m'), 'Centre gap (m)', 0.00001, 0.005)  #: Scope the proof to a positive central subtractive gap in SI metres.
    r['temperature_C'] = finite(r.get('temperature_C', 25), 'Temperature (C)', 0, 100)  #: Bound the material screening range without asserting arbitrary-temperature qualification.
    r['frequency_Hz'] = finite(r.get('frequency_Hz', 100000), 'Frequency (Hz)', 1, 1e6)  #: Carry the operating-point frequency without pretending this is an AC field solve.
    r['primary_current_rms_A'] = finite(r.get('primary_current_rms_A', 0.001), 'Primary RMS current (A)', 0.000001, 1)  #: Use an explicit small excitation for initial-permeability screening.
    r['turns'] = int(finite(r.get('turns'), 'Turns', 1, 1000))  #: Bound turn count for the two-winding screening example.
    if r['turns'] != request['turns']:  #: Do not silently truncate a fractional electrical turn count.
        raise ValueError('Turns must be an integer')  #: Reject unsupported fractional turns explicitly.
    if r.get('reluctance_model', 'CLASSIC') not in ['CLASSIC', 'ZHANG']:  #: Expose only the two actual external model selections tested here.
        raise ValueError('Choose CLASSIC or ZHANG reluctance model')  #: Avoid arbitrary unverified model names.
    r.setdefault('reluctance_model', 'CLASSIC')  #: Keep the selected gap model in the recorded physical input.
    return r  #: Return the complete normalised request used for reproducibility.


def calculate(request):  #: Delegate actual component calculations to the qualified OpenMagnetics package.
    r = validate_request(request)  #: Apply Python-side physical and schema guards before native execution.
    status = dependency_status()  #: Capture availability and qualification of optional packages.
    if not all(row['supported'] for row in status.values()):  #: Do not claim successful native CAD integration with missing or different versions.
        raise RuntimeError('Optional backend versions unavailable: ' + json.dumps(status))  #: Report exact installed/expected packages without installing them.
    import PyOpenMagnetics as om  #: Import the real external engine only when explicitly requested.
    om.load_databases({})  #: Initialise upstream catalogue data before any lookup or calculation.
    shape = om.find_core_shape_by_name(r['shape'])  #: Use upstream shape dimensions and catalogue resolution.
    if shape.get('family') != 'e':  #: Restrict CAD volume/unit checks to the verified rectangular E-core family.
        raise ValueError('This first bridge supports rectangular E cores only')  #: Keep unsupported shapes out of qualified output.
    core_input = {'functionalDescription': {'type': 'two-piece set', 'shape': r['shape'], 'material': r['material'], 'numberStacks': 1, 'gapping': [{'type': 'subtractive', 'length': r['gap_m']}]}}  #: Pass a native core description with a single central subtractive gap.
    core = om.calculate_core_data(core_input, False)  #: Let MKF compute actual effective parameters and CAD piece descriptions.
    coil = {'bobbin': r['bobbin'], 'functionalDescription': [{'name': 'screening__primary', 'isolationSide': 'primary', 'numberTurns': r['turns'], 'numberParallels': 1, 'wire': r['wire']}, {'name': 'screening__secondary', 'isolationSide': 'secondary', 'numberTurns': r['turns'], 'numberParallels': 1, 'wire': r['wire']}]}  #: Define separate equal-turn electrical windings; this does not generate their CAD or leakage model.
    excitations = []  #: Construct two explicit operating-point excitations with known RMS convention.
    for current in [r['primary_current_rms_A'], 0.0]:  #: Use a primary screening current and open-circuit secondary current.
        peak = math.sqrt(2) * current  #: Convert sinusoidal RMS amperes to waveform peak amperes exactly once.
        excitations.append({'frequency': r['frequency_Hz'], 'current': {'processed': {'label': 'sinusoidal', 'rms': current, 'peak': peak, 'peakToPeak': 2 * peak, 'offset': 0.0, 'dutyCycle': 0.5, 'effectiveFrequency': r['frequency_Hz']}}})  #: Supply the upstream processed signal descriptor without inventing voltage or switching waveforms.
    op = {'conditions': {'ambientTemperature': r['temperature_C']}, 'excitationsPerWinding': excitations}  #: Set actual material temperature and winding excitation inputs.
    inductance = om.calculate_inductance_from_number_turns_and_gapping(core, coil, op, {'reluctance': r['reluctance_model']})  #: Compute real model-based magnetising inductance in MKF rather than substituting our own formula.
    wire = om.find_wire_by_name(r['wire'])  #: Resolve the selected actual wire description.
    resistance = om.calculate_dc_resistance_per_meter(wire, r['temperature_C'])  #: Compute upstream DC resistance per metre in ohms per metre.
    material = om.find_wire_material_by_name(wire['material'])  #: Retain the resistivity data needed for independent arithmetic checks.
    values = {'magnetizing_inductance_H': inductance, 'wire_dc_resistance_ohm_per_m': resistance}  #: Keep the two supported calculated outputs dimensionally explicit.
    if any(not math.isfinite(v) or v <= 0 for v in values.values()):  #: Reject invalid native numerical results even when the API returns normally.
        raise RuntimeError('OpenMagnetics returned invalid physical outputs')  #: Prevent publishing nonphysical screening results.
    return {'kind': 'openmagnetics_core_screening', 'backend': 'OpenMagnetics MKF through PyOpenMagnetics', 'method': 'reluctance model and DC wire model; not FEM', 'request': r, 'dependencies': status, 'core': core, 'coil': coil, 'operating_point': op, 'wire': wire, 'wire_material': material, 'values': values, 'limitations': ['Core CAD only; winding/bobbin solids are not generated', 'No leakage, AC loss, thermal solve or field/circuit transient is computed', 'No FEM mesh or error-driven refinement is performed', 'No geometry equivalence with an existing Studio FEM case is established', 'Not independently validated against Maxwell or measurements']}  #: Preserve model inputs, results and explicit applicability limits together.


def create_case(request, output_directory):  #: Produce checked real CAD and numerical output from the optional backend.
    result = calculate(request)  #: Complete numerical calculation before creating a publishable result.
    import cadquery as cq  #: Load the qualified CAD kernel only in this explicit external-backend operation.
    from OpenMagneticsVirtualBuilder.builder import Builder  #: Reuse MVB's actual core generator.
    geometry = copy.deepcopy(result['core']['geometricalDescription'])  #: Preserve upstream output for audit while translating only the CAD input copy.
    for part in geometry:  #: Adapt the actual spelling mismatch between the pinned packages.
        if part.get('type') != 'halfSet':  #: Refuse unverified spacer/toroid/unknown piece semantics in this first bridge.
            raise ValueError('Unsupported native core piece type')  #: Avoid MVB silently omitting an unrecognised part.
        part['type'] = 'half set'  #: Map MKF's camel-case enum to the pinned MVB enum expected by get_core.
    destination = pathlib.Path(output_directory).resolve()  #: Treat the output as a caller-chosen directory rather than a core-name-derived path.
    destination.mkdir(parents=True, exist_ok=True)  #: Prepare the destination without overwriting its existing case files.
    with tempfile.TemporaryDirectory(prefix='om_core_', dir=destination) as temporary:  #: Stage native exports separately until geometry and units pass.
        files = Builder('CadQuery').get_core('screening', geometry, output_path=temporary, save_files=False, export_files=True)  #: Run real MVB/CadQuery generation with a fixed safe filename.
        if not files or len(files) != 2 or any(not f or not pathlib.Path(f).is_file() for f in files):  #: MVB may return null paths after swallowing a native exception.
            raise RuntimeError('MVB failed to export both core CAD files')  #: Preserve previous outputs rather than claiming an incomplete export.
        solid = cq.importers.importStep(str(files[0])).val()  #: Reimport the actual STEP file to check exported geometry rather than an in-memory preview.
        solids = solid.Solids()  #: Count actual volumetric solids in the exchange file.
        if len(solids) != 2 or not solid.isValid():  #: Reject the empty-success failure and invalid topology.
            raise RuntimeError('CAD must contain two valid E-core solids')  #: Do not label a returned filename as successful CAD.
        bbox = solid.BoundingBox()  #: Measure the exported bounding box in STEP millimetres as read by CadQuery.
        measured = [bbox.xlen / 1000, bbox.ylen / 1000, bbox.zlen / 1000]  #: Convert exchange-file millimetres back to the common SI metre convention.
        dimensions = result['core']['geometricalDescription'][0]['shape']['dimensions']  #: Use the exact catalogue dimensions selected by MKF.
        nominal = {}  #: Resolve the same midpoint dimensions used by pinned MVB.
        for key in ['A', 'B', 'C', 'D', 'E', 'F']:  #: The supported E-core outline has six dimensions in metres.
            v = dimensions[key]  #: Read the catalogue tolerance record for this dimension.
            nominal[key] = v['nominal'] if v.get('nominal') is not None else round((v['minimum'] + v['maximum']) / 2, 6)  #: Match MVB's bounded midpoint convention without altering the catalogue data.
        expected_bbox = [nominal['A'], nominal['C'], 2 * nominal['B'] + 5e-6]  #: Pinned MVB inserts a documented-in-provenance 5 micrometre mating gap.
        expected_volume = 2 * nominal['C'] * (nominal['A'] * nominal['B'] - (nominal['E'] - nominal['F']) * nominal['D']) - nominal['F'] * nominal['C'] * result['request']['gap_m']  #: Independently check the rectangular E outline and removed central-gap material in cubic metres.
        volume = solid.Volume() / 1e9  #: Convert STEP cubic millimetres to cubic metres exactly once.
        central_faces = []  #: Measure the actual central gap faces rather than inferring their placement from total volume.
        for face in solid.Faces():  #: Inspect the real reimported STEP topology.
            centre = face.Center()  #: Locate each face in the exported millimetre coordinate system.
            if face.geomType() == 'PLANE' and abs(centre.x) < 1e-7 and abs(centre.y) < 1e-7 and abs(face.Area() / 1e6 - nominal['F'] * nominal['C']) < 1e-10 and abs(face.normalAt().z) > 1 - 1e-10:  #: Identify the two central-leg end faces by position, area and axial normal.
                central_faces.append(centre.z / 1000)  #: Record their actual axial positions in metres.
        if len(central_faces) != 2:  #: Reject a shape that does not expose the expected central E-core gap topology.
            raise RuntimeError('Cannot verify the two central gap faces')  #: Keep unsupported or changed upstream geometry out of the verified path.
        central_gap = max(central_faces) - min(central_faces)  #: Measure actual separation of the two central-leg faces.
        if any(abs(a - b) > 1e-8 for a, b in zip(measured, expected_bbox)) or abs(volume - expected_volume) > 1e-6 * expected_volume:  #: Reject axis/scale/gap mistakes using independent dimensional and volume bounds.
            raise RuntimeError('CAD dimension or material-volume verification failed')  #: Fail closed if the packages are incompatible despite matching version strings.
        if abs(central_gap - result['request']['gap_m'] - 5e-6) > 1e-8:  #: Include MVB's additional mating gap when checking actual central face separation.
            raise RuntimeError('CAD central gap placement verification failed')  #: Detect correct-volume machining placed on the wrong core faces.
        result['cad'] = {'scope': 'core only', 'solid_count': len(solids), 'valid': True, 'step_length_unit': 'mm', 'bbox_m': measured, 'expected_bbox_m': expected_bbox, 'volume_m3': volume, 'expected_volume_m3': expected_volume, 'mvb_mating_gap_m': 5e-6, 'expected_central_face_separation_m': result['request']['gap_m'] + 5e-6, 'measured_central_face_separation_m': central_gap, 'type_translation': 'halfSet -> half set'}  #: Preserve the measured extra gap so future field comparisons cannot silently assume identical geometry.
        result['files'] = {}  #: Attach exact CAD provenance to the result.
        for file in files:  #: Check each actual export before copying it into the stable output location.
            p = pathlib.Path(file)  #: Convert native path strings into filesystem paths.
            if p.stat().st_size < 100:  #: Reject trivially empty STEP/STL exports.
                raise RuntimeError('CAD export is empty')  #: Never replace a previous case with an empty geometry file.
            result['files'][p.name] = {'bytes': p.stat().st_size, 'sha256': hashlib.sha256(p.read_bytes()).hexdigest()}  #: Tie the numerical report to the exact exported CAD bytes.
        encoded = json.dumps(result, indent=2, allow_nan=False)  #: Validate finite serialisation before publishing CAD output.
        for file in files:  #: Only publish files after the full calculation and geometry verification succeed.
            shutil.copy2(file, destination / pathlib.Path(file).name)  #: Replace this case's CAD files while preserving unrelated output files.
        (destination / 'result.json').write_text(encoded + '\n', encoding='utf-8')  #: Save exact calculation inputs, outputs, verification and provenance.
    return result  #: Allow the CLI and reproducible benchmark to inspect actual checked values.
