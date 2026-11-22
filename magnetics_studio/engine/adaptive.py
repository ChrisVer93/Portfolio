"""Local conforming refinement for linear planar magnetostatics.

The residual indicator guides refinement; its uncalibrated magnitude is not
a certified error bound. The mesh is adapted to the supplied operating point,
not to every unit excitation of a subsequently requested inductance matrix.
"""
import copy  #: Copy mesh metadata without mutating the last accepted mesh.
import math  #: Use Euclidean lengths, stable sums and square roots.
import time  #: Measure the complete adaptive run rather than only its last solve.
from .materials import MU0  #: Convert relative permeability to reluctivity in SI units.
from .mesh import build_mesh, triangle_geometry  #: Reuse fitted initial meshes and P1 geometry.
from .project import validate, number  #: Apply the existing strict model and numeric validation.
from .sparse import check_cancel  #: Honour cancellation during estimation and refinement.


class MeshBudgetExceeded(ValueError):  #: Distinguish budget stops from invalid geometry or solver failure.
    pass  #: Inherit ValueError behaviour with a specific exception identity.


def edges(triangle):  #: Represent an undirected triangle edge by a canonical node pair.
    return [tuple(sorted((triangle[i], triangle[(i + 1) % 3]))) for i in range(3)]  #: Cyclic edges share one key across neighbouring elements.


def triangle_quality(points):  #: Compute geometric diagnostics from actual triangle vertices.
    area, _ = triangle_geometry(points)  #: Also reject inverted or degenerate triangles.
    lengths = [math.dist(points[i], points[(i + 1) % 3]) for i in range(3)]  #: Edge lengths are in metres.
    angles = []  #: Collect all three vertex angles.
    for i in range(3):  #: Inspect each vertex once.
        u = [points[(i + 1) % 3][k] - points[i][k] for k in range(2)]  #: First outgoing side vector.
        v = [points[(i + 2) % 3][k] - points[i][k] for k in range(2)]  #: Second outgoing side vector.
        cross = abs(u[0] * v[1] - u[1] * v[0])  #: Positive twice-area factor for this angle.
        product = sum(a * b for a, b in zip(u, v))  #: Dot product distinguishes acute and obtuse angles.
        angles.append(math.degrees(math.atan2(cross, product)))  #: atan2 remains stable for narrow elements.
    return min(angles), max(lengths) ** 2 / (2 * area)  #: Return minimum angle and longest-side/altitude ratio.


