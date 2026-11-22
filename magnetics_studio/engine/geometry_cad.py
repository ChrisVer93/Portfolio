"""Checked rectangular 3D and faceted planar field CAD, not finite-copper physics."""
import base64  #: Transport only checked fixed-name archive bytes from the isolated worker.
import hashlib  #: Tie exported geometry and source project to exact bytes.
import importlib.metadata as metadata  #: Check this CAD adapter independently of the older OpenMagnetics pins.
import json  #: Store finite source/provenance data beside the STEP files.
import math  #: Sum independent analytical volumes and validate measured geometry.
from pathlib import Path  #: Keep generated filenames within the caller's staging directory.
import zipfile  #: Offer all checked STEP parts and their manifest as one portable download.
from .connections import series_key  #: Preserve the existing independent electrical port identities.
from .project import validate  #: Reuse source validation without changing field/circuit semantics.
from .cad_planar import planar_bodies  #: Extend actual 2D field polygons without changing the rectangular spatial adapter.

CAD_PINS = {'cadquery': '2.7.0', 'cadquery-ocp': '7.8.1.1.post1'}  #: Qualify the actual installed Linux CAD combination for this separate adapter only.
AXES = ('x', 'y', 'z')  #: Use the solver's physical coordinate order without an implicit builder rotation.


def subtract_box(box, mask):  #: Partition a rectangular material region outside one later-priority region.
    cut = {axis + end: (max if end == '0' else min)(box[axis + end], mask[axis + end]) for axis in AXES for end in ('0', '1')}  #: Intersect all three axis intervals.
    if any(cut[a + '0'] >= cut[a + '1'] for a in AXES):  #: Touching boundaries do not remove material volume.
        return [dict(box)]  #: Preserve a detached original box when there is no positive-volume overlap.
    remainder, middle = [], dict(box)  #: Peel at most six disjoint slabs around the intersection.
    for axis in AXES:  #: Clip successive dimensions so slabs never overlap each other.
        for end, opposite in [('0', '1'), ('1', '0')]:  #: Add the low and high side of this axis.
            slab = dict(middle)  #: Keep coordinates from the already clipped preceding axes.
            slab[axis + opposite] = cut[axis + end]  #: Bound the slab by the corresponding intersection face.
            if slab[axis + '1'] > slab[axis + '0']: remainder.append(slab)  #: Ignore empty slabs while keeping every positive-volume piece.
        middle.update({axis + '0': cut[axis + '0'], axis + '1': cut[axis + '1']})  #: Restrict the unprocessed middle to the intersection along this axis.
    return remainder  #: The omitted final middle is exactly the volume overwritten by the later region.


def volume(box):  #: Compute an SI rectangular volume independently of the native CAD kernel.
    return math.prod(box[a + '1'] - box[a + '0'] for a in AXES)  #: Metre side lengths yield cubic metres.


def bounds(boxes):  #: Compute the enclosing SI bounds of a nonempty list of primitives.
    return {a + e: (min if e == '0' else max)(b[a + e] for b in boxes) for a in AXES for e in ('0', '1')}  #: Preserve all six signed-coordinate bounds.


