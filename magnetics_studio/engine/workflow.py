"""Circuit -> independent electrical windings -> physical sections.
Circuit is a named container (as in the supplied MATLAB manager), NOT an
instruction to force all primary/secondary windings into one series circuit.
"""
import copy,math,re
from .project import number


def ident(value,label,limit=40):
    if not isinstance(value,str) or not re.fullmatch(r'[A-Za-z0-9_-]{1,'+str(limit)+'}',value):raise ValueError(label+' must use a bounded number of letters, digits, _ or -')
    return value


def integer(v,label,lo=1,hi=1000):
    number(v,label,lo,hi)
    if int(v)!=v:raise ValueError(label+' must be an integer')
    return int(v)


def upgrade(spec):
    """Retain v0.5 section geometry while making its implicit windings explicit."""
    s=copy.deepcopy(spec)
    if s.get('workflow_version')==2:return s
    groups={};layout=[]
    for i,sec in enumerate(s.get('sections',[])):
        old=sec.get('circuit','Winding');key=str(old)
        if key not in groups:
            w=copy.deepcopy(sec);w.update(id='w'+str(len(groups)+1),name=key,turns=0,limbs=[],n_layers=0,turn_orientation='vertical',phase_deg=0,nameplate=copy.deepcopy(s.get('nameplate',{})));groups[key]=w
        w=groups[key];w['turns']+=sec['turns']
        if sec['limb'] not in w['limbs']:w['limbs'].append(sec['limb'])
        layout.append({'id':'legacy_'+str(i+1),'circuit_id':'c1','winding_id':w['id'],'limb':sec['limb'],'turns':sec['turns'],'build_mm':sec.get('build_mm',0),'height_override_mm':sec.get('height_override_mm',0),'turns_per_layer':sec.get('turns_per_layer',sec['turns'])})
    if not groups:raise ValueError('Builder needs at least one winding')
    for w in groups.values():
        for key,value in {'conductivity_MSm':58,'turn_insulation_mm':s['packing'].get('turn_insulation_mm',.1),'tape_mm':s['packing'].get('section_insulation_mm',.5),'bobbin_mm':s['packing'].get('bobbin_mm',.5),'clearance_mm':s['packing'].get('clearance_mm',.5),'tape_part_number':'','tape_material':'Insulation','bobbin_part_number':'','bobbin_material':'Bobbin'}.items():w.setdefault(key,value)
    s['workflow_version']=2;s['circuits']=[{'id':'c1','name':'Circuit 1','winding_count':len(groups),'arrangement':'interleaved' if len(layout)>len(groups) else 'single','orientation':s['packing'].get('orientation','radial'),'windings':list(groups.values())}]
    s['layout']=layout;s['custom_sections']=True;s['excitation_mode']='instantaneous';s['snapshot_angle_deg']=0;s['workflow_note']='Upgraded v0.5: former circuit labels are now separate windings in Circuit 1. Existing explicit section geometry is preserved until packing is regenerated.';s.pop('sections',None)
    return s


def definitions(spec):
    circuits=spec.get('circuits',[])
    if not isinstance(circuits,list) or not 1<=len(circuits)<=8:raise ValueError('Define 1–8 named circuit containers')
    lookup={};ids=set();names=set();layers=[]
    for ci in circuits:
        cid=ident(ci.get('id'),'Circuit ID');name=ci.get('name','').strip()
        if cid in ids or name in names or not name:raise ValueError('Circuit IDs and names must be nonempty and unique')
        ids.add(cid);names.add(name)
        if ci.get('arrangement') not in ['single','multilayer','interleaved']:raise ValueError('Choose single, multilayer or interleaved arrangement per circuit')
        if ci.get('orientation') not in ['radial','axial']:raise ValueError('Choose radial/horizontal or axial/vertical section stacking')
        windings=ci.get('windings',[])
        if not isinstance(windings,list) or len(windings)!=integer(ci.get('winding_count',len(windings)),'Winding count',1,16):raise ValueError('Circuit winding count does not match its winding definitions')
        wids=set();wnames=set();by_w=[]
        for w in windings:
            wid=ident(w.get('id'),'Winding ID');wn=w.get('name','').strip();key=(cid,wid)
            if wid in wids or wn in wnames or not wn:raise ValueError('Winding IDs and names must be unique within each circuit')
            wids.add(wid);wnames.add(wn);turns=integer(w['turns'],'Winding total turns',1,1000);number(w.get('current_A',0),'Winding current',-1e6,1e6);number(w.get('phase_deg',0),'Winding phase',-36000,36000)
            limbs=w.get('limbs',[])
            if not isinstance(limbs,list) or not limbs or len(set(limbs))!=len(limbs):raise ValueError('Select unique wound limbs for each winding')
            for limb in limbs:integer(limb,'Wound limb',0,4)
            if ci['arrangement']=='single' and len(limbs)!=1:raise ValueError('Single arrangement permits one limb per winding')
            if w.get('turn_orientation','vertical') not in ['horizontal','vertical']:raise ValueError('Choose horizontal/vertical turn placement')
            tpl=turns if ci['arrangement']=='single' else integer(w.get('turns_per_layer',turns),'Turns per layer',1,1000)
            needed=math.ceil(turns/tpl);declared=integer(w.get('n_layers',0),'Number of layers',0,1000)
            if not spec.get('custom_sections') and declared and declared!=needed:raise ValueError(f'{name}/{wn}: layers must equal ceil(turns / turns per layer), or use 0 for automatic')
            if not spec.get('custom_sections') and needed<len(limbs):raise ValueError('Every selected limb needs at least one layer')
            for quantity,unit in [('frequency','Hz'),('voltage','V'),('current','A'),('power','W')]:
                np=w.get('nameplate',{})
                lo=number(np.get(quantity+'_min_'+unit,0),quantity+' minimum',0,1e9);hi=number(np.get(quantity+'_max_'+unit,0),quantity+' maximum',0,1e9)
                if lo>hi:raise ValueError('Winding nameplate '+quantity+' minimum exceeds maximum')
            lookup[key]=(ci,w);wl=[]
            for j in range(needed):wl.append({'id':cid+'__'+wid+'__layer_'+str(j+1),'circuit_id':cid,'winding_id':wid,'limb':limbs[j%len(limbs)],'turns':min(tpl,turns-j*tpl)})
            by_w.append(wl)
        if ci['arrangement']=='interleaved':
            for j in range(max(map(len,by_w))):
                for wl in by_w:
                    if j<len(wl):layers.append(wl[j])
        else:
            for wl in by_w:layers.extend(wl)
    if len(lookup)>16:raise ValueError('This release supports at most 16 independently excited electrical windings')
    return lookup,layers


