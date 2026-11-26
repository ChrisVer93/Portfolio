"""S006: separate point sampling from cell-average discrepancy; verification only."""
import hashlib,json,math,sys,time  #: Record exact inputs, vector magnitudes and actual solve timing without changing runtime code.
from pathlib import Path  #: Resolve the explicitly selected preceding source checkout.
ROOT=Path(sys.argv[1]).resolve();sys.path.insert(0,str(ROOT))  #: Bind all FEM calls to the source whose digest is reported.
from engine.project import validate  #: Preserve original physical schema and current conventions.
from engine.mesh import build_mesh,tetra_geometry,dot,sub,cross  #: Inspect actual tetrahedral geometry and containing cells.
from engine.analysis import _solve_on_mesh  #: Execute unchanged reference spatial assembly and field extraction.
MU0=4*math.pi*1e-7  #: Use air permeability in henries per metre for both independent references.

def reference(point,n=128):  #: Integrate sheet height numerically while evaluating each finite directed side analytically.
    result=[0.,0.,0.];corners=[(.4,.4),(.6,.4),(.6,.6),(.4,.6)]  #: Keep the same positive-z unit-turn closed rectangular source and full return path as S005.
    for iz in range(n):  #: Independently midpoint-integrate the uniform turn distribution along its0.2m axial height.
        z=.4+.2*(iz+.5)/n  #: Use physical source positions in the original unshifted coordinate frame.
        for start,end in zip(corners,corners[1:]+corners[:1]):  #: Include all four directed straight current sides.
            u=(start[0]-point[0],start[1]-point[1],z-point[2]);v=(end[0]-point[0],end[1]-point[1],z-point[2]);a=math.sqrt(dot(u,u));b=math.sqrt(dot(v,v));c=cross(u,v);den=a*b*(a*b+dot(u,v))  #: Form the exact finite-segment Biot–Savart endpoint geometry.
            if den<=0:raise ValueError('Observation on a singular source line')  #: Reject undefined singular evaluations rather than clamp an infinite field.
            for k in range(3):result[k]+=MU0/(4*math.pi*n)*c[k]*(a+b)/den  #: Sum exact side integrals with unit current and uniform unit total turns.
    return result  #: Return the full free-space vector B in tesla.

def norm(v):  #: Keep vector comparisons independent of signed component cancellation.
    return math.sqrt(dot(v,v))  #: Evaluate Euclidean tesla magnitude.

def cell_reference(vertices,level):  #: Approximate a tetrahedron-volume mean with nested deterministic midpoint cubature.
    total=[0.,0.,0.];weight=0.  #: Accumulate the Duffy-transformed tetrahedral integral and normalization.
    for i in range(level):  #: Resolve the first unit-cube coordinate of the tetrahedral transform.
        u=(i+.5)/level  #: Use interior quadrature positions, avoiding element-boundary coincidences.
        for j in range(level):  #: Resolve the second transformed coordinate independently.
            v=(j+.5)/level  #: Use midpoint evaluation throughout the unit cube.
            for k in range(level):  #: Resolve the third transformed coordinate.
                w=(k+.5)/level;l=[1-u,u*(1-v),u*v*(1-w),u*v*w];jac=u*u*v;p=[sum(l[t]*vertices[t][d] for t in range(4)) for d in range(3)];b=reference(p)  #: Map to barycentric coordinates with Jacobian u²v and independently evaluate physical free-space B.
                for d in range(3):total[d]+=jac*b[d]  #: Integrate each signed vector component, not just its magnitude.
                weight+=jac  #: Normalize the cubature explicitly to the cell-volume mean.
    return [v/weight for v in total]  #: Return the reference constant field appropriate to an elementwise-constant observable.

