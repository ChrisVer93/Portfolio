"""P002C2B: closed rounded-rectangle turns/sleeves, separate from solved sheets."""
import base64  #: Transport only fully checked fixed-name CAD archive bytes.
import hashlib  #: Bind the complete field-source snapshot and new geometry to exact bytes.
import json  #: Store finite winding/layer/turn identity and geometric provenance.
import math  #: Compute independent swept-path length, cross-section and volume expectations.
from pathlib import Path  #: Keep staged output under the private worker directory.
import zipfile  #: Bundle old checked field geometry and new checked turn/sleeve files together.
from .builder import build, conductor  #: Reuse actual shared geometry/packing validation and conductor dimensions.
from .geometry_cad import export_cad, AXES  #: Retain established qualified STEP units, field parts and ideal source sheets unchanged.
from .mas_exchange import canonical  #: Compare finite source data without display-name aliases.
from .project import validate  #: Validate the detached exact source snapshot before planning geometry.
from .workflow import expand  #: Preserve ordered layer IDs, independent winding IDs and signed snapshot excitation.


def turn_plan(project):  #: Derive supported physical turn paths from a source-consistent builder model.
    p=validate(project)  #: Never mutate a caller's accepted field model during CAD planning.
    if p['mode']!='3d' or not isinstance(p.get('builder'),dict): raise ValueError('Closed-turn CAD requires a 3D builder model; use the builder then Use model')  #: Reject arbitrary boxes or planar extrusions as if they defined spatial turns.
    built=build(p['builder']);actual=built['project'];normal,saved,lookup=expand(actual['builder'])  #: Rebuild the real source hierarchy and complete section-packing summary.
    if saved['family'] not in ('e_core','two_limb','five_limb','planar'): raise ValueError('Closed-turn CAD requires rectangular limbs')  #: Do not infer curved/toroidal winding paths from unsupported core geometry.
    for key in ('mode','domain','regions','materials','windings','circuit_definitions'):  #: Keep field/source/material assignments exactly associated with this retained recipe.
        if canonical(p.get(key))!=canonical(actual.get(key)): raise ValueError('Builder and current '+key+' differ; rebuild with Use model before turn CAD')  #: Reject stale raw field edits instead of silently changing winding geometry or currents.
    if sum(s['turns'] for s in normal['sections'])>64: raise ValueError('Closed-turn CAD pilot supports at most 64 total turns')  #: Bound native sweep/export/collision work separately from field mesh budgets.
    turns=[];sleeves={};seen=set()  #: Preserve each turn and deduplicate physically identical sleeves without connecting electrical windings.
    for sec,stat,winding in zip(normal['sections'],built['summary']['sections'],actual['windings']):  #: Retain the user's actual physical section/interleaving order.
        w,h,copper=conductor(sec);ins=sec.get('turn_insulation_mm',saved['packing'].get('turn_insulation_mm',.1));n=sec['turns'];tpl=stat['turns_per_layer'];box=winding['window']  #: Use the same bare dimensions, insulation and row/layer counts as the builder.
        if stat['build_mm']+1e-9<stat['layers']*(w+2*ins) or stat['height_mm']+1e-9<min(tpl,n)*(h+2*ins): raise ValueError('Section '+sec['layer_id']+' is a homogenised block whose individual turns do not fit')  #: Refuse to squeeze real conductors into an allowed overfilled source block.
        distance=stat['radial_inner_mm'];radius=(distance+stat['build_mm']/2)/1000;cx=(box['x0']+box['x1'])/2;cy=(box['y0']+box['y1'])/2  #: Recover physical limb/depth centrelines from the exact ideal source window.
        limb_width=box['x1']-box['x0']-2*radius;depth=box['y1']-box['y0']-2*radius  #: Remove declared mean-radius offsets, not display clamping or a hidden coordinate rotation.
        if min(limb_width,depth)<=0: raise ValueError('Turn CAD needs positive limb width and stack depth')  #: Reject degenerate native path geometry before CAD import.
        common={'layer_id':sec['layer_id'],'source_id':winding['id'],'series_group':sec['series_group'],'logical_circuit_id':sec['logical_circuit_id'],'electrical_winding_id':sec['electrical_winding_id'],'limb':stat['limb'],'current_A':winding['current'],'source_window_m':dict(box)}  #: Attach real electrical and field-source identities to every geometric turn.
        for j in range(n):  #: Generate each declared turn exactly once without changing source ampere-turns.
            layer,row=divmod(j,tpl);r=(distance+ins+w/2+layer*(w+2*ins))/1000;z=(box['z0']+box['z1']-min(tpl,n)*(h+2*ins)/1000)/2+(ins+h/2+row*(h+2*ins))/1000  #: Match the original 2D builder's row/radial packing, centred within the actual section envelope.
            length=2*(limb_width+depth)+2*math.pi*r;round_wire=sec.get('conductor','round') in ('round','litz');area=math.pi*(w/1000)**2/4 if round_wire else w*h/1e6  #: Use the actual closed rounded path length and geometric profile area, not the old rectangular-sheet estimate.
            turns.append({'id':'turn_'+str(len(turns)+1),'kind':'litz_bundle_envelope_not_strands' if sec.get('conductor')=='litz' else 'bare_closed_turn_geometry_not_solved_copper',**common,'turn_in_section':j+1,'radial_row':layer,'axial_row':row,'profile':'round' if round_wire else 'rectangular','width_m':w/1000,'height_m':h/1000,'copper_area_m2_metadata':copper/1e6,'insulation_per_side_m':ins/1000,'centre_m':[cx,cy,z],'limb_width_m':limb_width,'stack_depth_m':depth,'path_offset_m':r,'path_length_m':length,'expected_volume_m3':area*length})  #: Keep litz bundle geometry distinct from strand/copper volume and field material regions.
        key=(stat['limb'],sec['series_group'])  #: Create one source-declared sleeve on the first section of each winding/limb pair.
        if key not in seen:  #: Later sections of the same winding do not duplicate the first bobbin sleeve.
            seen.add(key);b=sec.get('bobbin_mm',saved['packing'].get('bobbin_mm',.5))/1000;clear=sec.get('clearance_mm',saved['packing'].get('clearance_mm',.5))/1000  #: Retain declared bobbin thickness and axial core clearance without inventing flange dimensions.
            if b>0:  #: Zero-thickness bobbin metadata does not create a fake native solid.
                lo=(saved.get('air_padding_mm',25)+saved['core']['bottom_yoke_mm'])/1000+clear;hi=lo+saved['core']['window_height_mm']/1000-2*clear;r=(distance/1000-b/2)  #: Place only a rounded sleeve in the declared clearance interval, separate from the field's incomplete insulation walls.
                if r<=b/2 or hi<=lo: raise ValueError('Sleeve needs positive inner radius and axial height; increase core clearance')  #: Avoid degenerate zero-radius sweeps rather than altering the source clearance.
                shape_key=(cx,cy,limb_width,depth,r,b,lo,hi)  #: Merge exact geometric aliases only; winding owners remain explicit independent IDs.
                sleeve=sleeves.setdefault(shape_key,{'id':'sleeve_'+str(len(sleeves)+1),'kind':'bobbin_sleeve_only_no_flanges_not_field_region','owners':[],'profile':'rectangular','width_m':b,'height_m':hi-lo,'centre_m':[cx,cy,(lo+hi)/2],'limb_width_m':limb_width,'stack_depth_m':depth,'path_offset_m':r,'path_length_m':2*(limb_width+depth)+2*math.pi*r,'expected_volume_m3':b*(hi-lo)*(2*(limb_width+depth)+2*math.pi*r)})  #: Record analytical sleeve volume independently of the native CAD kernel.
                sleeve['owners'].append({'series_group':sec['series_group'],'limb':stat['limb']})  #: Shared physical sleeves never imply electrical series/parallel connections.
    return {'format':'magnetics-studio.closed-turn-plan/1','project':p,'turns':turns,'sleeves':list(sleeves.values()),'layer_order':[s['layer_id'] for s in normal['sections']],'source_sha256':hashlib.sha256(canonical(p)).hexdigest(),'limitations':['Rounded paths are a stated geometric completion around rectangular limbs, distinct from existing rectangular ideal source sheets','Closed rings are individually labelled, not a connected multi-turn winding; no leads, pitch, transitions, terminals or circuit topology inferred','Round profiles are bare solids; litz is a round bundle envelope, not resolved strands or copper fill','Sleeves have no flanges, tape, creepage or clearance certification; not a complete bobbin or solved insulation region','No CAD-to-FEM remesh, finite-conductor current/eddy loss, changed solver, curved core or external validation']}  #: State the exact association and unsupported electrical/manufacturing/field implications in exported data.


