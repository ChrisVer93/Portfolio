import copy
import math
import time
from .connections import series_key, series_name, require_static_sources  #: Share canonical ports and reject AC solids in static field paths.
from .project import validate
from .mesh import build_mesh
from .planar import PlanarSystem
from .spatial import SpatialSystem
from .sparse import check_cancel
from .inductance import sweep_sections, sweep_currents, static_inductance  #: Share explicit source grouping and physically labelled sweep postprocessing.


def mesh_public(mesh):
    return {k:mesh[k] for k in ['dimension','nodes','elements','tags','grids','quality']}


def solve_project(project, matrix=True, progress=None, cancel=None):
    started = time.perf_counter()
    p = validate(project)
    require_static_sources(p)  #: Reject incompatible AC-solid input before meshing rather than computing a misleading static zero field.
    mesh = build_mesh(p,progress,cancel)
    result = _solve_on_mesh(p,mesh,matrix,progress,cancel)  #: Reuse assembly/postprocessing on the ordinary fitted mesh.
    result['stats']['seconds'] = time.perf_counter() - started  #: Preserve total ordinary-solve timing, including validation and meshing.
    return result  #: Keep the original public solved-result schema.


def _solve_on_mesh(p, mesh, matrix=True, progress=None, cancel=None):  #: Internal mesh injection lets adaptive passes reuse the existing verified physics.
    """Solve a validated project on an internally generated mesh."""
    started = time.perf_counter()
    require_static_sources(p)  #: Protect internal mesh-injection callers as well as the public ordinary solve.
    cls = PlanarSystem if p['mode']=='2d' else SpatialSystem
    system = cls(p,mesh,progress,cancel)
    rhs = [sum(b[i]*w['current'] for b,w in zip(system.bases,p['windings'])) for i in range(system.n)]
    if progress:
        progress('Solving magnetic field')
    a,info = system.solve(rhs)
    post = system.post(a)
    linkages = [system.linkage(b,a) for b in system.bases]
    peaks = [math.sqrt(sum(v*v for v in b)) for b in post['B']]
    lm = None
    reciprocity = None
    if matrix and not system.nonlinear and system.bases:
        lm = [[0.]*len(system.bases) for _ in system.bases]
        for j,b in enumerate(system.bases):
            check_cancel(cancel)
            if progress:
                progress(f'Inductance matrix: unit excitation {j+1}/{len(system.bases)}')
            unit,_ = system.solve(b)
            for i,bi in enumerate(system.bases):
                lm[i][j] = system.linkage(bi,unit)
        scale = max(abs(v) for row in lm for v in row) or 1.
        reciprocity = max(abs(lm[i][j]-lm[j][i])/scale for i in range(len(lm)) for j in range(len(lm)))
        if reciprocity > 1e-6:
            raise RuntimeError('Inductance reciprocity check failed')
    source_energy = .5*sum(w['current']*v for w,v in zip(p['windings'],linkages))
    energy_error = abs(source_energy-post['energy_J'])/max(abs(source_energy),post['energy_J'],1e-30) if not system.nonlinear else None
    if energy_error is not None and energy_error > 1e-6:
        raise RuntimeError('Field/source magnetic energy consistency check failed')
    warnings = [
        'Closed outer boundary: Az=0 in 2D; tangential A=0 in 3D. Check sensitivity to the air-domain size.',
        'Peak field is elementwise and may be sensitive to sharp corners and mesh resolution.',
        'Independent research software; benchmark evidence is limited to the documented tests.']
    if p['mode']=='3d':
        warnings.append('3D windings are ideal closed rectangular current sheets about z. No finite copper thickness, eddy currents or end-turn resistance.')
    if mesh['quality']['largest_cell_axis_aspect_ratio'] > 10:
        warnings.append('Mesh has cell aspect ratios above 10. Inspect narrow features and check field convergence; fitted interfaces alone do not ensure mesh quality.')
    if system.nonlinear:
        warnings.append('Reversible single-valued B-H law; no hysteresis. Beyond the final point, differential permeability is mu0. No linear inductance matrix is reported.')
    stats = {'mode':p['mode'],'nodes':len(mesh['nodes']),'elements':len(mesh['elements']),
             'dofs':system.n-len(system.fixed),'peak_B_T':max(peaks,default=0.),
             'energy_J':post['energy_J'],'seconds':time.perf_counter()-started,
             'solver':info,'energy_consistency':energy_error,'reciprocity':reciprocity,
             'nonlinear':system.nonlinear,'mesh_quality':mesh['quality']}
    region_stats = []
    for tag,r in enumerate(p['regions']):
        indices = [i for i,t in enumerate(mesh['tags']) if t==tag]
        volume = sum(post['measures'][i] for i in indices)
        avg = sum(peaks[i]*post['measures'][i] for i in indices)/volume if volume else 0.
        region_stats.append({'id':r['id'],'name':r['name'],'volume_m3':volume,
                             'mean_B_T':avg,'peak_B_T':max((peaks[i] for i in indices),default=0.)})
    groups=[]
    for w in p['windings']:
        key=series_key(w)  #: Identify an electrical series port or an independent source by stable ID.
        if key not in groups:groups.append(key)
    grouped=None
    if lm:
        grouped=[[sum(lm[i][j] for i,wi in enumerate(p['windings']) for j,wj in enumerate(p['windings']) if series_key(wi)==a and series_key(wj)==b) for b in groups] for a in groups]  #: Aggregate canonical same-current ports without merging independent names.
    group_names=[]
    for key in groups:
        w=next(w for w in p['windings'] if series_key(w)==key)  #: Resolve representative metadata without using equal display names as connections.
        group_names.append(series_name(w))  #: Imported legacy groups do not require builder-only labels.
    circuit_results={'names':group_names,'group_ids':groups,'inductance_H':grouped}
    if grouped and len(groups)==2:
        a,b,c,d=grouped[0][0],grouped[0][1],grouped[1][0],grouped[1][1]
        circuit_results.update(coupling=b/math.sqrt(a*d),short_circuit_input_H=a-b*c/d)
    pairs=[]
    if grouped:
        import itertools
        for circuit in p.get('circuit_definitions',[]):
            for wa,wb in itertools.combinations(circuit['windings'],2):
                ga=circuit['id']+'__'+wa['id'];gb=circuit['id']+'__'+wb['id']
                if ga not in groups or gb not in groups:continue
                ia,ib=groups.index(ga),groups.index(gb);la,lb,mab,mba=grouped[ia][ia],grouped[ib][ib],grouped[ia][ib],grouped[ib][ia]
                pairs.append({'circuit':circuit['name'],'input_winding':wa['name'],'shorted_winding':wb['name'],'input_open_H':la,'other_open_H':lb,'mutual_H':mab,'short_circuit_input_H':la-mab*mba/lb,'coupling':mab/math.sqrt(la*lb),'condition':'This winding pair only; all other winding currents zero/open. Not all secondaries shorted simultaneously.'})
    circuit_results['logical_circuit_pairs']=pairs
    if p.get('builder_summary'):warnings.extend(p['builder_summary']['notes'])
    if any(r.get('polygon') for r in p['regions']):warnings.append('2D conductor/core curves are explicitly faceted convex polygons; refine facet count and mesh to check geometry and field convergence.')
    return {'circuits':circuit_results,'project':p,'mesh':mesh_public(mesh),'fields':post,'stats':stats,
            'windings':[{'id':w['id'],'name':w['name'],'current_A':w['current'],
                         'turns':w['turns'],'linkage_Wb_turn':l} for w,l in zip(p['windings'],linkages)],
            'inductance_H':lm,'regions':region_stats,'warnings':warnings}