old=json.loads((ROOT/'sample_results/local_field_s005/results.json').read_text());probes=old['probes_m'];point_reference=[reference(p,256) for p in probes]  #: Retain the preceding exact physical probes and refine the independent axial quadrature.
segment_checks=[norm(sub(a,b))/norm(a) for a,b in zip(point_reference,old['free_space_B_T'])];assert max(segment_checks)<.001  #: Cross-check exact-side integration against S005's separately discretized side/height quadrature.
assert norm(sub(point_reference[1],point_reference[2]))/norm(point_reference[1])<1e-10  #: Enforce physical inversion symmetry independently of any FEM result.
base=old['rows'][0]['project'];rows=[]  #: Reuse the complete preceding air-only physical model, without adding magnetic material or changing currents.
for h in [1,2,4]:  #: Compare genuinely nested meshes at the same1m closed exterior boundary.
    p=validate(base);p['domain']['budget']='extended';mesh=build_mesh(p,interval_factor=h);started=time.perf_counter();solved=_solve_on_mesh(p,mesh,False);observations=[]  #: Explicitly select the existing larger direct-QA memory budget; GUI study ceilings remain unchanged.
    for point,truth in zip(probes,point_reference):  #: Compare point and cell-average observables at identical source-relative locations.
        ids=[];vertices=[]  #: Identify every incident tetrahedron using actual mesh connectivity.
        for index,e in enumerate(mesh['elements']):  #: Search actual solved cells, never use coordinates from another mesh.
            v=[mesh['nodes'][n] for n in e];_,g=tetra_geometry(v);delta=sub(point,v[0]);lam=[1+dot(g[0],delta)]+[dot(x,delta) for x in g[1:]]  #: Locate the physical point with independent barycentric containment.
            if min(lam)>=-1e-10 and max(lam)<=1+1e-10:ids.append(index);vertices.append(v)  #: Preserve all incident traces under the same explicit averaging convention as S005.
        assert ids  #: Refuse an unresolved or exterior probe.
        fem=[sum(solved['fields']['B'][i][d] for i in ids)/len(ids) for d in range(3)];averages=[]  #: Define the actual piecewise-constant FEM observable before comparing it with a smooth reference.
        for level in [2,4]:  #: Measure empirical tetrahedral-volume quadrature sensitivity separately.
            vals=[cell_reference(v,level) for v in vertices];averages.append([sum(x[d] for x in vals)/len(vals) for d in range(3)])  #: Average exact reference cell means using the same incident-cell weights as the FEM sample.
        point_error=sub(fem,truth);cell_error=sub(fem,averages[1]);sampling_error=sub(averages[1],truth)  #: Decompose the complete signed vector error without adding unrelated scalar percentages.
        assert norm(sub(point_error,[a+b for a,b in zip(cell_error,sampling_error)]))<1e-18  #: Verify the exported vector decomposition closes to floating-point tolerance.
        observations.append(dict(point_m=point,incident_cells=len(ids),fem_B_T=fem,point_reference_B_T=truth,cell_reference_B_T=averages[1],point_relative_disagreement=norm(point_error)/norm(truth),cell_relative_disagreement=norm(cell_error)/norm(truth),sampling_relative_difference=norm(sampling_error)/norm(truth),cell_quadrature_relative_change=norm(sub(*averages))/norm(truth),point_error_T=point_error,cell_error_T=cell_error,sampling_error_T=sampling_error))  #: Retain all actual vectors and independently distinguish sampling, cell and cubature discrepancies.
    rows.append(dict(interval_factor=h,elements=len(mesh['elements']),nodes=len(mesh['nodes']),seconds=time.perf_counter()-started,mesh_sha256=hashlib.sha256(json.dumps({k:mesh[k] for k in ['nodes','elements','tags']},sort_keys=True).encode()).hexdigest(),project=p,observations=observations,stats=solved['stats']));print(h,len(mesh['elements']),[(r['point_relative_disagreement'],r['cell_relative_disagreement'],r['sampling_relative_difference'],r['cell_quadrature_relative_change']) for r in observations],flush=True)  #: Preserve exact mesh/project identity and actual unresolved numerical results for each real solve.
Path('s006/results.json').write_text(json.dumps(dict(segment_crosscheck_relative=segment_checks,rows=rows,limits='Free-space versus closed-box fields; cell residual includes boundary, FE/source representation and quadrature. No certified bound, finite copper, core, AC, Maxwell/hardware or new runtime qualification.'),indent=2)+'\n')  #: Save complete real evidence without inventing an accuracy pass.
