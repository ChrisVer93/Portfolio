"""Independent native bobbin fit views of a three-limb EE assembly."""
from collections import Counter  #: Count turns by their stable layer identifier.
from copy import deepcopy  #: Rebase native copies without editing the full assembly coil.

from .mas_core_geometry import export_core_geometry  #: Reuse validated nominal core, gap and material data.
from .project import number  #: Check explicit thicknesses in SI.


def bind_limb_bobbins(source, packet, dimensions):  #: Add local fit views to a geometry-enabled exchange.
    if not isinstance(dimensions, dict) or set(dimensions) != {'0', '1', '2'}:  #: Require declarations even on an unwound neighbour.
        raise ValueError('limb_bobbin_dimensions_m requires Studio limbs 0, 1 and 2')
    walls, columns = [], []  #: Keep axial and radial declarations separate.
    for limb in range(3):  #: Parse in Studio left-to-right limb order.
        values = dimensions[str(limb)]
        if not isinstance(values, dict) or set(values) != {'wall', 'column'}:
            raise ValueError('Each limb requires wall and column thicknesses in metres')
        walls.append(number(values['wall'], 'Bobbin axial wall (m)', 0, 10))
        columns.append(number(values['column'], 'Bobbin column wall (m)', 0, 10))
    core = export_core_geometry(source)  #: Enforce the existing symmetric rectangular EE scope.
    d = {key: item['nominal'] for key, item in core['mas_shape']['dimensions'].items()}
    outer_x = (d['A'] + d['E']) / 4  #: Outer-limb centre measured from the main column.
    centres = [-outer_x, 0, outer_x]
    outer_half = (d['A'] - d['E']) / 4
    halves = [outer_half, d['F'] / 2, outer_half]
    gap = (d['E'] - d['F']) / 2  #: Clear distance between adjacent bare core faces.
    pad = source.get('air_padding_mm', 25) / 1000  #: Limit the outer face by the actual builder air padding.
    coil = packet['mas_coil']
    use_native_orientation = packet['options'].get('native_single_turn_orientation', False)
    turns_per_layer = Counter(turn['layer'] for turn in coil['turnsDescription'])
    limb_by_section = {link['section']: link['studio_limb'] for link in packet['coil_geometry']['section_limbs']}
    winding_limb = {}
    for link in packet['layer_links']:  #: A local native fit view must contain an entire independent winding.
        if winding_limb.setdefault(link['winding'], link['limb']) != link['limb']:
            raise ValueError('Local bobbin fit requires each electrical winding on one limb')
    views = []
    for limb in sorted(set(winding_limb.values())):
        half = halves[limb]
        left_extent = pad if limb == 0 else gap - columns[limb - 1]
        right_extent = pad if limb == 2 else gap - columns[limb + 1]
        inner = half + columns[limb]
        outer = half + min(left_extent, right_extent)  #: Use the stricter face for a closed winding.
        height = 2 * (d['D'] - walls[limb])
        width = outer - inner
        if width <= 0 or height <= 0:
            raise ValueError(f'Bobbin walls consume the window on limb {limb}')
        view = {'bobbin': {'name': f"{coil['bobbin']} / limb {limb}", 'processedDescription': {
            'columnShape': 'rectangular',
            'wallThickness': walls[limb],
            'columnThickness': columns[limb],
            'columnWidth': inner,
            'columnDepth': d['C'] / 2 + columns[limb],
            'coordinates': [0, 0, 0],
            'windingWindows': [{'shape': 'rectangular', 'width': width, 'height': height,
                                'area': width * height, 'coordinates': [(inner + outer) / 2, 0, 0]}],
        }}}
        view['functionalDescription'] = deepcopy([
            row for row in coil['functionalDescription'] if winding_limb[row['name']] == limb
        ])
        for kind in ('sectionsDescription', 'layersDescription', 'turnsDescription'):
            view[kind] = []  #: Retain relative ordering within each local copy.
            for original in coil[kind]:
                section = original['name'] if kind == 'sectionsDescription' else original['section']
                if limb_by_section[section] != limb:
                    continue
                row = deepcopy(original)
                row['coordinates'][0] -= centres[limb]  #: Translate from assembly X to the local core datum.
                if kind == 'sectionsDescription':
                    x, y = row['coordinates']
                    w, h = row['dimensions']
                    if x - w / 2 < inner - 1e-12 or x + w / 2 > outer + 1e-12 or abs(y) + h / 2 > height / 2 + 1e-12:
                        raise ValueError(f"Section {section} exceeds the matched window on limb {limb}")
                    row['windingWindow'] = 0  #: Each local scalar bobbin has exactly one window.
                if use_native_orientation and kind == 'layersDescription' and turns_per_layer[row['name']] == 1:
                    row['orientation'] = 'overlapping'  #: A one-turn row has no axial sequence; match the pinned native fit convention.
                view[kind].append(row)
        views.append({'studio_limb': limb, 'assembly_origin_x_m': centres[limb], 'mas_coil': view})
    packet['coil_geometry']['limb_bobbin_views'] = views
    packet['coil_geometry']['matched_core'] = {
        key: core[key] for key in ('mas_shape', 'mas_gaps', 'material_binding')
    }
    packet['coil_geometry']['scope'] = 'Assembly geometry and separate local nominal bobbin fit views.'
    packet['limitations'].append('Local bobbins use a conservative two-face section check. The views do not form one native multi-bobbin assembly or certify physical insulation and end clearances.')
    if use_native_orientation:
        packet['limitations'].append('Single-turn layers in local fit views use overlapping orientation for PyOpenMagnetics 1.7.35 compatibility. The fit checker is a separate operation.')

    if packet['options'].get('native_bobbin_assembly', False):
        packet['coil_geometry']['native_bobbin_assembly'] = native_assembly(coil, views, limb_by_section)


def native_assembly(coil, views, limb_by_section):  #: Map the supported fully wound EE to the pinned native column order.
    by_limb = {view['studio_limb']: view for view in views}
    if set(by_limb) != {0, 1, 2}:
        raise ValueError('Native bobbin assembly requires all three limbs to be wound')
    order = (1, 2, 0)  #: Nominal native EE column order is centre, right, left.
    column_by_limb = {limb: index for index, limb in enumerate(order)}
    assembly = deepcopy(coil)
    assembly['bobbin'] = []
    layer_orientations = {}
    for index, limb in enumerate(order):
        view = by_limb[limb]
        local = view['mas_coil']
        bobbin = deepcopy(local['bobbin'])
        description = bobbin['processedDescription']
        window = description['windingWindows'][0]
        offset = view['assembly_origin_x_m']
        description['coordinates'][0] += offset
        window['coordinates'][0] += offset
        window['column'] = index
        assembly['bobbin'].append(bobbin)
        layer_orientations.update((row['name'], row['orientation']) for row in local['layersDescription'])
    for section in assembly['sectionsDescription']:
        section['windingWindow'] = column_by_limb[limb_by_section[section['name']]]
    for layer in assembly['layersDescription']:
        layer['orientation'] = layer_orientations[layer['name']]
    return {'studio_limb_order': list(order), 'mas_coil': assembly}
