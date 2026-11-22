"""Explicit same-owner bare-profile connection geometry; no FEM circuit terminals."""
import base64  #: Return only a fully checked fixed-name native archive.
import copy  #: Keep source,cut and connection packets detached during validation.
import hashlib  #: Bind exact source,cut packet and transferred STEP bytes.
import json  #: Serialize finite provenance and the physical/reference representation split.
import math  #: Compute independent path length,circular area,volume and geometric tolerances.
from pathlib import Path  #: Restrict staged outputs to private fixed-name worker files.
import re  #: Keep user link IDs safe before they become reference filenames.
import zipfile  #: Package only declared physical parts and labelled reference pieces.
from .mas_exchange import canonical  #: Compare immutable finite source/anchor metadata exactly.
from .project import number  #: Reuse strict finite nonboolean SI validation.
from .turn_ports import port_plan,draft_ports,measure_ports  #: Bind to actual cut faces and reuse transferred exposed-face checks.


def draft_links(project,ports):  #: Expose actual selected cut terminals without guessing connection routes.
    plan=port_plan(project,ports);terminals=[{**copy.deepcopy(t),'source':copy.deepcopy(c['source'])} for c in plan['cuts'] for t in c['terminals']]  #: Preserve each actual turn,layer,independent electrical owner,profile and signed excitation.
    return {'format':'magnetics-studio.turn-links/1','source_sha256':ports['source_sha256'],'ports_sha256':hashlib.sha256(canonical(ports)).hexdigest(),'terminals':terminals,'links':[]}  #: An empty draft is association data,not a joined winding or inferred network.


