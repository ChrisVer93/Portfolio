"""Reference linear multiport mesh/air sensitivity; empirical changes, not error bounds."""
import copy  #: Keep all study cases detached from the user's saved source and builder recipe.
import hashlib  #: Bind original and generated projects to exact finite SI JSON snapshots.
import json  #: Preserve reproducible source identity and complete study inputs/results.
from .project import validate  #: Reuse original material, geometry and electrical-series validation.
from .connections import require_static_sources,series_key  #: Preserve stable electrical ports and reject ignored AC sources.
from .mesh import build_mesh  #: Preflight actual fitted cell counts rather than underestimate interface subdivision.
from .analysis import solve_project,_solve_on_mesh  #: Solve either the unchanged ordinary target mesh or an explicitly constructed nested mesh using the same original physics.
from .port_reduction import reduce_ports  #: Retain all explicitly selected short-to-short mutual couplings.
from .sparse import check_cancel  #: Cooperate with cancellation between cases and original solves.


def project_digest(project):  #: Identify exact detached source/coordinate/mesh settings without relying on display names.
    return hashlib.sha256(json.dumps(project,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()  #: Bind source data to finite JSON bytes, independently of incidental dictionary order.


def plan_study(project, options, cancel=None):  #: Reject all unsupported or excessive cases before replacing a prior accepted job.
    p=validate(project);require_static_sources(p)  #: Preserve original static source compatibility and canonical same-current membership.
    if any(m.get('bh') for m in p['materials']) or any(r.get('polygon') for r in p['regions']):raise ValueError('Port studies currently require linear materials and rectangular reference geometry')  #: Keep nonlinear tangent and faceted-geometry convergence outside this declared scope.
    if not isinstance(options,dict) or set(options)-{'mesh_mode'}!={'input_id','shorted_ids','mesh_factors','air_factors'}:raise ValueError('Declare input_id, shorted_ids, mesh_factors and air_factors')  #: Require complete explicit electrical and variation intent without guessed defaults.
    keys=list(dict.fromkeys(series_key(w) for w in p['windings']))  #: Match reference electrical matrix order without merging equal display labels.
    if options['input_id'] not in keys or not isinstance(options['shorted_ids'],list) or any(not isinstance(k,str) or k not in keys for k in options['shorted_ids']) or len(set(options['shorted_ids']))!=len(options['shorted_ids']) or options['input_id'] in options['shorted_ids']:raise ValueError('Choose a known input and distinct other shorted electrical IDs')  #: Reject ambiguous short selections before launching field solves.
    mode=options.get('mesh_mode','target')  #: Preserve legacy requested-target behavior when old saved requests omit the new option.
    if mode not in ('target','interval'):raise ValueError('Choose target or interval mesh_mode')  #: Reject an unknown numerical refinement definition before accepting a job.
    mesh=options['mesh_factors'];air=options['air_factors']  #: Keep numerical refinement and exterior-air expansion as distinct axes.
    for values,allowed in [(mesh,(1,2,4) if mode=='interval' else (1,2,3)),(air,(1,2,3))]:  #: Validate mesh and air factors by their distinct roles even if a Python caller aliases both lists.
        if not isinstance(values,list) or not values or len(values)>3 or any(type(v) is not int or v not in allowed for v in values) or values!=sorted(set(values)) or values[0]!=1:raise ValueError('Increasing unique factors must start at1; interval mesh uses1,2,4; target mesh and air use1,2,3')  #: Reject silently rounded, duplicate, boolean and unordered scale requests.
    if not 2<=len(mesh)*len(air)<=6:raise ValueError('Request 2..6 explicit mesh/air cases')  #: Bound work while requiring an actual numerical sensitivity comparison.
    axes=list(zip('xyz',['width','height','depth']))[:2 if p['mode']=='2d' else 3];cases=[];work=0  #: Preserve planar stack depth and expand all three exterior dimensions only in 3D.
    for a in air:  #: Group mesh comparisons at a fixed physical outer boundary.
        for h in mesh:  #: Refine the same source/material geometry independently of the air axis.
            check_cancel(cancel);q=copy.deepcopy(p);shift=[0.,0.,0.]  #: Honour cancellation and isolate every generated project.
            for i,(axis,size) in enumerate(axes):  #: Translate the component rigidly to the centre of the enlarged exterior.
                shift[i]=p['domain'][size]*(a-1)/2;q['domain'][size]=p['domain'][size]*a;q['domain']['n'+axis]=p['domain']['n'+axis]*(h if mode=='target' else 1)*a  #: Keep source sizes fixed; interval refinement retains base targets while target mode scales them; air changes preserve nominal physical spacing.
                for box in q['regions']+([w['window'] for w in q['windings']] if q['mode']=='3d' else []):  #: Shift every region and ideal-sheet support together, retaining original ordering and polarity.
                    for end in ['0','1']:box[axis+end]+=shift[i]  #: Preserve all physical feature dimensions and separations under rigid translation.
            if q.get('builder'):q['builder_edits_after_generation']=True  #: Mark detached expanded-domain FEM cases as edited instead of silently changing their retained builder recipe.
            q=validate(q);fitted=build_mesh(q,cancel=cancel,interval_factor=h if mode=='interval' else 1);count=len(fitted['elements']);work+=count*(len(q['windings'])+1)  #: Count the actual chosen target or dyadically refined mesh for every physical unit excitation and original-current solve.
            if count>24000 or work>240000:raise ValueError('Port study budget: at most24000 actual cells per case and240000 cell-excitations total; lower base subdivisions or factors')  #: Bound both desktop and browser studies before a new job is accepted.
            cases.append(dict(project=q,mesh_mode=mode,mesh_factor=h,air_factor=a,translation_m=shift,actual_elements=count,project_sha256=project_digest(q),mesh_sha256=project_digest({k:fitted[k] for k in ['nodes','elements','tags']})))  #: Export exact project, mesh definition/factor, physical translation and full mesh hash for reproducible refined solves.
    return dict(project=p,source_sha256=project_digest(p),options=copy.deepcopy(options),cases=cases,cell_excitations=work)  #: Preserve the complete original source and all explicit bounded study cases.


def port_study(project, options, progress=None, cancel=None):  #: Run actual independent unit-excitation solves on every requested mesh and exterior domain.
    plan=plan_study(project,options,cancel);rows=[];last_mesh={};last_air={}  #: Keep separate numerical comparisons along each declared variation axis.
    for case in plan['cases']:  #: Never interpolate, reuse saved fields or fabricate a refined sample.
        check_cancel(cancel)  #: Stop before starting the next complete numerical case.
        if progress:progress('Reference port study: mesh×'+str(case['mesh_factor'])+', air×'+str(case['air_factor']))  #: Expose the actual numerical case through the existing job log.
        if case['mesh_mode']=='interval':  #: Execute the exact new fitted-interval mesh definition rather than merely changing nominal targets.
            fitted=build_mesh(case['project'],progress,cancel,interval_factor=case['mesh_factor'])  #: Reconstruct the same bounded dyadic Cartesian refinement used during preflight.
            if project_digest({k:fitted[k] for k in ['nodes','elements','tags']})!=case['mesh_sha256']:raise RuntimeError('Study mesh hash differs from its preflight plan')  #: Reject any changed connectivity, coordinates or material assignment before solving.
            solved=_solve_on_mesh(case['project'],fitted,True,progress,cancel)  #: Assemble and solve the original scalar or vector formulation on the actual refined mesh.
        else:solved=solve_project(case['project'],True,progress,cancel)  #: Preserve the prior target-mode execution and its original validation/timing behavior.
        measurement=reduce_ports(solved['circuits'],options['input_id'],options['shorted_ids'])  #: Apply the same explicit simultaneous-short conditions to the genuinely solved full matrix.
        if solved['stats']['elements']!=case['actual_elements']:raise RuntimeError('Study mesh differs from its preflight plan')  #: Reject a changed or mismatched mesh rather than crediting another numerical problem.
        value=measurement['input_inductance_H'];h=case['mesh_factor'];a=case['air_factor']  #: Track the selected signed-linkage input inductance in henries.
        def change(previous):  #: Retain signed differences and a dimensionless empirical change without claiming an error estimate.
            return None if previous is None else dict(delta_H=value-previous,relative_change=abs(value-previous)/max(abs(value),abs(previous),1e-30))  #: Leave an unpaired first sample undefined and normalize consistently for either variation axis.
        previous=last_mesh.get(a);identical=previous is not None and previous['mesh_sha256']==case['mesh_sha256']  #: Detect when increased requested subdivisions create no new fitted mesh rather than crediting false zero-change refinement.
        row={**case,'measurement':measurement,'stats_at_original_currents':solved['stats'],'identical_previous_mesh':identical,'mesh_change':None if identical else change(None if previous is None else previous['value']),'air_change':change(last_air.get(h))}  #: Export exact generated projects, actual solve diagnostics and separate observable changes.
        rows.append(row);last_mesh[a]=dict(value=value,mesh_sha256=case['mesh_sha256']);last_air[h]=value  #: Compare only adjacent accepted points at the same other-axis setting.
    return dict(kind='port_study',project=plan['project'],source_sha256=plan['source_sha256'],options=plan['options'],rows=rows,cell_excitations=plan['cell_excitations'],note='Original reference linear2D/3D backend; every matrix is freshly solved. Physical source/material geometry and turns are preserved; 2D depth is fixed. Interval mode subdivides every fitted base interval by1,2or4 with nested dyadic levels; target mode changes requested global subdivisions and may repeat a mesh. Exact project plus mesh_mode/mesh_factor reproduce each mesh; project alone does not encode interval refinement. Uniform subdivision retains aspect ratios and is not local error-driven adaptation or quality optimization. Air expansion holds nominal physical spacing and subdivisions between geometry planes, but exterior air topology changes. Identical adjacent fitted meshes are flagged and excluded from mesh-change comparisons. Changes are empirical sensitivity, not certified error/convergence, independent validation or a unique Lm/leakage split. Stats/fields are at original prescribed currents; selected1A short energy/linkage come from the matrix. Original accepted field is retained. Repeat mesh studies at larger domains; source geometry/material errors remain unmeasured.')  #: Keep resource, source, boundary, discretization and physical interpretation limits with every study export.