def refine_mesh(mesh, marked, max_nodes=24000, max_elements=46000, cancel=None):  #: Refine selected triangles and conforming neighbours.
    if mesh['dimension'] != 2:  #: This implementation does not split tetrahedra.
        raise ValueError('Local adaptive refinement currently requires a 2D mesh')  #: Reject unsupported dimensionality explicitly.
    nodes = list(mesh['nodes'])  #: Keep old vertices, allowing nested P1 approximation spaces.
    selected = set(marked)  #: Remove duplicate element selections.
    if any(type(i) is not int or i < 0 or i >= len(mesh['elements']) for i in selected):  #: Validate every selected element index.
        raise ValueError('Invalid refinement element index')  #: Never allow Python negative-index behaviour here.
    owners = {}  #: Map each original edge to its adjacent triangle indices.
    for index, triangle in enumerate(mesh['elements']):  #: Build adjacency before inserting any midpoint.
        if index % 1000 == 0:  #: Avoid expensive cancellation polling on every element.
            check_cancel(cancel)  #: Stop before completing a large adjacency scan if requested.
        for edge in edges(triangle):  #: All three sides participate in conformity checks.
            owners.setdefault(edge, []).append(index)  #: Adjacent elements refer to the same edge key.
    if any(len(items) > 2 for items in owners.values()):  #: A valid planar manifold has at most two owners per edge.
        raise ValueError('Non-manifold input mesh')  #: Refuse ambiguous adjacency rather than creating cracks.
    split_edges = {edge for i in selected for edge in edges(mesh['elements'][i])}  #: Red-refine all three sides of each marked triangle.
    pending = list(sorted(split_edges))  #: Propagate an additional quality constraint through the edge adjacency graph.
    while pending:  #: Continue until every affected triangle also has its longest side split.
        edge = pending.pop()  #: Inspect one newly selected edge.
        for index in owners[edge]:  #: The constraint applies on both sides of an internal edge.
            sides = edges(mesh['elements'][index])  #: Obtain the affected triangle's three canonical sides.
            longest = max(sides, key=lambda side: math.dist(nodes[side[0]], nodes[side[1]]))  #: Identify the longest physical side, with deterministic local tie-breaking.
            if longest not in split_edges:  #: Splitting a short side alone can create unnecessarily narrow children.
                split_edges.add(longest)  #: Include the longest side before choosing a conforming split template.
                pending.append(longest)  #: Apply the same quality rule to the neighbouring triangle across this new side.
        if len(pending) % 1000 == 0:  #: Keep propagation responsive during large edge-closure chains.
            check_cancel(cancel)  #: Cancellation discards this unfinished refinement proposal.
    if len(nodes) + len(split_edges) > max_nodes:  #: Check node memory before constructing children.
        raise MeshBudgetExceeded('Adaptive node budget reached')  #: Preserve the previous accepted solution in the caller.
    predicted = sum(1 + sum(edge in split_edges for edge in edges(t)) for t in mesh['elements'])  #: Zero/one/two/three split edges create one/two/three/four children.
    if predicted > max_elements:  #: Include all conformity neighbours in the element budget.
        raise MeshBudgetExceeded('Adaptive element budget reached')  #: Do not silently relax the requested budget.
    midpoint = {}  #: Share exactly one new vertex for every split edge.
    boundary = set(mesh['boundary'])  #: Retain existing homogeneous Dirichlet boundary nodes.
    for edge in sorted(split_edges):  #: Sorting makes node numbering and exported results reproducible.
        a, b = edge  #: Obtain the two endpoint node indices.
        midpoint[edge] = len(nodes)  #: Reserve the midpoint's new index.
        nodes.append(tuple((nodes[a][k] + nodes[b][k]) / 2 for k in range(2)))  #: Insert an exact geometric midpoint.
        if len(owners[edge]) == 1:  #: Only an actual exterior edge extends the constrained boundary.
            boundary.add(midpoint[edge])  #: Do not constrain internal diagonals joining boundary vertices.
    elements, tags, parents = [], [], []  #: Accumulate the refined connectivity and inherited region identities.
    for index, triangle in enumerate(mesh['elements']):  #: Split every affected neighbour, not just marked elements.
        if index % 1000 == 0:  #: Keep refinement cancellable.
            check_cancel(cancel)  #: Cancellation prevents a partial mesh from being returned.
        sides = edges(triangle)  #: Local cyclic order is needed for the split templates.
        active = [i for i, edge in enumerate(sides) if edge in midpoint]  #: Identify which sides acquired midpoints.
        a, b, c = triangle  #: The input mesh is counterclockwise.
        if not active:  #: Unaffected triangles remain unchanged.
            children = [triangle]  #: Preserve their existing approximation region.
        elif len(active) == 1:  #: Green refinement closes a single split edge.
            i = active[0]  #: Rotate the template to the affected side.
            a, b, c = [triangle[(i + j) % 3] for j in range(3)]  #: Keep counterclockwise ordering after rotation.
            m = midpoint[sides[i]]  #: Use the shared midpoint on side a–b.
            children = [(a, m, c), (m, b, c)]  #: Two children exactly cover the original triangle.
        elif len(active) == 2:  #: Two split sides leave a corner triangle and a quadrilateral.
            i = next(i for i in range(3) if i not in active)  #: Find the unsplit side before rotating the template.
            a, b, c = [triangle[(i + 1 + j) % 3] for j in range(3)]  #: The split sides are now a–b and b–c.
            ab, bc = midpoint[tuple(sorted((a, b)))], midpoint[tuple(sorted((b, c)))]  #: Resolve both shared midpoint indices.
            first = [(a, ab, bc), (a, bc, c)]  #: First admissible quadrilateral diagonal is a–bc.
            second = [(a, ab, c), (ab, bc, c)]  #: Second admissible diagonal is ab–c.
            def score(candidates):  #: Compare the worst angle of each possible triangulation.
                return min(triangle_quality([nodes[n] for n in child])[0] for child in candidates)  #: Prefer the option with the larger minimum angle.
            children = [(b, bc, ab)] + (first if score(first) >= score(second) else second)  #: Add the corner and the better diagonal choice.
        else:  #: All three sides split in a red refinement.
            ab, bc, ca = [midpoint[edge] for edge in sides]  #: Midpoints follow the triangle's cyclic side order.
            children = [(a, ab, ca), (ab, b, bc), (ca, bc, c), (ab, bc, ca)]  #: Four counterclockwise children form a complete partition.
        elements.extend(children)  #: Append all children in deterministic order.
        tags.extend([mesh['tags'][index]] * len(children))  #: Inherit material and conductor tags without centroid reclassification.
        parents.extend([index] * len(children))  #: Retain parent indices for conservation and topology verification.
    diagnostics = [triangle_quality([nodes[n] for n in t]) for t in elements]  #: Recompute quality on the refined mesh itself.
    quality = copy.deepcopy(mesh['quality'])  #: Preserve initial fitted-grid diagnostics as historical metadata.
    quality.update(minimum_triangle_angle_deg=min(q[0] for q in diagnostics), maximum_triangle_aspect_ratio=max(q[1] for q in diagnostics))  #: Add actual triangle quality measures.
    quality['refinement'] = 'conforming red-green midpoint subdivision with longest-edge closure; no smoothing or coarsening'  #: State exactly which optimisation is implemented.
    return dict(mesh, nodes=nodes, elements=elements, tags=tags, boundary=boundary, quality=quality, parents=parents)  #: Return a new mesh while leaving the input untouched.


