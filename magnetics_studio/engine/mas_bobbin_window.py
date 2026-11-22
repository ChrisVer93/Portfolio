"""Matched nominal rectangular central-limb bobbin window for MAS export."""
from .mas_core_geometry import export_core_geometry  #: Use the exact supported EE shape, gap and material mapping.
from .project import number  #: Reject nonnumeric, nonfinite or out-of-range wall inputs.


def bind_bobbin_window(source, packet, dimensions):
    """Attach a custom central-column bobbin to a geometry-enabled packet."""
    if not isinstance(dimensions, dict) or set(dimensions) != {'wall', 'column'}:  #: Require both nominal thicknesses in SI metres.
        raise ValueError('bobbin_dimensions_m requires wall and column thicknesses')
    wall = number(dimensions['wall'], 'Bobbin axial wall (m)', 0, 10)
    column = number(dimensions['column'], 'Bobbin column wall (m)', 0, 10)
    if any(link['studio_limb'] != 1 for link in packet['coil_geometry']['section_limbs']):  #: The supported native bobbin governs only the middle limb.
        raise ValueError('Matched bobbin windows currently require all sections on the central limb')
    core = export_core_geometry(source)
    dims = {key: data['nominal'] for key, data in core['mas_shape']['dimensions'].items()}
    left, right = dims['F'] / 2 + column, dims['E'] / 2
    half_height = dims['D'] - wall
    width = right - left
    if width <= 0 or half_height <= 0:  #: Require positive clear radial and axial extent.
        raise ValueError('Bobbin walls consume the entire core winding window')
    coil = packet['mas_coil']
    for section in coil['sectionsDescription']:
        x, y = section['coordinates']
        w, h = section['dimensions']
        tolerance = 1e-12  #: Admit only arithmetic round-off at a coincident boundary in metres.
        if x - w / 2 < left - tolerance or x + w / 2 > right + tolerance or abs(y) + h / 2 > half_height + tolerance:
            raise ValueError(f"Section {section['name']} exceeds the matched bobbin window")
        section['windingWindow'] = 0  #: Bind the unchanged section to the one declared central-column window.
    coil['bobbin'] = {
        'name': coil['bobbin'],
        'processedDescription': {
            'columnShape': 'rectangular',
            'wallThickness': wall,
            'columnThickness': column,
            'columnWidth': left,  #: PyOpenMagnetics' processed column width is a half-width including the wall.
            'columnDepth': dims['C'] / 2 + column,
            'coordinates': [0, 0, 0],
            'windingWindows': [{
                'shape': 'rectangular',
                'width': width,
                'height': 2 * half_height,
                'area': width * 2 * half_height,
                'coordinates': [(left + right) / 2, 0, 0],
                'column': 0,  #: The MAS main column is index zero in the supported native core convention.
            }],
        },
    }
    packet['coil_geometry']['scope'] = 'Rounded closed CAD paths and checked nominal central-column front-plane window.'
    packet['coil_geometry']['matched_core'] = {
        key: core[key] for key in ('mas_shape', 'mas_gaps', 'material_binding')
    }
    packet['limitations'][:2] = [
        'The nominal front-plane bobbin window is matched to a symmetric rectangular EE. Physical bobbin solids and multi-limb assignment remain pending.',
        'Winding section coordinates and source packing are preserved. Native window fit does not qualify rounded ends, leads or insulation.',
    ]
