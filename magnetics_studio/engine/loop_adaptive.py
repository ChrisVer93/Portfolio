"""Native residual-driven refinement with exact parent-affine current transfer."""
from collections import Counter  #: Independently verify the refined tetrahedral exterior.
import copy  #: Preserve accepted fields and caller-owned request data.
import itertools  #: Recover faces, edge lengths and native tetrahedron topology.
import math  #: Evaluate physical current residuals, flux jumps and energy changes.
from .loop_fem import solve_loop_fem  #: Validate the initial request and retain a genuinely solved reference baseline.
from .loop_native import solve_native_transfer  #: Solve the same current with the pinned native mixed-gauge operator.
from .mesh import cross,dot,sub,tetra_geometry  #: Use physical cell geometry and source barycentric gradients.
from .project import number  #: Enforce explicit finite option limits.
from .sparse import check_cancel  #: Preserve cooperative cancellation between bounded phases.


def bind_source(source, mesh, cancel=None):  #: Bind nested child cells to complete original source tetrahedra without changing the current field.
    import numpy as np  #: Bound candidate search memory while testing exact physical containment.
    old = source['mesh'];points=np.asarray(old['nodes_m'])[old['tetrahedra']]  #: Read the original unmodified finite-current source geometry.
    coordinates=np.asarray(mesh['nodes'],dtype=float)  #: Check the complete candidate coordinate array before containment arithmetic.
    if coordinates.ndim!=2 or coordinates.shape[1]!=3 or not np.all(np.isfinite(coordinates)):raise ValueError('Adaptive mesh coordinates must be finite three-vectors')  #: Reject nonfinite geometry before a NaN can evade a tolerance check.
    if len(points)>1536 or len(mesh['elements'])>60000 or len(mesh['nodes'])>30000:  #: Limit this nested-source verification adapter independently of original application budgets.
        raise ValueError('Adaptive source binding exceeds 1536 source cells, 60000 cells or 30000 nodes')  #: Reject unbounded geometry before candidate searches.
    mins,maxs=points.min(axis=1),points.max(axis=1);geometry=[tetra_geometry(p) for p in points]  #: Retain source bounding boxes and exact affine barycentric gradients.
    children=[0.]*len(points);tags=[];scale=float(np.max(maxs-mins));tolerance=1e-10*scale  #: Accumulate physical volume coverage for every original current cell.
    seen=set()  #: Reject duplicate refined volume cells rather than masking them by summed volumes.
    for index,cell in enumerate(mesh['elements']):  #: Match every refined cell to its exact source parent or zero-current air.
        if index%256==0:check_cancel(cancel)  #: Stop during potentially long containment checks.
        if len(cell)!=4 or any(type(n) is not int or not 0<=n<len(mesh['nodes']) for n in cell) or len(set(cell))!=4 or tuple(sorted(cell)) in seen:  #: Require unique valid tetrahedral topology.
            raise ValueError('Invalid or duplicate adaptive tetrahedron')  #: Never accept a duplicated or escaped source volume.
        seen.add(tuple(sorted(cell)));vertices=np.asarray([mesh['nodes'][n] for n in cell]);center=vertices.mean(axis=0)  #: Recover the actual child geometry and interior point.
        volume,_=tetra_geometry(vertices);candidates=np.flatnonzero(np.all(center>=mins-tolerance,axis=1)&np.all(center<=maxs+tolerance,axis=1))  #: Use bounding boxes only as a broad-phase filter.
        parents=[]  #: Require actual barycentric containment rather than nearest-centroid interpolation.
        for parent in candidates:  #: Test each possible original source tetrahedron.
            grads=np.asarray(geometry[parent][1]);barycentric=1+np.sum(grads*(center-points[parent]),axis=1)  #: Evaluate all four source barycentric coordinates at the child interior point.
            if np.min(barycentric)>=-1e-9:parents.append(int(parent))  #: Retain only source cells that actually contain the child centroid.
        if len(parents)>1:raise ValueError('Ambiguous adaptive source parent')  #: Reject overlapping or inconsistent original source geometry.
        tag=parents[0] if parents else -1;tags.append(tag)  #: Mark genuine added air with exactly zero current.
        if tag>=0:  #: Preserve the original parent-affine current throughout this copper child.
            barycentric=1+np.sum(np.asarray(geometry[tag][1])[None,:,:]*(vertices[:,None,:]-points[tag][None,:,:]),axis=2)  #: Check every child vertex against all original parent faces.
            if np.min(barycentric)<-1e-8:raise ValueError('Adaptive cell crosses the original current interface')  #: Refuse nonconforming source interpolation across a current discontinuity.
            children[tag]+=volume  #: Measure actual copper coverage of this exact original source cell.
    errors=[abs(v/geometry[i][0]-1) for i,v in enumerate(children)]  #: Independently test complete parent-by-parent source volume conservation.
    if max(errors,default=0)>1e-9:raise ValueError('Adaptive source volume coverage failed')  #: Never silently lose copper or replace it with air.
    return tags,{'source_cells':len(points),'copper_children':sum(t>=0 for t in tags),'max_relative_parent_volume_error':max(errors,default=0)}  #: Return explicit ownership and independently measured source-preservation evidence.