def residual_indicator(project, mesh, fields, cancel=None):  #: Estimate the spatial distribution of discretisation error.
    materials = {m['id']: m for m in project['materials']}  #: Resolve each region's linear isotropic material.
    windings = {w['id']: w for w in project['windings']}  #: Resolve prescribed currents and turn counts.
    areas, cell_data = {}, []  #: Accumulate effective source areas and geometric element data.
    for index, (triangle, tag) in enumerate(zip(mesh['elements'], mesh['tags'])):  #: Tags already encode overlap priority.
        if index % 1000 == 0:  #: Keep large estimation passes responsive to cancellation.
            check_cancel(cancel)  #: Refuse to publish partial estimator data.
        points = [mesh['nodes'][n] for n in triangle]  #: Fetch this triangle's physical coordinates.
        area, _ = triangle_geometry(points)  #: Element area is required for source integration.
        region = project['regions'][tag] if tag >= 0 else {}  #: Untagged cells are background air.
        material = materials[region.get('material', 'air')]  #: Use explicit air when there is no region.
        nu = 1 / (MU0 * material.get('mu_r', 1.0))  #: Linear reluctivity ν has units A/(T·m).
        key = None  #: A cell without a winding contributes no volume current source.
        if region.get('winding'):  #: Match the existing solver's explicit/legacy turn-weighting rules.
            key = region['id'] if 'turns' in region else (region['winding'], region['polarity'])  #: Explicit sections normalise separately; legacy sides normalise together.
            areas[key] = areas.get(key, 0.0) + area  #: Preserve the total area of each source normalisation group.
        h = max(math.dist(points[i], points[(i + 1) % 3]) for i in range(3))  #: Use triangle diameter as the cell length scale.
        cell_data.append((area, nu, region, key, h))  #: Reuse this data after group areas are known.
    indicators, norm_squared = [], 0.0  #: Store squared local indicators and the field energy norm per depth.
    fluxes, owners = [], {}  #: The scalar-PDE flux is ν∇Az, not the raw magnetic B field.
    for index, (triangle, data) in enumerate(zip(mesh['elements'], cell_data)):  #: Evaluate sources and fluxes element by element.
        area, nu, region, key, h = data  #: Unpack the cached SI geometry and material values.
        current_density = 0.0  #: Background and unexcited material cells have zero impressed Jz.
        if key is not None:  #: Recover the source used for this winding section.
            winding = windings[region['winding']]  #: Obtain this electrical source's independent current.
            current_density = region['polarity'] * region.get('turns', winding['turns']) * winding['current'] / areas[key]  #: Jz = signed section ampere-turns divided by effective area.
        indicators.append(h * h * area * current_density ** 2 / nu)  #: For piecewise-constant ν and P1 Az, the interior residual is Jz.
        hx, hy, _ = fields['H'][index]  #: H = νB is piecewise constant for this linear P1 field.
        fluxes.append((-hy, hx))  #: B=(∂yAz,−∂xAz), hence ν∇Az=(−Hy,Hx).
        norm_squared += area * nu * sum(v * v for v in fields['B'][index])  #: Integrate ν|B|², equal to 2W/depth for linear media.
        for edge in edges(triangle):  #: Build internal-edge adjacency for flux jumps.
            owners.setdefault(edge, []).append(index)  #: A shared side receives contributions from both elements.
    for (a, b), adjacent in owners.items():  #: Evaluate each edge only once.
        if len(adjacent) == 2:  #: Homogeneous Dirichlet exterior edges do not add a Neumann residual.
            left, right = adjacent  #: Either orientation gives the same squared jump.
            dx, dy = [mesh['nodes'][b][k] - mesh['nodes'][a][k] for k in range(2)]  #: Build an oriented side vector.
            length = math.hypot(dx, dy)  #: This also supplies the edge length scale.
            jump = sum((fluxes[left][k] - fluxes[right][k]) * n for k, n in enumerate((dy / length, -dx / length)))  #: Project the flux difference onto a common unit normal.
            nu_edge = (cell_data[left][1] + cell_data[right][1]) / 2  #: Use an explicit arithmetic interface reluctivity weight.
            contribution = length * length * jump * jump / nu_edge / 2  #: hE∫jump²/νE is shared equally between the two cells.
            indicators[left] += contribution  #: Add the left half of the internal-edge residual.
            indicators[right] += contribution  #: Add the right half without double counting the edge.
    relative = math.sqrt(math.fsum(indicators) / norm_squared) if norm_squared > 0 else 0.0  #: Normalise by the operating field's energy norm.
    return indicators, relative  #: The ratio is a refinement indicator, not a calibrated error percentage.