def convergence(project, progress=None, cancel=None):
    """Three global refinements; this is a study, not adaptive error control."""
    p = validate(project)
    rows = []
    for factor in [.65,1.,1.4]:
        check_cancel(cancel)
        q = copy.deepcopy(p)
        for k in ['nx','ny']+(['nz'] if p['mode']=='3d' else []):
            q['domain'][k] = max(2,round(p['domain'][k]*factor))
        if progress:
            progress(f'Convergence study: refinement {len(rows)+1}/3')
        r = solve_project(q,False,progress,cancel)
        row = {k:r['stats'][k] for k in ['nodes','elements','peak_B_T','energy_J','seconds']}
        row['subdivisions'] = {k:q['domain'][k] for k in ['nx','ny']+(['nz'] if p['mode']=='3d' else [])}
        row['linkages_Wb_turn'] = [w['linkage_Wb_turn'] for w in r['windings']]
        row['energy_change'] = abs(row['energy_J']-rows[-1]['energy_J'])/max(abs(row['energy_J']),1e-30) if rows else None
        rows.append(row)
    return {'kind':'convergence','rows':rows,'note':'Global fitted-mesh refinement. Small energy change is not proof of physical accuracy or peak-field convergence.'}


def current_sweep(project, winding_id, values, progress=None, cancel=None):
    p = validate(project)
    require_static_sources(p)  #: Reject declared or assigned AC solids in static studies, including a dangling region-only assignment.
    indices = sweep_sections(p, winding_id)  #: Measure all and only the selected winding's same-current series sections.
    values = sweep_currents(values)  #: Validate finite distinct currents before launching a field solve.

    rows = []
    for value in values:
        check_cancel(cancel)
        q = copy.deepcopy(p)
        for i in indices:  #: Keep other electrical winding currents at their explicitly saved values.
            q['windings'][i]['current'] = value  #: Sweep every physical section of the selected series port together.
        if progress:
            progress(f'Current sweep: {value:g} A ({len(rows)+1}/{len(values)})')
        r = solve_project(q,False,progress,cancel)
        row = {k:r['stats'][k] for k in ['peak_B_T','energy_J','seconds']}
        row.update({'current_A':value,'linkages_Wb_turn':[w['linkage_Wb_turn'] for w in r['windings']]})
        rows.append(row)
    zero = next((row for row in rows if row['current_A'] == 0), None)  #: Reuse a requested zero-current solution when present.
    baseline = sum(zero['linkages_Wb_turn'][i] for i in indices) if zero else 0.0  #: Zero excitation of every winding gives exactly zero linkage for the supported reversible laws.
    if zero is None and any(w['current'] for i, w in enumerate(p['windings']) if i not in indices):  #: Fixed nonzero currents can link bias flux into the selected winding.
        check_cancel(cancel)  #: Honour cancellation before the additional bias solution.
        q = copy.deepcopy(p)  #: Preserve the original other-winding bias state.
        for i in indices:  #: Remove only the swept electrical port excitation.
            q['windings'][i]['current'] = 0  #: Define lambda(0) with other winding currents unchanged.
        if progress:  #: Make the real additional solve visible to the user.
            progress('Current sweep: zero-current bias linkage reference')  #: Explain the work needed to avoid mutual-flux contamination.
        reference = solve_project(q, False, progress, cancel)  #: Recompute the actual field rather than infer a nonlinear bias offset.
        baseline = sum(reference['windings'][i]['linkage_Wb_turn'] for i in indices)  #: Sum the same measured series-port linkages.
    study = {'kind':'sweep','project':p,'winding_id':winding_id,'rows':rows,'solver_scope':'Reference magnetostatic solver; 2D planar or 3D ideal-sheet sources. Native Netgen settings are not used by this study.'}  #: Save the actual source model and disclose the existing sweep backend rather than imply a preceding native solve selected it.
    study['selected_winding_name'] = p['windings'][indices[0]].get('electrical_winding_name', p['windings'][indices[0]]['name'])  #: Label the measured electrical winding without exposing only a physical layer name.
    return static_inductance(study, indices, baseline)  #: Export chord and finite-interval inductance with complete physical definitions.
