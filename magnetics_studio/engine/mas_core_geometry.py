"""P002C1: editable MAS E-shape/gap subdocuments, not a complete MAS assembly."""
import copy  #: Preserve the original winding workflow and material declarations on export and import.
import hashlib  #: Tie immutable continuation metadata to the exact finite source recipe.
import math  #: Check symmetric shape constraints and supported gap coordinates numerically.
from .builder import build  #: Rebuild through the existing real 2D/3D geometry, packing and material checks.
from .mas_exchange import canonical, MAS_COMMIT  #: Reuse deterministic finite JSON and the already pinned licensed MAS schema revision.
from .project import number  #: Reject booleans, nonfinite values and unsupported dimensional ranges.
from .workflow import upgrade  #: Preserve independent windings and ordered layers from either builder recipe version.

FORMAT = 'magnetics-studio.mas-core-geometry/1'  #: Keep this editable subdocument envelope distinct from both full MAS and the prior coil exchange.


def millimetres(value):  #: Decode SI geometry into the builder's explicit picometre data resolution.
    return round(number(value, 'MAS dimension (m)', 1e-9, 10) * 1000, 9)  #: Import positive finite metre dimensions once; rounding is data resolution, not manufacturing accuracy.


def export_core_geometry(specification):  #: Export supported rectangular EE dimensions and every actual distributed gap.
    saved = upgrade(specification)  #: Resolve the existing winding hierarchy before lightweight geometric representability checks.
    c = saved['core']  #: Read builder dimensions in millimetres explicitly.
    if saved['family'] != 'e_core' or len(c['limbs_mm']) != 3 or len(c['windows_mm']) != 2: raise ValueError('MAS core geometry currently requires rectangular 3-limb e_core')  #: Never relabel rounded, planar or toroidal families as an exact E shape.
    left, centre, right = c['limbs_mm']; w0, w1 = c['windows_mm']  #: Keep lateral/central widths distinct from window widths.
    if not math.isclose(left, right, rel_tol=0, abs_tol=1e-10) or not math.isclose(w0, w1, rel_tol=0, abs_tol=1e-10) or not math.isclose(c['top_yoke_mm'], c['bottom_yoke_mm'], rel_tol=0, abs_tol=1e-10): raise ValueError('MAS E dimensions require equal lateral limbs, windows and top/bottom yokes')  #: Reject asymmetry rather than averaging a user's dimensions.
    values = [left, centre, right, w0, w1, c['window_height_mm'], c['top_yoke_mm'], c['bottom_yoke_mm'], c['depth_mm']] + [g['length_mm'] for g in c.get('gaps', []) if g['count']]  #: Include every mapped dimension and nonempty cut length in the exchange-resolution check.
    if any(abs(v - round(v, 9)) > 1e-12 for v in values): raise ValueError('MAS core geometry uses millimetre inputs with at most nine decimal places')  #: Avoid silently quantising a source recipe beyond the supported data resolution.
    built = build(saved); saved = built['project']['builder']  #: Finish actual geometry/material/winding-fit validation and retain its canonical complete workflow.
    A, D, C = left + centre + right + w0 + w1, c['window_height_mm'] / 2, c['depth_mm']  #: MAS E: A is total width, D half-window axial height, C stack depth.
    dimensions = dict(A=A, B=D + c['top_yoke_mm'], C=C, D=D, E=w0 + centre + w1, F=centre)  #: Map the six actual E parameters without catalogue lookup or a mating-gap offset.
    shape = {'type': 'custom', 'family': 'e', 'name': str(saved.get('part_number') or 'Studio custom EE'), 'dimensions': {k: {'nominal': number(v / 1000, 'MAS E dimension (m)', 1e-9, 10)} for k, v in dimensions.items()}}  #: Produce an actual MAS shape subdocument with nominal SI metres only.
    xs = [-(A - left) / 2, 0, (A - right) / 2]  #: Locate all three column centres relative to the central column's centre.
    gaps = []  #: Retain all distributed cuts rather than replacing them by one equivalent reluctance gap.
    for row in sorted(c.get('gaps', []), key=lambda g: g['limb']):  #: Give native gap arrays a stable geometric ordering independent of source table row order.
        for j in range(row['count']):  #: Preserve every real cut in each limb.
            y = -D + (j + 1) * 2 * D / (row['count'] + 1)  #: Match the existing builder's equally distributed axial gap centres.
            gaps.append({'type': 'subtractive', 'length': row['length_mm'] / 1000, 'coordinates': [xs[row['limb']] / 1000, y / 1000, 0], 'shape': 'rectangular'})  #: Use the MAS XY front-plane convention with Z through stack depth, not solver-3D XYZ.
    pad = saved.get('air_padding_mm', 25)  #: Retain the actual builder offset instead of inferring it from a rendered model.
    origin = [pad + A / 2, pad + c['bottom_yoke_mm'] + D, C / 2] if saved['mode'] == '2d' else [pad + A / 2, pad + C / 2, pad + c['bottom_yoke_mm'] + D]  #: Locate the assembly-centre origin in each solver's physical coordinate order.
    return {'format': FORMAT, 'schema_basis': MAS_COMMIT, 'source_specification': copy.deepcopy(saved), 'source_sha256': hashlib.sha256(canonical(saved)).hexdigest(), 'mas_shape': shape, 'mas_gaps': gaps, 'material_binding': {'mas_name_reference': saved['material'].get('name', 'Custom ferrite'), 'studio_characteristics': copy.deepcopy(saved['material']), 'catalogue_resolution': 'not performed; no saturation/loss data invented'}, 'coordinates': {'unit': 'm', 'solver_origin_m': [v / 1000 for v in origin], 'MAS_axes_from_solver': [0, 1, 2] if saved['mode'] == '2d' else [0, 2, 1], 'scope': 'geometry positions only; no vector-field rotation or manufacturing-piece assignment'}, 'limitations': ['Native MAS shape/gap subdocuments only; no complete core assembly type or geometrical piece list inferred', 'Distributed cuts preserve field geometry; they do not imply a two-piece manufacturing assembly', 'Only rectangular symmetric EE; no rounded or arbitrary CAD import', 'Material name remains unresolved; complete original material and winding workflow retained', 'No new MKF calculation, MVB production qualification, PDE, native nonlinear/AC or external Maxwell validation']}  #: Expose the exact mapping and every unestablished assembly/material/solver assumption in the downloadable packet.