def residual_indicators(frame, solution, cancel=None):  #: Compute lowest-order curl residual and interior tangential-H jump indicators in joules.
    if solution.get('order')!=0:raise ValueError('Residual marking currently requires native order zero')  #: Avoid applying a constant-field residual formula to a higher-order field.
    mesh=frame['mesh'];source=frame['source'];current=source['conservative_current'];mu0=4*math.pi*1e-7  #: Retain identical physical material and current conventions.
    fields=solution['B_at_cell_centroids_T']  #: For native order zero these are the complete constant curl fields.
    if len(fields)!=len(mesh['elements']):raise ValueError('Indicator field/mesh mismatch')  #: Reject stale volume fields before marking cells.
    eta=[0.]*len(fields);owners={};q1,q2=(5+3*math.sqrt(5))/20,(5-math.sqrt(5))/20  #: Initialize cell indicators and degree-two current integration.
    for t,(cell,tag) in enumerate(zip(mesh['elements'],mesh['copper_source_cell'])):  #: Evaluate every actual accepted cell and source parent.
        if t%256==0:check_cancel(cancel)  #: Honor cancellation during residual evaluation.
        p=[mesh['nodes'][n] for n in cell];volume,_=tetra_geometry(p);diameter=max(math.dist(a,b) for a,b in itertools.combinations(p,2))  #: Use actual physical cell diameter and volume.
        for face in itertools.combinations(cell,3):owners.setdefault(tuple(sorted(face)),[]).append(t)  #: Recover actual shared faces for flux-jump measurements.
        if tag<0:continue  #: The constant-field volume curl residual is zero in current-free air.
        center=[sum(source['mesh']['nodes_m'][n][d] for n in source['mesh']['tetrahedra'][tag])/4 for d in range(3)]  #: Use the original parent datum for the exact affine current.
        squared=0.  #: Integrate |J| squared rather than a centroid-only surrogate.
        for vertex in range(4):  #: Apply the symmetric degree-two tetrahedron rule.
            point=[sum((q1 if k==vertex else q2)*p[k][d] for k in range(4)) for d in range(3)]  #: Map each quadrature point into the refined copper cell.
            vector=[j+current['divergence_A_m3'][tag]*(x-y)/3 for j,x,y in zip(current['current_density_at_cell_centroid_A_m2'][tag],point,center)]  #: Evaluate the exact retained parent-affine current.
            squared+=dot(vector,vector)/4  #: Accumulate the exact polynomial current-residual integral.
        eta[t]+=mu0*diameter**2*volume*squared  #: Since curl H is zero inside an order-zero cell, the volume residual is minus J.
    for face,cells in owners.items():  #: Measure the actual interior tangential-H discontinuity.
        if len(cells)>2:raise ValueError('Nonmanifold adaptive indicator mesh')  #: Reject invalid shared-face topology.
        if len(cells)!=2:continue  #: Essential tangential-A exterior faces do not receive an interior-jump term.
        p=[mesh['nodes'][n] for n in face];normal=cross(sub(p[1],p[0]),sub(p[2],p[0]));length=math.sqrt(dot(normal,normal))  #: Compute the physical face normal and area measure.
        normal=tuple(v/length for v in normal);jump=tuple((a-b)/mu0 for a,b in zip(fields[cells[0]],fields[cells[1]]))  #: Evaluate the same-oriented H jump across the face.
        tangential=cross(normal,jump);diameter=max(math.dist(a,b) for a,b in itertools.combinations(p,2))  #: Use the tangential jump and actual face diameter.
        value=mu0*diameter*length/2*dot(tangential,tangential)  #: Integrate the constant tangential-H jump with physical joule scaling.
        for t in cells:eta[t]+=value/2  #: Count each shared-face contribution once globally and split it equally between owners.
    return eta  #: These residual proxies drive marking; no reliability constant or certified error bound is claimed.


