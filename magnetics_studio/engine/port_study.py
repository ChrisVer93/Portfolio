"""Reference linear multiport mesh/air sensitivity; empirical changes, not error bounds."""
import copy  #: Keep all study cases detached from the user's saved source and builder recipe.
import hashlib  #: Bind original and generated projects to exact finite SI JSON snapshots.
import json  #: Preserve reproducible source identity and complete study inputs/results.
from .project import validate  #: Reuse original material, geometry and electrical-series validation.
from .connections import require_static_sources,series_key  #: Preserve stable electrical ports and reject ignored AC sources.
from .mesh import build_mesh  #: Preflight actual fitted cell counts rather than underestimate interface subdivision.
from .analysis import solve_project  #: Execute genuine original reference 2D/3D unit-excitation fields.
from .port_reduction import reduce_ports  #: Retain all explicitly selected short-to-short mutual couplings.
from .sparse import check_cancel  #: Cooperate with cancellation between cases and original solves.


def project_digest(project):  #: Identify exact detached source/coordinate/mesh settings without relying on display names.
    return hashlib.sha256(json.dumps(project,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()  #: Bind source data to finite JSON bytes, independently of incidental dictionary order.


def plan_study(project, options, cancel=None):  #: Reject all unsupported or excessive cases before replacing a prior accepted job.
    p=validate(project);require_static_sources(p)  #: Preserve original static source compatibility and canonical same-current membership.
    if any(m.get('bh') for m in p['materials']) or any(r.get('polygon') for r in p['regions']):raise ValueError('Port studies currently require linear materials and rectangular reference geometry')  #: Keep nonlinear tangent and faceted-geometry convergence outside this declared scope.
    if not isinstance(options,dict) or set(options)!={'input_id','shorted_ids','mesh_factors','air_factors'}:raise ValueError('Declare input_id, shorted_ids, mesh_factors and air_factors')  #: Require complete explicit electrical and variation intent without guessed defaults.
    keys=list(dict.fromkeys(series_key(w) for w in p['windings']))  #: Match reference electrical matrix order without merging equal display labels.
    if options['input_id'] not in keys or not isinstance(options['shorted_ids'],list) or any(not isinstance(k,str) or k not in keys for k in options['shorted_ids']) or len(set(options['shorted_ids']))!=len(options['shorted_ids']) or options['input_id'] in options['shorted_ids']:raise ValueError('Choose a known input and distinct other shorted electrical IDs')  #: Reject ambiguous short selections before launching field solves.
    mesh=options['mesh_factors'];air=options['air_factors']  #: Keep numerical refinement and exterior-air expansion as distinct axes.
    for values in [mesh,air]:  #: Require exact integer scaling so nominal physical spacing is held during air changes.
        if not isinstance(values,list) or not values or len(values)>3 or any(type(v) is not int or not 1<=v<=3 for v in values) or values!=sorted(set(values)) or values[0]!=1:raise ValueError('Factors must be increasing unique integers 1..3 starting at1')  #: Reject silently rounded, duplicate, boolean and unordered scale requests.
    if not 2<=len(mesh)*len(air)<=6:raise ValueError('Request 2..6 explicit mesh/air cases')  #: Bound work while requiring an actual numerical sensitivity comparison.
    axes=list(zip('xyz',['width','height','depth']))[:2 if p['mode']=='2d' else 3];cases=[];work=0  #: Preserve planar stack depth and expand all three exterior dimensions only in 3D.
    for a in air:  #: Group mesh comparisons at a fixed physical outer boundary.
        for h in mesh:  #: Refine the same source/material geometry independently of the air axis.
            check_cancel(cancel);q=copy.deepcopy(p);shift=[0.,0.,0.]  #: Honour cancellation and isolate every generated project.
            for i,(axis,size) in enumerate(axes):  #: Translate the component rigidly to the centre of the enlarged exterior.
                shift[i]=p['domain'][size]*(a-1)/2;q['domain'][size]=p['domain'][size]*a;q['domain']['n'+axis]=p['domain']['n'+axis]*h*a  #: Keep physical source sizes fixed and nominal spacing size/n independent of air factor.
                for box in q['regions']+([w['window'] for w in q['windings']] if q['mode']=='3d' else []):  #: Shift every region and ideal-sheet support together, retaining original ordering and polarity.
                    for end in ['0','1']:box[axis+end]+=shift[i]  #: Preserve all physical feature dimensions and separations under rigid translation.
            if q.get('builder'):q['builder_edits_after_generation']=True  #: Mark detached expanded-domain FEM cases as edited instead of silently changing their retained builder recipe.
            q=validate(q);fitted=build_mesh(q,cancel=cancel);count=len(fitted['elements']);work+=count*(len(q['windings'])+1)  #: Check actual interface-fitted work for all physical unit excitations and the original operating-point solve.
            if count>24000 or work>240000:raise ValueError('Port study budget: at most24000 actual cells per case and240000 cell-excitations total; lower base subdivisions or factors')  #: Bound both desktop and browser studies before a new job is accepted.
            cases.append(dict(project=q,mesh_factor=h,air_factor=a,translation_m=shift,actual_elements=count,project_sha256=project_digest(q),mesh_sha256=project_digest({k:fitted[k] for k in ['nodes','elements','tags']})))  #: Retain exact generated inputs and physical translation for independent reproduction.
    return dict(project=p,source_sha256=project_digest(p),options=copy.deepcopy(options),cases=cases,cell_excitations=work)  #: Preserve the complete original source and all explicit bounded study cases.


def port_study(project, options, progress=None, cancel=None):  #: Run actual independent unit-excitation solves on every requested mesh and exterior domain.
    plan=plan_study(project,options,cancel);rows=[];last_mesh={};last_air={}  #: Keep separate numerical comparisons along each declared variation axis.
    for case in plan['cases']:  #: Never interpolate, reuse saved fields or fabricate a refined sample.
        check_cancel(cancel)  #: Stop before starting the next complete numerical case.
        if progress:progress('Reference port study: mesh×'+str(case['mesh_factor'])+', air×'+str(case['air_factor']))  #: Expose the actual numerical case through the existing job log.
        solved=solve_project(case['project'],True,progress,cancel);measurement=reduce_ports(solved['circuits'],options['input_id'],options['shorted_ids'])  #: Extract the genuine full linear matrix and enforce the explicit simultaneous-short conditions.
        if solved['stats']['elements']!=case['actual_elements']:raise RuntimeError('Study mesh differs from its preflight plan')  #: Reject a changed or mismatched mesh rather than crediting another numerical problem.
        value=measurement['input_inductance_H'];h=case['mesh_factor'];a=case['air_factor']  #: Track the selected signed-linkage input inductance in henries.
        def change(previous):  #: Retain signed differences and a dimensionless empirical change without claiming an error estimate.
            return None if previous is None else dict(delta_H=value-previous,relative_change=abs(value-previous)/max(abs(value),abs(previous),1e-30))  #: Leave an unpaired first sample undefined and normalize consistently for either variation axis.
        previous=last_mesh.get(a);identical=previous is not None and previous['mesh_sha256']==case['mesh_sha256']  #: Detect when increased requested subdivisions create no new fitted mesh rather than crediting false zero-change refinement.
        row={**case,'measurement':measurement,'stats_at_original_currents':solved['stats'],'identical_previous_mesh':identical,'mesh_change':None if identical else change(None if previous is None else previous['value']),'air_change':change(last_air.get(h))}  #: Export exact generated projects, actual solve diagnostics and separate observable changes.
        rows.append(row);last_mesh[a]=dict(value=value,mesh_sha256=case['mesh_sha256']);last_air[h]=value  #: Compare only adjacent accepted points at the same other-axis setting.
    return dict(kind='port_study',project=plan['project'],source_sha256=plan['source_sha256'],options=plan['options'],rows=rows,cell_excitations=plan['cell_excitations'],note='Original reference linear2D/3D backend; every matrix is freshly solved. Physical source/material geometry and turns are preserved; 2D depth is fixed. Air expansion holds nominal physical spacing and subdivisions between geometry planes, but exterior air topology changes. Identical adjacent fitted meshes are flagged and excluded from mesh-change comparisons. Changes are empirical sensitivity, not certified error/convergence, independent validation or a unique Lm/leakage split. Stats/fields are at original prescribed currents; selected1A short energy/linkage come from the matrix. Original accepted field is retained. Repeat mesh studies at larger domains; source geometry/material errors remain unmeasured.')  #: Keep resource, source, boundary, discretization and physical interpretation limits with every study export.
