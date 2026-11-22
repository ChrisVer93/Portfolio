"""Project Studio's E-core packing to MAS Cartesian coil geometry."""
from itertools import groupby  #: Split the ordered CAD paths into source sections and packed radial rows.
from .builder import build  #: Construct a spatial geometry reference for either supported input dimension.
from .turn_cad import turn_plan  #: Use the same rounded path coordinates and lengths as checked turn CAD.


def coil_geometry(source, functional):
    """Return native coil arrays and the transform back to Studio coordinates."""
    if source['family'] != 'e_core':
        raise ValueError('MAS coil geometry currently requires a rectangular E-core')
    spatial = dict(source, mode='3d')
    spatial['packing'] = dict(source['packing'], representation='blocks')
    plan = turn_plan(build(spatial)['project'])
    core = {region['id']: region for region in plan['project']['regions']}
    main = core['limb_1_0']
    origin_x = (main['x0'] + main['x1']) / 2
    origin_z = (core['bottom_yoke']['z1'] + core['top_yoke']['z0']) / 2
    sources = {winding['id']: winding for winding in plan['project']['windings']}
    total_turns = {winding['name']: winding['numberTurns'] for winding in functional}
    sections, layers, turns, limb_links = [], [], [], []

    for section_id, section_turns in groupby(plan['turns'], key=lambda turn: turn['layer_id']):
        packed = list(section_turns)
        first = packed[0]
        winding = first['series_group']
        cx, _, _ = first['centre_m']
        limb_right = cx + first['limb_width_m'] / 2
        window = first['source_window_m']
        build_width = sources[first['source_id']]['display_build_m']
        centre = window['x1']
        section_height = window['z1'] - window['z0']
        sections.append({
            'name': section_id,
            'type': 'conduction',
            'layersOrientation': 'overlapping',
            'partialWindings': [{'winding': winding, 'parallelsProportion': [len(packed) / total_turns[winding]]}],
            'dimensions': [build_width, section_height],
            'coordinates': [centre - origin_x, (window['z0'] + window['z1']) / 2 - origin_z],
            'coordinateSystem': 'cartesian',
        })
        limb_links.append({'section': section_id, 'studio_limb': first['limb']})
        for row, row_turns in groupby(packed, key=lambda turn: turn['radial_row']):
            members = list(row_turns)
            layer_id = section_id + ':row:' + str(row + 1)
            insulation = first['insulation_per_side_m']
            width = first['width_m'] + 2 * insulation
            height = first['height_m'] + 2 * insulation
            radial = limb_right + members[0]['path_offset_m'] - origin_x
            lower = members[0]['centre_m'][2] - origin_z
            upper = members[-1]['centre_m'][2] - origin_z
            layers.append({
                'name': layer_id,
                'section': section_id,
                'type': 'conduction',
                'orientation': 'contiguous',
                'partialWindings': [{'winding': winding, 'parallelsProportion': [len(members) / total_turns[winding]]}],
                'dimensions': [width, upper - lower + height],
                'coordinates': [radial, (upper + lower) / 2],
                'coordinateSystem': 'cartesian',
            })
            for turn in members:
                turns.append({
                    'name': turn['id'],
                    'winding': winding,
                    'section': section_id,
                    'layer': layer_id,
                    'parallel': 0,
                    'orientation': 'counterClockwise',
                    'length': turn['path_length_m'],
                    'dimensions': [width, height],
                    'coordinates': [radial, turn['centre_m'][2] - origin_z],
                    'crossSectionalShape': turn['profile'],
                    'coordinateSystem': 'cartesian',
                })
    return {
        'sectionsDescription': sections,
        'layersDescription': layers,
        'turnsDescription': turns,
    }, {
        'studio_spatial_origin_xz_m': [origin_x, origin_z],
        'coordinate_convention': 'Right-side turn centres in the Studio X/Z plane, relative to the main column and window mid-height',
        'section_limbs': limb_links,
        'scope': 'Rounded closed CAD paths. No winding-window index, bobbin fit, leads, or finite-conductor field claim.',
    }