def export_turn_cad(project,output_directory,include_sleeves=False,bobbin_parts=None,turn_ports=None):  #: Generate checked turns with optional explicit slit terminals and bobbin geometry.
    if type(include_sleeves) is not bool: raise ValueError('include_bobbin_sleeves must be boolean')  #: Keep optional geometric completion explicit at the direct native API boundary too.
    if bobbin_parts is not None and include_sleeves:raise ValueError('Explicit bobbin parts and inferred sleeves are mutually exclusive')  #: Prevent hidden mixing of explicit dimensional intent with inferred full-height geometry.
    from .bobbin_cad import bobbin_plan  #: Reuse lightweight packet validation while keeping the circular turn dependency local to this optional export.
    extra=bobbin_plan(project,bobbin_parts) if bobbin_parts is not None else {'bodies':[],'limitations':[]}  #: Validate every explicit source-bound dimension before native export starts.
    from .turn_ports import port_plan,slit,measure_ports  #: Share explicit cut validation and actual terminal-face checks without changing ordinary exports.
    ports=port_plan(project,turn_ports) if turn_ports is not None else {'cuts':[],'limitations':[]};cut_by_id={c['turn_id']:c for c in ports['cuts']}  #: Validate exact selected turn identities and SI gaps before native geometry begins.
    plan=turn_plan(project);result=export_cad(project,output_directory,False);manifest=result['geometry_manifest'];destination=Path(output_directory)  #: Reuse existing version-gated core/source STEP checks, omitting overlapping decorative bulk envelopes.
    plan['sleeve_candidates']=plan['sleeves'];plan['sleeves']=plan['sleeves'] if include_sleeves else [];plan['sleeves_requested']=include_sleeves  #: Keep original candidate/source data visible while distinguishing actual exported sleeves from unverified candidates.
    import cadquery as cq  #: Load the established native kernel only inside the isolated optional worker.
    shapes=[]  #: Retain exact imported physical core parts for positive-volume collision checks.
    for body in manifest['bodies']:  #: Existing ideal source sheets are not solids or obstacles to the added turn geometry.
        if body['kind']=='field_region':  #: Cache exact source solid measures once rather than recomputing them for every turn.
            shape=cq.importers.importStep(str(destination/body['file'])).val();shapes.append((body,shape,shape.BoundingBox(),shape.Volume()/1e9))  #: Compare against actual transferred material with reusable native bounds/volume.
    added=[];checks=0  #: Track new body provenance and bounded actual native intersection work.
    for body in plan['turns']+plan['sleeves']+extra['bodies']:  #: Check every explicit bobbin ring after the original turns/sleeves, retaining all original turn and layer order.
        print('Closed-turn CAD: '+body['id'],flush=True)  #: Expose actual native progress through the existing bounded worker log.
        cx,cy,z=[v*1000 for v in body['centre_m']];r=body['path_offset_m']*1000;w=body['width_m']*1000;h=body['height_m']*1000  #: Convert all source SI dimensions once to the established millimetre STEP kernel convention.
        wire=cq.Workplane('XY',origin=(cx,cy,z)).rect(body['limb_width_m']*1000+2*r,body['stack_depth_m']*1000+2*r).val();path=wire.fillet2D(r,wire.Vertices());edge=path.Edges()[0]  #: Complete a tangent closed rounded rectangle around the real rectangular column.
        profile=cq.Workplane(cq.Plane(origin=edge.startPoint(),xDir=(0,0,1),normal=edge.tangentAt(0)))  #: Orient the profile with axial height along Z and radial thickness normal to the path.
        profile=profile.circle(w/2) if body['profile']=='round' else profile.rect(h,w)  #: Use exact circular bare/bundle geometry or the actual rectangular/foil cross-section.
        solid=profile.sweep(path,isFrenet=True).val()  #: Retain the established closed ring before any deliberately requested source-bound cut.
        if body['id'] in cut_by_id:solid=slit(cq,solid,body,cut_by_id[body['id']])  #: Remove only the explicitly selected straight portion; all other turn/core/source geometry stays original.
        file=destination/(body['id']+'.step');cq.exporters.export(solid,str(file));data=file.read_bytes();imported=cq.importers.importStep(str(file)).val()  #: Export and reimport the exact completed closed solid before trusting a native success.
        if b'SI_UNIT(.MILLI.,.METRE.)' not in data or not imported.isValid() or len(imported.Solids())!=1: raise RuntimeError('Invalid closed-turn STEP topology/units: '+body['id'])  #: Require one valid real solid and declared exchange units, not an attractive preview.
        expected={'x0':body['centre_m'][0]-body['limb_width_m']/2-(r+w/2)/1000,'x1':body['centre_m'][0]+body['limb_width_m']/2+(r+w/2)/1000,'y0':body['centre_m'][1]-body['stack_depth_m']/2-(r+w/2)/1000,'y1':body['centre_m'][1]+body['stack_depth_m']/2+(r+w/2)/1000,'z0':body['centre_m'][2]-h/2000,'z1':body['centre_m'][2]+h/2000}  #: Predict all six outer bounds independently from the path/profile specification.
        box=imported.BoundingBox();measured={a+e:getattr(box,a+('min' if e=='0' else 'max'))/1000 for a in AXES for e in ('0','1')};volume=imported.Volume()/1e9  #: Measure actual serialized/reimported bounds and SI volume.
        if any(abs(measured[k]-v)>2e-9 for k,v in expected.items()) or abs(volume-body['expected_volume_m3'])>max(1e-18,body['expected_volume_m3']*1e-7): raise RuntimeError('Closed-turn STEP bounds/volume mismatch: '+body['id'])  #: Catch scale, path, placement, missing return and cross-section errors independently of validity.
        if body['id'] in cut_by_id:body['measured_terminals']=measure_ports(imported,cut_by_id[body['id']])  #: Verify two distinct transferred planar cross-sections with actual areas, centres and outward normals.
        if imported.isInside(cq.Vector(cx,cy,z),1e-7): raise RuntimeError('Closed-turn bore is filled: '+body['id'])  #: A valid solid with the right outer bounds must still retain its physical central bore.
        for other_body,other,ob,other_volume in shapes:  #: Reuse exact native bounds/volume while checking prior solids without modifying geometry.
            if any(min(getattr(box,a+'max'),getattr(ob,a+'max'))-max(getattr(box,a+'min'),getattr(ob,a+'min'))<=1e-7 for a in AXES): continue  #: Touching/disjoint bounds have no positive-volume overlap.
            if all(abs(other_body.get(k,float('inf'))-body[k])<1e-12 for k in ('limb_width_m','stack_depth_m')) and all(abs(a-b)<1e-12 for a,b in zip(other_body.get('centre_m',[float('inf')]*3)[:2],body['centre_m'][:2])):  #: Recognise only genuinely coaxial loops around the same exact rectangular base.
                if abs(other_body['path_offset_m']-body['path_offset_m'])>=(other_body['width_m']+body['width_m'])/2-1e-12: continue  #: Disjoint radial profile bands cannot intersect, including round and nested sleeve geometry.
            if all(getattr(ob,a+'min')>=c-base/2-1e-7 and getattr(ob,a+'max')<=c+base/2+1e-7 for a,c,base in [('x',cx,body['limb_width_m']*1000),('y',cy,body['stack_depth_m']*1000)]): continue  #: The original rectangular limb footprint lies entirely inside every positive-radius bore; avoid expensive guaranteed-empty Booleans.
            checks+=1  #: Count only actual native intersection candidates.
            if checks>1500: raise ValueError('Turn CAD exceeds 1500 collision checks; simplify winding geometry')  #: Fail explicitly before unbounded native pair work.
            overlap=imported.intersect(other).Volume()/1e9  #: Independently measure true solid overlap rather than assuming nested bounds imply a collision.
            if overlap>max(1e-18,min(volume,other_volume)*1e-8): raise ValueError('Closed-turn CAD overlap: '+body['id']+' with '+other_body['id'])  #: Reject penetrating cores/turns/sleeves instead of publishing an impossible geometry.
        shapes.append((body,imported,box,volume));body.update(file=file.name,sha256=hashlib.sha256(data).hexdigest(),bytes=len(data),bounds_m=measured,measured_volume_m3=volume,valid=True);added.append(body)  #: Cache each accepted native measure and bind checked geometry/identities to exact serialized bytes.
    manifest.update(format='magnetics-studio.field-cad/3',closed_turn_geometry=plan,closed_turn_collision_checks=checks);manifest['bodies']+=added;manifest['limitations']+=plan['limitations']  #: Version the additive geometric representation without changing or claiming a new field solution.
    if bobbin_parts is not None:manifest.update(format='magnetics-studio.field-cad/4',explicit_bobbin_geometry=extra);manifest['limitations']+=extra['limitations']  #: Version the explicitly dimensioned parts without altering earlier export contracts or field results.
    if turn_ports is not None:manifest.update(format='magnetics-studio.field-cad/5',turn_ports_geometry=ports);manifest['limitations']+=ports['limitations']  #: Version slit-turn terminal geometry independently of unchanged field-source and earlier CAD contracts.
    (destination/'geometry_manifest.json').write_text(json.dumps(manifest,indent=2,allow_nan=False));archive=destination/'model_geometry.zip'  #: Publish finite complete provenance only after every added solid passes checks.
    with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED) as z:  #: Replace the staged base archive with all checked fixed-name parts, not arbitrary paths.
        for name in [b['file'] for b in manifest['bodies']]+['geometry_manifest.json']:z.write(destination/name,name)  #: Include exactly the declared checked core/source/turn/sleeve files.
    with zipfile.ZipFile(archive) as z:  #: Check transport integrity after all native geometry work.
        if z.testzip() is not None: raise RuntimeError('Closed-turn CAD ZIP integrity failure')  #: Never return corrupt completed geometry.
    result['cad_files']={'model_geometry.zip':base64.b64encode(archive.read_bytes()).decode('ascii')}  #: Return exact checked archive bytes through the existing cancellable CAD result protocol.
    return result  #: Preserve field_result and all existing PDE/source equations; these solids remain geometry only.