def geometry_plan(project, include_envelopes=True):  #: Resolve supported spatial boxes and planar polygon prisms without importing CAD.
    p = validate(project)  #: Work on the validated detached project rather than mutating a user model.
    if type(include_envelopes) is not bool:  #: Avoid interpreting strings such as false as an enabled display geometry request.
        raise ValueError('include_envelopes must be boolean')  #: Keep the only current CAD option explicit.
    if p['mode'] == '3d' and (len(p['regions']) > 60 or len(p['windings']) > 32):  #: Preserve existing spatial resource limits independently of the planar extension.
        raise ValueError('Spatial CAD pilot supports at most 60 regions and 32 winding sections')  #: Keep a geometry budget separate from field-solver capacity.
    parts = []  #: Retain material priority as disjoint rectangular pieces.
    for index, region in enumerate(p['regions'] if p['mode'] == '3d' else []):  #: Keep the original spatial box partition; planar geometry uses the exact polygon path below.
        box = {a + e: region[a + e] if a != 'z' or p['mode'] == '3d' else (0 if e == '0' else p['domain']['depth']) for a in AXES for e in ('0', '1')}  #: Extrude planar XY geometry by model depth; spatial geometry keeps its actual XYZ axes.
        parts = [(old_index, piece) for old_index, old_box in parts for piece in subtract_box(old_box, box)]  #: Remove all portions overwritten by this later region, including explicit air cuts.
        if region['material'] != 'air': parts.append((index, box))  #: Air remains a void in component CAD rather than an opaque surrounding solid.
        if len(parts) > 1000:  #: Prevent pathological priority partitions from expanding without a bound.
            raise ValueError('CAD partition exceeds 1000 boxes; simplify overlapping regions')  #: Refuse a capacity overrun before native exports or publication.
    bodies = []  #: Keep each original region/source identity separate in the neutral exchange bundle.
    for index, region in enumerate(p['regions']):  #: Preserve original region order even when it has several disjoint pieces.
        boxes = [box for owner, box in parts if owner == index]  #: Collect only material that survives all later-priority masks.
        if boxes: bodies.append({'id': 'region_' + str(index), 'kind': 'field_region', 'source_id': region['id'], 'material': region['material'], 'boxes_m': boxes, 'expected_volume_m3': math.fsum(volume(b) for b in boxes)})  #: Retain exact material/region labels without fusing independent assignments.
    planar = {}  #: Spatial source boxes do not acquire a planar geometric tolerance or extrusion claim.
    if p['mode'] == '2d': bodies, planar = planar_bodies(p)  #: Partition actual convex regions, preserving original polygon facets, holes and signed planar sources.
    if p['mode'] == '3d':  #: Spatial impressed windings are ideal sheets on the four lateral faces of their Tz enclosure.
        for index, winding in enumerate(p['windings']):  #: Keep every physical layer/section, even if several belong to one series winding.
            box = dict(winding['window'])  #: Use the actual field source window, not the decorative winding envelope.
            dx, dy, dz = [box[a + '1'] - box[a + '0'] for a in AXES]  #: Measure SI source dimensions and sheet height.
            common = {'source_id': winding['id'], 'series_group': series_key(winding), 'turns': winding['turns'], 'current_A': winding['current']}  #: Keep electrical identity, turns and signed snapshot current attached to the CAD source.
            bodies.append({'id': 'source_' + str(index), 'kind': 'ideal_source_sheet', **common, 'boxes_m': [box], 'expected_area_m2': 2 * dz * (dx + dy), 'expected_volume_m3': 0, 'unit_surface_current_A_per_m_per_A': winding['turns'] / dz})  #: Export only active lateral sheet faces; top/bottom normals create no curl(Tz ez) source.
            if include_envelopes and 'display_build_m' in winding:  #: Make optional display solids only from an explicit stored thickness.
                width = winding['display_build_m']  #: Never invent a conductor thickness from the source-window size.
                if isinstance(width, bool) or not isinstance(width, (int, float)) or not math.isfinite(width) or not 0 < width < min(dx, dy):  #: Require a valid positive ring thickness with an open inner window.
                    raise ValueError('Display winding build must be positive and smaller than both source-window spans')  #: Do not silently apply the old viewer's thickness clamp.
                outer, inner = dict(box), dict(box)  #: Centre the display-only envelope on the same ideal current sheet.
                for axis in ('x', 'y'):  #: Expand/shrink only radial cross-section axes, never the axial sheet height.
                    outer.update({axis + '0': box[axis + '0'] - width / 2, axis + '1': box[axis + '1'] + width / 2})  #: Include the declared half build outside the mean source surface.
                    inner.update({axis + '0': box[axis + '0'] + width / 2, axis + '1': box[axis + '1'] - width / 2})  #: Include the declared half build inside the mean source surface.
                ring = subtract_box(outer, inner)  #: Form four nonoverlapping rectangular ring bars with no cap across the bore.
                bodies.append({'id': 'envelope_' + str(index), 'kind': 'display_envelope_not_solved_copper', **common, 'boxes_m': ring, 'expected_volume_m3': 2 * width * (dx + dy) * dz})  #: Keep decorative volume out of the field-material volume accounting.
    if not bodies:  #: An all-air model has no component geometry to export.
        raise ValueError('CAD requires at least one non-air region or spatial source sheet')  #: Avoid an apparently successful empty STEP bundle.
    return {'format': 'magnetics-studio.field-cad/' + ('2' if p['mode'] == '2d' else '1'), 'project': p, 'bodies': bodies, 'planar_geometry': planar, 'coordinate_system': 'solver XYZ in m; 2D XY extruded from z=0 to model depth; no hidden axis rotation', 'limitations': ['Spatial rectangular regions or planar convex polygon prisms; air omitted; last-region-wins material partition preserved', 'Planar round wires and annular cores retain their original straight facets, not exact circular or general curved 3D geometry', 'Planar conductor-shaped prisms retain prescribed axial sources, not closed 3D turns, terminals or eddy-current physics', 'Ideal spatial source sheets are zero-thickness current sources, not finite conductive turns or terminals', 'Envelope solids are display-only and may overlap materials or each other; not manufacturing/clearance certification', 'Insulation solids are existing field regions, not a reconstructed complete bobbin', 'No matched MAS core/layer/turn conversion or new mesh, field, loss or circuit solve', 'No MVB mating offset added; actual source geometry and gaps are retained']}  #: Version the new planar prism contract explicitly while retaining the existing spatial format and all physical scope limits.


