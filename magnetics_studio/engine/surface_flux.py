"""Signed triangular pickup flux on an exactly clipped affine tetrahedral mesh."""
import math  #: Use physical lengths, areas, finite checks and compensated sums.
from .mesh import cross,dot,sub,tetra_geometry  #: Reuse the actual affine tetrahedron geometry in SI metres.
from .sparse import check_cancel  #: Honor cancellation during bounded clipping and field evaluation.


def validate_surfaces(surfaces):  #: Detach and validate explicitly oriented triangular pickup surfaces.
    if not isinstance(surfaces,list) or not 1<=len(surfaces)<=16:raise ValueError('Use 1 to 16 triangular flux surfaces')  #: Keep postprocessing resource use explicit.
    result=[];names=set()  #: Preserve caller order and reject ambiguous output identities.
    for surface in surfaces:  #: Validate every pickup before evaluating a field.
        if not isinstance(surface,dict) or set(surface)!={'id','vertices_m'}:raise ValueError('Flux surface requires only id and vertices_m')  #: Reject misspelled or inferred geometry fields.
        name=surface['id'];points=surface['vertices_m']  #: Keep physical orientation in the supplied vertex order.
        if not isinstance(name,str) or not name.strip() or len(name)>80 or name in names:raise ValueError('Flux surface IDs must be unique nonempty strings')  #: Never merge equally named pickups silently.
        if not isinstance(points,list) or len(points)!=3 or any(not isinstance(p,(list,tuple)) or len(p)!=3 or any(type(v) not in (int,float) or not math.isfinite(v) for v in p) for p in points):raise ValueError('Flux vertices must be three finite SI triples')  #: Reject booleans, nonfinite data and incomplete coordinates.
        points=[list(map(float,p)) for p in points];normal=cross(sub(points[1],points[0]),sub(points[2],points[0]));twice=math.sqrt(dot(normal,normal))  #: Measure signed orientation and physical triangle area.
        scale=max(math.dist(a,b) for a in points for b in points)  #: Compare degeneracy to the actual pickup size.
        if not math.isfinite(twice) or scale==0 or twice<=1e-12*scale**2:raise ValueError('Flux triangle is degenerate or too slender')  #: Reject ill-conditioned surfaces rather than assign an arbitrary normal.
        names.add(name);result.append(dict(id=name,vertices_m=points,normal=[v/twice for v in normal],area_m2=twice/2))  #: Retain detached physical inputs and normalized orientation.
    return result  #: Return only bounded, finite and oriented pickup geometry.


def _clip(poly,vertex,gradient):  #: Intersect an ordered planar polygon with one exact tetrahedron half-space.
    output=[]  #: Preserve convex polygon order through Sutherland-Hodgman clipping.
    for a,b in zip(poly,poly[1:]+poly[:1]):  #: Visit each closed oriented polygon edge once.
        fa=1+dot(gradient,sub(a,vertex));fb=1+dot(gradient,sub(b,vertex))  #: Evaluate the physical barycentric coordinate defining this half-space.
        fa=0. if abs(fa)<1e-12 else fa;fb=0. if abs(fb)<1e-12 else fb  #: Snap only roundoff-scale dimensionless barycentric distances on coincident fitted faces.
        if fa>=0:output.append(a)  #: Retain points on or inside the selected cell face.
        if (fa<0<fb) or (fb<0<fa):  #: Add only genuine crossings, avoiding repeated exact endpoints.
            t=fa/(fa-fb);output.append([x+t*(y-x) for x,y in zip(a,b)])  #: Locate the exact affine segment-plane intersection.
    return output  #: Empty and zero-area intersections contribute no pickup flux.