def refine_frame(frame, marked, cancel=None):  #: Let pinned Netgen refine a detached mesh and rebind every child to its original source.
    import ngsolve as ng  #: Use the established conforming local-refinement implementation.
    from netgen.meshing import Mesh,MeshPoint,Element3D,Element2D,FaceDescriptor  #: Transfer the exact accepted geometry before setting refinement flags.
    from netgen.csg import Pnt  #: Preserve physical SI coordinates.
    check_cancel(cancel);old=frame['mesh'];raw=Mesh(dim=3);vertices=[raw.Add(MeshPoint(Pnt(*p))) for p in old['nodes']]  #: Construct a separate candidate rather than mutate the accepted field mesh.
    keys={tuple(sorted(c)):i for i,c in enumerate(old['elements'])}  #: Map native traversal back to actual accepted cell identities.
    for cell in old['elements']:  #: Preserve each old physical tetrahedron and its volume.
        c=list(cell);p=[old['nodes'][n] for n in c]  #: Correct orientation without changing any vertex position.
        if dot(sub(p[1],p[0]),cross(sub(p[2],p[0]),sub(p[3],p[0])))>0:c[0],c[1]=c[1],c[0]  #: Match Netgen's tetrahedron orientation convention.
        raw.Add(Element3D(index=1,vertices=[vertices[n] for n in c]))  #: Keep one homogeneous physical magnetic material.
    raw.SetMaterial(1,'mu0');fd=raw.Add(FaceDescriptor(surfnr=1,domin=1,bc=1));raw.SetBCName(0,'outer')  #: Preserve the exact physical exterior boundary condition.
    for face in old['boundary_faces']:raw.Add(Element2D(index=fd,vertices=[vertices[n] for n in face]))  #: Transfer all accepted exterior triangles.
    native=ng.Mesh(raw)  #: Create the detached native candidate with no remeshing or geometric projection.
    for cell in native.Elements(ng.VOL):native.SetRefinementFlag(cell,keys[tuple(sorted(v.nr for v in cell.vertices))] in marked)  #: Mark the actual selected physical cells independently of native traversal order.
    native.Refine();check_cancel(cancel)  #: Run native local bisection and conformity closure, then honor cancellation.
    if native.ne>60000 or native.nv>30000:raise ValueError('Adaptive source binding exceeds candidate mesh budget')  #: Stop before constructing Python face tables for an oversized refinement.
    nodes=[tuple(v.point) for v in native.vertices];cells=[tuple(v.nr for v in e.vertices) for e in native.Elements(ng.VOL)]  #: Extract genuine refined volume topology and physical points.
    faces=Counter(tuple(sorted(f)) for c in cells for f in itertools.combinations(c,3));boundary=[f for f,n in faces.items() if n==1]  #: Independently recover the refined manifold exterior.
    if any(n>2 for n in faces.values()):raise ValueError('Native refinement produced a nonmanifold volume mesh')  #: Reject invalid geometry before a candidate magnetic solve.
    surface={tuple(sorted(v.nr for v in e.vertices)) for e in native.Elements(ng.BND)}  #: Read native exterior labels independently of volume incidence.
    if set(boundary)!=surface:raise ValueError('Native refinement exterior mismatch')  #: Reject interior cracks or missing boundary labels.
    old_volume=math.fsum(tetra_geometry([old['nodes'][n] for n in c])[0] for c in old['elements']);new_volume=math.fsum(tetra_geometry([nodes[n] for n in c])[0] for c in cells)  #: Independently compare physical magnetic-domain volume before and after refinement.
    if abs(new_volume/old_volume-1)>1e-10:raise ValueError('Adaptive magnetic-domain volume changed')  #: Keep source and air-domain refinement distinct from boundary movement.
    mesh={'dimension':3,'nodes':nodes,'elements':cells,'tags':[-1]*len(cells),'boundary_faces':boundary,'boundary':sorted({n for f in boundary for n in f})}  #: Store a JSON-safe complete refined magnetic mesh.
    tags,proof=bind_source(frame['source'],mesh,cancel);mesh['copper_source_cell']=tags  #: Require exact nested source containment and complete parent volume coverage.
    proof['relative_domain_volume_error']=abs(new_volume/old_volume-1)  #: Record actual fixed-domain preservation alongside parent-current coverage.
    return {'format':'magnetics-studio.loop-transfer/1','input':copy.deepcopy(frame['input']),'source':frame['source'],'mesh':mesh},proof  #: Return a separate geometry/current frame without inventing a reference field solve.


