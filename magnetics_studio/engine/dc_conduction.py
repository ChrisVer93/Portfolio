"""Two-terminal DC conduction on straight and annular-sector verification meshes."""
from collections import Counter
from itertools import combinations
import math
import os
import time
import warnings

from .mesh import build_mesh, dot, sub, tetra_geometry
from .project import number
from .sparse import check_cancel, matvec, pcg


def solve_dc(spec, cancel=None):
    """Solve one isolated homogeneous conductor with two equipotential caps."""
    if not isinstance(spec, dict) or spec.get('shape') not in ('bar', 'sector'):
        raise ValueError('DC shape must be bar or sector')
    is_bar = spec['shape'] == 'bar'
    dimensions = ('length_m', 'width_m') if is_bar else ('inner_radius_m', 'outer_radius_m', 'angle_rad')
    if set(spec) != {*dimensions, 'shape', 'thickness_m', 'cells', 'conductivity_S_m', 'voltage_V'}:
        raise ValueError('Provide exactly the DC dimensions, mesh, conductivity and voltage')
    thickness = number(spec['thickness_m'], 'Thickness [m]', 1e-5, 10)
    sigma = number(spec['conductivity_S_m'], 'Conductivity [S/m]', 1e-3, 1e9)
    voltage = number(spec['voltage_V'], 'Terminal voltage [V]', -1e4, 1e4)
    cells = spec['cells']
    if not isinstance(cells, list) or len(cells) != 3 or any(type(n) is not int or not 1 <= n <= 128 for n in cells):
        raise ValueError('Supply three integer cell counts in [1, 128]')
    nx, ny, nz = cells
    if is_bar:
        length = number(spec['length_m'], 'Bar length [m]', 1e-5, 10)
        width = number(spec['width_m'], 'Bar width [m]', 1e-5, 10)
        expected_r = length / (sigma * width * thickness)
    else:
        inner = number(spec['inner_radius_m'], 'Inner radius [m]', 1e-5, 10)
        outer = number(spec['outer_radius_m'], 'Outer radius [m]', inner + 1e-5, 10)
        angle = number(spec['angle_rad'], 'Sector angle [rad]', 0.01, math.pi)
        if nx < 2:
            raise ValueError('A sector requires at least two angular cells')
        expected_r = angle / (sigma * thickness * math.log1p((outer - inner) / inner))
    check_cancel(cancel)
    size = dict(width=1., height=1., depth=1., nx=nx, ny=ny, nz=nz, budget='extended')
    grid = build_mesh({'mode': '3d', 'domain': size}, cancel=cancel)
    if is_bar:
        nodes = [(length*x, width*y, thickness*z) for x, y, z in grid['nodes']]
    else:
        nodes = [((inner + (outer-inner)*y)*math.cos(angle*x),
                  (inner + (outer-inner)*y)*math.sin(angle*x), thickness*z)
                 for x, y, z in grid['nodes']]
    # Tag on the reference grid so a rotated sector cannot change terminal ownership.
    high = {i for i, p in enumerate(grid['nodes']) if p[0] == 0}
    low = {i for i, p in enumerate(grid['nodes']) if p[0] == 1}
    result = solve_tagged_dc(nodes, grid['elements'], high, low, sigma, voltage,
                             lift=[1-p[0] for p in grid['nodes']], cancel=cancel)
    return {**result, 'input': {**spec, 'cells': list(cells)}, 'analytic_resistance_ohm': expected_r}