def link_plan(project,ports,packet):  #: Validate explicit directed paths between consecutive same-owner bare round or foil turns.
    draft=draft_links(project,ports)  #: Rebuild exact terminal/source association from the actual retained builder snapshot.
    if not isinstance(packet,dict) or set(packet)!=set(draft):raise ValueError('Link packet requires format,source_sha256,ports_sha256,terminals and links')  #: Reject null,missing and silently ignored declarations.
    if canonical({k:v for k,v in packet.items() if k!='links'})!=canonical({k:v for k,v in draft.items() if k!='links'}):raise ValueError('Link source,cut binding or terminals changed; create a new draft')  #: A changed slit or source cannot silently reuse previous endpoints.
    links=packet['links'];terms={t['id']:t for t in draft['terminals']};all_turns=draft_ports(project)['anchors'];seen=set();used=set();out=[];d=project['domain']  #: Resolve original electrical/turn order without connecting equal display names.
    if not isinstance(links,list) or not 1<=len(links)<=8:raise ValueError('Specify 1-8 explicit links')  #: Bound native path/contact/Boolean work and reject unedited drafts.
    for link in links:  #: Validate each proposed geometric connection independently before native execution.
        if not isinstance(link,dict) or set(link)!={'id','from_terminal','to_terminal','points_m'}:raise ValueError('Link fields must be id,from_terminal,to_terminal,points_m')  #: No inferred voltage,parallel network,material or manufacturing fields are accepted.
        name=link['id'];a=link['from_terminal'];b=link['to_terminal']  #: Keep route IDs and actual source-bound geometric terminal selection explicit.
        if not isinstance(name,str) or not re.fullmatch(r'[A-Za-z][A-Za-z0-9_-]{0,39}',name) or name in seen:raise ValueError('Link IDs must be unique safe names')  #: Reject filename traversal and duplicate identity.
        if not isinstance(a,str) or not isinstance(b,str) or a not in terms or b not in terms or a in used or b in used or not a.endswith(':right') or not b.endswith(':left'):raise ValueError('Use unique right-to-left selected terminals')  #: Forbid branching/reused terminals and preserve a directed two-ended chain convention.
        ta=terms[a]['source'];tb=terms[b]['source'];order=[t['id'] for t in all_turns if t['series_group']==ta['series_group']]  #: Use stable independent electrical group identity and actual original section/turn order.
        if ta['series_group']!=tb['series_group'] or order.index(tb['id'])!=order.index(ta['id'])+1:raise ValueError('Links require consecutive turns of the same independent electrical winding')  #: Reject cross-owner connections,cycles,self-links and skipped turns without changing interleaving.
        if any(t['profile'] not in ('round','rectangular') or 'litz' in t['kind'] for t in (ta,tb)) or ta['profile']!=tb['profile'] or any(abs(ta[k]-tb[k])>1e-12 for k in ('width_m','height_m','current_A')):raise ValueError('Links require matching bare round or foil profiles,dimensions and signed source current')  #: Reject mixed profiles,dimension mismatch,litz envelopes and conflicting sources before native execution.
        width=ta['width_m'];height=ta['height_m'];profile=ta['profile'];radius=width/2 if profile=='round' else math.hypot(width,height)/2;span=2*radius;area=math.pi*radius*radius if profile=='round' else width*height;points=link['points_m']  #: Preserve circle dimensions while bounding rectangular transport by its conservative circumcircle and independent width-times-height area.
        if not isinstance(points,list) or not 2<=len(points)<=12:raise ValueError('Specify 2-12 explicit SI path points')  #: Bound native sweep complexity without autorouting or fitting missing coordinates.
        clean=[]  #: Validate declared values without moving endpoints or silently smoothing bends.
        for point in points:  #: Keep all coordinates in the original solver XYZ frame.
            if not isinstance(point,list) or len(point)!=3:raise ValueError('Each path point needs three SI coordinates')  #: Reject mixed dimensions and ambiguous coordinate data.
            clean.append([number(v,'Link coordinate m',radius,d[k]-radius) for v,k in zip(point,('width','height','depth'))])  #: Require finite nonboolean coordinates with conservative radius clearance inside the actual domain.
        if math.dist(clean[0],terms[a]['centre_m'])>1e-12 or math.dist(clean[-1],terms[b]['centre_m'])>1e-12:raise ValueError('Link endpoints must match their actual cut-face centres')  #: No hidden snapping,bridging of a gap or unreviewed terminal relocation.
        vectors=[[v-u for u,v in zip(x,y)] for x,y in zip(clean,clean[1:])];lengths=[math.sqrt(sum(v*v for v in delta)) for delta in vectors]  #: Compute independent Euclidean segment lengths from explicit coordinates.
        if any(length<=span+1e-6 or sum(abs(v)>1e-12 for v in delta)!=1 for delta,length in zip(vectors,lengths)):raise ValueError('Path segments must be axis-aligned and longer than the profile bounding diameter plus 1 micrometre')  #: Keep either mitered profile nondegenerate and explicitly bounded.
        units=[[v/length for v in delta] for delta,length in zip(vectors,lengths)]  #: Derive actual incoming/outgoing directions without altering path values.
        if any(abs(v-n)>1e-10 for v,n in zip(units[0],terms[a]['outward_normal'])) or any(abs(v+n)>1e-10 for v,n in zip(units[-1],terms[b]['outward_normal'])) or any(abs(sum(u*v for u,v in zip(x,y)))>1e-10 for x,y in zip(units,units[1:])):raise ValueError('Path needs outward/inward terminal tangency and explicit right-angle bends')  #: Reject reversed entry,foldback and unsupported bend conventions.
        for i in range(len(vectors)):  #: Conservatively reject nonadjacent centreline approaches before native solid checks.
            for j in range(i+2,len(vectors)):  #: Adjacent segments share their deliberately specified bend.
                distance=math.sqrt(sum(max(0,min(clean[i][k],clean[i+1][k])-max(clean[j][k],clean[j+1][k]),min(clean[j][k],clean[j+1][k])-max(clean[i][k],clean[i+1][k]))**2 for k in range(3)))  #: Axis-aligned zero-width segment boxes give the exact closest centreline distance.
                if distance<=span+2e-9:raise ValueError('Link path self-approach or crossing')  #: Reject obvious self-shortening/interference; native validity and independent volume remain mandatory.
        seen.add(name);used.update((a,b));out.append({'id':name,'from_terminal':a,'to_terminal':b,'turn_ids':[ta['id'],tb['id']],'series_group':ta['series_group'],'points_m':clean,'profile':profile,'width_m':width,'height_m':height,'area_m2':area,'bound_radius_m':radius,**({'diameter_m':width} if profile=='round' else {}),'length_m':math.fsum(lengths),'expected_volume_m3':area*math.fsum(lengths)})  #: Preserve explicit directed incidence and independent profile-area-times-length expectation;only circles declare a diameter.
    groups=[];remaining={t for link in out for t in link['turn_ids']}  #: Derive geometric connected components without changing electrical project definitions.
    while remaining:  #: Every selected turn belongs to exactly one exported joined component.
        members={min(remaining)};changed=True  #: Start a deterministic bounded graph traversal.
        while changed:  #: Expand only explicitly declared graph adjacency.
            before=len(members);members.update(t for link in out if members.intersection(link['turn_ids']) for t in link['turn_ids']);changed=len(members)!=before  #: Never connect by proximity,display name or container membership.
        ordered=[t['id'] for t in all_turns if t['id'] in members];groups.append(ordered);remaining-=members  #: Retain original physical turn/section order inside each component.
    return {'chain_coverage':chain_coverage(all_turns,out,groups),'packet':copy.deepcopy(packet),'links':out,'components':groups,'used_terminals':sorted(used),'limitations':['Explicit bare-round/foil right-angle mitered connections are CAD geometry only; no FEM terminal,circuit or finite-current solve','No autorouting,bend-radius,contact-resistance,manufacturing or creepage qualification','Only consecutive same-owner matching bare profiles; litz and mixed-source connections rejected; native foil end-orientation contact must pass','Original ideal-sheet currents,materials,turn/layer order and field results remain unchanged']}  #: State the narrow connection model and unsupported physical implications.


