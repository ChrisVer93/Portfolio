"""Conforming finite-loop current transfer into the reference H(curl) kernel."""
from collections import Counter, deque  #: Recover the true exterior and a boundary-collapsed spanning tree.
import copy  #: Detach every source, mesh and probe request from caller edits.
import itertools  #: Use the existing Freudenthal edge and tetrahedron orientation convention.
import math  #: Evaluate physical geometry, norms and explicit SI limits.

from .closed_loop import solve_loop  #: Retain the qualified closed copper current and same-source Biot-Savart probes.
from .dc_conduction import _direct_dc  #: Reuse the existing homogeneous-constraint SuperLU elimination and true-residual check.
from .mesh import dot, sub, tetra_geometry  #: Use the unchanged physical tetrahedron geometry and barycentric gradients.
from .project import number  #: Reject nonfinite, boolean and out-of-range SI inputs.
from .sparse import check_cancel  #: Cooperate with cancellation at bounded assembly stages.
from .spatial import SpatialSystem  #: Reuse the original lowest-order Nedelec curl-curl matrix and field/energy postprocessor.


class LoopSystem(SpatialSystem):  #: Change only exterior topology and gauge construction for the cylindrical verification domain.
    def __init__(self, project, mesh, reverse, cancel):  #: Select one of two reproducible spanning trees before original matrix assembly.
        self.reverse = reverse  #: Retain the explicit gauge ordering for the invariance check.
        super().__init__(project,mesh,cancel=cancel)  #: Assemble the unchanged reference Nedelec operator.

    def gauge(self):  #: Collapse every actual exterior vertex rather than assuming six Cartesian box faces.
        exterior = self.mesh['boundary_faces']  #: Use manifold exterior triangles recovered from all tetrahedra.
        boundary = {n for f in exterior for n in f}  #: Contract the connected outer boundary to one scalar gauge root.
        boundary_edges = {tuple(sorted(e)) for f in exterior for e in itertools.combinations(f,2)}  #: Constrain only edges actually lying on the exterior surface.
        fixed = {i for i,e in enumerate(self.edges) if e in boundary_edges}  #: Enforce homogeneous tangential vector potential.
        adjacency = [[] for _ in self.mesh['nodes']]  #: Build the exact complete edge graph.
        for e,(i,j) in enumerate(self.edges):  #: Preserve each global edge identity and its orientation.
            adjacency[i].append((j,e));adjacency[j].append((i,e))  #: Traverse physical mesh connectivity in either direction.
        seen = set(boundary);queue = deque(sorted(boundary,reverse=self.reverse));tree = set()  #: Seed the boundary-collapsed spanning tree deterministically.
        while queue:  #: Reach each interior vertex once.
            n = queue.popleft()  #: Expand one visited vertex.
            for other,e in sorted(adjacency[n],reverse=self.reverse):  #: Vary the spanning tree without changing physics, mesh or source.
                if other not in seen:  #: Add exactly one gradient constraint per new interior vertex.
                    seen.add(other);queue.append(other);tree.add(e)  #: Record the new vertex and its tree edge.
        if len(seen)!=len(adjacency) or len(tree)!=len(adjacency)-len(boundary):  #: Require a connected, fully reached contractible-domain mesh.
            raise ValueError('Loop magnetic gauge graph is disconnected')  #: Refuse an incomplete gradient-nullspace constraint.
        return fixed|tree,tree  #: Keep physical boundary conditions separate from the removable gauge edges.