def build_surface_plan(mesh,surfaces,cancel=None):  #: Split each pickup into actual cell intersections and bounded polynomial quadrature.
    prepared=validate_surfaces(surfaces);nodes=mesh['nodes'];cells=mesh['elements']  #: Bind observation geometry to the supplied magnetic mesh.
    if not 1<=len(cells)<=60000 or len(nodes)>30000:raise ValueError('Flux mesh budget exceeded')  #: Preserve the finite-loop transfer limits.
    if any(len(p)!=3 or any(type(v) not in (int,float) or not math.isfinite(v) for v in p) for p in nodes):raise ValueError('Flux mesh coordinates must be finite triples')  #: Refuse a nonphysical detached mesh.
    seen=set();faces={};geometry=[]  #: Cache physical cell gradients, bounds and face multiplicities.
    for i,cell in enumerate(cells):  #: Inspect each complete tetrahedron identity exactly once.
        if i%256==0:check_cancel(cancel)  #: Stop promptly during large-mesh observation preflight.
        if len(cell)!=4 or any(type(n) is not int or not 0<=n<len(nodes) for n in cell) or len(set(cell))!=4 or tuple(sorted(cell)) in seen:raise ValueError('Flux mesh has invalid or duplicate tetrahedra')  #: Reject duplicated coverage before quadrature.
        seen.add(tuple(sorted(cell)));points=[nodes[n] for n in cell];volume,gradients=tetra_geometry(points)  #: Compute actual physical barycentric planes independently of native traversal order.
        if not math.isfinite(volume) or volume<=0:raise ValueError('Flux tetrahedron has invalid volume')  #: Refuse degenerate cells.
        bounds=[(min(p[d] for p in points),max(p[d] for p in points)) for d in range(3)]  #: Use boxes only as candidate filters.
        geometry.append((points,gradients,bounds))  #: Retain exact affine half-spaces for actual clipping.
        for j in range(4):  #: Count every original topological face.
            key=tuple(sorted(cell[:j]+cell[j+1:]));faces[key]=faces.get(key,0)+1  #: Distinguish coincident interior traces from a physical exterior.
            if faces[key]>2:raise ValueError('Flux mesh has nonmanifold faces')  #: Refuse ambiguous overlap ownership.
    q=math.sqrt(6/5);abscissae=[-math.sqrt((3+2*q)/7),-math.sqrt((3-2*q)/7),math.sqrt((3-2*q)/7),math.sqrt((3+2*q)/7)]  #: Derive four-point Gauss-Legendre locations without a runtime numerical dependency.
    weights=[(18-math.sqrt(30))/72,(18+math.sqrt(30))/72,(18+math.sqrt(30))/72,(18-math.sqrt(30))/72];abscissae=[(x+1)/2 for x in abscissae]  #: Transform nodes and weights to the unit interval.
    plans=[];total_samples=0  #: Bound memory over all requested surfaces.
    for surface in prepared:  #: Keep independent pickup results separate and ordered.
        points=surface['vertices_m'];bounds=[(min(p[d] for p in points),max(p[d] for p in points)) for d in range(3)];samples=[];areas=[];patches=0  #: Track independently measured coverage and actual integration work.
        for i,(vertices,gradients,box) in enumerate(geometry):  #: Split the requested physical surface against every possible cell.
            if i%256==0:check_cancel(cancel)  #: Honor cancellation before native field sampling.
            if any(bounds[d][1]<box[d][0] or box[d][1]<bounds[d][0] for d in range(3)):continue  #: Reject disjoint boxes without substituting box overlap for intersection.
            poly=points  #: Begin with the exact requested triangle for each cell.
            for vertex,gradient in zip(vertices,gradients):  #: Apply all four barycentric inequalities.
                if not poly:break  #: Avoid processing empty intersections.
                poly=_clip(poly,vertex,gradient)  #: Clip the complete polygon rather than sample a centroid mask.
            if len(poly)<3:continue  #: Ignore point and line intersections of zero physical area.
            common=[j for j,(v,g) in enumerate(zip(vertices,gradients)) if all(abs(1+dot(g,sub(p,v)))<1e-10 for p in poly)]  #: Detect a pickup patch lying exactly on a tetrahedron facet.
            factor=1/faces[tuple(sorted(cells[i][:common[0]]+cells[i][common[0]+1:]))] if len(common)==1 else 1  #: Count two incident normal traces with half weight and exterior traces once.
            for b,c in zip(poly[1:-1],poly[2:]):  #: Triangulate the convex clipped polygon without changing its normal orientation.
                a=poly[0];twice=math.sqrt(dot(cross(sub(b,a),sub(c,a)),cross(sub(b,a),sub(c,a))))  #: Measure each real subtriangle area in square metres.
                if twice<=1e-22*surface['area_m2']:continue  #: Discard only numerically zero-area fragments.
                areas.append(factor*twice/2);patches+=1  #: Record coverage independently of field values.
                for u,wu in zip(abscissae,weights):  #: Apply a Duffy product rule that is exact for triangle polynomials through degree six.
                    for v,wv in zip(abscissae,weights):  #: Resolve each clipped-cell polynomial with sixteen interior samples.
                        p=[a[d]+u*(b[d]-a[d])+(1-u)*v*(c[d]-a[d]) for d in range(3)]  #: Map the reference square into the physical oriented subtriangle.
                        samples.append((i,p,factor*twice*(1-u)*wu*wv));total_samples+=1  #: Keep cell identity, SI point and positive physical area weight together.
                        if total_samples>200000:raise ValueError('Flux quadrature sample budget exceeded')  #: Fail preflight before allocating unbounded native evaluation work.
        measured=math.fsum(areas);error=abs(measured/surface['area_m2']-1)  #: Compare complete clipped coverage with the independent requested area.
        if error>1e-8:raise ValueError('Flux surface '+surface['id']+' is outside mesh or has incomplete/overlapping coverage: relative area '+str(error))  #: Refuse extrapolation, missing area and double counting.
        plans.append(dict(surface=surface,samples=samples,covered_area_m2=measured,relative_area_error=error,patches=patches))  #: Retain detached geometry, exact coverage and reproducible integration plan.
    return plans  #: Return fully checked plans before any field result is published.


def integrate_surface_plan(plans,field,cancel=None):  #: Integrate a genuine cell-aware vector field on every checked pickup.
    results=[]  #: Publish only complete finite measurements.
    for plan in plans:  #: Preserve caller pickup order and orientation.
        values=[];surface=plan['surface']  #: Keep flux accumulation separate from geometric coverage.
        for j,(cell,point,weight) in enumerate(plan['samples']):  #: Evaluate actual clipped-cell quadrature rather than centroid interpolation.
            if j%256==0:check_cancel(cancel)  #: Honor cancellation during postprocessing.
            b=list(field(cell,point))  #: Obtain the real field at this physical SI point.
            if len(b)!=3 or any(not math.isfinite(v) for v in b):raise ValueError('Flux field must return a finite vector')  #: Reject invalid native or manufactured field data.
            values.append(weight*dot(b,surface['normal']))  #: Integrate signed normal magnetic flux density times physical area.
        flux=math.fsum(values)  #: Use compensated summation for opposing flux contributions.
        results.append(dict(id=surface['id'],vertices_m=surface['vertices_m'],normal=surface['normal'],area_m2=surface['area_m2'],covered_area_m2=plan['covered_area_m2'],relative_area_error=plan['relative_area_error'],integration_patches=plan['patches'],quadrature_evaluations=len(values),flux_Wb=flux,mean_normal_B_T=flux/surface['area_m2']))  #: Report signed weber flux and tesla area mean without implying winding linkage or inductance.
    return results  #: Return finite complete measurements with geometry and quadrature provenance.
