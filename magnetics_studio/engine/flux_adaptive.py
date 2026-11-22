"""Bounded fixed-source h refinement stopped by empirical signed pickup-flux stability."""
import copy  #: Detach physical inputs and accepted observation provenance.
import math  #: Compare finite signed fluxes and accumulate residual marking mass.
from .loop_adaptive import bind_source,refine_frame,residual_indicators  #: Reuse qualified current-preserving native refinement and residual marking.
from .loop_fem import solve_loop_fem  #: Retain the genuine initial reference source/mesh/field solve.
from .loop_native import solve_native_transfer  #: Solve the actual source and measure native order-zero surface flux.
from .project import number  #: Preserve explicit finite scalar option validation.
from .surface_flux import validate_surfaces  #: Validate oriented finite pickup geometry and stable unique IDs.
from .sparse import check_cancel  #: Honor cancellation between bounded source, native and measurement phases.


def validate_control(control):  #: Require a complete explicit empirical flux-stability specification.
    if not isinstance(control,dict) or set(control)!={'surfaces','relative_tolerance','absolute_tolerance_Wb','stable_intervals'}:raise ValueError('Supply surfaces and explicit relative/absolute flux tolerances and stable_intervals')  #: Reject silent defaults, unknown controls and incomplete targets.
    control=copy.deepcopy(control);surfaces=validate_surfaces(control['surfaces'])  #: Validate and detach all requested pickup orientations and identities.
    control['relative_tolerance']=number(control['relative_tolerance'],'Relative flux tolerance',0.,.2);control['absolute_tolerance_Wb']=number(control['absolute_tolerance_Wb'],'Absolute flux tolerance Wb',0.,1.)  #: Use dimensionless relative and explicit weber absolute tolerances with bounded finite values.
    if control['relative_tolerance']==0 and control['absolute_tolerance_Wb']==0:raise ValueError('At least one flux tolerance must be positive')  #: Reject a meaningless exact-equality target.
    if type(control['stable_intervals']) is not int or not 1<=control['stable_intervals']<=3:raise ValueError('Use 1..3 consecutive stable flux intervals')  #: Keep stability history within the four-pass pilot limit.
    control['surfaces']=[dict(id=s['id'],vertices_m=s['vertices_m']) for s in surfaces]  #: Retain only detached public SI input fields rather than derived normals or hidden defaults.
    return control  #: Return the complete declared criterion without changing physical geometry.


def flux_status(control,observations,previous=None):  #: Compare actual signed observations with one previous accepted mesh and its streak.
    names=[s['id'] for s in control['surfaces']]  #: Bind comparisons to explicit pickup identities and caller order.
    if not isinstance(observations,list) or len(observations)!=len(names) or [o.get('id') for o in observations]!=names:raise ValueError('Flux observations do not match requested pickup identities')  #: Refuse missing, reordered, duplicate or extra measurements.
    values=[o.get('flux_Wb') for o in observations]  #: Use signed weber flux, preserving reversals and near-zero values.
    if any(type(v) not in (float,int) or not math.isfinite(v) for v in values):raise ValueError('Flux observations must be finite signed numbers')  #: Prevent NaNs or truth values from satisfying a numerical comparison.
    if previous is not None and [r['id'] for r in previous['pickups']]!=names:raise ValueError('Previous flux identities changed')  #: Reject comparison across a different physical observation selection.
    records=[]  #: Preserve a separate error scale and decision for every pickup.
    for i,(name,value) in enumerate(zip(names,values)):  #: Check every selected triangle independently, avoiding cancellation of summed errors.
        old=previous['pickups'][i]['flux_Wb'] if previous is not None else None  #: Use only a completely accepted predecessor, never a rejected candidate.
        delta=abs(value-old) if old is not None else None;scale=max(abs(value),abs(old)) if old is not None else None  #: Preserve signed changes while defining a symmetric nonnegative relative scale.
        limit=control['absolute_tolerance_Wb']+control['relative_tolerance']*scale if scale is not None else None  #: Combine explicit weber and dimensionless tolerances without dividing by a near-zero flux.
        records.append(dict(id=name,flux_Wb=float(value),absolute_change_Wb=delta,allowed_change_Wb=limit,relative_change=delta/scale if scale else None,interval_met=delta<=limit if delta is not None else False))  #: Keep the initial interval undefined and expose every actual signed measurement/decision.
    interval=all(r['interval_met'] for r in records);streak=(previous['stable_intervals_observed']+1 if previous is not None else 1) if interval else 0  #: Reset the whole-selection streak whenever any pickup fails.
    return dict(pickups=records,interval_met=interval,stable_intervals_observed=streak,stable_intervals_required=control['stable_intervals'],stability_met=streak>=control['stable_intervals'],accuracy_certified=False)  #: Report only empirical successive-mesh stability, never a physical error bound.