def fit_mesh(source, radial, axial, holes, cancel=None):  #: Extend the exact source tetrahedra into conforming hole and exterior air.
    counts = source['input']['cells'];nt,nr,nz = counts  #: Retain original angular/radial/axial source ordering.
    original = source['mesh']['nodes_m']  #: Use exact stored source coordinates at every copper vertex.
    inner = [original[j*(nt+1)][0] for j in range(nr+1)]  #: Recover source radial planes without recomputing their rounding.
    zsource = [original[k*(nt+1)*(nr+1)][2] for k in range(nz+1)]  #: Recover exact source axial planes.
    radii = [inner[0]*j/holes for j in range(holes)]+inner+radial  #: Fill the hole and append explicitly requested exterior radial planes.
    zs = [-z for z in reversed(axial)]+zsource+axial  #: Extend both sides of the copper with explicit symmetric air planes.
    nrad,nzall = len(radii)-1,len(zs)-1  #: Count every physical annular band and axial slab.
    predicted = nt*(3+6*(nrad-1))*nzall  #: Central wedges have three tetrahedra; other hexahedra have six.
    if predicted>60000 or (1+nt*nrad)*len(zs)>30000:  #: Bound new verification mesh memory before allocating geometry or a matrix.
        raise ValueError('Conforming loop mesh exceeds 60000 tetrahedra or 30000 nodes')  #: Preserve explicit source-development budgets.
    nodes = [];lookup = {}  #: Retain unique welded mesh identities including one axis vertex per axial plane.
    for k,z in enumerate(zs):  #: Build each physical horizontal cross-section.
        for j,r in enumerate(radii):  #: Cover the entire filled cylinder rather than leaving a topological hole.
            for i in range(1 if j==0 else nt):  #: Weld all angular identities on the axis and at the 0/2pi seam.
                if holes<=j<=holes+nr and len(axial)<=k<=len(axial)+nz:  #: Preserve all copper coordinates bit-for-bit.
                    p = original[(k-len(axial))*(nt+1)*(nr+1)+(j-holes)*(nt+1)+i]  #: Bind the original DC vertex by its exact reference-grid identity.
                else:  #: Construct only the added air vertices.
                    angle = 2*math.pi*i/nt;p = (r*math.cos(angle),r*math.sin(angle),z)  #: Use straight-sided cylindrical air geometry in metres.
                lookup[i,j,k] = len(nodes);nodes.append(tuple(p))  #: Allocate one global node identity per physical grid vertex.
    def vertex(i,j,k):  #: Resolve seam and axis identifications for tetrahedron connectivity.
        return lookup[0 if j==0 else i%nt,j,k]  #: Weld coincident coordinates through topology rather than a distance search.
    source_map = {}  #: Bind each exact original copper tetrahedron to its welded global-node set.
    for t,cell in enumerate(source['mesh']['tetrahedra']):  #: Preserve all source-cell identities and RT0 values.
        mapped = [vertex(n%(nt+1),holes+(n//(nt+1))%(nr+1),len(axial)+n//((nt+1)*(nr+1))) for n in cell]  #: Apply the exact logical grid map to all four vertices.
        source_map[tuple(sorted(mapped))] = t  #: Use a complete vertex-set identity to forbid geometric nearest-cell guesses.
    cells = [];copper = [];faces = Counter()  #: Store complete physical volume topology and actual exterior incidence.
    for k in range(nzall):  #: Extrude every axial air or copper slab.
        check_cancel(cancel)  #: Stop before another bounded radial/angular assembly slice.
        for j in range(nrad):  #: Build both hole wedges and annular bands.
            for i in range(nt):  #: Cover the complete closed physical loop and surrounding cylinder.
                for permutation in itertools.permutations(range(3)):  #: Match the unchanged source Freudenthal subdivision.
                    p = [i,j,k];cell = [vertex(*p)]  #: Begin the monotone reference-cube path.
                    for axis in permutation:  #: Advance each logical coordinate once.
                        p[axis]+=1;cell.append(vertex(*p))  #: Append the corresponding physical vertex.
                    if len(set(cell))<4:continue  #: Remove only the analytically collapsed zero-volume axis tetrahedra.
                    cells.append(tuple(cell));copper.append(source_map.get(tuple(sorted(cell)),-1))  #: Bind exact source cells and tag all other cells as zero-current air.
                    faces.update(tuple(sorted(f)) for f in itertools.combinations(cell,3))  #: Recover actual shared and exterior triangles.
    if any(v>2 for v in faces.values()) or sorted(t for t in copper if t>=0)!=list(range(len(source_map))):  #: Require manifold connectivity and one exact copy of every source tetrahedron.
        raise ValueError('Conforming source-cell coverage or manifold topology failed')  #: Never publish an incomplete or duplicate current transfer.
    boundary = [f for f,n in faces.items() if n==1]  #: Identify the outer curved side and both end-cap surfaces.
    tolerance = max(radial[-1],axial[-1])*1e-10  #: Use a geometry-scaled roundoff tolerance for the actual exterior check.
    if any(not (all(abs(math.hypot(*nodes[n][:2])-radial[-1])<tolerance for n in f) or all(abs(nodes[n][2]-axial[-1])<tolerance for n in f) or all(abs(nodes[n][2]+axial[-1])<tolerance for n in f)) for f in boundary):  #: Require every exterior triangle to lie on the intended side or one end cap.
        raise ValueError('Magnetic mesh contains an unintended interior crack')  #: Prevent hidden internal boundaries from changing the physical field problem.
    edges = {tuple(sorted(e)) for c in cells for e in itertools.combinations(c,2)}  #: Bound the actual H(curl) dimension before matrix allocation.
    if len(edges)>80000:  #: Keep the separate reference pilot below its declared edge budget.
        raise ValueError('Conforming loop mesh exceeds 80000 edges')  #: Do not alter existing native-FEM budgets.
    return {'dimension':3,'nodes':nodes,'elements':cells,'tags':[-1]*len(cells),'boundary_faces':boundary,'boundary':sorted({n for f in boundary for n in f}),'copper_source_cell':copper}  #: Return a fully filled, source-conforming magnetic domain with deterministic JSON-safe boundary identities.


def solve_loop_fem(request, cancel=None):  #: Transfer a closed finite current into the unchanged magnetic reference formulation.
    if not isinstance(request,dict) or set(request)!={'source','radial_air_m','axial_air_m','hole_cells','gauge'}:  #: Keep this matched verification request separate from application project schemas.
        raise ValueError('Supply source, radial_air_m, axial_air_m, hole_cells and gauge')  #: Reject undeclared materials, sources or solver defaults.
    request = copy.deepcopy(request)  #: Preserve exact nested source and probe provenance.
    if type(request['hole_cells']) is not int or not 1<=request['hole_cells']<=16 or request['gauge'] not in ('forward','reverse'):  #: Bound the hole mesh and explicit gauge choice.
        raise ValueError('Use 1..16 hole cells and forward or reverse gauge')  #: Never choose an unreported gauge policy.
    source = solve_loop(request['source'],cancel)  #: Actually solve and close the finite copper current before magnetic transfer.
    for name,minimum in [('radial_air_m',source['input']['outer_radius_m']),('axial_air_m',source['input']['thickness_m']/2)]:  #: Validate both explicit outer-domain plane lists in metres.
        values = request[name]  #: Retain caller ordering for reproducible domain/refinement studies.
        if not isinstance(values,list) or not 1<=len(values)<=16:  #: Limit layered-domain complexity.
            raise ValueError('Air planes require 1..16 ordered coordinates')  #: Require a nonempty exterior air domain.
        previous = minimum  #: Begin strictly outside the physical copper.
        for value in values:  #: Check finite, increasing physical plane locations.
            number(value,'Air plane [m]',previous+1e-5,10);previous=value  #: Reject duplicates, reversed planes and zero air clearance.
    radius,height = request['radial_air_m'][-1],request['axial_air_m'][-1]  #: Use actual final radial and axial boundary locations.
    nt = source['input']['cells'][0]  #: Account for straight-sided polygonal domain boundaries.
    if any(math.hypot(*p[:2])>=radius*math.cos(math.pi/nt)-radius*1e-8 or abs(p[2])>=height-height*1e-8 for p in source['input']['probes_m']):  #: Require every magnetic observation strictly inside the fitted domain.
        raise ValueError('FEM probes must lie inside the magnetic air domain')  #: Do not extrapolate the computed volume field.
    mesh = fit_mesh(source,request['radial_air_m'],request['axial_air_m'],request['hole_cells'],cancel)  #: Weld the source seam and preserve every exact original copper tetrahedron.
    project = {'domain':{},'materials':[{'id':'air','mu_r':1.}],'regions':[],'windings':[]}  #: Use homogeneous mu0 and no ideal-sheet winding source in this matched pilot.
    system = LoopSystem(project,mesh,request['gauge']=='reverse',cancel)  #: Assemble the unchanged original curl-curl stiffness matrix.
    load = [0.]*system.n;recovered = source['conservative_current']  #: Build an independent finite-current edge load, without the old sheet-source basis.
    q1,q2 = (5+3*math.sqrt(5))/20,(5-math.sqrt(5))/20  #: Use degree-two exact tetrahedral source-times-edge quadrature.
    for count,((tet,vol,nu,ids,curls,grads,pairs),tag) in enumerate(zip(system.data,mesh['copper_source_cell'])):  #: Visit every actual magnetic cell and its exact source binding.
        if count%256==0:check_cancel(cancel)  #: Check cancellation during finite-current assembly.
        if tag<0:continue  #: Assign exactly zero impressed current in added air.
        center = [sum(mesh['nodes'][n][d] for n in tet)/4 for d in range(3)]  #: Locate the original source centroid on the matching magnetic tetrahedron.
        for vertex in range(4):  #: Integrate all four symmetric source quadrature points.
            lambdas = [q1 if k==vertex else q2 for k in range(4)]  #: Retain the complete affine basis coordinates.
            p = [sum(lambdas[k]*mesh['nodes'][tet[k]][d] for k in range(4)) for d in range(3)]  #: Evaluate the physical source point on the exact matched cell.
            current = [j+recovered['divergence_A_m3'][tag]*(x-y)/3 for j,x,y in zip(recovered['current_density_at_cell_centroid_A_m2'][tag],p,center)]  #: Transfer the full RT0 field including its roundoff-sized divergence term.
            for edge,(i,j) in zip(ids,pairs):  #: Use the original globally oriented Nedelec basis functions.
                load[edge] += vol*.25*sum(current[d]*(lambdas[i]*grads[j][d]-lambdas[j]*grads[i][d]) for d in range(3))  #: Assemble integral J dot v in amperes with degree-two exactness.
    gradient = [0.]*len(mesh['nodes'])  #: Independently test source orthogonality to every nodal gradient.
    for value,(i,j) in zip(load,system.edges):  #: Apply the exact oriented edge-to-vertex incidence transpose.
        gradient[i]-=value;gradient[j]+=value  #: Compute G-transpose times the current load.
    norm = math.sqrt(math.fsum(v*v for v in load));compatibility = math.sqrt(math.fsum(v*v for v in gradient))/max(norm,1e-30)  #: Normalize source-gradient incompatibility independently of the magnetic solve.
    if compatibility>1e-9:  #: Fail before solving an incompatible curl-curl equation.
        raise RuntimeError('Transferred finite current is incompatible with discrete gradients')  #: Never hide a charge defect with gauge regularisation.
    a,info = _direct_dc(system.rows,load,system.fixed,cancel)  #: Reuse homogeneous-constraint sparse elimination with its true free-row residual check.
    residual = [math.fsum(v*a[j] for j,v in system.rows[i].items())-load[i] for i in system.tree]  #: Evaluate every omitted interior gauge equation afterwards.
    gauge_residual = math.sqrt(math.fsum(v*v for v in residual))/max(norm,1e-30)  #: Normalize the independent omitted-equation check.
    if gauge_residual>1e-7:raise RuntimeError('Finite-current magnetic gauge equations failed')  #: Reject an inaccurate or physically incompatible solution.
    post = system.post(a);work = math.fsum(x*y for x,y in zip(load,a))/2  #: Compute B-volume energy and independent one-half source work.
    energy_error = abs(post['energy_J']-work)/max(abs(work),1e-30)  #: Check the stationary energy identity without asserting mesh accuracy.
    if energy_error>1e-8:raise RuntimeError('Finite-current magnetic energy identity failed')  #: Refuse inconsistent field/source postprocessing.
    probes = []  #: Preserve exact requested observation ordering.
    for point,direct in zip(source['input']['probes_m'],source['magnetic_field']):  #: Compare the PDE field with the same finite-source Biot-Savart field.
        candidates = [(vol,b) for (tet,vol,nu,ids,curls,grads,pairs),b in zip(system.data,post['B']) if all(1+dot(g,sub(point,mesh['nodes'][n]))>=-1e-9 for n,g in zip(tet,grads))]  #: Locate all incident tetrahedra, including a point on a face, edge or axis vertex.
        if not candidates:raise RuntimeError('FEM probe could not be located')  #: Never silently extrapolate or substitute a reference value.
        volume = math.fsum(v for v,b in candidates);field = [math.fsum(v*b[d] for v,b in candidates)/volume for d in range(3)]  #: Define the sample as a volume-weighted trace average of incident constant-curl fields.
        denominator = math.sqrt(dot(direct['B_T'],direct['B_T']))  #: Retain a true vector norm for the independent same-source comparison.
        probes.append({'point_m':point,'B_T':field,'incident_cells':len(candidates),'same_source_Biot_Savart_B_T':direct['B_T'],'relative_vector_difference':math.dist(field,direct['B_T'])/denominator if denominator else None})  #: Preserve actual PDE samples and explicit zero-field undefined normalization.
    current = source['terminal_current_into_conductor_A']['high']  #: Use the solved signed cut circulation for this one fixed current mode.
    inductance = 2*post['energy_J']/current**2 if current else None  #: Define the linear source-mode energy inductance in henries; leave zero-current normalization undefined.
    linkage = 2*work/current if current else None  #: Contract the source-mode vector potential into a signed linkage in webers.
    return {'format':'magnetics-studio.closed-loop-fem/1','input':request,'source':source,'mesh':mesh,'edges':system.edges,'edge_A_Wb':a,'B_T':post['B'],'energy_J':post['energy_J'],'half_source_work_J':work,'energy_inductance_H':inductance,'source_mode_linkage_Wb':linkage,'relative_energy_identity_error':energy_error,'source_gradient_compatibility':compatibility,'omitted_gauge_residual':gauge_residual,'gauge_tree_edges':sorted(system.tree),'boundary_condition':'Homogeneous tangential A on the complete finite cylindrical boundary','solver':info,'probes':probes}  #: Return exact transfer topology, field, single-mode magnetic quantities, gauge/source checks and finite-boundary limitations.
