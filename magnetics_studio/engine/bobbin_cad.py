"""Explicit source-bound bobbin ring segments/flanges; geometry, not field insulation."""
import copy  #: Preserve accepted source projects and user part data during detached validation.
import math  #: Compute the independent rounded-ring swept volume in SI units.
import re  #: Restrict part IDs before they become fixed worker filenames.
from .mas_exchange import canonical  #: Compare finite source/association metadata without display-name aliases.
from .project import number  #: Reuse finite typed SI-number validation instead of guessing units.
from .turn_cad import turn_plan  #: Anchor every explicit part to the actual rebuilt spatial winding/source geometry.


def draft_bobbin(project):  #: Expose source binding and available layer anchors without inventing bobbin dimensions.
    plan=turn_plan(project);anchors=[]  #: Require the same exact source consistency and physical turn-fit checks as existing CAD.
    for layer in plan['layer_order']:  #: Preserve the actual original physical section order.
        turn=next(t for t in plan['turns'] if t['layer_id']==layer)  #: Read an actual completed turn path around this rectangular limb.
        anchors.append({k:copy.deepcopy(turn[k]) for k in ('layer_id','source_id','series_group','logical_circuit_id','electrical_winding_id','limb','limb_width_m','stack_depth_m','source_window_m')})  #: Retain unambiguous independent electrical/source identity and SI geometry, not an inferred connection graph.
        anchors[-1]['centre_xy_m']=turn['centre_m'][:2]  #: Declare the physical limb centreline explicitly in the solver XYZ frame.
    return {'format':'magnetics-studio.bobbin-parts/1','source_sha256':plan['source_sha256'],'anchors':anchors,'parts':[]}  #: An empty editable draft is data only and is not a checked/exported bobbin.


def bobbin_plan(project,packet):  #: Validate deliberately specified sleeve segments/flanges against one exact field-source snapshot.
    draft=draft_bobbin(project)  #: Rebuild source-derived anchors rather than trusting packet geometry claims.
    if not isinstance(packet,dict) or set(packet)!=set(draft):raise ValueError('Bobbin packet requires format, source_sha256, anchors and parts')  #: Reject ambiguous or silently unused fields.
    if canonical({k:packet[k] for k in packet if k!='parts'})!=canonical({k:draft[k] for k in draft if k!='parts'}):raise ValueError('Bobbin source binding or anchors changed; create a new draft')  #: Prevent stale/raw-edited geometry from being accepted as current-source CAD.
    parts=packet['parts'];anchors={a['layer_id']:a for a in draft['anchors']}  #: Resolve owners through actual layer IDs, never equal display names.
    if not isinstance(parts,list) or not 1<=len(parts)<=16:raise ValueError('Specify 1-16 explicit bobbin parts')  #: Bound native sweep and collision work without inferring missing geometry.
    fields={'id','kind','anchor_layer_id','owner_layer_ids','inner_offset_m','radial_thickness_m','z0_m','z1_m'};seen=set();bodies=[]  #: Define the complete supported dimensional/editable contract.
    d=turn_plan(project)['project']['domain']  #: Read the actual finite spatial domain in the same source frame.
    for part in parts:  #: Validate each user-defined part independently before a native job can replace accepted state.
        if not isinstance(part,dict) or set(part)!=fields:raise ValueError('Explicit bobbin part fields differ from the supported contract')  #: Do not silently ignore dimensional, material or electrical fields.
        name=part['id']  #: Keep the original user ID for provenance, with a fixed native filename prefix below.
        if not isinstance(name,str) or not re.fullmatch(r'[A-Za-z][A-Za-z0-9_-]{0,39}',name) or name in seen:raise ValueError('Bobbin part IDs must be unique safe names')  #: Reject collisions and path traversal before output filenames exist.
        seen.add(name)  #: Require one declared physical part for each unique ID.
        if part['kind'] not in ('sleeve_segment','flange'):raise ValueError('Bobbin kind must be sleeve_segment or flange')  #: Both supported parts are explicit rounded rectangular rings, not arbitrary CAD.
        if not isinstance(part['anchor_layer_id'],str) or part['anchor_layer_id'] not in anchors:raise ValueError('Unknown bobbin anchor layer')  #: Bind dimensions to an existing source limb/layer.
        anchor=anchors[part['anchor_layer_id']];owners=part['owner_layer_ids']  #: Keep physical ownership separate from series/parallel electrical connectivity.
        if not isinstance(owners,list) or not owners or any(not isinstance(x,str) or x not in anchors for x in owners) or len(set(owners))!=len(owners):raise ValueError('Bobbin owners need unique existing layer IDs')  #: Prevent missing, duplicated or invalid owner membership.
        for owner in owners:  #: Shared physical geometry is allowed only around the same exact source limb base.
            if anchors[owner]['limb']!=anchor['limb'] or any(abs(anchors[owner][k]-anchor[k])>1e-12 for k in ('limb_width_m','stack_depth_m')) or any(abs(a-b)>1e-12 for a,b in zip(anchors[owner]['centre_xy_m'],anchor['centre_xy_m'])):raise ValueError('Shared bobbin owners must use the same limb geometry')  #: Permit only round-off within one picometre on the same limb base; do not reposition geometry or connect unrelated sources.
        inner=number(part['inner_offset_m'],'Bobbin inner offset m',1e-6,1);wall=number(part['radial_thickness_m'],'Bobbin radial thickness m',1e-6,1)  #: Require explicit positive finite SI dimensions and reject booleans.
        z0=number(part['z0_m'],'Bobbin z0 m',0,d['depth']);z1=number(part['z1_m'],'Bobbin z1 m',0,d['depth'])  #: Preserve the declared axial position rather than infer a full-height sleeve.
        if z1-z0<1e-6:raise ValueError('Bobbin axial extent must be at least 1 micrometre')  #: Avoid reversed/zero/degenerate native profiles.
        r=inner+wall/2;w=anchor['limb_width_m'];depth=anchor['stack_depth_m'];cx,cy=anchor['centre_xy_m'];height=z1-z0  #: Derive the centre path from explicit inner/outer offsets around the source base.
        if cx-w/2-inner-wall<0 or cx+w/2+inner+wall>d['width'] or cy-depth/2-inner-wall<0 or cy+depth/2+inner+wall>d['height']:raise ValueError('Explicit bobbin exceeds the source domain')  #: Reject out-of-domain geometry before launching native operations.
        bodies.append({'id':'bobbin_'+name,'kind':'explicit_bobbin_'+part['kind']+'_not_field_region','user_part_id':name,'anchor_layer_id':part['anchor_layer_id'],'owners':[copy.deepcopy(anchors[x]) for x in owners],'profile':'rectangular','width_m':wall,'height_m':height,'centre_m':[cx,cy,(z0+z1)/2],'limb_width_m':w,'stack_depth_m':depth,'path_offset_m':r,'path_length_m':2*(w+depth)+2*math.pi*r,'expected_volume_m3':wall*height*(2*(w+depth)+2*math.pi*r)})  #: Use the exact ring area difference/swept volume and preserve ownership without changing any winding source.
    return {'packet':copy.deepcopy(packet),'bodies':bodies,'limitations':['Explicit ring segments/flanges are export-only geometry, not a complete bobbin or solved dielectric region','No automatic placement, leads, winding connections, pitch, creepage or manufacturing clearance certification','Positive-volume native collisions are rejected; touching surfaces and required insulation distances need separate qualification']}  #: State what explicit data and later native checks do and do not establish.