def solve_adaptive_loop(request, cancel=None):  #: Solve, estimate, bulk-mark and refine a fixed physical finite-current mode.
    if not isinstance(request,dict) or set(request)!={'model','max_passes','bulk_fraction','indicator_target','energy_target'}:raise ValueError('Supply model and explicit adaptive pass/bulk/indicator/energy controls')  #: Keep the adaptive request distinct from all original application schemas.
    request=copy.deepcopy(request);passes=request['max_passes']  #: Detach all nested model and probe arrays before solving.
    if type(passes) is not int or not 1<=passes<=4:raise ValueError('Use 1..4 adaptive passes')  #: Preserve the current bounded native pilot pass range.
    bulk=number(request['bulk_fraction'],'Bulk fraction',.1,.9);target=number(request['indicator_target'],'Indicator target',.001,1);energy_target=number(request['energy_target'],'Energy target',1e-5,.2)  #: Validate finite explicit stopping and marking controls.
    check_cancel(cancel);initial=solve_loop_fem(request['model'],cancel);frame={'format':'magnetics-studio.loop-transfer/1','input':initial['input'],'source':initial['source'],'mesh':initial['mesh']}  #: Retain a real reference baseline and an honestly typed source-transfer frame.
    tags,proof=bind_source(frame['source'],frame['mesh'],cancel);frame['mesh']['copper_source_cell']=tags  #: Check the initial source contract before any adaptive native solve.
    history=[];previous=None;stop='pass_limit'  #: Keep actual accepted solutions and unmet stopping criteria explicit.
    for step in range(passes):  #: Execute only the user-declared bounded number of real solve passes.
        check_cancel(cancel)  #: Never substitute partial fields for an interrupted operation.
        try:solution=solve_native_transfer(frame,0,cancel=cancel)  #: Solve the actual current mesh with the qualified lowest-order mixed formulation.
        except ValueError as error:  #: Retain an earlier accepted field only for the explicit native DOF ceiling.
            if history and str(error)=='Native mixed loop space exceeds 45000 DOFs':stop='budget_limit';break  #: Distinguish resource exhaustion from convergence or a failed source check.
            raise  #: Propagate all unexpected model, dependency and numerical failures.
        indicators=residual_indicators(frame,solution,cancel);total=math.fsum(indicators);energy=solution['energy_J'];relative=math.sqrt(total/max(2*energy,1e-30))  #: Normalize the residual proxy without claiming it equals true error.
        change=abs(energy/previous-1) if previous else None;record={'pass':step+1,'tetrahedra':len(frame['mesh']['elements']),'mixed_dofs':solution['mixed_dofs'],'energy_J':energy,'energy_inductance_H':solution['energy_inductance_H'],'relative_residual_indicator':relative,'relative_energy_change':change,'source_binding':proof,'source_gradient_compatibility':solution['source_gradient_compatibility'],'probes':solution['probes'],'mesh':frame['mesh'],'cell_B_T':solution['B_at_cell_centroids_T']}  #: Retain actual field, energy, source-conservation and stopping evidence for each solved mesh.
        history.append(record);accepted_frame=frame;accepted_solution=solution;previous=energy  #: Accept only a completely solved, checked and measured candidate.
        if frame['source']['terminal_current_into_conductor_A']['high']==0:stop='zero_source';break  #: Leave zero-current inductance undefined and avoid meaningless refinement.
        if relative<=target and change is not None and change<=energy_target:stop='targets_met';break  #: Require both implemented heuristic targets before reporting their completion.
        if step+1==passes:break  #: Never refine a candidate that will not be solved.
        marked=[];mass=0.  #: Bulk-mark the actual largest residual contributions in deterministic tie order.
        for index in sorted(range(len(indicators)),key=lambda i:(-indicators[i],i)):  #: Use measured field residuals rather than predetermined geometry refinement.
            marked.append(index);mass+=indicators[index]  #: Accumulate the selected squared-indicator mass.
            if mass>=bulk*total:break  #: Stop once the requested bulk is covered.
        record['marked_cells']=marked;record['marked_indicator_fraction']=mass/total if total else 0.  #: Preserve the exact mark set and its observed residual coverage.
        try:frame,proof=refine_frame(frame,set(marked),cancel)  #: Produce and check a separate native conforming refinement candidate.
        except ValueError as error:  #: Preserve the accepted field for the explicit adapter memory ceiling only.
            if str(error).startswith('Adaptive source binding exceeds'):stop='budget_limit';break  #: Report a genuine bounded-resource stop without accepting the oversized candidate.
            raise  #: Never disguise failed geometry or source conservation as a budget stop.
    return {'format':'magnetics-studio.adaptive-loop/1','input':request,'initial_reference':initial,'frame':accepted_frame,'native':accepted_solution,'history':history,'stop_reason':stop,'scope':'Fixed faceted source/domain, native order zero, uncalibrated residual-driven h refinement'}  #: Export exactly the last accepted field and honest scope/stopping evidence.