def solve_tagged_dc(nodes, tetrahedra, high, low, sigma, voltage, *, lift=None, cancel=None, linear_solver='pcg'):
    """Solve on a conforming conductor mesh with two disjoint terminal node sets."""
    if not high or not low or high & low:
        raise ValueError('Both terminal node sets must exist and be disjoint')
    if linear_solver not in ('pcg', 'scipy-direct'):
        raise ValueError('Unknown DC linear solver')
    rows = [{} for _ in nodes]
    geometry = []
    face_counts = Counter()
    quality = 1.
    for i, tet in enumerate(tetrahedra):
        if i % 256 == 0:
            check_cancel(cancel)
        points = [nodes[j] for j in tet]
        volume, grads = tetra_geometry(points)
        for a, na in enumerate(tet):
            for b, nb in enumerate(tet):
                rows[na][nb] = rows[na].get(nb, 0.) + volume*dot(grads[a], grads[b])
        edges = [sub(a, b) for a, b in combinations(points, 2)]
        quality = min(quality, 12*(3*volume)**(2/3) / sum(dot(e, e) for e in edges))
        face_counts.update(tuple(sorted(f)) for f in combinations(tet, 3))
        geometry.append((volume, grads))
    faces = {'high': [], 'low': [], 'insulated': []}
    for face, count in face_counts.items():
        if count == 1:
            tag = 'high' if high.issuperset(face) else 'low' if low.issuperset(face) else 'insulated'
            faces[tag].append(face)
    # Solve for a unit voltage with a continuous lift in reference coordinates.
    if lift is None:
        lift = [float(i in high) for i in range(len(nodes))]
    rhs, fixed = [-v for v in matvec(rows, lift)], high | low
    if linear_solver == 'scipy-direct':
        correction, info = _direct_dc(rows, rhs, fixed, cancel)
    else:
        correction, info = pcg(rows, rhs, fixed, tol=1e-10, maxiter=4000, cancel=cancel)
    phi = [a+b for a, b in zip(lift, correction)]
    reactions = matvec(rows, phi)
    conductance = sigma*math.fsum(reactions[i] for i in high)
    return_conductance = sigma*math.fsum(reactions[i] for i in low)
    gradients = [tuple(math.fsum(phi[n]*g[d] for n, g in zip(tet, grads)) for d in range(3))
                 for tet, (_, grads) in zip(tetrahedra, geometry)]
    unit_power = sigma*math.fsum(volume*dot(g, g) for (volume, _), g in zip(geometry, gradients))
    if not math.isfinite(conductance) or conductance <= 0:
        raise RuntimeError('DC conduction requires positive conductance')
    imbalance = abs(conductance + return_conductance) / conductance
    power_error = abs(conductance - unit_power) / conductance
    if max(imbalance, power_error) > 1e-7:
        raise RuntimeError('Terminal current or Joule power balance failed')
    return {
        'format': 'magnetics-studio.dc-conduction/1',
        'mesh': {'nodes_m': nodes, 'tetrahedra': tetrahedra, 'boundary_triangles': faces,
                 'volume_m3': math.fsum(v for v, _ in geometry), 'minimum_mean_ratio': quality},
        'potential_V': [voltage*p for p in phi],
        'current_density_A_m2': [tuple(-sigma*voltage*v for v in g) for g in gradients],
        'terminal_current_into_conductor_A': {'high': voltage*conductance, 'low': voltage*return_conductance},
        'joule_power_W': voltage**2*unit_power,
        'resistance_ohm': 1/conductance,
        'relative_current_imbalance': imbalance,
        'relative_power_error': power_error,
        'solver': info,
    }


def _direct_dc(rows, rhs, fixed, cancel):
    if os.environ.get('MAGNETICS_PURE_PYTHON') == '1':
        raise ValueError('SciPy direct DC requires the SciPy-enabled profile')
    try:
        import numpy as np
        from scipy.sparse import csr_matrix
        from scipy.sparse.linalg import MatrixRankWarning, spsolve
    except ImportError as exc:
        raise ValueError('SciPy direct DC requires NumPy and SciPy') from exc

    check_cancel(cancel)
    start = time.perf_counter()
    free = [i for i in range(len(rows)) if i not in fixed]
    correction = [0.] * len(rows)
    residual = 0.
    if free:
        index = {node: i for i, node in enumerate(free)}
        values, columns, pointers = [], [], [0]
        for node in free:
            for column, value in rows[node].items():
                if column in index:
                    columns.append(index[column])
                    values.append(value)
            pointers.append(len(values))
        matrix = csr_matrix((values, columns, pointers), shape=(len(free), len(free)))
        b = np.asarray([rhs[i] for i in free])
        with warnings.catch_warnings():
            warnings.simplefilter('error', MatrixRankWarning)
            solution = spsolve(matrix, b, use_umfpack=False)
        check_cancel(cancel)
        norm = float(np.linalg.norm(b))
        error = float(np.linalg.norm(matrix @ solution - b))
        residual = error/norm if norm else error
        if not math.isfinite(residual) or residual > 1e-9:
            raise RuntimeError('SciPy direct DC failed the true residual check')
        for i, value in zip(free, solution.tolist()):
            correction[i] = value
    return correction, {'iterations': None, 'residual': residual,
                        'backend': 'SciPy / SuperLU', 'seconds': time.perf_counter()-start}