def expand(spec):
    s=copy.deepcopy(spec);lookup,expected=definitions(s);layout=s.get('layout') or expected
    if not isinstance(layout,list) or not 1<=len(layout)<=64:raise ValueError('Use 1–64 physical winding layers/sections')
    if not s.get('custom_sections'):
        emap={r['id']:r for r in expected}
        if len(layout)!=len(expected) or {r.get('id') for r in layout}!=set(emap):raise ValueError('Winding packing changed. Regenerate the interleaving layout.')
        for row in layout:
            if any(row.get(k)!=emap[row['id']][k] for k in ['circuit_id','winding_id','limb','turns']):raise ValueError('Interleaving section does not match its winding layer; regenerate packing')
    ids=set();totals={key:0 for key in lookup};used={key:set() for key in lookup};sections=[];limb_orientation={}
    excitation=s.get('excitation_mode','instantaneous')
    if excitation not in ['instantaneous','sinusoidal_snapshot']:raise ValueError('Choose instantaneous currents or a sinusoidal current snapshot')
    angle=number(s.get('snapshot_angle_deg',0),'Snapshot phase',-36000,36000)
    for row in layout:
        rid=ident(row.get('id'),'Layer ID',120)
        if rid in ids:raise ValueError('Every layer/section must occur once in the layout')
        ids.add(rid);key=(row.get('circuit_id'),row.get('winding_id'))
        if key not in lookup:raise ValueError('Section references an undefined circuit/winding')
        ci,w=lookup[key];limb=integer(row.get('limb'),'Layer limb',0,4);turns=integer(row.get('turns'),'Layer turns',1,1000)
        if limb not in w['limbs']:raise ValueError('Section limb is not selected for its winding')
        if limb in limb_orientation and limb_orientation[limb]!=ci['orientation']:raise ValueError('Circuits sharing a limb must use the same layer stacking direction')
        limb_orientation[limb]=ci['orientation'];totals[key]+=turns;used[key].add(limb)
        sec=copy.deepcopy(w);group=ci['id']+'__'+w['id'];display=ci['name']+' / '+w['name'];sec.update(circuit=group,name=display+' · '+rid,display_group_name=display,limb=limb,turns=turns,logical_circuit_id=ci['id'],logical_circuit_name=ci['name'],electrical_winding_id=w['id'],electrical_winding_name=w['name'],series_group=ci['id']+'__'+w['id'],layer_id=rid,stack_orientation=ci['orientation'])
        if s.get('custom_sections'):
            for k in ['build_mm','height_override_mm','turns_per_layer']:sec[k]=row.get(k,sec.get(k,0))
        else:sec['turns_per_layer']=turns if w.get('turn_orientation','vertical')=='vertical' else 1
        sec['current_A']=w.get('current_A',0)*(math.cos(math.radians(angle+w.get('phase_deg',0))) if excitation=='sinusoidal_snapshot' else 1)
        sections.append(sec)
    for key,(_,w) in lookup.items():
        if totals[key]!=w['turns'] or used[key]!=set(w['limbs']):raise ValueError('Section turns/limbs do not match the declared electrical winding; regenerate layout')
    s['layout']=copy.deepcopy(layout);normal=copy.deepcopy(s);normal['sections']=sections
    return normal,s,lookup