def solve_flux_adaptive(request,cancel=None):  #: Solve a fixed physical source while monitoring every pickup on actual accepted meshes.
    if not isinstance(request,dict) or set(request)!={'model','max_passes','bulk_fraction','flux_control'}:raise ValueError('Supply model, max_passes, bulk_fraction and flux_control')  #: Keep this explicit alternative controller separate from original project and adaptive schemas.
    request=copy.deepcopy(request);control=validate_control(request['flux_control']);passes=request['max_passes']  #: Detach all source and pickup geometry before any solve.
    if type(passes) is not int or not 1<=passes<=4:raise ValueError('Use 1..4 flux-adaptive passes')  #: Preserve the current bounded pilot pass budget.
    bulk=number(request['bulk_fraction'],'Bulk fraction',.1,.9);request['flux_control']=control  #: Validate residual-driven marking independently of flux-stopping tolerances.
    check_cancel(cancel);initial=solve_loop_fem(request['model'],cancel);frame=dict(format='magnetics-studio.loop-transfer/1',input=initial['input'],source=initial['source'],mesh=initial['mesh'])  #: Retain a genuine source/reference baseline rather than invent a solved transfer field.
    tags,proof=bind_source(frame['source'],frame['mesh'],cancel);frame['mesh']['copper_source_cell']=tags  #: Verify complete original current support before native execution.
    history=[];previous=None;previous_energy=None;stop='pass_limit'  #: Preserve accepted states, undefined first changes and honest unmet-target stops.
    for step in range(passes):  #: Execute no more than the explicitly requested number of real native passes.
        check_cancel(cancel)  #: Never accept an interrupted or partially evaluated field.
        try:solution=solve_native_transfer(frame,0,cancel=cancel,flux_surfaces=control['surfaces'])  #: Integrate actual native polynomial flux on the same field/mesh being accepted.
        except ValueError as error:  #: Retain prior fields only for the known explicit mixed-space resource ceiling.
            if history and str(error)=='Native mixed loop space exceeds 45000 DOFs':stop='budget_limit';break  #: A rejected unsolved candidate cannot create a stability interval.
            raise  #: Propagate source, coverage, dependency and numerical defects.
        status=flux_status(control,solution['surface_flux'],previous);energy=solution['energy_J'];indicators=residual_indicators(frame,solution,cancel);total=math.fsum(indicators)  #: Measure genuine signed flux changes and the existing independent residual-marking proxy.
        record=dict(pass_number=step+1,tetrahedra=len(frame['mesh']['elements']),mixed_dofs=solution['mixed_dofs'],energy_J=energy,relative_energy_change=abs(energy/previous_energy-1) if previous_energy else None,relative_residual_indicator=math.sqrt(total/max(2*energy,1e-30)),source_binding=proof,source_gradient_compatibility=solution['source_gradient_compatibility'],surface_flux=solution['surface_flux'],flux_stability=status,mesh=frame['mesh'],cell_B_T=solution['B_at_cell_centroids_T'])  #: Store complete actual geometry/field, source proof, diagnostics and pickup-by-pickup stopping evidence.
        history.append(record);accepted_frame=frame;accepted_solution=solution;previous=status;previous_energy=energy  #: Accept only a completely solved and measured field with its actual mesh.
        if frame['source']['terminal_current_into_conductor_A']['high']==0:stop='zero_source';break  #: Avoid meaningless no-source refinement without declaring flux accuracy achieved.
        if status['stability_met']:stop='flux_stability_met';break  #: Identify the declared empirical criterion explicitly instead of calling it convergence or accuracy certification.
        if step+1==passes:break  #: Do not generate a mesh that will not be solved and measured.
        marked=[];mass=0.  #: Retain deterministic residual bulk marking independently of the stopping observable.
        for index in sorted(range(len(indicators)),key=lambda i:(-indicators[i],i)):  #: Rank genuinely computed cell indicators with stable identity ties.
            marked.append(index);mass+=indicators[index]  #: Accumulate the selected squared-indicator mass.
            if mass>=bulk*total:break  #: Stop at the smallest prefix covering the requested bulk fraction.
        record['marked_cells']=marked;record['marked_indicator_fraction']=mass/total if total else 0.  #: Persist the actual mark set and measured residual coverage.
        try:frame,proof=refine_frame(frame,set(marked),cancel)  #: Reuse native conforming refinement with exact original parent-affine current preservation.
        except ValueError as error:  #: Retain accepted fields for the explicitly declared candidate-memory ceiling only.
            if str(error).startswith('Adaptive source binding exceeds'):stop='budget_limit';break  #: Never attach accepted fields to an oversized unsolved candidate.
            raise  #: Do not disguise geometry or current-transfer failures as a normal stop.
    return dict(format='magnetics-studio.flux-adaptive-loop/1',input=request,initial_reference=initial,frame=accepted_frame,native=accepted_solution,history=history,stop_reason=stop,flux_stability=history[-1]['flux_stability'],accuracy_certified=False,scope='Fixed source/domain, native order-zero residual marking; empirical signed pickup-flux stability only')  #: Export exactly the final accepted mesh/field and a qualified empirical stopping result.
