"""Pinned NGSolve mixed-gauge verification of a matched finite-loop source."""
from importlib import metadata  #: Check the exact optional native runtime before importing compiled code.
import math  #: Evaluate oriented physical volume, vector norms and fixed mu0 units.
import os  #: Honor the explicit standard-library-only execution profile.

from .mesh import cross, dot, sub, tetra_geometry  #: Preserve the same exact physical source and magnetic tetrahedra.
from .sparse import check_cancel  #: Cooperate with cancellation between bounded native phases.


def solve_native_transfer(reference, order=2, full_gradients=False, cancel=None, flux_surfaces=None):  #: Apply the native mixed formulation and optional signed pickup flux to a checked source/mesh frame.
    if os.environ.get('MAGNETICS_PURE_PYTHON')=='1':raise ValueError('Native loop transfer requires the SciPy-enabled native profile')  #: Never enable compiled dependencies under an explicit pure-Python request.
    if not isinstance(reference,dict) or reference.get('format') not in ('magnetics-studio.closed-loop-fem/1','magnetics-studio.loop-transfer/1') or type(order) is not int or order not in (0,2,3) or type(full_gradients) is not bool:  #: Accept an actual reference result or an explicitly checked geometry/current transfer frame, retaining native order and gauge limits.
        raise ValueError('Use a checked loop FEM result, order 0/2/3 and a boolean gradient option')  #: Refuse unsupported input without guessing a source model.
    from .surface_flux import build_surface_plan,integrate_surface_plan  #: Integrate optional signed pickup flux from genuine native fields on clipped cell patches.
    flux_plan=build_surface_plan(reference['mesh'],flux_surfaces,cancel) if flux_surfaces is not None else []  #: Validate complete pickup coverage before allocating a native FEM solve.
    for package,version in [('ngsolve','6.2.2608'),('netgen-mesher','6.2.2608'),('netgen-occt','7.8.1')]:  #: Preserve the qualified compiled geometry and FEM combination.
        if metadata.version(package)!=version:raise ValueError('Native loop verification requires '+package+'=='+version)  #: Reject a silently changed native implementation.
    import numpy as np  #: Interpolate the exact affine source into native discontinuous local basis coefficients.
    import ngsolve as ng  #: Use the established high-order H(curl) operator and mixed-space solver.
    from netgen.meshing import Mesh, MeshPoint, Element3D, Element2D, FaceDescriptor  #: Transfer exact existing topology without generating a different mesh.
    from netgen.csg import Pnt  #: Construct native physical coordinates in metres.
    ng.SetNumThreads(1)  #: Keep this bounded qualification process deterministic and single-threaded.
    meshdata = reference['mesh'];source = reference['source'];nodes = meshdata['nodes'];cells = meshdata['elements']  #: Retain the same copper, return and exterior air cells as the reference solve.
    if len(cells)>60000 or len(nodes)>30000 or len(meshdata['copper_source_cell'])!=len(cells):  #: Reapply the declared transfer memory and coverage limits.
        raise ValueError('Native loop transfer mesh budget or source coverage failed')  #: Do not accept an unbounded detached result.
    check_cancel(cancel)  #: Stop before allocating compiled mesh or finite-element spaces.
    raw = Mesh(dim=3);vertices = [raw.Add(MeshPoint(Pnt(*p))) for p in nodes]  #: Preserve all physical points and their explicit identities.
    for i,cell in enumerate(cells):  #: Transfer every existing tetrahedron rather than remeshing around the source.
        if i%256==0:check_cancel(cancel)  #: Honor cancellation during native topology construction.
        c = list(cell);p = [nodes[n] for n in c]  #: Retain the physical vertex set while correcting native orientation.
        if dot(sub(p[1],p[0]),cross(sub(p[2],p[0]),sub(p[3],p[0])))>0:c[0],c[1]=c[1],c[0]  #: Use Netgen's tetrahedron orientation convention without changing geometry.
        raw.Add(Element3D(index=1,vertices=[vertices[n] for n in c]))  #: Keep one physical homogeneous magnetic material region.
    raw.SetMaterial(1,'mu0');descriptor = raw.Add(FaceDescriptor(surfnr=1,domin=1,bc=1));raw.SetBCName(0,'outer')  #: Bind the complete actual exterior to one named tangential-A condition.
    for face in meshdata['boundary_faces']:  #: Preserve every fitted side and end-cap triangle.
        raw.Add(Element2D(index=descriptor,vertices=[vertices[n] for n in face]))  #: Avoid boundary inference from coordinate thresholds.
    mesh = ng.Mesh(raw)  #: Construct the compiled FEM mesh from the exact transferred topology.
    if [tuple(v.point) for v in mesh.vertices]!=[tuple(p) for p in nodes]:  #: Require explicit node-identity preservation before binding source cells.
        raise RuntimeError('Native mesh reordered or altered source coordinates')  #: Never substitute a nearest-neighbour source map.
    measured = ng.Integrate(1,mesh);expected = math.fsum(tetra_geometry([nodes[n] for n in cell])[0] for cell in cells)  #: Independently compare native and reference physical volume measures.
    if abs(measured/expected-1)>1e-11:raise RuntimeError('Native tetrahedron volume transfer failed')  #: Reject orientation, scaling or topology discrepancies.
    field = ng.HCurl(mesh,order=order,nograds=not full_gradients,dirichlet='outer')  #: Select the declared high-order curl space and optional removal of higher gradient modes.
    scalar = ng.H1(mesh,order=order+1 if full_gradients else 1,dirichlet='outer')  #: Match the remaining gradient kernel with an exact mixed gauge constraint.
    space = field*scalar  #: Use a saddle-point gauge rather than an added magnetic mass penalty.
    if space.ndof>45000:raise ValueError('Native mixed loop space exceeds 45000 DOFs')  #: Preserve the existing native solve-size ceiling for this pilot.
    dg = ng.L2(mesh,order=1);components = [ng.GridFunction(dg) for _ in range(3)]  #: Represent the physical RT0 current as an exact elementwise affine vector field.
    mapping = {tuple(sorted(cell)):tag for cell,tag in zip(cells,meshdata['copper_source_cell'])}  #: Match source ownership by all four global node identities.
    rule = ng.IntegrationRule(ng.ET.TET,2);recovered = source['conservative_current'];seen = set()  #: Use four independent physical points to interpolate each source cell exactly.
    for element in mesh.Elements(ng.VOL):  #: Permit native element traversal order to differ from the original source order.
        key = tuple(sorted(v.nr for v in element.vertices))  #: Identify the exact physical tetrahedron, independent of orientation.
        if key not in mapping or key in seen:raise RuntimeError('Native source-cell identity mismatch')  #: Reject missing, duplicated or changed native volume topology.
        seen.add(key);tag = mapping[key]  #: Retain explicit zero-current air and the exact original copper-cell index.
        if tag<0:continue  #: Leave all added air current coefficients exactly zero.
        points = np.asarray(ng.CF((ng.x,ng.y,ng.z))(mesh.GetTrafo(element)(rule)))  #: Evaluate the native physical interpolation points in metres.
        center = np.mean([source['mesh']['nodes_m'][n] for n in source['mesh']['tetrahedra'][tag]],axis=0)  #: Recover the matching source-cell datum directly from its original mesh.
        values = np.asarray(recovered['current_density_at_cell_centroid_A_m2'][tag])+recovered['divergence_A_m3'][tag]*(points-center)/3  #: Evaluate the full conservative affine source without centroid-only approximation.
        basis = np.asarray([dg.GetFE(element).CalcShape(*point.point) for point in rule])  #: Read the exact local native discontinuous scalar basis.
        coefficients = np.linalg.solve(basis,values);dofs = list(dg.GetDofNrs(element))  #: Interpolate the three affine physical components in that actual basis.
        for d,g in enumerate(components):g.vec.FV().NumPy()[dofs]=coefficients[:,d]  #: Bind each component only to this cell's independent discontinuous coefficients.
    if len(seen)!=len(cells):raise RuntimeError('Incomplete native current transfer')  #: Require every original magnetic cell to be present once.
    current = ng.CF(tuple(components));mu0 = 4*math.pi*1e-7  #: Use the exact same declared free-space magnetic material constant.
    (u,p),(v,q) = space.TnT();form = ng.BilinearForm(space,symmetric=True)  #: Build the mixed vector-potential and scalar gauge formulation.
    form += (ng.curl(u)*ng.curl(v)+ng.grad(p)*v+ng.grad(q)*u)/mu0*ng.dx(bonus_intorder=4)  #: Assemble curl energy and exact gauge constraints without artificial magnetic energy.
    load = ng.LinearForm(space);load += current*v*ng.dx(bonus_intorder=4)  #: Integrate the actual full finite-copper current against native edge test functions.
    check_cancel(cancel);form.Assemble();load.Assemble()  #: Assemble the physical source and coupled sparse mixed system.
    gradient_space = ng.H1(mesh,order=order+1,dirichlet='outer');gradient = ng.LinearForm(gradient_space)  #: Independently test compatibility against the complete higher-order nodal gradient space.
    gradient += current*ng.grad(gradient_space.TestFunction())*ng.dx(bonus_intorder=4);gradient.Assemble()  #: Measure every weak discrete charge constraint on the transferred affine current.
    norm = float(np.linalg.norm(load.vec.FV().NumPy()));compatibility = float(np.linalg.norm(gradient.vec.FV().NumPy()))/max(norm,1e-30)  #: Normalize charge incompatibility before solving the magnetic system.
    if compatibility>1e-9:raise RuntimeError('Native source is incompatible with discrete gradients')  #: Refuse to conceal source defects through a gauge variable.
    potential = ng.GridFunction(space);potential.vec.data = form.mat.Inverse(space.FreeDofs(),inverse='umfpack')*load.vec  #: Solve the actual bounded symmetric-indefinite mixed system with sparse UMFPACK.
    check_cancel(cancel)  #: Honor cancellation before evaluating or publishing native results.
    residual_vector = load.vec.CreateVector();residual_vector.data = form.mat*potential.vec-load.vec  #: Materialize the native residual expression into an owned vector.
    residual = residual_vector.FV().NumPy();free = np.asarray(list(space.FreeDofs()),dtype=bool)  #: Recompute the true assembled-system residual on every free physical and gauge row.
    relative_residual = float(np.linalg.norm(residual[free]))/max(norm,1e-30)  #: Record a true residual rather than an iterative recurrence estimate.
    if relative_residual>1e-8:raise RuntimeError('Native mixed loop residual failed')  #: Reject an inaccurate sparse solve.
    magnetic = ng.curl(potential.components[0]);energy = ng.Integrate(magnetic*magnetic/(2*mu0),mesh,order=2*order+4)  #: Integrate physical magnetic energy using the full high-order field.
    work = ng.Integrate(current*potential.components[0]/2,mesh,order=2*order+4);identity = abs(energy-work)/max(abs(work),1e-30)  #: Independently integrate one-half source work without any gauge-energy term.
    if identity>1e-8:raise RuntimeError('Native magnetic energy identity failed')  #: Require consistent physical source and field energy.
    probes = []  #: Use the same defined incident-cell trace-average observation operator as the reference pilot.
    for point,direct in zip(source['input']['probes_m'],source['magnetic_field']):  #: Retain the exact requested point and same-source free-space comparison.
        samples = []  #: Evaluate each incident native field trace on its own interior side.
        for cell in cells:  #: Locate candidate cells independently of native point-finder tie breaking.
            volume,grads = tetra_geometry([nodes[n] for n in cell])  #: Recover physical barycentric gradients and measure.
            if not all(1+dot(g,sub(point,nodes[n]))>=-1e-9 for n,g in zip(cell,grads)):continue  #: Exclude cells not containing the requested observation.
            center = [sum(nodes[n][d] for n in cell)/4 for d in range(3)]  #: Define an interior direction for a point lying on an interface.
            interior = [x+1e-7*(y-x) for x,y in zip(point,center)]  #: Approach the incident trace at a declared tiny relative interior offset.
            samples.append((volume,list(magnetic(mesh(*interior)))))  #: Evaluate the genuine high-order native field, not the reference field or a fitted analytical value.
        if not samples:raise RuntimeError('Native magnetic probe is outside transferred mesh')  #: Refuse silent extrapolation.
        volume = math.fsum(w for w,b in samples);value = [math.fsum(w*b[d] for w,b in samples)/volume for d in range(3)]  #: Apply the defined volume-weighted trace average to the native field.
        denominator = math.sqrt(dot(direct['B_T'],direct['B_T']))  #: Preserve a complete vector norm for the same-source comparison.
        probes.append({'point_m':list(point),'B_T':value,'incident_cells':len(samples),'relative_vector_difference':math.dist(value,direct['B_T'])/denominator if denominator else None})  #: Keep zero-drive normalization undefined and probe provenance detached.
    cell_fields = [list(magnetic(mesh(*(sum(nodes[n][d] for n in cell)/4 for d in range(3))))) for cell in cells]  #: Preserve genuine native volume-field samples at every original cell centroid.
    surface_flux=integrate_surface_plan(flux_plan,lambda cell,point:magnetic(mesh(*point)),cancel)  #: Evaluate actual high-order normal fields at every clipped physical quadrature point.
    circulation = source['terminal_current_into_conductor_A']['high']  #: Normalize only the solved closed one-turn current mode.
    return {'format':'magnetics-studio.native-loop-transfer/1','ngsolve_version':ng.__version__,'order':order,'full_gradients':full_gradients,'mixed_dofs':space.ndof,'gradient_test_dofs':gradient_space.ndof,'native_volume_m3':measured,'relative_volume_transfer_error':abs(measured/expected-1),'source_gradient_compatibility':compatibility,'relative_residual':relative_residual,'energy_J':energy,'half_source_work_J':work,'relative_energy_identity_error':identity,'energy_inductance_H':2*energy/circulation**2 if circulation else None,'source_mode_linkage_Wb':2*work/circulation if circulation else None,'hcurl_coefficients':potential.components[0].vec.FV().NumPy().tolist(),'gauge_coefficients':potential.components[1].vec.FV().NumPy().tolist(),'B_at_cell_centroids_T':cell_fields,'probes':probes,'probe_interior_fraction':1e-7,'surface_flux':surface_flux}  #: Return the actual native solution, source/gauge/energy checks, volume fields, point conventions and signed pickup flux.
