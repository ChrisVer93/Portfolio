"""S005 independent air-sheet local-field verification; no runtime modification."""
import copy,hashlib,json,math,sys  #: Preserve cases, exact provenance and SI vector arithmetic.
from pathlib import Path  #: Resolve the explicitly supplied tested application checkout.
ROOT=Path(sys.argv[1]).resolve();sys.path.insert(0,str(ROOT))  #: Import the exact preceding reference implementation.
from engine.project import validate  #: Reuse physical model validation without changing its source conventions.
from engine.mesh import build_mesh,tetra_geometry,dot,sub  #: Inspect actual tetrahedral containment for field sampling.
from engine.analysis import _solve_on_mesh  #: Run actual original edge-element fields on the declared fitted refinement.
MU0=4*math.pi*1e-7  #: Use vacuum permeability in henries per metre for this air-only numerical comparison.

def reference(point,n):  #: Independently integrate Biot–Savart over four straight sides and uniform axial sheet height.
    value=[0.,0.,0.];corners=[(.4,.4),(.6,.4),(.6,.6),(.4,.6)]  #: Orient a unit-turn positive-z closed rectangular loop counterclockwise.
    for iz in range(n):  #: Midpoint-integrate the uniform turn distribution over its0.2m axial support.
        z=.4+.2*(iz+.5)/n  #: Place source integration points strictly inside the sheet height.
        for a,b in zip(corners,corners[1:]+corners[:1]):  #: Include the complete explicit return path, not just an active coil side.
            dl=((b[0]-a[0])/n,(b[1]-a[1])/n,0.)  #: Integrate each directed straight conductor using independent midpoint segments.
            for j in range(n):  #: Resolve the line integral separately from the axial sheet integral.
                r=(point[0]-a[0]-(j+.5)*dl[0],point[1]-a[1]-(j+.5)*dl[1],point[2]-z);d=sum(x*x for x in r)**1.5  #: Compute the source-to-observation vector and cubic distance in SI units.
                cross=(dl[1]*r[2],-dl[0]*r[2],dl[0]*r[1]-dl[1]*r[0])  #: Evaluate the directed dl cross r contribution independently of all FEM source bases.
                for k in range(3):value[k]+=MU0/(4*math.pi*n)*cross[k]/d  #: Weight unit current and the uniform unit-turn axial distribution.
    return value  #: Return actual free-space Bx,By,Bz in tesla.

def sample(result,point):  #: Average incident elementwise fields at a fixed physical observation point.
    values=[];mesh=result['mesh']  #: Retain actual solved tetrahedra, never interpolate saved reference data.
    for e,v in zip(mesh['elements'],result['fields']['B']):  #: Locate all genuine incident cells to avoid an arbitrary one-sided trace at grid planes.
        vertices=[mesh['nodes'][i] for i in e];_,g=tetra_geometry(vertices);delta=sub(point,vertices[0]);weights=[1+dot(g[0],delta)]+[dot(x,delta) for x in g[1:]]  #: Use independent barycentric containment on actual vertices.
        if min(weights)>=-1e-10 and max(weights)<=1+1e-10:values.append(v)  #: Admit only cells whose closure contains the declared physical probe.
    assert values,'Probe outside solved mesh'  #: Refuse missing-field samples instead of filling them with zero.
    return [sum(v[k] for v in values)/len(values) for k in range(3)]  #: Define a reproducible incident-element mean, not a certified continuous point value.

p=json.loads((ROOT/'examples/air_coil_3d.json').read_text());p['domain'].update(width=1.,height=1.,depth=1.,nx=4,ny=4,nz=4);p['regions']=[];p['windings']=[dict(id='coil',name='coil',turns=1,current=1,window=dict(x0=.4,x1=.6,y0=.4,y1=.6,z0=.4,z1=.6))]  #: Use an explicit air-only unit rectangular sheet, with the entire closed return and no finite copper/core claim.
probes=[(.5,.5,.5),(.53,.52,.54),(.47,.48,.46)];refs=[reference(x,128) for x in probes];coarse=[reference(x,64) for x in probes]  #: Compare full off-axis vectors and a symmetric point pair with separately refined quadrature.
quad=[math.sqrt(sum((a-b)**2 for a,b in zip(x,y)))/math.sqrt(sum(a*a for a in x)) for x,y in zip(refs,coarse)];assert max(quad)<.001  #: Require quadrature stability below0.1percent without treating it as a certified integration bound.
a=b=.1;dz=.2/2000;analytic=sum(MU0/.2*a*b/(math.pi*math.sqrt(a*a+b*b+z*z))*(1/(a*a+z*z)+1/(b*b+z*z))*dz for z in [-.1+(i+.5)*dz for i in range(2000)]);assert abs(refs[0][2]/analytic-1)<.001  #: Independently check the centre reference against the known rectangular-loop axial expression integrated over height.
rows=[]  #: Retain all real field comparisons, including any large discrepancies.
for air in [1,2]:  #: Separate fixed-geometry exterior-domain changes from refinement.
    q=copy.deepcopy(p);shift=(air-1)/2  #: Rigidly translate the same coil and probes into the enlarged closed box.
    for axis,size in zip('xyz',['width','height','depth']):  #: Expand exterior air only, keeping nominal physical base spacing constant.
        q['domain'][size]=air;q['domain']['n'+axis]=4*air  #: Retain physical base target spacing as the domain grows.
        for end in ['0','1']:q['windings'][0]['window'][axis+end]+=shift  #: Preserve every physical winding dimension and unit source.
    for h in [1,2]:  #: Refine every fitted interval using the actual preceding S004 implementation.
        validated=validate(q);mesh=build_mesh(validated,interval_factor=h);result=_solve_on_mesh(validated,mesh,False);samples=[sample(result,tuple(v+shift for v in point)) for point in probes]  #: Execute genuine spatial edge-element fields and sample the same source-relative probes.
        errors=[math.sqrt(sum((a-b)**2 for a,b in zip(v,r)))/math.sqrt(sum(a*a for a in r)) for v,r in zip(samples,refs)]  #: Report full-vector disagreement normalized by the independent free-space vector norm.
        rows.append(dict(air_factor=air,interval_factor=h,elements=len(mesh['elements']),project=validated,B_T=samples,relative_vector_disagreement=errors,energy_consistency=result['stats']['energy_consistency']))  #: Preserve exact physical models, actual vectors and internal energy checks without a manufactured pass label.
output=dict(source_release='0.9.35',probes_m=probes,free_space_B_T=refs,quadrature_relative_changes=quad,independent_center_Bz_T=analytic,rows=rows,limits='Free-space reference versus closed tangential-A=0 FEM boundary; disagreement combines mesh/boundary/source discretization. Incident-cell averaging is explicit. Air only, ideal sheets; no finite copper/core, AC, hardware or Maxwell validation.')  #: Preserve assumptions and unresolved numerical errors with every result.
Path('s005/results.json').write_text(json.dumps(output,indent=2)+'\n');print(json.dumps({k:v for k,v in output.items() if k!='rows'},indent=2));print([(r['air_factor'],r['interval_factor'],r['elements'],r['relative_vector_disagreement']) for r in rows])  #: Save genuine complete results and display concise actual disagreements.