def export_cad(project, output_directory, include_envelopes=True):  #: Generate and verify real STEP exchange files in an isolated worker.
    plan = geometry_plan(project, include_envelopes)  #: Finish supported-geometry and resource checks before importing native CAD.
    versions = {name: metadata.version(name) for name in CAD_PINS}  #: Record the native combination actually used for exchange.
    if versions != CAD_PINS: raise RuntimeError('Use the qualified field-CAD versions: ' + json.dumps(CAD_PINS))  #: Do not qualify arbitrary versions by availability alone.
    import cadquery as cq  #: Import the established OpenCASCADE-based CAD API only for this explicit operation.
    destination = Path(output_directory)  #: The worker supplies a private staging directory, never a browser-supplied path.
    destination.mkdir(parents=True, exist_ok=True)  #: Prepare private staged export files.
    def solid(box):  #: Construct a native solid with explicit SI-to-STEP conversion.
        return cq.Solid.makeBox(*[(box[a + '1'] - box[a + '0']) * 1000 for a in AXES], pnt=cq.Vector(*[box[a + '0'] * 1000 for a in AXES]))  #: CadQuery's STEP dimensions are millimetres; convert each axis once.
    def prism(piece):  #: Extrude the exact surviving straight-edged planar boundary.
        wire = cq.Wire.makePolygon([cq.Vector(x * 1000, y * 1000, piece['z0'] * 1000) for x, y in piece['polygon']], close=True)  #: Keep every facet and actual XY coordinate; never replace a round-wire polygon with a box or circle.
        return cq.Solid.extrudeLinear(wire, [], cq.Vector(0, 0, (piece['z1'] - piece['z0']) * 1000))  #: Use the established CAD kernel's linear extrusion along the invariant physical Z direction.
    for body in plan['bodies']:  #: Independently verify every labelled component offered for download.
        shapes = [prism(piece) for piece in body['prisms_m']] if 'prisms_m' in body else [solid(box) for box in body['boxes_m']]  #: Build exact polygon prisms or unchanged spatial boxes according to the explicit plan representation.
        is_sheet = body['kind'] == 'ideal_source_sheet'  #: Keep zero-thickness mathematical sources separate from volume materials.
        if is_sheet: shapes = [face for face in shapes[0].Faces() if abs(face.normalAt().z) < .5]  #: Retain four lateral faces and omit the two inactive horizontal caps.
        shape = cq.Compound.makeCompound(shapes)  #: Preserve separate partition pieces rather than silently fusing source/material labels.
        path = destination / (body['id'] + '.step')  #: Use fixed generated names independent of untrusted user IDs.
        cq.exporters.export(shape, str(path))  #: Write an actual STEP BREP exchange file.
        data = path.read_bytes()  #: Inspect the exact serialized bytes that will be downloaded.
        if b'SI_UNIT(.MILLI.,.METRE.)' not in data: raise RuntimeError('STEP does not declare millimetre length units')  #: Check the actual file's unit declaration, not just the in-memory shape.
        imported = cq.importers.importStep(str(path)).val()  #: Reimport the exchange file before trusting the CAD output.
        if not imported.isValid(): raise RuntimeError('STEP reimport has invalid topology: ' + body['id'])  #: Reject a kernel/file failure instead of presenting a returned filename as valid CAD.
        expected = body['expected_bounds_m'] if 'prisms_m' in body else bounds(body['boxes_m'])  #: Use surviving polygon coordinates or unchanged spatial box bounds for independent exchange checks.
        bbox = imported.BoundingBox()  #: Measure the actual reimported BREP in millimetres.
        measured = {a + e: getattr(bbox, a + ('min' if e == '0' else 'max')) / 1000 for a in AXES for e in ('0', '1')}  #: Convert measured bounds back to source SI coordinates.
        if any(abs(measured[key] - value) > 1e-9 for key, value in expected.items()): raise RuntimeError('STEP coordinate/bounds mismatch: ' + body['id'])  #: Detect scaling, axis, placement or lost-part errors.
        measured_volume = 0.0 if is_sheet else imported.Volume() / 1e9  #: An open surface's kernel mass property is not a physical solid volume.
        if len(imported.Solids()) != (0 if is_sheet else len(body.get('prisms_m', body.get('boxes_m', [])))): raise RuntimeError('STEP solid-count mismatch: ' + body['id'])  #: Check every surviving prism or box and keep mathematical source sheets distinct from solids.
        if abs(measured_volume - body['expected_volume_m3']) > max(1e-18, body['expected_volume_m3'] * 1e-7): raise RuntimeError('STEP volume mismatch: ' + body['id'])  #: Check material/envelope volume against analytical SI measures.
        area = imported.Area() / 1e6  #: Convert actual surface area to square metres.
        if 'prisms_m' in body and abs(area - body['expected_area_m2']) > max(1e-16, body['expected_area_m2'] * 1e-7): raise RuntimeError('STEP polygon surface-area mismatch: ' + body['id'])  #: Check all end and lateral facets, including exposed faces between unfused partition fragments.
        if is_sheet and (len(imported.Faces()) != 4 or abs(area - body['expected_area_m2']) > body['expected_area_m2'] * 1e-7): raise RuntimeError('STEP active source-sheet area mismatch')  #: Detect accidentally exported source caps or missing return faces.
        body.update(file=path.name, bytes=len(data), sha256=hashlib.sha256(data).hexdigest(), bounds_m=measured, measured_volume_m3=measured_volume, measured_area_m2=area, valid=True)  #: Bind every verified measurement to exact exchange bytes.
    plan.update(backend_versions=versions, step_length_unit='mm', project_sha256=hashlib.sha256(json.dumps(plan['project'], sort_keys=True, allow_nan=False).encode()).hexdigest())  #: Retain exact project identity and native exchange environment.
    manifest = destination / 'geometry_manifest.json'  #: Include the complete geometric/source mapping in the downloadable bundle.
    manifest.write_text(json.dumps(plan, indent=2, allow_nan=False), encoding='utf-8')  #: Serialize only fully checked finite geometry/provenance data.
    archive = destination / 'model_geometry.zip'  #: Publish one fixed-name archive only after all native part checks succeed.
    with zipfile.ZipFile(archive, 'w', zipfile.ZIP_DEFLATED) as bundle:  #: Keep the neutral CAD download compatible with ordinary ZIP readers.
        for name in [body['file'] for body in plan['bodies']] + [manifest.name]: bundle.write(destination / name, name)  #: Include only this job's checked parts and manifest, not unrelated staging files.
    with zipfile.ZipFile(archive) as bundle:  #: Verify compression integrity before transport.
        if bundle.testzip() is not None: raise RuntimeError('CAD bundle integrity check failed')  #: Do not return corrupt neutral exchange bytes.
    encoded = base64.b64encode(archive.read_bytes()).decode('ascii')  #: Transport only completed verified archive bytes through the fixed worker protocol.
    return {'kind': 'field_geometry_cad', 'geometry_manifest': plan, 'cad_files': {archive.name: encoded}}  #: No field solution or finite-copper capability is asserted by this result contract.
