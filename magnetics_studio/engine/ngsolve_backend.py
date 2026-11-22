"""Optional Netgen/NGSolve linear magnetostatics; native libraries load in a worker."""
from .connections import series_key, require_static_sources  #: Share validated electrical port identities with the reference solver and sweeps.
import math  #: Evaluate norms and physical stopping criteria.
import time  #: Record full mesh/solve execution time.
from .project import validate, number  #: Preserve the current project boundary and finite-input guards.
from .materials import MU0  #: Use the same SI permeability convention as the reference backend.


def solve_native(project, options=None, matrix=True, progress=None):  #: Solve a validated ordinary project using the optional external backend.
    import ngsolve as ng  #: Load native FEM only inside the isolated worker process.
    from netgen.occ import Box, Pnt, WorkPlane, Glue, OCCGeometry  #: Reuse OpenCASCADE geometry and Netgen meshing.
    if ng.__version__ != '6.2.2608':  #: Qualify only the version exercised in this increment.
        raise RuntimeError('Use the tested ngsolve==6.2.2608 development environment')  #: Refuse silently different native solver versions.
    ng.SetNumThreads(1)  #: Bound resource use and make benchmark execution reproducible.
    started = time.perf_counter()  #: Include native geometry generation and meshing in elapsed time.
    p = validate(project)  #: Retain all independent winding, material and source identities.
    require_static_sources(p)  #: Protect direct native CLI/worker calls from silently ignoring region-only AC assignments.
    if any(m.get('bh') for m in p['materials']) or p.get('ac_conductors'):  #: The new backend is explicitly linear magnetostatic in this increment.
        raise ValueError('Native backend currently supports linear magnetostatics; use existing 2D nonlinear/AC actions separately')  #: Do not silently discard nonlinear or eddy-current physics.
    if len(p['regions']) > 60:  #: Bound Boolean geometry work before entering native operations.
        raise ValueError('Native pilot supports at most 60 regions; use winding blocks or the reference backend')  #: Explain the current modelling capacity limit.
    o = dict(options or p.get('native_settings', {}))  #: Keep caller settings separate from the saved source project.
    dim = 2 if p['mode'] == '2d' else 3  #: Select scalar planar or vector spatial FEM explicitly.
    d = p['domain']  #: Use SI geometry already validated by the existing project boundary.
    sizes = [d[k] for k in ['width', 'height', 'depth'][:dim]]  #: Keep true 3D depth distinct from planar model depth.
    h = number(o.get('maxh_m', max(sizes) / 8), 'Native maximum element size', min(sizes) / 10000, max(sizes))  #: Bound the requested Netgen size in metres.
    passes = number(o.get('max_passes', 1), 'Native passes', 1, 4)  #: Bound the complete solve/estimate/refine sequence.
    if int(passes) != passes:  #: Reject fractional pass counts rather than truncate them.
        raise ValueError('Native passes must be an integer')  #: Name the invalid execution control.
    marking = number(o.get('marking_fraction', .5), 'Bulk marking fraction', .1, .9)  #: Use squared-indicator mass for deterministic local marking.
    target = number(o.get('indicator_target', .15), 'Indicator target', .001, 1)  #: This is an uncalibrated recovery ratio, not a certified accuracy percentage.
    energy_target = number(o.get('energy_target', .01), 'Energy change target', .00001, .2)  #: Require an integral change check as well as a spatial indicator.
    epsilon = number(o.get('gauge_epsilon', 1e-8), '3D gauge regularisation', 1e-12, 1e-4)  #: Bound the explicit numerical regularisation used by the vector solve.
    if not isinstance(o.get('probes_m', []), list) or len(o.get('probes_m', [])) > 64:  #: Bound optional physical probes before native geometry or result allocation.
        raise ValueError('Use at most 64 native field probes')  #: Keep explicit inspection requests within the pilot resource profile.
    budget = 30000 if dim == 3 else 46000  #: Keep pilot mesh capacity explicit and predictable.
    if math.prod(sizes)/h**dim*(2 if dim == 2 else 6) > budget:  #: Reject obviously excessive uniform-size requests before native mesh allocation.
        raise ValueError('Requested element size is too small for the native pilot budget')  #: Keep a predictable source-form test capacity.
    if passes > 1 and not any(w['current'] for w in p['windings']):  #: Operating-point refinement needs an actual nonzero field source.
        raise ValueError('Adaptive native solve requires a nonzero winding current')  #: Do not claim refinement of an unexcited inductance matrix.
    def log(s):  #: Forward short progress records to the parent process.
        if progress:  #: CLI use may omit a callback.
            progress(s)  #: Keep native progress separate from result data.
    def shape(box):  #: Map current project geometry into native solids or planar faces.
        if dim == 3:  #: Preserve volume regions and source-window surfaces in the spatial model.
            return Box(Pnt(box['x0'], box['y0'], box['z0']), Pnt(box['x1'], box['y1'], box['z1']))  #: Create an exact SI rectangular solid.
        if box.get('polygon'):  #: Retain existing faceted individual-turn polygons.
            points = box['polygon']  #: Do not replace a polygon by its bounding rectangle.
            wire = WorkPlane().MoveTo(*points[0])  #: Start the exact piecewise-linear contour.
            for point in points[1:]:  #: Add every supplied conductor/core facet.
                wire.LineTo(*point)  #: Preserve physical polygon vertices.
            return wire.Close().Face()  #: Create the bounded native planar region.
        return WorkPlane().MoveTo(box['x0'], box['y0']).Rectangle(box['x1']-box['x0'], box['y1']-box['y0']).Face()  #: Preserve exact rectangular 2D region dimensions.
    domain_box = dict(x0=0, y0=0, x1=sizes[0], y1=sizes[1])  #: Build the common finite outer domain.
    if dim == 3:  #: A spatial domain needs actual volume bounds.
        domain_box.update(z0=0, z1=sizes[2])  #: Keep the real model depth in the CAD representation.
    parts = [(shape(domain_box), -1, ())]  #: Start with air and no sheet-source membership.
    masks = [(r, i, None) for i, r in enumerate(p['regions'])]  #: Apply region priority in the same order as the reference backend.
    if dim == 3:  #: Spatial sources are enclosed ideal-sheet windows, not display copper envelopes.
        masks += [(w['window'], None, i) for i, w in enumerate(p['windings'])]  #: Fit every source-window interface into the native partition.
    for box, tag, winding in masks:  #: Partition geometry so cells have unambiguous material and source membership.
        mask = shape(box)  #: Build the next exact region or sheet-window volume.
        updated = []  #: Preserve disjoint pieces after this Boolean operation.
        for piece, old_tag, membership in parts:  #: Split each existing physical partition independently.
            for intersection, is_inside in [(piece-mask, False), (piece*mask, True)]:  #: Keep both exterior and interior pieces without overlaps.
                entities = intersection.solids if dim == 3 else intersection.faces  #: Ignore genuinely empty Boolean results.
                if len(entities):  #: Do not add null regions to the mesher.
                    updated.append((intersection, tag if is_inside and tag is not None else old_tag, membership + (winding,) if is_inside and winding is not None else membership))  #: Preserve last-region-wins material priority and additive sheet-source membership.
        parts = updated  #: Use the complete new disjoint partition for the next region.
        if len(parts) > 500:  #: Bound geometry complexity independently of element size.
            raise ValueError('Native partition exceeds 500 pieces; simplify overlapping regions')  #: Fail before creating an uncontrolled CAD/mesh workload.
    labels = {}  #: Map native material names to original regions and electrical sheet sources.
    for i, (piece, tag, membership) in enumerate(parts):  #: Give every disjoint piece a stable job-local physical label.
        label = 'cell_' + str(i)  #: Avoid user labels accidentally becoming regular expressions.
        (piece.solids if dim == 3 else piece.faces).name = label  #: Attach physical assignment before meshing.
        labels[label] = (tag, membership)  #: Retain the mapping for fields, source bases and exports.
    glued = Glue([piece for piece, _, _ in parts])  #: Generate conforming shared interfaces through the established CAD kernel.
    for boundary in (glued.faces if dim == 3 else glued.edges):  #: Identify exterior boundaries without constraining internal material interfaces.
        centre = boundary.center  #: The supported domain boundaries are planar coordinate faces.
        boundary.name = 'outer' if any(abs(centre[k]) < 1e-10 or abs(centre[k]-sizes[k]) < 1e-10 for k in range(dim)) else 'interface'  #: Set homogeneous potential only on the actual finite-domain exterior.
    log('Netgen: generating conforming unstructured ' + ('triangles' if dim == 2 else 'tetrahedra'))  #: State the actual mesh generator and dimensionality.
    mesh = ng.Mesh(OCCGeometry(glued, dim=dim).GenerateMesh(maxh=h))  #: Use Netgen rather than the custom Cartesian splitter.
    mats = {m['id']: m for m in p['materials']}  #: Resolve source-project material IDs after partitioning.
    nus = {label: 1/(MU0*mats[p['regions'][tag]['material'] if tag >= 0 else 'air'].get('mu_r', 1)) for label, (tag, _) in labels.items()}  #: Assign real isotropic reluctivity without changing material identity.
    nu = mesh.MaterialCF(nus)  #: Let the FEM engine integrate the piecewise material law on its actual mesh.
    depth = d['depth'] if dim == 2 else 1.0  #: Scale planar energy/linkage by depth exactly once.
    history = []  #: Record accepted mesh/solve/indicator evidence.
    stop = 'pass_limit'  #: Never imply that reaching the pass count proves convergence.
    result = None  #: Preserve the final accepted field record explicitly.
    for step in range(int(passes)):  #: Solve and estimate on each accepted native mesh.
        if mesh.ne > budget:  #: Check actual mesh capacity before assembling native matrices.
            raise ValueError('Native mesh exceeds element budget; increase maximum element size')  #: Preserve previous application results on failed jobs.
        space = ng.H1(mesh, order=1, dirichlet='outer') if dim == 2 else ng.HCurl(mesh, order=0, dirichlet='outer', nograds=True)  #: Use scalar nodal or vector edge FEM with explicit exterior trace conditions.
        if space.ndof > 45000:  #: Bound sparse factorisation size in the pilot.
            raise ValueError('Native finite-element space exceeds 45000 DOFs')  #: Avoid an uncontrolled direct-solver memory request.
        u, v = space.TnT()  #: Use the external engine's trial/test spaces and assembly.
        differential = ng.grad if dim == 2 else ng.curl  #: Planar B is a rotation of grad(Az); spatial B is curl(A).
        gauge = epsilon / max(sizes)**2 if dim == 3 else 0  #: Make the vector regularisation dimensionally consistent with curl-curl.
        a = ng.BilinearForm(nu*differential(u)*differential(v)*ng.dx + gauge*nu*u*v*ng.dx)  #: Assemble the physical field energy plus the explicitly recorded 3D numerical gauge term.
        a.Assemble()  #: Perform real native element integration and sparse assembly.
        inverse = a.mat.Inverse(space.FreeDofs(), inverse='sparsecholesky')  #: Reuse a native sparse factorisation for the operating point and unit excitations.
        areas = {i: 0.0 for i in range(len(p['regions']))}  #: Normalise 2D turn/current density using effective nonoverlapping region areas.
        for label, (tag, _) in labels.items():  #: Integrate only the physical partition actually meshed.
            if tag >= 0:  #: Unassigned air carries no impressed winding section.
                areas[tag] += ng.Integrate(1, mesh, definedon=mesh.Materials(label))  #: Measure exact effective areas rather than count mesh centroids.
        sources = []  #: Build one independent unit-current field coupling per existing winding/section.
        for wi, w in enumerate(p['windings']):  #: Preserve the original independent electrical source ordering.
            coefficients = {}  #: Associate unit source coefficients with native cell labels.
            for label, (tag, membership) in labels.items():  #: Keep source assignment on fitted interfaces.
                value = 0.0  #: Cells without this winding remain unexcited by its unit basis.
                if dim == 3 and wi in membership:  #: The current-sheet potential is constant inside its enclosed window volume.
                    value = w['turns']/(w['window']['z1']-w['window']['z0'])  #: Tz per ampere gives the same closed ideal-sheet source as the reference solver.
                elif dim == 2 and tag >= 0 and p['regions'][tag].get('winding') == w['id']:  #: Source only the physical 2D section assigned to this winding.
                    r = p['regions'][tag]  #: Retain explicit section turns and conductor polarity.
                    total = sum(area for ri, area in areas.items() if p['regions'][ri].get('winding') == w['id'] and p['regions'][ri]['polarity'] == r['polarity'])  #: Treat each current direction independently.
                    if areas[tag] <= 0 or total <= 0:  #: An overwritten conductor cannot silently carry finite ampere-turns.
                        raise ValueError('A winding section has no effective native mesh area')  #: Reject source normalisation failure explicitly.
                    value = r['polarity']*(r['turns']/areas[tag] if 'turns' in r else w['turns']/total)  #: Preserve either explicit section turns or uniform signed total NI.
                coefficients[label] = value  #: Complete the scalar Jz or Tz source coefficient map.
            sources.append(mesh.MaterialCF(coefficients))  #: Retain native coefficient functions for unit solves and flux linkage.
        forms = []  #: Assemble independent field-port right-hand sides once per mesh.
        for source in sources:  #: Current bases must be the same in excitation and linkage extraction.
            f = ng.LinearForm(source*(v if dim == 2 else ng.curl(v)[2])*ng.dx)  #: Use uniform Jz in 2D and curl(T) weak loading in 3D.
            f.Assemble()  #: Let NGSolve integrate the real source on conforming cells.
            forms.append(f)  #: Preserve the exact discrete field-port coupling.
        rhs = ng.LinearForm(space)  #: Allocate a vector with the native space's correct layout.
        rhs.Assemble()  #: Initialise an actual zero load of the correct native type.
        for w, f in zip(p['windings'], forms):  #: Superpose prescribed winding currents without merging circuit containers.
            rhs.vec.data += w['current']*f.vec  #: Apply the user's physical static ampere excitations.
        solution = ng.GridFunction(space)  #: Hold the solved potential on this accepted mesh.
        solution.vec.data = inverse*rhs.vec  #: Run the native sparse solve.
        residual = rhs.vec.CreateVector()  #: Recompute algebraic residual independently of the factorisation status.
        residual.data = a.mat*solution.vec-rhs.vec  #: Measure the equations actually assembled.
        residual[~space.FreeDofs()] = 0  #: Exclude prescribed boundary reactions from the free-equation residual.
        relative = ng.Norm(residual)/max(ng.Norm(rhs.vec), 1e-30)  #: Normalise the actual free residual.
        b = ng.CoefficientFunction((ng.grad(solution)[1], -ng.grad(solution)[0])) if dim == 2 else ng.curl(solution)  #: Construct real physical B from the correct dimensional potential.
        energy = depth*.5*ng.Integrate(nu*(b*b), mesh)  #: Integrate physical magnetic energy without including artificial gauge energy.
        gauge_energy = depth*.5*ng.Integrate(gauge*nu*solution*solution, mesh)  #: Quantify numerical regularisation contamination explicitly.
        links = [depth*ng.InnerProduct(f.vec, solution.vec) for f in forms]  #: Extract flux linkages from the same assembled source bases.
        source_energy = .5*sum(w['current']*l for w, l in zip(p['windings'], links))  #: Independently form the source-work magnetic energy.
        balance = abs(source_energy-energy)/max(abs(source_energy), abs(energy), 1e-30)  #: Check physical energy rather than only an algebraic residual.
        if relative > 1e-7 or balance > 1e-5:  #: Do not publish numerically inconsistent native output.
            raise RuntimeError('Native residual or physical energy check failed')  #: Preserve a failed job as failure, not an attractive field plot.
        source_t = sum((w['current']*s for w, s in zip(p['windings'], sources)), ng.CoefficientFunction(0))  #: Form the actual summed Jz or Tz coefficient for recovery.
        flux = nu*ng.grad(solution) if dim == 2 else nu*b-ng.CoefficientFunction((0, 0, source_t))  #: Recover normal-continuous planar flux or tangential-continuous H-minus-T in 3D.
        recovered = ng.GridFunction(ng.HDiv(mesh, order=0) if dim == 2 else ng.HCurl(mesh, order=0))  #: Use the external compatible recovery space.
        recovered.Set(flux)  #: Project the computed field into the continuity-constrained recovery representation.
        errors = ng.Integrate((flux-recovered)*(flux-recovered)/nu, mesh, element_wise=True)  #: Compute one squared recovery indicator per native element.
        eta = math.sqrt(max(0, sum(errors))/max(2*energy/depth, 1e-30)) if energy else 0  #: Report an uncalibrated normalised indicator without calling it a certified bound.
        change = abs(energy-history[-1]['energy_J'])/max(abs(energy), 1e-30) if history else None  #: Track the actual integral change between accepted meshes.
        history.append({'pass': step+1, 'elements': mesh.ne, 'dofs': space.ndof, 'energy_J': energy, 'relative_indicator': eta, 'energy_change': change})  #: Preserve reproducible refinement/stopping evidence.
        log(f'NGSolve pass {step+1}: {mesh.ne} elements; W={energy:.8g} J; indicator={eta:.4g}')  #: Report numerical progress without conflating it with external validation.
        result_probes = []  #: Record explicitly requested physical field probes for analytical comparisons.
        for probe in o.get('probes_m', []):  #: Probe coordinates are SI points inside the finite domain.
            if len(probe) != dim:  #: Refuse coordinates with the wrong dimensionality.
                raise ValueError('Probe dimension does not match the project')  #: Avoid evaluating a different physical point silently.
            point = [number(x, 'Probe coordinate', 0, sizes[k]) for k, x in enumerate(probe)]  #: Validate every requested physical coordinate.
            result_probes.append({'point_m': point, 'B_T': list(b(mesh(*point)))})  #: Preserve the actual native field evaluation, not a plot interpolation.
        nodes = [list(vertex.point)[:dim] for vertex in mesh.vertices]  #: Export actual unstructured native vertex coordinates.
        elements, tags, bs, hs, measures = [], [], [], [], []  #: Build the existing viewer/export schema from actual native cells.
        cell_measures = ng.Integrate(1, mesh, element_wise=True)  #: Integrate actual cell measures once instead of repeating a global pass per element.
        for el in mesh.Elements():  #: Preserve the correspondence between fields and the actual triangle/tetrahedron mesh.
            vertices = [vtx.nr for vtx in el.vertices]  #: Use native mesh vertex IDs with zero-based indexing.
            centre = [sum(nodes[i][k] for i in vertices)/len(vertices) for k in range(dim)]  #: Sample the lowest-order cell field at its interior centroid.
            point = mesh(*centre)  #: Evaluate inside the native cell.
            bv = list(b(point))  #: Extract real B components in tesla.
            hv = [float(nu(point))*x for x in bv]  #: Apply local material reluctivity for H in amperes/metre.
            elements.append(vertices)  #: Export unstructured connectivity, not a display reconstruction.
            tags.append(labels[el.mat][0])  #: Recover the original region identity after geometry partitioning.
            bs.append(bv); hs.append(hv)  #: Keep B/H arrays aligned with the exported element order.
            measures.append(float(cell_measures[el.nr])*depth)  #: Export actual cell volume or planar area-times-depth.
        result = {'project': p, 'mesh': {'dimension': dim, 'nodes': nodes, 'elements': elements, 'tags': tags, 'grids': [[size*i/18 for i in range(19)] for size in sizes], 'quality': {'generator': 'Netgen', 'requested_maxh_m': h, 'largest_cell_axis_aspect_ratio': None}}, 'fields': {'B': bs, 'H': hs, 'measures': measures, 'energy_J': energy}, 'stats': {'mode': p['mode'], 'nodes': len(nodes), 'elements': len(elements), 'dofs': sum(space.FreeDofs()), 'peak_B_T': max((math.sqrt(sum(x*x for x in v)) for v in bs), default=0), 'energy_J': energy, 'seconds': time.perf_counter()-started, 'solver': {'backend': 'Netgen/NGSolve 6.2.2608', 'residual': relative, 'gauge_energy_fraction': gauge_energy/max(energy, 1e-30)}, 'nonlinear': False, 'energy_consistency': balance, 'reciprocity': None}, 'windings': [{'id': w['id'], 'name': w['name'], 'turns': w['turns'], 'current_A': w['current'], 'linkage_Wb_turn': link} for w, link in zip(p['windings'], links)], 'regions': [], 'warnings': ['Limited linear magnetostatic backend; no external FEMM/Maxwell validation.', 'Finite outer boundary: Az=0 in 2D; tangential A=0 in 3D. Check air-domain sensitivity.', '3D winding sources are ideal sheets, not finite solved copper.', 'Recovery indicators are uncalibrated; corner peaks and matrix accuracy require independent refinement studies.']}  #: Preserve compatibility with current field/CAD views while making physical limits explicit.
        edge_ratios = []  #: Measure actual simplex shape quality rather than treating requested size as achieved quality.
        for cell in elements:  #: Inspect all actual unstructured cell edges.
            lengths = [math.dist(nodes[cell[i]], nodes[cell[j]]) for i in range(len(cell)) for j in range(i) ]  #: Compute physical edge lengths directly from native connectivity.
            edge_ratios.append(max(lengths)/min(lengths))  #: Retain a simple measured sliver/elongation diagnostic.
        result['mesh']['quality'].update(maximum_simplex_edge_ratio=max(edge_ratios, default=0), minimum_cell_measure=min(measures, default=0))  #: Label only measured quality quantities, without asserting a certified mesh optimum.
        result['probes'] = result_probes  #: Expose explicit benchmark/inspection probes in full JSON output.
        result['native_settings'] = o  #: Keep the actual selected run controls with the exported solution.
        if dim == 2:  #: Retain nodal planar potential for the existing Az plot and exports.
            result['fields']['Az'] = [float(solution(mesh(*point))) for point in nodes]  #: Evaluate the actual native nodal field.
        if eta <= target and change is not None and change <= energy_target:  #: Require both requested operating-point criteria on accepted meshes.
            stop = 'targets_met'  #: State only the implemented heuristic stopping criteria were met.
            break  #: Retain this last accepted field.
        if step+1 == passes:  #: Do not refine a mesh that will not be solved.
            break  #: Preserve exact exported field/mesh consistency.
        if mesh.ne*8 > budget:  #: Conservatively bound worst-case refinement growth before mutating the accepted mesh.
            stop = 'budget_limit'  #: Distinguish resource stopping from convergence.
            break  #: Return the actual last accepted solution and unmet criteria.
        threshold = marking*sum(errors)  #: Choose the requested bulk of squared indicator mass.
        marked = set(); total = 0.0  #: Track deterministic selected native cell IDs.
        for index in sorted(range(len(errors)), key=lambda i: (-errors[i], i)):  #: Refine high-indicator cells in a stable tie order.
            marked.add(index); total += errors[index]  #: Accumulate the squared mass covered by selected cells.
            if total >= threshold:  #: Stop once the actual requested bulk is selected.
                break  #: Avoid unnecessary refinement elsewhere.
        for el in mesh.Elements():  #: Let Netgen handle conformity and actual element subdivision.
            mesh.SetRefinementFlag(el, el.nr in marked)  #: Set native local refinement flags.
        mesh.Refine()  #: Use external conforming local refinement rather than our custom splitter.
    lm = None  #: Inductance extraction is optional and uses the final accepted field mesh.
    if matrix:  #: Preserve the standard user-controlled matrix option.
        lm = [[0.0]*len(forms) for _ in forms]  #: Retain every independent source basis in the output ordering.
        for j, f in enumerate(forms):  #: Solve each unit excitation on the same final mesh/factorisation.
            unit = ng.GridFunction(space)  #: Use the exact same native trial space as the operating point.
            unit.vec.data = inverse*f.vec  #: Reuse the established sparse direct solver.
            for i, fi in enumerate(forms):  #: Couple each observation winding to that unit source.
                lm[i][j] = depth*ng.InnerProduct(fi.vec, unit.vec)  #: Extract the discrete energy-consistent mutual/self inductance.
        scale = max((abs(x) for row in lm for x in row), default=1) or 1  #: Normalise reciprocity without dividing by near-zero individual mutual terms.
        reciprocity = max((abs(lm[i][j]-lm[j][i])/scale for i in range(len(lm)) for j in range(len(lm))), default=0)  #: Check the actual assembled field-port symmetry.
        if reciprocity > 1e-7:  #: Refuse a failed matrix consistency check.
            raise RuntimeError('Native inductance reciprocity failed')  #: Do not publish a numerically inconsistent matrix.
        result['stats']['reciprocity'] = reciprocity  #: Preserve the actual matrix-check result.
    result['inductance_H'] = lm  #: Keep the ordinary section-level matrix export available.
    groups = list(dict.fromkeys(series_key(w) for w in p['windings']))  #: Group only explicitly connected physical winding sections.
    grouped = [[sum(lm[i][j] for i, wi in enumerate(p['windings']) for j, wj in enumerate(p['windings']) if series_key(wi) == a and series_key(wj) == b) for b in groups] for a in groups] if lm is not None else None  #: Aggregate section coupling without merging independent electrical windings in a named container.
    result['circuits'] = {'names': groups, 'group_ids': groups, 'inductance_H': grouped}  #: Supply the existing matrix view's grouped result contract.
    for tag, region in enumerate(p['regions']):  #: Retain region-based field inspection for original model identities.
        indices = [i for i, t in enumerate(result['mesh']['tags']) if t == tag]  #: Associate exported native cells with their original region.
        volume = sum(result['fields']['measures'][i] for i in indices)  #: Integrate actual region volume represented by the mesh.
        peaks = [math.sqrt(sum(x*x for x in result['fields']['B'][i])) for i in indices]  #: Use actual cell magnetic flux magnitude.
        result['regions'].append({'id': region['id'], 'name': region['name'], 'volume_m3': volume, 'mean_B_T': sum(v*result['fields']['measures'][i] for v, i in zip(peaks, indices))/volume if volume else 0, 'peak_B_T': max(peaks, default=0)})  #: Preserve standard region metrics without inventing values for omitted regions.
    result['native_refinement'] = {'history': history, 'stop_reason': stop, 'indicator_target': target, 'energy_target': energy_target, 'scope': 'operating point only; uncalibrated recovery estimator'}  #: Record stopping evidence explicitly even when pass/budget targets remain unmet.
    result['stats']['seconds'] = time.perf_counter()-started  #: Include unit-excitation postprocessing in complete elapsed time.
    return result  #: Return actual native solution and reproducible scope/evidence.