def chain_coverage(turns,links,groups):  #: Derive declared ordered chain coverage only after the common source/graph/path validator has succeeded.
    owners=list(dict.fromkeys(t['series_group'] for t in turns));by_id={t['id']:t for t in turns};chains=[];windings=[]  #: Preserve stable independent winding and original physical section/turn order.
    for index,members in enumerate(groups,1):  #: Match the same deterministic component order used by native joined output.
        owner=by_id[members[0]]['series_group'];whole=[t['id'] for t in turns if t['series_group']==owner];selected={tuple(link['turn_ids']):link for link in links if set(link['turn_ids'])<=set(members)}  #: Resolve actual directed adjacency without depending on packet link order or display names.
        transitions=[{'link_id':selected[(a,b)]['id'],'from_turn':a,'to_turn':b,'from_layer':by_id[a]['layer_id'],'to_layer':by_id[b]['layer_id'],'crosses_section':by_id[a]['layer_id']!=by_id[b]['layer_id']} for a,b in zip(members,members[1:])]  #: Expose every physical section transition in the original electrical turn order.
        chains.append({'id':'chain_'+str(index),'series_group':owner,'turn_ids':copy.deepcopy(members),'link_ids':[t['link_id'] for t in transitions],'section_order':list(dict.fromkeys(by_id[t]['layer_id'] for t in members)),'source_ids':list(dict.fromkeys(by_id[t]['source_id'] for t in members)),'transitions':transitions,'free_terminal_ids':[members[0]+':left',members[-1]+':right'],'covers_entire_source_winding':members==whole,'excluded_turn_ids':[t for t in whole if t not in members]})  #: Explicitly distinguish one partial component from coverage of all source turns;free faces are planned geometric labels only.
    for owner in owners:  #: Account for every independent winding,including untouched ones outside the selected links.
        whole=[t for t in turns if t['series_group']==owner];selected=[c for c in chains if c['series_group']==owner];joined={t for c in selected for t in c['turn_ids']}  #: Do not silently drop unconnected source turns or another winding inside a named container.
        windings.append({'series_group':owner,'source_turn_ids':[t['id'] for t in whole],'source_layer_order':list(dict.fromkeys(t['layer_id'] for t in whole)),'chain_ids':[c['id'] for c in selected],'unlinked_turn_ids':[t['id'] for t in whole if t['id'] not in joined],'status':'complete_declared_chain' if len(selected)==1 and selected[0]['covers_entire_source_winding'] else 'partial' if selected else 'unconnected'})  #: A complete label requires exactly one declared chain covering every source turn;it is never a field/circuit-solve claim.
    return {'format':'magnetics-studio.chain-coverage/1','scope':'declared_connectivity_only','chains':chains,'windings':windings,'limitations':['Planned adjacency does not prove native contact;inspect verified_chain on a completed exported component','Complete declared chain means all source winding turns in one geometric chain;no FEM current/voltage terminals or solved network','Untouched windings and unlinked turns remain explicit;source materials,currents and interleaving are unchanged']}  #: Keep the metadata preview physically qualified as planned connectivity even when retained inside a completed native manifest.


