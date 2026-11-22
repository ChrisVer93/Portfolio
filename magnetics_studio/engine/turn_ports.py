"""Explicit slit-turn terminal geometry; no connected winding or field terminal source."""
import copy  #: Keep source projects and editable packets detached during validation.
import math  #: Compute independent circular terminal cross-sections in SI units.
from .mas_exchange import canonical  #: Bind one exact finite source snapshot and immutable turn anchors.
from .project import number  #: Reuse finite nonboolean typed SI validation.


def draft_ports(project):  #: Expose real ordered turn identities without inventing cut dimensions.
    from .turn_cad import turn_plan  #: Avoid a module import cycle while sharing actual source/packing validation.
    plan=turn_plan(project)  #: Reject stale recipes, unsupported dimensions and physically unfit individual turns.
    keys=('id','layer_id','source_id','series_group','logical_circuit_id','electrical_winding_id','turn_in_section','profile','kind','width_m','height_m','centre_m','limb_width_m','stack_depth_m','path_offset_m','current_A')  #: Preserve independent electrical ownership, geometry and signed source excitation.
    return {'format':'magnetics-studio.turn-ports/1','source_sha256':plan['source_sha256'],'anchors':[{k:copy.deepcopy(t[k]) for k in keys} for t in plan['turns']],'cuts':[]}  #: Return an empty source-bound draft, not an automatically cut winding.


def port_plan(project,packet):  #: Validate deliberately requested straight-side cuts on exact existing turns.
    draft=draft_ports(project)  #: Derive immutable association afresh from the actual field source.
    if not isinstance(packet,dict) or set(packet)!=set(draft):raise ValueError('Turn-port packet requires format, source_sha256, anchors and cuts')  #: Reject null, missing and silently ignored fields.
    if canonical({k:v for k,v in packet.items() if k!='cuts'})!=canonical({k:v for k,v in draft.items() if k!='cuts'}):raise ValueError('Turn-port source binding or anchors changed; create a new draft')  #: Prevent stale or edited anchor metadata from silently relocating terminal geometry.
    cuts=packet['cuts'];anchors={t['id']:t for t in draft['anchors']};seen=set();out=[]  #: Resolve cuts by stable actual turn ID, never display names.
    if not isinstance(cuts,list) or not 1<=len(cuts)<=16:raise ValueError('Specify 1-16 turn cuts')  #: Bound native cut/face work and reject unedited empty drafts.
    for cut in cuts:  #: Validate each selected physical turn independently before accepting a job.
        if not isinstance(cut,dict) or set(cut)!={'turn_id','gap_m'}:raise ValueError('Turn cut requires only turn_id and gap_m')  #: Do not accept inferred paths, voltages, materials or dielectric parameters.
        key=cut['turn_id']  #: Keep user selection separate from fixed native output filenames.
        if not isinstance(key,str) or key not in anchors or key in seen:raise ValueError('Turn cuts need unique existing turn IDs')  #: Reject missing/duplicate membership before native work.
        seen.add(key);t=anchors[key];gap=number(cut['gap_m'],'Turn gap m',1e-6,1)  #: Require explicit positive finite SI gap dimensions without boolean coercion.
        if gap+2*t['width_m']>t['limb_width_m']:raise ValueError('Turn cut must remain on the top straight side with one conductor-width corner margins')  #: Keep the slit away from rounded corners and preserve a nondegenerate remaining path.
        cx,cy,z=t['centre_m'];y=cy+t['stack_depth_m']/2+t['path_offset_m'];area=math.pi*t['width_m']**2/4 if t['profile']=='round' else t['width_m']*t['height_m']  #: Derive exact top-straight centre and actual bare/bundle cross-sectional area.
        out.append({'turn_id':key,'gap_m':gap,'centre_m':[cx,y,z],'area_m2':area,'removed_volume_m3':area*gap,'terminals':[{'id':key+':left','centre_m':[cx-gap/2,y,z],'outward_normal':[1,0,0]},{'id':key+':right','centre_m':[cx+gap/2,y,z],'outward_normal':[-1,0,0]}],'source':copy.deepcopy(t)})  #: Record geometric terminal centres/normals without assigning new electrical boundary conditions or changing source polarity.
    return {'packet':copy.deepcopy(packet),'cuts':out,'limitations':['Slit turns have two geometric faces, not leads, connected multi-turn windings or FEM current/voltage terminals','Original signed ideal-sheet currents, turns, material laws and field results are unchanged','Round/foil geometry is bare; litz remains a bundle envelope, not resolved strands or connected copper','No creepage, manufacturing clearance, circuit topology, impedance or dielectric-field qualification']}  #: Keep geometric progress distinct from electrical/physical solver coverage.


def slit(cq,solid,body,cut):  #: Remove one explicit straight-side section before exporting the exact turn solid.
    cx,cy,z=[x*1000 for x in cut['centre_m']];epsilon=.001  #: Use existing millimetre CAD units with a declared1micrometre cutter overshoot outside the conductor profile.
    cutter=cq.Workplane('XY').box(cut['gap_m']*1000,body['width_m']*1000+2*epsilon,body['height_m']*1000+2*epsilon).translate((cx,cy,z)).val()  #: Cut only the selected top straight cross-section with exact X separation.
    opened=solid.cut(cutter);expected=body['expected_volume_m3']-cut['removed_volume_m3']  #: Subtract the independently derived area-times-gap volume from the original closed ring.
    if not opened.isValid() or len(opened.Solids())!=1 or abs(opened.Volume()/1e9-expected)>max(1e-18,expected*1e-7):raise ValueError('Invalid slit-turn topology or removed volume')  #: Reject failed cuts, disconnected fragments or wrong dimensions before writing STEP.
    body.update(expected_closed_volume_m3=body['expected_volume_m3'],expected_volume_m3=expected,kind='slit_'+body['kind'],terminal_cut=copy.deepcopy(cut))  #: Preserve original closed-volume provenance and label the changed export-only representation.
    return opened  #: Return one actual open-ended solid without moving any surviving conductor geometry.


def measure_ports(imported,cut):  #: Verify actual terminal faces only after STEP bytes have been reimported.
    import cadquery as cq  #: Load the already qualified native API only while measuring an exported solid.
    measured=[]  #: Require a distinct actual planar face for each predicted cut terminal.
    for terminal in cut['terminals']:  #: Preserve left/right geometric identity without inventing a winding connection.
        matches=[f for f in imported.Faces() if f.geomType()=='PLANE' and (f.Center()-cq.Vector(*[x*1000 for x in terminal['centre_m']])).Length<2e-6]  #: Find the actual planar cross-section centre within2nm in serialized millimetre geometry.
        if len(matches)!=1:raise ValueError('Slit-turn terminal face missing or ambiguous')  #: An outer bounding box alone cannot establish two usable terminal surfaces.
        face=matches[0];normal=face.normalAt().toTuple();area=face.Area()/1e6  #: Measure transferred surface orientation and actual SI cross-sectional area.
        if any(abs(a-b)>1e-8 for a,b in zip(normal,terminal['outward_normal'])) or abs(area-cut['area_m2'])>max(1e-18,cut['area_m2']*1e-7):raise ValueError('Slit-turn terminal area or orientation mismatch')  #: Reject reversed faces, partial cuts and wrong profile/unit scaling.
        measured.append({**terminal,'measured_area_m2':area,'measured_outward_normal':normal,'measured_centre_m':[x/1000 for x in face.Center().toTuple()]})  #: Bind terminal metadata to actual reimported surface measures, not persistent native face numbering.
    return measured  #: Face indices are deliberately not claimed stable across later CAD operations.
