"""Verify CAD provenance and bind one complete bare chain to field source IDs."""
from hashlib import sha256
import importlib.metadata
import json
import math
from pathlib import Path
import tempfile
from zipfile import ZipFile

from .geometry_cad import AXES, CAD_PINS, bounds, geometry_plan
from .mas_exchange import canonical
from .turn_links import link_plan
from .turn_ports import measure_ports, port_plan


def bind_cad_chain(project, archive, winding):
    """Return measured candidate regions and faces for later meshing."""
    if any(importlib.metadata.version(name) != version for name, version in CAD_PINS.items()):
        raise ValueError('CAD binding requires the qualified CadQuery/OCP versions')
    import cadquery as cq

    expected = geometry_plan(project, False)
    source = expected['project']
    if source['mode'] != '3d':
        raise ValueError('CAD chain binding requires a spatial project')
    with ZipFile(archive) as bundle, tempfile.TemporaryDirectory() as directory:
        entries = bundle.infolist()
        if len(entries) > 256 or sum(item.file_size for item in entries) > 64_000_000:
            raise ValueError('CAD bundle exceeds binding budget')
        if len({item.filename for item in entries}) != len(entries):
            raise ValueError('Duplicate CAD bundle entry')
        manifest = json.loads(bundle.read('geometry_manifest.json'))
        if manifest.get('format') not in ('magnetics-studio.field-cad/6', 'magnetics-studio.field-cad/7'):
            raise ValueError('Use a checked joined-turn CAD bundle')
        if manifest.get('step_length_unit') != 'mm' or canonical(manifest['project']) != canonical(source):
            raise ValueError('CAD bundle does not match the SI field project')
        cuts = manifest['turn_ports_geometry']['packet']
        connections = manifest['connection_geometry']['packet']
        plan = link_plan(source, cuts, connections)
        chains = [row for row in plan['chain_coverage']['chains'] if row['series_group'] == winding]
        if len(chains) != 1 or not chains[0]['covers_entire_source_winding']:
            raise ValueError('Select one complete bare conductor chain for the winding')
        chain = chains[0]
        bodies = manifest['bodies']
        candidates = [b for b in bodies if b.get('turn_ids') == chain['turn_ids'] and b.get('series_group') == winding]
        if len(candidates) != 1 or candidates[0]['kind'] not in (
            'joined_round_turn_geometry_not_solved_copper', 'joined_rectangular_turn_geometry_not_solved_copper'
        ):
            raise ValueError('Missing or ambiguous physical joined conductor')
        conductor = candidates[0]

        def read_shape(body, filename):
            raw = bundle.read(filename)
            if sha256(raw).hexdigest() != body['sha256'] or b'SI_UNIT(.MILLI.,.METRE.)' not in raw:
                raise ValueError(f'STEP digest or units differ for {filename}')
            path = Path(directory) / 'part.step'
            path.write_bytes(raw)
            shape, = cq.importers.importStep(str(path)).vals()
            if not shape.isValid():
                raise ValueError(f'Invalid reimported solid: {filename}')
            return shape

        index = chain['id'].removeprefix('chain_')
        filename = f'joined_{index}.step'
        if conductor['id'] != f'joined_{index}' or conductor['file'] != filename:
            raise ValueError('Joined conductor file association differs')
        solid = read_shape(conductor, filename)
        box = solid.BoundingBox()
        for axis, dimension in zip(AXES, ('width', 'height', 'depth'), strict=True):
            if getattr(box, axis + 'min') < -2e-6 or getattr(box, axis + 'max') > 1000 * source['domain'][dimension] + 2e-6:
                raise ValueError('Reimported conductor exceeds the field domain')
        measured_volume = solid.Volume() / 1e9
        if len(solid.Solids()) != 1 or not math.isfinite(measured_volume) or measured_volume <= 0:
            raise ValueError('Joined conductor must be one positive-volume solid')
        ports = port_plan(source, cuts)
        selected_cuts = [cut for cut in ports['cuts'] if cut['turn_id'] in chain['turn_ids']]
        copper_volume = math.fsum(
            cut['area_m2'] * (2 * (cut['source']['limb_width_m'] + cut['source']['stack_depth_m'])
                              + math.tau * cut['source']['path_offset_m'] - cut['gap_m'])
            for cut in selected_cuts
        )
        copper_volume += math.fsum(link['expected_volume_m3'] for link in plan['links'] if link['id'] in chain['link_ids'])
        if not math.isclose(measured_volume, copper_volume, rel_tol=1e-7, abs_tol=1e-18):
            raise ValueError('Joined conductor volume differs from source cuts and leads')
        terminals = {}
        for cut in selected_cuts:
            ends = [t for t in cut['terminals'] if t['id'] in chain['free_terminal_ids']]
            if ends:
                terminals.update((t['id'], t) for t in measure_ports(solid, dict(cut, terminals=ends)))
        if set(terminals) != set(chain['free_terminal_ids']):
            raise ValueError('Joined conductor does not expose the expected terminal pair')
        regions = []
        for region in expected['bodies']:
            if region['kind'] != 'field_region':
                continue
            matches = [body for body in bodies if body['id'] == region['id']]
            if len(matches) != 1 or any(matches[0].get(k) != region[k] for k in ('kind', 'source_id', 'material', 'boxes_m')):
                raise ValueError(f"CAD material identity mismatch: {region['source_id']}")
            record = matches[0]
            shape = read_shape(record, region['id'] + '.step')
            box = shape.BoundingBox()
            extents = {axis + end: getattr(box, axis + suffix) / 1000
                       for axis in AXES for end, suffix in (('0', 'min'), ('1', 'max'))}
            expected_bounds = bounds(region['boxes_m'])
            volume = shape.Volume() / 1e9
            if (len(shape.Solids()) != len(region['boxes_m'])
                    or not math.isclose(volume, region['expected_volume_m3'], rel_tol=1e-7, abs_tol=1e-18)
                    or any(abs(extents[key] - expected_bounds[key]) > 1e-9 for key in extents)):
                raise ValueError(f"Reimported CAD region differs: {region['source_id']}")
            for primitive in region['boxes_m']:
                point = cq.Vector(*(1000 * primitive[axis + '0'] for axis in AXES))
                spans = [1000 * (primitive[axis + '1'] - primitive[axis + '0']) for axis in AXES]
                reference = cq.Solid.makeBox(*spans, point)
                common = shape.intersect(reference).Volume()
                if not math.isclose(common, reference.Volume(), rel_tol=1e-7, abs_tol=1e-9):
                    raise ValueError(f"CAD region does not occupy its source box: {region['source_id']}")
            if solid.distance(shape) / 1000 <= 2e-9:
                raise ValueError(f"Conductor touches field material: {region['source_id']}")
            regions.append({'body_id': region['id'], 'region_id': region['source_id'],
                            'material': region['material'], 'volume_m3': volume, 'sha256': record['sha256']})
    return {
        'format': 'magnetics-studio.cad-field-binding/1',
        'scope': 'Measured CAD candidates for a future spatial mesh',
        'project_sha256': sha256(canonical(source)).hexdigest(),
        'field_material_regions': regions,
        'conductor': {'body_id': conductor['id'], 'series_group': winding,
                      'source_ids': chain['source_ids'], 'turn_ids': chain['turn_ids'],
                      'sha256': conductor['sha256'], 'volume_m3': measured_volume, 'expected_volume_m3': copper_volume,
                      'geometric_terminals': [terminals[key] for key in chain['free_terminal_ids']]},
        'limitations': ['One selected complete bare chain. Remaining conductors, insulation and return paths need their own mapping.',
                        'The chain checks cover topology count, volume, domain and end faces. They do not establish complete path equivalence for arbitrary STEP.',
                        'No mesh, conductivity, terminal boundary conditions or field solution is generated.'],
    }
