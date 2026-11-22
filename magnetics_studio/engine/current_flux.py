"""Conservative face-current projection and RT0 reconstruction for DC results."""
import math
import os
import warnings

from .mesh import cross, dot, sub, tetra_geometry
from .sparse import check_cancel


def reconstruct_current(result, cancel=None, *, periodic_pairs=None):  #: Permit only explicitly paired coincident terminal cuts to form a closed source.
    """Project a connected two-terminal DC result onto shared conservative fluxes."""
    if os.environ.get('MAGNETICS_PURE_PYTHON') == '1':
        raise ValueError('Current reconstruction requires the SciPy-enabled profile')
    import numpy as np
    from scipy.sparse import coo_matrix, diags
    from scipy.sparse.csgraph import connected_components
    from scipy.sparse.linalg import MatrixRankWarning, spsolve

    if result.get('format') not in ('magnetics-studio.dc-conduction/1', 'magnetics-studio.cad-winding-dc/1'):
        raise ValueError('Use a solved DC conductor result')
    mesh = result['mesh']
    nodes, cells = mesh['nodes_m'], mesh['tetrahedra']
    raw = result['current_density_A_m2']
    currents = result['terminal_current_into_conductor_A']
    labels = mesh['boundary_triangles']
    if (not 0 < len(cells) <= 90000 or not 4 <= len(nodes) <= 30000
            or len(raw) != len(cells) or len(currents) != 2 or 'insulated' in currents
            or set(labels) != {*currents, 'insulated'}):
        raise ValueError('Require one bounded tetrahedral conductor and two named terminals')
    if any(len(v) != 3 or any(isinstance(x, bool) or not isinstance(x, (int, float))
                             or not math.isfinite(x) for x in v) for v in (*nodes, *raw)):
        raise ValueError('Coordinates and current densities must be finite 3-vectors')
    names = list(currents)
    values = [currents[name] for name in names]
    if any(isinstance(x, bool) or not isinstance(x, (int, float)) or not math.isfinite(x) for x in values):
        raise ValueError('Terminal currents must be finite')
    scale = max(map(abs, values))
    if abs(sum(values)) > 1e-7*max(scale, 1e-30):
        raise ValueError('Input terminal currents do not balance')
    boundary = {}
    for name, triangles in labels.items():
        if not triangles:
            raise ValueError('All three boundary groups require triangles')
        for face in triangles:
            key = tuple(sorted(face))
            if len(key) != 3 or len(set(key)) != 3 or key in boundary:
                raise ValueError('Boundary triangles must be unique and unambiguous')
            boundary[key] = name

    owners, volumes, centers, opposite = {}, [], [], []
    seen = set()
    for t, cell in enumerate(cells):
        if t % 256 == 0:
            check_cancel(cancel)
        if (len(cell) != 4 or len(set(cell)) != 4 or any(type(n) is not int or not 0 <= n < len(nodes) for n in cell)
                or tuple(sorted(cell)) in seen):
            raise ValueError('Invalid or duplicate tetrahedron')
        seen.add(tuple(sorted(cell)))
        volume, _ = tetra_geometry([nodes[i] for i in cell])
        volumes.append(volume)
        centers.append(tuple(sum(nodes[i][d] for i in cell)/4 for d in range(3)))
        local = {}
        for omitted in cell:
            face = tuple(sorted(i for i in cell if i != omitted))
            owners.setdefault(face, []).append(t)
            local[face] = omitted
        opposite.append(local)
    if any(len(v) > 2 for v in owners.values()) or {f for f, v in owners.items() if len(v) == 1} != set(boundary):
        raise ValueError('Boundary tags must equal the manifold tetrahedral exterior')

    # A face points out of its first owning cell and into the second cell or electrode.
    faces, areas, vectors, left, right, guesses, weights = [], [], [], [], [], [], []
    electrode = {name: len(cells)+i for i, name in enumerate(names)}
    adjacency_left, adjacency_right = [], []
    for face, own in owners.items():
        first = own[0]
        a, b, c = (nodes[i] for i in face)
        area_vector = tuple(x/2 for x in cross(sub(b, a), sub(c, a)))
        if dot(area_vector, sub(nodes[opposite[first][face]], a)) > 0:
            area_vector = tuple(-x for x in area_vector)
        area = math.sqrt(dot(area_vector, area_vector))
        faces.append(face)
        areas.append(area)
        vectors.append(area_vector)
        tag = boundary.get(face)
        if len(own) == 2:
            second = own[1]
            if dot(area_vector, sub(nodes[opposite[second][face]], a)) <= 0:
                raise ValueError('Adjacent cells occupy the same side of a shared face')
            adjacency_left.extend((first, second))
            adjacency_right.extend((second, first))
        else:
            second = electrode.get(tag, -1)
        left.append(first)
        right.append(second)
        guesses.append(sum(dot(raw[t], area_vector) for t in own)/len(own))
        weights.append(area*area/sum(volumes[t] for t in own))
    graph = coo_matrix((np.ones(len(adjacency_left)), (adjacency_left, adjacency_right)),
                       shape=(len(cells), len(cells))).tocsr()
    if connected_components(graph, directed=False, return_labels=False) != 1:
        raise ValueError('DC cells must form one face-connected conductor')

    paired = {}  #: Store first-cut face to coincident second-cut face indices.
    if periodic_pairs is not None:  #: Close only a caller-declared, conforming geometric cut.
        high_nodes = {n for f in labels[names[0]] for n in f}  #: Collect the complete first terminal node set.
        low_nodes = {n for f in labels[names[1]] for n in f}  #: Collect the complete second terminal node set.
        if (not isinstance(periodic_pairs, list) or any(not isinstance(p, (list, tuple)) or len(p) != 2
                or any(type(n) is not int for n in p) for p in periodic_pairs)):  #: Reject malformed or noninteger topology declarations.
            raise ValueError('Periodic pairs require explicit integer node pairs')  #: Stop before indexing or changing the projection.
        mapping = dict(periodic_pairs)  #: Map only nodes on the first cap to nodes on the second.
        if (len(mapping) != len(periodic_pairs) or set(mapping) != high_nodes
                or set(mapping.values()) != low_nodes or len(set(mapping.values())) != len(mapping)):
            raise ValueError('Periodic pairs must bijectively cover both terminal cuts')  #: Refuse partial or duplicate closure.
        span = max(max(p[d] for p in nodes)-min(p[d] for p in nodes) for d in range(3))  #: Scale coincidence tolerance with the conductor extent.
        if any(math.dist(nodes[a], nodes[b]) > 1e-10*span for a, b in mapping.items()):  #: Never hide a physical gap with an implicit lead.
            raise ValueError('Periodic cut nodes must be geometrically coincident')  #: Require the actual return geometry to reach the cut.
        indices = {f: i for i, f in enumerate(faces)}  #: Match faces by their exact declared node identities.
        for face in labels[names[0]]:  #: Pair all triangles on the first side of the cut.
            i = indices[tuple(sorted(face))]  #: Retain the canonical outward direction from the first cap owner.
            partner = tuple(sorted(mapping[n] for n in face))  #: Transfer the full triangle to the opposite cut.
            if partner not in boundary or boundary[partner] != names[1]:  #: Require matching triangulation rather than a nearest-centre guess.
                raise ValueError('Periodic cut triangulations must match')  #: Reject nonconforming seam topology.
            j = indices[partner]  #: Bind the second-cap face explicitly.
            if math.dist(vectors[i], tuple(-v for v in vectors[j])) > 1e-9*areas[i]:  #: Require equal areas and opposite outward normals.
                raise ValueError('Periodic cut face normals must oppose')  #: Reject overlapping same-side cells.
            paired[i] = j  #: Keep a single current degree of freedom across the seam.
            right[i], right[j] = left[j], -2  #: Connect the two real cells and mark the partner as an alias.
            guesses[i] = (guesses[i]-guesses[j])/2  #: Average both raw normal estimates in the same orientation.
            weights[i] = areas[i]**2/(volumes[left[i]]+volumes[left[j]])  #: Use the same metric as an internal shared face.
        if len(paired) != len(labels[names[1]]):  #: Ensure there are no unpaired second-side faces.
            raise ValueError('Periodic cut face counts differ')  #: Reject incomplete closure.

    active = [i for i, r in enumerate(right) if r >= 0]  #: Omit insulated faces and seam aliases from the independent unknowns.
    rows = [left[i] for i in active] + [right[i] for i in active]
    cols = list(range(len(active)))*2
    if periodic_pairs is not None:  #: Add a circulation constraint to prevent the closed source collapsing to zero current.
        cut_columns = [k for k, i in enumerate(active) if i in paired]  #: Identify all first-cap fluxes in the circulation row.
        rows += [len(cells)]*len(cut_columns)  #: Append one equation for the total outward current across the cut.
        cols += cut_columns  #: Use exactly the shared seam degrees of freedom.
    data = [1.]*len(active)+[-1.]*len(active)+([1.]*len(cut_columns) if periodic_pairs is not None else [])  #: Assemble cell incidence and optional circulation coefficients.
    incidence = coo_matrix((data, (rows, cols)), shape=(len(cells)+(1 if periodic_pairs is not None else 2), len(active))).tocsr()  #: Preserve ordinary electrode rows for open conductors.
    target = np.zeros(incidence.shape[0])  #: Set zero volume charge production in every tetrahedron.
    # Use one authoritative terminal reaction and its exact opposite for compatibility.
    if periodic_pairs is None:  #: Retain the existing two-terminal projection exactly.
        target[-2:] = values[0], -values[0]  #: Use one reaction and its exact opposite for compatibility.
    else:  #: A cut is an excitation datum, not an external current sink.
        target[-1] = -values[0]  #: Match outward cut flux to minus the original incoming reaction.
    guess = np.asarray([guesses[i] for i in active])
    weight = np.asarray([weights[i] for i in active])
    keep = list(range(len(cells)-1))+[len(cells)] if periodic_pairs is not None else list(range(len(cells)+1))  #: Remove one dependent cell balance for a closed loop or one electrode row for an open conductor.
    reduced = incidence[keep]  #: Keep the independent balances and the prescribed circulation.
    laplacian = (reduced @ diags(weight) @ reduced.T).tocsc()
    rhs = target[keep] - reduced @ guess  #: Correct the raw face estimates toward all independent constraints.
    check_cancel(cancel)
    with warnings.catch_warnings():
        warnings.simplefilter('error', MatrixRankWarning)
        multiplier = spsolve(laplacian, rhs, use_umfpack=False)
    check_cancel(cancel)
    flux = np.zeros(len(faces))
    flux[active] = guess + weight*(reduced.T @ multiplier)
    for i, j in paired.items():  #: Reconstruct the opposite cut-side outward current.
        flux[j] = -flux[i]  #: Enforce pointwise normal continuity across the coincident physical seam.
    defect = incidence @ flux[active] - target
    norm = max(scale, float(np.max(np.abs(flux))), 1e-30)
    if not np.all(np.isfinite(flux)) or np.max(np.abs(defect))/norm > 1e-8:
        raise RuntimeError('Conservative current projection failed its cell or terminal balance')

    # RT0 basis on the face opposite v is (x-v)/(3 volume), with unit outward flux.
    cell_fluxes = [[] for _ in cells]
    reconstructed = [[0., 0., 0.] for _ in cells]
    for i, face in enumerate(faces):
        for t in owners[face]:
            sign = 1 if t == left[i] else -1
            q = sign*float(flux[i])
            cell_fluxes[t].append(q)
            basis = sub(centers[t], nodes[opposite[t][face]])
            for d in range(3):
                reconstructed[t][d] += q*basis[d]/(3*volumes[t])
    divergence = [math.fsum(q)/v for q, v in zip(cell_fluxes, volumes)]
    raw_norm = math.fsum(v*dot(j, j) for v, j in zip(volumes, raw))
    change = math.fsum(v*dot(sub(a, b), sub(a, b)) for v, a, b in zip(volumes, reconstructed, raw))
    return {
        'format': 'magnetics-studio.conservative-current/1',
        'method': 'Weighted shared-face projection with RT0 reconstruction',
        'faces': faces, 'first_cell': left, 'second_cell_or_electrode': right,
        'electrode_graph_rows': {} if periodic_pairs is not None else electrode, 'outward_face_current_A': flux.tolist(),  #: Closed sources have no external electrode graph nodes.
        'face_area_m2': areas, 'face_area_vectors_m2': vectors,
        'current_density_at_cell_centroid_A_m2': reconstructed,
        'divergence_A_m3': divergence,
        'terminal_current_into_conductor_A': {names[0]: values[0], names[1]: -values[0]},
        'terminal_input_adjustment_A': -values[0]-values[1],
        'max_cell_current_defect_A': float(np.max(np.abs(defect[:len(cells)]))),
        'max_relative_balance_defect': float(np.max(np.abs(defect)))/norm,
        'relative_centroid_field_correction': math.sqrt(change/raw_norm) if raw_norm else 0.,
        **({'periodic_closure': {'face_pairs': list(paired.items()), 'node_pairs': periodic_pairs,
                                'cut_outward_current_A': float(sum(flux[i] for i in paired))}}
           if periodic_pairs is not None else {}),  #: Record exact seam topology and signed circulation only for an explicitly closed source.
    }