def mark_bulk(indicators, fraction=0.5):  #: Select cells containing a requested fraction of squared indicator mass.
    if not 0 < fraction <= 1:  #: A nonempty positive fraction is needed for bulk marking.
        raise ValueError('Marking fraction must be in (0, 1]')  #: Reject meaningless marking requests.
    if any(not math.isfinite(v) or v < 0 for v in indicators):  #: Squared residual indicators must be finite and nonnegative.
        raise ValueError('Invalid residual indicator')  #: Never sort invalid data into an accepted refinement.
    total = math.fsum(indicators)  #: Stable total of the squared local indicators.
    if total == 0:  #: An exact zero indicator needs no marked cells.
        return []  #: Avoid arbitrary refinement of tied zero-valued cells.
    order = sorted(range(len(indicators)), key=lambda i: (-indicators[i], i))  #: Largest contributions first with deterministic tie-breaking.
    chosen, accumulated = [], 0.0  #: Track selected cells and captured indicator mass.
    for index in order:  #: Add the smallest sorted prefix reaching the bulk target.
        chosen.append(index)  #: Select this high-contribution triangle.
        accumulated += indicators[index]  #: Account for its squared residual contribution.
        if accumulated >= fraction * total:  #: Stop only once the requested fraction is covered.
            break  #: Additional cells would increase work without being required by this rule.
    return chosen  #: Conformity neighbours are added later by the mesh splitter.


