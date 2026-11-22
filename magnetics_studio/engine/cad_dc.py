"""Mesh verified joined winding STEP and solve a conductor-only DC problem."""
from hashlib import sha256
from importlib.metadata import PackageNotFoundError, version
import math
from pathlib import Path
from tempfile import TemporaryDirectory
from zipfile import ZipFile

from .cad_field_binding import bind_cad_chain
from .dc_conduction import solve_tagged_dc
from .mesh import cross, dot, sub
from .project import number

NETGEN = {'netgen-mesher': '6.2.2608', 'netgen-occt': '7.8.1'}


def mesh_winding_dc(project, archive, winding, driven, sigma, voltage, maxh, *, curvature_safety=2., linear_solver='pcg'):
    """Bind one STEP winding and drive the selected cap in a separate DC study."""
    sigma = number(sigma, 'Conductivity [S/m]', 1e-3, 1e9)
    voltage = number(voltage, 'Terminal voltage [V]', -1e4, 1e4)
    maxh = number(maxh, 'Maximum tetrahedral size [m]', .0001, .005)
    curvature_safety = number(curvature_safety, 'Netgen curvature safety', 1., 5.)
    if linear_solver not in ('pcg', 'scipy-direct'):
        raise ValueError('Unknown DC linear solver')
    try:
        versions = {name: version(name) for name in NETGEN}
    except PackageNotFoundError as exc:
        raise ValueError('Install the qualified optional Netgen mesh dependencies') from exc
    if versions != NETGEN:
        raise ValueError(f'Expected the qualified Netgen mesh versions: {NETGEN}')

    binding = bind_cad_chain(project, archive, winding)
    conductor = binding['conductor']
    terminals = {t['id']: t for t in conductor['geometric_terminals']}
    if len(terminals) != 2 or driven not in terminals:
        raise ValueError('Select the measured ID of the driven terminal')
    ground, = terminals.keys() - {driven}
    with ZipFile(archive) as bundle, TemporaryDirectory() as directory:
        raw = bundle.read(conductor['body_id']+'.step')
        if sha256(raw).hexdigest() != conductor['sha256']:
            raise ValueError('Winding STEP changed after CAD verification')
        path = Path(directory)/'winding.step'
        path.write_bytes(raw)
        nodes, cells, faces = _native_mesh(path, terminals, maxh, curvature_safety)

    high, low = ({i for face in faces[key] for i in face} for key in (driven, ground))
    result = solve_tagged_dc(nodes, cells, high, low, sigma, voltage, linear_solver=linear_solver)
    for tag, name in (('high', driven), ('low', ground), ('insulated', 'insulated')):
        if set(result['mesh']['boundary_triangles'][tag]) != faces[name]:
            raise ValueError('Native surface tags do not match the tetrahedral exterior')
    area_errors = {}
    for key, t in terminals.items():
        center, normal = t['measured_centre_m'], t['measured_outward_normal']
        if any(abs(dot(sub(nodes[i], center), normal)) > 2e-8 for face in faces[key] for i in face):
            raise ValueError('Meshed terminal vertices leave the measured CAD cap plane')
        area = math.fsum(_area(nodes, face) for face in faces[key])
        area_errors[key] = area/t['measured_area_m2'] - 1
    volume_error = result['mesh']['volume_m3']/conductor['volume_m3'] - 1
    if max(abs(volume_error), *(abs(e) for e in area_errors.values())) > .12:
        raise ValueError('Faceted volume or terminal area differs from CAD by more than 12%')
    result['mesh']['boundary_triangles'] = {key: sorted(value) for key, value in faces.items()}
    currents = result['terminal_current_into_conductor_A']
    result['terminal_current_into_conductor_A'] = {driven: currents['high'], ground: currents['low']}
    result.update(format='magnetics-studio.cad-winding-dc/1', binding=binding,
                  input=dict(driven_terminal=driven, grounded_terminal=ground,
                             maxh_m=maxh, curvature_safety=curvature_safety,
                             conductivity_S_m=sigma, voltage_V=voltage, linear_solver=linear_solver),
                  netgen_versions=versions, relative_volume_error=volume_error,
                  relative_terminal_area_error=area_errors)
    return result


def _area(nodes, face):
    a, b, c = (nodes[i] for i in face)
    normal = cross(sub(b, a), sub(c, a))
    return math.sqrt(dot(normal, normal))/2


def _native_mesh(path, terminals, maxh, curvature_safety):
    from netgen.occ import OCCGeometry

    geo = OCCGeometry(str(path))
    if len(geo.solids) != 1:
        raise ValueError('Expected one joined winding solid in Netgen')
    named = set()
    for face in geo.faces:
        face.name = 'insulated'
        center = tuple(x/1000 for x in face.center)
        for key, terminal in terminals.items():
            area = terminal['measured_area_m2']
            if (math.dist(center, terminal['measured_centre_m']) <= 2e-9
                    and math.isclose(face.mass/1e6, area, rel_tol=1e-7)):
                if key in named or face.name != 'insulated':
                    raise ValueError('Ambiguous native terminal face')
                face.name = key
                named.add(key)
    if named != terminals.keys():
        raise ValueError('Netgen did not recover both measured terminal faces')

    mesh = OCCGeometry(geo.shape).GenerateMesh(maxh=1000*maxh, grading=.4,
                                               curvaturesafety=curvature_safety)
    cell_count, node_count = len(mesh.Elements3D()), len(mesh.Points())
    if not 0 < cell_count <= 90000 or not 0 < node_count <= 30000:
        raise ValueError(f'Native winding mesh exceeds the DC mesh budget or is empty: '
                         f'{cell_count} tetrahedra, {node_count} nodes')
    nodes = [tuple(x/1000 for x in point.p) for point in mesh.Points()]
    cells = [tuple(v.nr-1 for v in el.vertices) for el in mesh.Elements3D()]
    faces = {key: set() for key in (*terminals, 'insulated')}
    for el in mesh.Elements2D():
        name = mesh.GetBCName(el.index-1)
        triangle = tuple(sorted(v.nr-1 for v in el.vertices))
        if name not in faces or len(triangle) != 3 or triangle in faces[name]:
            raise ValueError('Unexpected native surface triangle or boundary name')
        faces[name].add(triangle)
    if any(len(tet) != 4 for tet in cells):
        raise ValueError('Expected first-order tetrahedra from Netgen')
    return nodes, cells, faces