def export_links(project,directory,ports,packet):  #: Join actual checked slit-turn solids through explicitly declared round or rectangular paths.
    from .turn_cad import export_turn_cad  #: Reuse all existing source,turn,STEP,bore,volume and collision checks first.
    plan=link_plan(project,ports,packet);result=export_turn_cad(project,directory,turn_ports=ports);m=result['geometry_manifest'];dest=Path(directory)  #: Complete the actual source-bound cut geometry inside the same isolated worker.
    import cadquery as cq  #: Load native geometry only for the explicitly requested isolated CAD operation.
    bodies={b['id']:b for b in m['bodies']};shapes={key:cq.importers.importStep(str(dest/b['file'])).val() for key,b in bodies.items() if b['kind']!='ideal_source_sheet'};leads=[];contacts=[];checks=0  #: Ideal mathematical sheets are not physical obstacles or contact surfaces.
    def face_at(shape,centre):  #: Resolve an actual planar terminal cap by geometric centre after transfer.
        v=cq.Vector(*[x*1000 for x in centre]);matches=[f for f in shape.Faces() if f.geomType()=='PLANE' and (f.Center()-v).Length<2e-6]  #: Use the established2nm geometric-centre tolerance,not transient face indices.
        if len(matches)!=1:raise ValueError('Connection cap missing or ambiguous')  #: A label or outer bound is insufficient evidence of a full contact face.
        return matches[0]  #: Return exactly one actual planar native surface.
    def transfer(shape,name,expected):  #: Verify exact newly serialized lead/component bytes before using their geometry.
        file=dest/name;file.parent.mkdir(parents=True,exist_ok=True);cq.exporters.export(shape,str(file));data=file.read_bytes();back=cq.importers.importStep(str(file)).val();volume=back.Volume()/1e9;box=back.BoundingBox()  #: Reimport the exact millimetre STEP file that will be delivered.
        if b'SI_UNIT(.MILLI.,.METRE.)' not in data or not back.isValid() or len(back.Solids())!=1 or abs(volume-expected)>max(1e-18,expected*1e-7):raise ValueError('Connection STEP topology,units or independent volume mismatch')  #: Reject corrupt,disconnected,self-overlapping or wrongly scaled geometry.
        record={'file':name,'sha256':hashlib.sha256(data).hexdigest(),'bytes':len(data),'valid':True,'measured_volume_m3':volume,'expected_volume_m3':expected,'bounds_m':{a+e:getattr(box,a+('min' if e=='0' else 'max'))/1000 for a in 'xyz' for e in ('0','1')}}  #: Bind actual measured SI bounds/volume to the exact transferred bytes.
        return back,record  #: Use only reimported accepted shapes for contact,collision and joining checks.
    terms={t['id']:t for t in draft_links(project,ports)['terminals']}  #: Rebuild exact original geometric endpoint ownership once.
    for link in plan['links']:  #: Build each explicit path with the original bare-wire profile.
        points=[cq.Vector(*[v*1000 for v in p]) for p in link['points_m']];wire=cq.Wire.makePolygon(points);plane=cq.Plane(origin=points[0],xDir=(0,1,0),normal=points[1]-points[0]);sketch=cq.Workplane(plane)  #: Fix the original cut-face radial width along global Y and axial height along Z before explicit path transport.
        sketch=sketch.circle(link['diameter_m']*500) if link['profile']=='round' else sketch.rect(link['width_m']*1000,link['height_m']*1000);tube=sketch.sweep(wire,transition='right').val()  #: Sweep the actual circle or rectangle without silently rotating the destination profile or adding a twist.
        tube,record=transfer(tube,'reference/lead_'+link['id']+'.step',link['expected_volume_m3']);record.update({**link,'id':'lead_'+link['id'],'kind':'reference_lead_in_joined_component'})  #: Keep standalone leads explicitly in the reference representation,not double-counted physical parts.
        radius=link['bound_radius_m']  #: Bound the entire axis-aligned swept lead inside its independently declared centreline envelope;rectangles use a circumcircle bound.
        if any(record['bounds_m'][a+'0']<min(p[k] for p in link['points_m'])-radius-2e-9 or record['bounds_m'][a+'1']>max(p[k] for p in link['points_m'])+radius+2e-9 for k,a in enumerate('xyz')):raise ValueError('Lead STEP exceeds declared path envelope')  #: Reject unexpected miter/scale/placement growth even if volume matches.
        for terminal in (link['from_terminal'],link['to_terminal']):  #: Prove both intended complete profile surface contacts before fusion.
            t=terms[terminal];owner=t['source']['id'];f=face_at(shapes[owner],t['centre_m']);g=face_at(tube,t['centre_m']);area=link['area_m2'];common=f.intersect(g).Area()/1e6;overlap=tube.intersect(shapes[owner]).Volume()/1e9  #: Face/face common area is required because touching solid intersections may contain no face topology.
            if abs(common-area)>max(1e-18,area*1e-7) or sum(a*b for a,b in zip(f.normalAt().toTuple(),g.normalAt().toTuple()))>-.99999999 or overlap>max(1e-18,link['expected_volume_m3']*1e-8):raise ValueError('Intended lead contact incomplete,reversed or penetrating its owner turn')  #: Require opposing full-area profile caps and reject hidden intersections elsewhere in either intended turn.
            contacts.append({'link_id':link['id'],'terminal_id':terminal,'common_area_m2':common,'overlap_m3':overlap,'owner_area_m2':f.Area()/1e6,'lead_area_m2':g.Area()/1e6,'normal_dot':sum(a*b for a,b in zip(f.normalAt().toTuple(),g.normalAt().toTuple()))})  #: Record measured intended contact separately from graph incidence metadata.
        for key,other in list(shapes.items())+[(x['id'],s) for x,s in leads]:  #: Check core,other turns and previously accepted leads without treating sheets as solids.
            if key in link['turn_ids']:continue  #: Intended owners were checked through exact cap area and penetrating-volume tests above.
            checks+=1  #: Count actual native distance tests against unintended physical contact.
            if checks>1500 or tube.distance(other)/1000<=2e-9:raise ValueError('Lead collision or unintended contact: '+link['id']+' with '+key)  #: Reject touching as well as penetrating unrelated geometry;2nm is a numerical guard,not manufacturing clearance.
        leads.append((record,tube))  #: Retain only fully checked transferred lead geometry for later joining.
    components=[];reference=[]  #: Separate the physical joined representation from its inspectable original input pieces.
    for index,members in enumerate(plan['components'],1):  #: Fuse each explicitly connected same-owner chain exactly once.
        selected=[(r,s) for r,s in leads if set(r['turn_ids'])<=set(members)];parts=[shapes[t] for t in members]+[s for _,s in selected];expected=math.fsum(bodies[t]['measured_volume_m3'] for t in members)+math.fsum(r['measured_volume_m3'] for r,_ in selected)  #: With zero-volume cap contacts,the independent component volume is the sum of disjoint accepted volumes.
        joined=parts[0].fuse(*parts[1:]).clean();joined,record=transfer(joined,'joined_'+str(index)+'.step',expected);record.update(id='joined_'+str(index),kind='joined_'+selected[0][0]['profile']+'_turn_geometry_not_solved_copper',turn_ids=members,series_group=selected[0][0]['series_group'])  #: Require one valid reimported connected solid,not a compound of adjacent unjoined pieces.
        record.update(source_ids=[bodies[t]['source_id'] for t in members],layer_ids=[bodies[t]['layer_id'] for t in members],logical_circuit_id=bodies[members[0]]['logical_circuit_id'],electrical_winding_id=bodies[members[0]]['electrical_winding_id'],current_A=bodies[members[0]]['current_A'])  #: Preserve original section/container/independent winding ownership and signed source metadata on the joined physical representation.
        expected_bounds={a+e:(min if e=='0' else max)(r['bounds_m'][a+e] for r in [bodies[t] for t in members]+[r for r,_ in selected]) for a in 'xyz' for e in ('0','1')}  #: Predict component outer bounds independently as the union of verified source pieces and leads.
        if any(abs(record['bounds_m'][k]-v)>2e-9 for k,v in expected_bounds.items()):raise ValueError('Joined component bounds changed')  #: Fusion must not move or create surviving geometry.
        record['exposed_terminals']=[]  #: Verify the actual remaining end faces after internal contacts have disappeared.
        for cut in m['turn_ports_geometry']['cuts']:  #: Preserve each original source-bound cut's terminal labels.
            if cut['turn_id'] not in members:continue  #: Ignore unrelated still-separate slit turns.
            exposed={**cut,'terminals':[t for t in cut['terminals'] if t['id'] not in plan['used_terminals']]};record['exposed_terminals']+=measure_ports(joined,exposed)  #: Measure only unconsumed original terminal faces on the final transferred component.
            for t in cut['terminals']:  #: Consumed caps must no longer remain boundary faces of the joined solid.
                if t['id'] in plan['used_terminals'] and any(f.geomType()=='PLANE' and (f.Center()-cq.Vector(*[x*1000 for x in t['centre_m']])).Length<2e-6 for f in joined.Faces()):raise ValueError('Consumed terminal remains an exposed face')  #: Reject a false join that merely retains coincident internal cap boundaries.
        if len(record['exposed_terminals'])!=2:raise ValueError('Joined chain must retain exactly two geometric end faces')  #: Reject closed loops,branching or missing endpoints even if a native solid looks valid.
        chain=plan['chain_coverage']['chains'][index-1];actual=[t['id'] for t in record['exposed_terminals']]  #: Bind this actual transferred component to its independently ordered declared chain.
        if set(actual)!=set(chain['free_terminal_ids']):raise ValueError('Native chain ends differ from declared connectivity')  #: Two arbitrary measured faces cannot qualify the wrong source/section traversal.
        record['verified_chain']={**copy.deepcopy(chain),'native_verified':True,'measured_free_terminal_ids':actual}  #: Mark only the fully checked exported component as natively joined;the separate preview remains unverified metadata.

        for key,other in shapes.items():  #: Preserve isolation from all other original physical parts.
            if key in members:continue  #: Internal selected turns belong to this one explicitly joined component.
            checks+=1  #: Include actual component distance tests in the bounded work count.
            if checks>1500 or joined.distance(other)/1000<=2e-9:raise ValueError('Joined component unintended contact: '+key)  #: Do not accept old zero-volume touches as electrically isolated connections.
        for prior,shape in components:  #: Keep independently joined components isolated as separate physical/electrical owners.
            if joined.distance(shape)/1000<=2e-9:raise ValueError('Joined components touch')  #: Spatial contact cannot silently connect independent declared chains.
        components.append((record,joined))  #: Keep only one actual accepted physical solid per declared chain.
        for key in members:  #: Preserve exact original slit-turn bytes under an explicitly reference-only path.
            body=bodies[key];target='reference/'+Path(body['file']).name;(dest/target).parent.mkdir(exist_ok=True);(dest/target).write_bytes((dest/body['file']).read_bytes());body['file']=target;reference.append(body)  #: The original verified hash remains valid because reference relocation does not rewrite STEP bytes.
    selected_ids={t for members in plan['components'] for t in members};m['bodies']=[b for b in m['bodies'] if b['id'] not in selected_ids]+[r for r,_ in components]  #: Replace joined inputs in the physical representation to avoid duplicate overlapping conductors.
    m.update(format='magnetics-studio.field-cad/'+('7' if any(x['profile']=='rectangular' for x in plan['links']) else '6'),connection_geometry={**plan,'reference_pieces':reference,'reference_leads':[r for r,_ in leads],'contacts':contacts,'native_contact_checks':checks});m['limitations']+=plan['limitations']  #: Record explicit graph,physical/reference roles,measured contacts and unchanged field-solver limits.
    (dest/'geometry_manifest.json').write_text(json.dumps(m,indent=2,allow_nan=False));archive=dest/'model_geometry.zip'  #: Publish only complete finite connection provenance after every native gate succeeds.
    with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED) as z:  #: Include exactly the declared checked physical/reference files.
        for name in [b['file'] for b in m['bodies']]+[b['file'] for b in reference]+[r['file'] for r,_ in leads]+['geometry_manifest.json']:z.write(dest/name,name)  #: Keep original inputs available for review without treating them as additional physical bodies.
    with zipfile.ZipFile(archive) as z:  #: Verify serialized neutral-CAD transport after joining.
        if z.testzip() is not None:raise RuntimeError('Connected CAD ZIP integrity failure')  #: Never return a corrupt completed result.
    result['cad_files']={'model_geometry.zip':base64.b64encode(archive.read_bytes()).decode('ascii')};return result  #: Existing field_result,ideal currents,materials and PDE equations remain unchanged.