def adaptive_solve(project, options=None, matrix=True, progress=None, cancel=None):  #: Public adaptive magnetostatic analysis entry point.
    from .analysis import _solve_on_mesh  #: Import lazily to avoid an analysis/adaptive circular import.
    started = time.perf_counter()  #: Include all estimation/refinement passes in total runtime.
    check_cancel(cancel)  #: Honour cancellation before validation or assembly begins.
    p = validate(project)  #: Work on an independent validated model copy.
    from .connections import require_static_sources  #: Apply the shared static-physics guard before initial meshing.
    require_static_sources(p)  #: An explicitly declared net-zero AC solid still cannot be discarded by a static adaptive solve.
    if p['mode'] != '2d' or any(m.get('bh') for m in p['materials']):  #: The current estimator is for linear planar media only.
        raise ValueError('Adaptive solve currently supports linear 2D magnetostatics only')  #: Do not silently linearise nonlinear data or project 3D models.
    if not any(w['current'] != 0 for w in p['windings']):  #: Refinement needs a nonzero operating-point excitation.
        raise ValueError('Adaptive solve needs a nonzero winding current; matrix-only adaptation is not implemented')  #: Avoid claiming accuracy from a trivially zero field.
    defaults = dict(max_passes=4, indicator_target=0.15, energy_target=0.01, marking_fraction=0.5, max_nodes=24000, max_elements=46000)  #: Conservative bounded defaults remain user-adjustable.
    if options is not None and not isinstance(options, dict):  #: Options must be a named JSON object.
        raise ValueError('Adaptive options must be an object')  #: Reject malformed API input before starting a solve.
    if set(options or {}) - set(defaults):  #: Unknown options often indicate an accidental misspelling.
        raise ValueError('Unknown adaptive option')  #: Never silently ignore a requested control.
    settings = dict(defaults, **(options or {}))  #: Merge explicit controls without changing the source project.
    for key, lower, upper in [('max_passes', 1, 8), ('indicator_target', 0.001, 1), ('energy_target', 0.00001, 0.2), ('marking_fraction', 0.05, 1), ('max_nodes', 8, 24000), ('max_elements', 8, 46000)]:  #: Define hard resource and numerical-control ranges.
        value = number(settings[key], key, lower, upper)  #: Reject nonfinite, boolean and out-of-range numeric values.
        if key in ('max_passes', 'max_nodes', 'max_elements') and int(value) != value:  #: Pass counts and budgets cannot be fractional.
            raise ValueError(key + ' must be an integer')  #: Avoid implicit rounding of resource controls.
        if key in ('max_passes', 'max_nodes', 'max_elements'):  #: Canonicalise validated integer-like JSON values.
            settings[key] = int(value)  #: Make range iteration and budget accounting type-safe.
    mesh = build_mesh(p, progress, cancel)  #: Start from the existing interface-fitted mesh.
    if len(mesh['nodes']) > settings['max_nodes'] or len(mesh['elements']) > settings['max_elements']:  #: Apply user budgets to the initial mesh as well.
        raise ValueError('Initial mesh exceeds the adaptive budget; reduce initial subdivisions or increase the budget')  #: Never exceed the chosen budget even on pass one.
    history, previous_energy = [], None  #: Record accepted solves and inter-pass energy changes.
    status = 'pass_limit'  #: A stopped run is not automatically a converged adaptive run.
    for step in range(settings['max_passes']):  #: Bound both runtime and mesh growth by pass count.
        check_cancel(cancel)  #: Stop between accepted refinement passes.
        if progress:  #: Progress reporting is optional for direct Python callers.
            progress(f'Adaptive pass {step + 1}/{settings["max_passes"]}')  #: Identify each solve in the GUI log.
        result = _solve_on_mesh(p, mesh, False, progress, cancel)  #: Solve actual fields on this mesh, without repeated unit-matrix solves.
        indicators, relative = residual_indicator(p, mesh, result['fields'], cancel)  #: Estimate where the current solution needs refinement.
        energy = result['stats']['energy_J']  #: The solved integral includes the physical stack depth.
        change = abs(energy - previous_energy) / max(abs(energy), abs(previous_energy or 0), 1e-30) if previous_energy is not None else None  #: First pass has no energy-change evidence.
        marked = mark_bulk(indicators, settings['marking_fraction'])  #: Apply deterministic bulk marking to squared contributions.
        history.append(dict(pass_number=step + 1, nodes=len(mesh['nodes']), elements=len(mesh['elements']), energy_J=energy, peak_B_T=result['stats']['peak_B_T'], relative_indicator=relative, energy_change=change, marked_elements=len(marked)))  #: Retain enough data to audit stopping decisions.
        if relative <= settings['indicator_target'] and change is not None and change <= settings['energy_target']:  #: Require both spatial-indicator and inter-pass-energy targets.
            status = 'targets_met'  #: State only that the configured indicators met their targets.
            break  #: Retain the accepted field on this final mesh.
        if step + 1 == settings['max_passes'] or not marked:  #: No further pass or useful marking remains.
            break  #: Return the last valid solution with an explicit incomplete target status.
        try:  #: Budget exhaustion is an expected controlled stop.
            mesh = refine_mesh(mesh, marked, settings['max_nodes'], settings['max_elements'], cancel)  #: Locally split cells and all conformity neighbours.
        except MeshBudgetExceeded:  #: Catch only resource exhaustion, not invalid geometry or numerical failure.
            status = 'budget_limit'  #: Explain why requested target values were not achieved.
            break  #: Keep the last accepted mesh and fields intact.
        previous_energy = energy  #: Compare the next accepted solve against this pass.
    if matrix:  #: Unit-excitation matrices are optional and can dominate multiwinding solve time.
        result = _solve_on_mesh(p, mesh, True, progress, cancel)  #: Calculate the final matrix only on the retained operating-point mesh.
    note = 'Residual indicator is uncalibrated, not a certified error bound. Refinement follows the prescribed operating point, not all matrix excitations. No smoothing/coarsening or 3D adaptation.'  #: Keep the accuracy and scope limits attached to exported data.
    result['adaptive'] = dict(status=status, targets_met=status == 'targets_met', settings=settings, rows=history, note=note)  #: Store the complete reproducible adaptive history beside the solved fields.
    result['warnings'].append(note)  #: Existing report/export paths already display warnings.
    if status != 'targets_met':  #: A valid algebraic solve can still miss adaptive targets.
        result['warnings'].append('Adaptive targets not met: ' + status)  #: Expose pass/budget stopping in the main results.
    result['stats']['seconds'] = time.perf_counter() - started  #: Report total wall time across every solve and refinement.
    return result  #: Return the ordinary solved-result schema plus its adaptive evidence.