def enrich_adaptive(result, order=2, cancel=None):  #: Try the requested higher order on the latest accepted mesh that fits the unchanged native DOF limit.
    if result.get('format')!='magnetics-studio.adaptive-loop/1' or type(order) is not int or order not in (2,3):raise ValueError('Use an actual adaptive result and enrichment order 2 or 3')  #: Keep the optional enrichment contract explicit.
    attempts=[]  #: Retain every genuine resource rejection instead of claiming an unconstrained high-order solve.
    for record in reversed(result['history']):  #: Try accepted meshes in newest-first order without modifying adaptive history.
        check_cancel(cancel);frame={'format':'magnetics-studio.loop-transfer/1','input':result['frame']['input'],'source':result['frame']['source'],'mesh':record['mesh']}  #: Recover a complete real source/mesh frame for this accepted pass.
        try:solution=solve_native_transfer(frame,order,cancel=cancel)  #: Execute the actual higher-order mixed solve on that exact mesh.
        except ValueError as error:  #: Fall back only when the explicit native DOF ceiling is reached.
            if str(error)=='Native mixed loop space exceeds 45000 DOFs':attempts.append({'pass':record['pass'],'status':'budget_limit'});continue  #: Preserve exact resource-limited attempts and try the preceding accepted mesh.
            raise  #: Do not hide source, geometry, dependency or solver failures.
        attempts.append({'pass':record['pass'],'status':'solved','mixed_dofs':solution['mixed_dofs']})  #: Credit only an actual successful higher-order field solve.
        return {'status':'solved','order':order,'selected_pass':record['pass'],'attempts':attempts,'frame':frame,'native':solution}  #: Keep the higher-order result on its own matching mesh, separate from the final order-zero adaptive field.
    return {'status':'budget_limit','order':order,'selected_pass':None,'attempts':attempts}  #: Report that no requested high-order solve fit without discarding the valid adaptive result.