def apply_core_geometry(packet, mode=None):  #: Deliberately apply supported native dimension/gap edits through the real builders.
    if not isinstance(packet, dict) or packet.get('format') != FORMAT: raise ValueError('Use a Studio core geometry packet with format ' + FORMAT)  #: Refuse arbitrary MAS files as if they contained a complete continuation recipe.
    original = export_core_geometry(packet['source_specification'])  #: Revalidate every retained material, winding and original geometry field.
    immutable = {k: v for k, v in packet.items() if k not in ('mas_shape', 'mas_gaps')}  #: Permit edits only to the explicitly supported native projections.
    if canonical(immutable) != canonical({k: v for k, v in original.items() if k not in ('mas_shape', 'mas_gaps')}): raise ValueError('Core exchange continuation metadata changed or is stale')  #: Do not silently ignore changed material bindings, source hashes, transforms or unsupported keys.
    shape = packet['mas_shape']  #: Read the caller's actual edited native shape.
    if not isinstance(shape, dict) or canonical({k: v for k, v in shape.items() if k != 'dimensions'}) != canonical({k: v for k, v in original['mas_shape'].items() if k != 'dimensions'}): raise ValueError('Edit E dimensions only; shape identity/type/family must remain unchanged')  #: Avoid reinterpreting an unsupported family or source identity.
    dims = shape.get('dimensions')  #: Decode a closed six-parameter nominal-only contract.
    if not isinstance(dims, dict) or set(dims) != set('ABCDEF') or any(not isinstance(v, dict) or set(v) != {'nominal'} for v in dims.values()): raise ValueError('Supply exactly nominal SI dimensions A, B, C, D, E and F')  #: Do not guess tolerance midpoints or ignore extra dimensional keys.
    A, B, C, D, E, F = [millimetres(dims[k]['nominal']) for k in 'ABCDEF']  #: Convert edited dimensions once into the existing builder's millimetre convention.
    if not A > E > F > 0 or not B > D > 0: raise ValueError('E dimensions require A > E > F > 0 and B > D > 0')  #: Keep all lateral limbs, windows and yokes physically positive.
    lateral, window = round((A - E) / 2, 9), round((E - F) / 2, 9)  #: Reconstruct symmetric lateral widths and window openings from the actual MAS values.
    gaps = packet['mas_gaps']  #: Preserve explicit distributed-gap coordinates instead of a total effective length.
    if not isinstance(gaps, list) or len(gaps) > 36: raise ValueError('Use at most 36 explicit MAS gaps')  #: Match the three-limb builder's per-limb count budget before grouping.
    groups = {}  #: Group only geometrically matched column centres, never electrical winding names.
    centres = [-(A - lateral) / 2, 0, (A - lateral) / 2]  #: Reconstruct all lateral/central column coordinates from the edited shape.
    for gap in gaps:  #: Validate every native cut before changing the source recipe.
        if not isinstance(gap, dict) or set(gap) != {'type', 'length', 'coordinates', 'shape'} or gap['type'] != 'subtractive' or gap['shape'] != 'rectangular': raise ValueError('Only explicit rectangular subtractive gaps are supported')  #: Do not silently turn residual/additive gaps into removed material.
        xyz = gap['coordinates']  #: MAS geometry positions are three SI coordinates in the declared front-plane convention.
        if not isinstance(xyz, list) or len(xyz) != 3: raise ValueError('Each gap needs three SI coordinates')  #: Reject ambiguous 2D/3D coordinate interpretations.
        for value in xyz: number(value, 'Gap coordinate (m)', -10, 10)  #: Reject booleans/nonfinite coordinates before any geometric comparisons.
        matches = [i for i, x in enumerate(centres) if math.isclose(xyz[0] * 1000, x, rel_tol=0, abs_tol=1e-9)]  #: A native gap must lie on one exact reconstructed column centre within the declared data tolerance.
        if len(matches) != 1 or abs(xyz[2]) > 1e-12: raise ValueError('Gap must lie on a supported column centre with MAS Z=0')  #: Refuse off-centre/through-depth machining that the existing builder cannot represent.
        groups.setdefault(matches[0], []).append((xyz[1] * 1000, millimetres(gap['length'])))  #: Keep each actual axial coordinate and length for representability checks.
    rows = []  #: Rebuild only gap rows demonstrated equivalent to the existing equally distributed builder.
    for limb, entries in sorted(groups.items()):  #: Keep geometric ordering stable regardless of native gap-array order.
        entries.sort()  #: Compare axial cuts in physical order without discarding any cut.
        n, length = len(entries), entries[0][1]  #: The builder supports one common cut length for each limb.
        if n > 12 or any(abs(g - length) > 1e-9 or abs(y - (-D + (j + 1) * 2 * D / (n + 1))) > 1e-9 for j, (y, g) in enumerate(entries)): raise ValueError('Gap coordinates/lengths must match equal spacing and equal length per limb; no automatic redistribution')  #: Reject duplicates, irregular cuts and stale coordinates instead of silently moving them.
        rows.append({'limb': limb, 'count': n, 'length_mm': length})  #: Preserve actual count and physical gap length in the existing builder schema.
    source = copy.deepcopy(original['source_specification'])  #: Retain all independent windings, layers, materials and excitation conventions exactly.
    c = source['core']  #: Update only the declared supported core dimensions and gapping.
    c.update(limbs_mm=[lateral, F, lateral], windows_mm=[window, window], window_height_mm=2 * D, top_yoke_mm=round(B - D, 9), bottom_yoke_mm=round(B - D, 9), depth_mm=C, gaps=rows)  #: Decode the edited native shape rather than reusing a stale saved core.
    if mode is not None:  #: Permit only an explicit dimensional adapter selection.
        if mode not in ('2d', '3d'): raise ValueError('Choose 2d or 3d for core geometry apply')  #: Keep the mode vocabulary closed.
        source['mode'] = mode  #: Existing nonlinear/turn/source restrictions remain enforced by build.
    return build(source)  #: Finish real winding-fit/material/source checks before returning an accepted builder design.
