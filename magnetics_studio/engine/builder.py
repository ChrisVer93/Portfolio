"""Guided magnetic geometry builder adapted from the user's MATLAB workflow.
All dimensions in the builder are mm; generated FEM projects use SI units.
"""
import copy
import json
import math
from pathlib import Path
from .project import number,validate
from .polygon_mesh import vertices

ROOT=Path(__file__).resolve().parents[1]
FAMILIES={'two_limb':2,'e_core':3,'five_limb':5,'planar':3,'toroid':0}


def defaults():
    return {'name':'Builder transformer','mode':'2d','family':'e_core','part_number':'Custom EE',
        'core':{'limbs_mm':[10,20,10],'windows_mm':[20,20],'window_height_mm':50,'top_yoke_mm':10,'bottom_yoke_mm':10,'depth_mm':30,'inner_diameter_mm':35,'outer_diameter_mm':65,'gaps':[{'limb':1,'count':1,'length_mm':.5}]},
        'material':{'name':'Custom ferrite','mu_r':2200,'law':'linear','bh':[],'conductivity_MSm':0,'temperature_C':25,'density_kg_m3':0},
        'packing':{'representation':'blocks','orientation':'radial','bobbin_mm':.5,'clearance_mm':.5,'section_insulation_mm':.5,'turn_insulation_mm':.1,'circle_segments':20},
        'sections':[{'circuit':'P','name':'Primary','limb':1,'turns':12,'current_A':1,'conductor':'round','diameter_mm':1.4,'width_mm':1.4,'height_mm':1.4,'turns_per_layer':12,'build_mm':3,'height_override_mm':36,'strands':100,'strand_diameter_mm':.1},
                    {'circuit':'S','name':'Secondary','limb':1,'turns':12,'current_A':0,'conductor':'round','diameter_mm':1.4,'width_mm':1.4,'height_mm':1.4,'turns_per_layer':12,'build_mm':3,'height_override_mm':36,'strands':100,'strand_diameter_mm':.1}],
        'nameplate':{'frequency_min_Hz':80000,'frequency_max_Hz':150000,'voltage_min_V':400,'voltage_max_V':800,'current_min_A':0,'current_max_A':40,'power_min_W':0,'power_max_W':27000,'electrical_angle_deg':0},
        'air_padding_mm':25,'mesh_subdivisions':28}


def catalog():
    return {'defaults':defaults(),'materials':json.loads((ROOT/'data/material_catalog.json').read_text()),'presets':json.loads((ROOT/'data/builder_presets.json').read_text())}


def finite(v,label,minimum=0,maximum=10000):
    return number(v,label,minimum,maximum)


def integer(v,label,lo=1,hi=300):
    finite(v,label,lo,hi)
    if int(v)!=v:raise ValueError(label+' must be an integer')
    return int(v)


def shapes_overlap(a,b):
    """Strict convex SAT: touching boundaries do not count as overlap."""
    ap,bp=vertices(a),vertices(b)
    for poly in [ap,bp]:
        for p,q in zip(poly,poly[1:]+poly[:1]):
            axis=(-(q[1]-p[1]),q[0]-p[0]);aa=[sum(x*y for x,y in zip(v,axis)) for v in ap];bb=[sum(x*y for x,y in zip(v,axis)) for v in bp]
            if min(max(aa),max(bb))-max(min(aa),min(bb))<=1e-10*math.hypot(*axis):return False
    return True


def conductor(section):
    kind=section.get('conductor','round')
    if kind not in ['round','litz','rectangular','foil']:raise ValueError('Choose round, litz, rectangular or foil conductor')
    if kind in ['round','litz']:
        w=h=finite(section['diameter_mm'],'Bundle/wire diameter',.005)
        area=math.pi*w*w/4
        if kind=='litz':
            strands=integer(section.get('strands',1),'Litz strands',1,100000)
            strand=finite(section.get('strand_diameter_mm',.1),'Strand diameter',.001)
            area=strands*math.pi*strand*strand/4
            if area>math.pi*w*w/4*.91:raise ValueError('Litz copper area exceeds the bundle envelope; increase bundle diameter')
    else:
        w=finite(section['width_mm'],'Conductor radial width',.005);h=finite(section['height_mm'],'Conductor axial height',.005);area=w*h
    return w,h,area


def build(specification):
    s=copy.deepcopy(specification);workflow=None;definitions=None
    if s.get('workflow_version')==2:
        from .workflow import expand
        s,workflow,definitions=expand(s)
    family=s.get('family');mode=s.get('mode')
    if family not in FAMILIES or mode not in ['2d','3d']:raise ValueError('Choose a supported core family and 2D/3D mode')
    if family=='toroid' and mode=='3d':raise ValueError('Toroidal builder currently uses a 2D annular section; curved 3D cores are not supported')
    c=s['core'];pack=s['packing'];mat=s['material'];sections=s.get('sections',[])
    if not 1<=len(sections)<=64:raise ValueError('Define 1–64 winding sections')
    rep=pack.get('representation','blocks');orientation=pack.get('orientation','radial')
    if rep not in ['blocks','turns'] or orientation not in ['radial','axial']:raise ValueError('Choose blocks/turns and radial/axial packing')
    if mode=='3d' and rep=='turns':raise ValueError('Individual-turn geometry is a 2D option; 3D uses ideal closed sheet sources')
    bobbin=finite(pack.get('bobbin_mm',.5),'Bobbin thickness');clearance=finite(pack.get('clearance_mm',.5),'Core clearance');tape=finite(pack.get('section_insulation_mm',.5),'Section insulation');ins=finite(pack.get('turn_insulation_mm',.1),'Turn insulation')
    segments=integer(pack.get('circle_segments',20),'Round-wire facets',8,64)
    depth=finite(c['depth_mm'],'Stack depth',.01);pad=finite(s.get('air_padding_mm',25),'Air padding',1);mesh=integer(s.get('mesh_subdivisions',28),'Mesh subdivisions',4,100 if mode=='2d' else 24)
    if mat.get('law','linear') not in ['linear','bh']:raise ValueError('Material law must be linear or bh')
    if mode=='3d' and mat.get('law')=='bh':raise ValueError('Nonlinear B–H is available in 2D; choose an explicit linear permeability for 3D')
    mu=finite(mat.get('mu_r',2200),'Relative permeability',1,1e6)
    finite(mat.get('conductivity_MSm',0),'Core conductivity',0,1000);finite(mat.get('density_kg_m3',0),'Core density',0,100000);finite(mat.get('temperature_C',25),'Material temperature',-273.15,10000)
    material={'id':'core','name':str(mat.get('name','Core'))[:120],'mu_r':mu,'color':'#678ca6','characteristics':copy.deepcopy(mat)}
    if mat.get('law')=='bh':material['bh']=copy.deepcopy(mat.get('bh',[]));
    if mat.get('law')=='bh' and not material.get('bh'):raise ValueError('Paste or select a B–H curve')
    p={'name':str(s.get('name','Built magnetic model'))[:240],'mode':mode,'materials':[{'id':'air','name':'Air','mu_r':1,'color':'#20334b'},material,{'id':'copper','name':'Copper / current region','mu_r':1,'color':'#d69a63'},{'id':'insulation','name':'Bobbin / insulation','mu_r':1,'color':'#70a4a2'}],'regions':[],'windings':[],'builder':s}
    notes=['Frequency, temperature, conductivity and nameplate data are retained; the solve is magnetostatic with the selected permeability/B–H curve. No AC or thermal material scaling.']
    circuits={};section_stats=[];envelopes=[];core_regions=[]
    def box(id,name,material,x0,x1,y0,y1,**extra):
        r={'id':id,'name':name,'material':material,'x0':x0,'x1':x1,'y0':y0,'y1':y1,**extra};p['regions'].append(r);return r
    def shape(id,name,material,cx,cy,w,h,round_wire=False,**extra):
        r=box(id,name,material,cx-w/2,cx+w/2,cy-h/2,cy+h/2,**extra)
        if round_wire:
            r['polygon']=[[cx+w/2*math.cos(2*math.pi*j/segments),cy+h/2*math.sin(2*math.pi*j/segments)] for j in range(segments)]
            r.update(x0=min(v[0] for v in r['polygon']),x1=max(v[0] for v in r['polygon']),y0=min(v[1] for v in r['polygon']),y1=max(v[1] for v in r['polygon']))
        return r
    if family=='toroid':
        din=finite(c['inner_diameter_mm'],'Inner diameter',1);dout=finite(c['outer_diameter_mm'],'Outer diameter',din+.1);width=height=dout;cx=cy=pad+dout/2;ri=din/2;ro=dout/2
        gaps=c.get('gaps',[]);n=sum(integer(g.get('count',0),'Gap count',0,12) for g in gaps);length=sum(g.get('count',0)*finite(g.get('length_mm',0),'Gap length') for g in gaps);angle=length/max(n,1)/((ri+ro)/2)
        if n and (length<=0 or angle*n>=math.pi):raise ValueError('Toroid total gap length must be positive and less than half its mean circumference')
        intervals=[(2*math.pi*j/n+angle/2,2*math.pi*(j+1)/n-angle/2) for j in range(n)] if n else [(0,2*math.pi)]
        for a,b in intervals:
            count=max(1,math.ceil((b-a)/(2*math.pi)*64))
            for j in range(count):
                u=a+(b-a)*j/count;v=a+(b-a)*(j+1)/count
                poly=[[cx+ri*math.cos(u),cy+ri*math.sin(u)],[cx+ro*math.cos(u),cy+ro*math.sin(u)],[cx+ro*math.cos(v),cy+ro*math.sin(v)],[cx+ri*math.cos(v),cy+ri*math.sin(v)]]
                core_regions.append(box('core_'+str(len(core_regions)),'Annular core facet','core',min(t[0] for t in poly),max(t[0] for t in poly),min(t[1] for t in poly),max(t[1] for t in poly),polygon=poly))
        limbs=[];window_height=din;bottom=0
        notes.append('Toroid: planar XY annular magnetic section, with + current in the bore and − return outside. Curvature is faceted; axial end effects are omitted.')
    else:
        n=FAMILIES[family];limb_widths=c['limbs_mm'];windows=c['windows_mm']
        if len(limb_widths)!=n or len(windows)!=n-1:raise ValueError(f'{family} needs {n} limb widths and {n-1} window widths')
        limb_widths=[finite(v,'Limb width',.1) for v in limb_widths];windows=[finite(v,'Window width',.1) for v in windows]
        window_height=finite(c['window_height_mm'],'Window height',1);top=finite(c['top_yoke_mm'],'Top yoke',.1);bottom=finite(c['bottom_yoke_mm'],'Bottom yoke',.1)
        width=sum(limb_widths)+sum(windows);height=bottom+window_height+top
        core_regions.extend([box('bottom_yoke','Bottom yoke','core',pad,pad+width,pad,pad+bottom),box('top_yoke','Top yoke','core',pad,pad+width,pad+bottom+window_height,pad+height)])
        limbs=[];x=pad
        gap_map={}
        for gap in c.get('gaps',[]):
            i=integer(gap['limb'],'Gap limb index',0,n-1)
            if i in gap_map:raise ValueError('Combine each limb’s gaps in one gap row')
            gap_map[i]=gap
        for i,w in enumerate(limb_widths):
            limbs.append((x,x+w));gap=gap_map.get(i,{});count=integer(gap.get('count',0),'Gap count',0,12);length=finite(gap.get('length_mm',0),'Gap length')
            if count and (length<=0 or count*length>=window_height):raise ValueError('Gap length must be positive, with total shorter than the limb')
            intervals=[];at=pad+bottom
            for j in range(count):
                mid=pad+bottom+(j+1)*window_height/(count+1);intervals.append((at,mid-length/2));at=mid+length/2
            intervals.append((at,pad+bottom+window_height))
            for j,(lo,hi) in enumerate(intervals):core_regions.append(box(f'limb_{i}_{j}',f'Limb {i+1} · segment {j+1}','core',x,x+w,lo,hi))
            x+=w+(windows[i] if i<n-1 else 0)
        if family=='planar':notes.append('Planar EQ/ER uses the supplied rectangular limb/window dimensions. Rounded EQ/ER surfaces and PCB traces are not inferred.')
    p['domain']={'width':width+2*pad,'height':height+2*pad,'depth':depth,'nx':mesh,'ny':mesh}
    # Circuit inputs and exact copper/source counts.
    total_turns=sum(integer(sec['turns'],'Section turns',1,300) for sec in sections)
    if rep=='turns' and total_turns>240:raise ValueError('Individual-turn mode supports up to 240 total turns; split the study or use blocks')
    for sec in sections:
        circuit=str(sec.get('circuit','P')).strip()
        if not circuit or len(circuit)>32:raise ValueError('Circuit name must have 1–32 characters')
        sec['circuit']=circuit
        current=finite(sec.get('current_A',0),'Circuit current',-1e6,1e6)
        if circuit not in circuits:circuits[circuit]={'id':'circuit_'+str(len(circuits)+1),'name':circuit,'turns':0,'current':current}
        if current!=circuits[circuit]['current']:raise ValueError('Sections in one series circuit require the same signed current')
        circuits[circuit]['turns']+=sec['turns']
    if len(circuits)>16:raise ValueError('Use at most 16 independently excited windings')
    if mode=='2d':p['windings']=list(circuits.values())
    offsets={};axial_total={};axial_last_tape={};seen_bobbins=set()
    prepared=[]
    for i,sec in enumerate(sections):
        turns=integer(sec['turns'],'Section turns',1,300);w,h,cu=conductor(sec);tpl=integer(sec.get('turns_per_layer',turns),'Turns per layer',1,300);layers=math.ceil(turns/tpl)
        sec_ins=finite(sec.get('turn_insulation_mm',pack.get('turn_insulation_mm',.1)),'Winding wire insulation')
        natural_build=layers*w+2*sec_ins*layers;natural_height=min(tpl,turns)*h+2*sec_ins*min(tpl,turns)
        build_width=finite(sec.get('build_mm',0),'Section build') or natural_build;build_height=finite(sec.get('height_override_mm',0),'Section height') or natural_height
        if rep=='turns' and (build_width+1e-10<natural_build or build_height+1e-10<natural_height):raise ValueError(f'Section {i+1}: turns do not fit its envelope; use 0 for automatic size or increase build/height')
        limb=integer(sec.get('limb',1),'Wound limb',0,max(0,len(limbs)-1)) if family!='toroid' else 0
        prepared.append((sec,w,h,cu,tpl,layers,build_width,build_height,limb))
        axial_last_tape[limb]=finite(sec.get('tape_mm',pack.get('section_insulation_mm',.5)),'Winding tape thickness')
        axial_total[limb]=axial_total.get(limb,0)+build_height+axial_last_tape[limb]
    for i,(sec,w,h,cu,tpl,layers,bw,bh,limb) in enumerate(prepared):
        orientation=sec.get('stack_orientation',pack.get('orientation','radial'));bobbin=finite(sec.get('bobbin_mm',pack.get('bobbin_mm',.5)),'Winding bobbin thickness');clearance=finite(sec.get('clearance_mm',pack.get('clearance_mm',.5)),'Winding clearance');tape=finite(sec.get('tape_mm',pack.get('section_insulation_mm',.5)),'Winding tape thickness');ins=finite(sec.get('turn_insulation_mm',pack.get('turn_insulation_mm',.1)),'Winding turn insulation')
        natural_height=min(tpl,sec['turns'])*h+2*ins*min(tpl,sec['turns'])
        circuit=circuits[sec['circuit']];turns=sec['turns'];id=f'section_{i+1}';name=sec.get('name') or circuit['name'];positive=[]
        if family=='toroid':
            if rep=='blocks':
                running=offsets.get(0,0);total=axial_total[0]-tape;y=cy-total/2+running+bh/2;offsets[0]=running+bh+tape
                if math.hypot(bw/2,abs(y-cy)+bh/2)>ri-clearance:raise ValueError('Toroid winding blocks do not fit the bore; reduce section build/height')
                coords=[(cx,y),(cx+ro+clearance+bw/2,y)]
                for sign,(xx,yy) in zip([1,-1],coords):shape(id+('_p' if sign==1 else '_n'),name+' block','copper',xx,yy,bw,bh,winding=circuit['id'],polarity=sign,turns=turns)
            else:
                start=offsets.get(0,0);radius_in=ri-clearance-max(w,h)/2-ins;radius_out=ro+clearance+max(w,h)/2+ins
                if radius_in<=0:raise ValueError('Toroid bore is too small for the conductors')
                for j in range(turns):
                    angle=2*math.pi*(start+j+.5)/total_turns
                    for sign,radius in [(1,radius_in),(-1,radius_out)]:shape(f'{id}_{j}_{sign}',name+f' turn {j+1}','copper',cx+radius*math.cos(angle),cy+radius*math.sin(angle),w,h,sec['conductor'] in ['round','litz'],winding=circuit['id'],polarity=sign,turns=1)
                offsets[0]=start+turns
            lmt=2*((dout-din)/2+depth+4*(clearance+(bw/2 if rep=='blocks' else max(w,h)/2)))
        else:
            left,right=limbs[limb];offset=offsets.get(limb,0)
            if orientation=='radial':
                winding_bobbin_key=(limb,sec['circuit']);new_bobbin=winding_bobbin_key not in seen_bobbins
                distance=max(bobbin+clearance,offset+(bobbin if new_bobbin else 0)) if workflow is not None and not workflow.get('custom_sections') else bobbin+clearance+offset;lo=pad+bottom+(window_height-bh)/2;hi=lo+bh;offsets[limb]=distance+bw+tape if workflow is not None and not workflow.get('custom_sections') else offset+bw+tape
            else:
                total=axial_total[limb]-axial_last_tape[limb];distance=bobbin+clearance;lo=pad+bottom+(window_height-total)/2+offset;hi=lo+bh;offsets[limb]=offset+bh+tape
            if lo<pad+bottom+clearance or hi>pad+bottom+window_height-clearance:raise ValueError(f'Section {i+1} exceeds the axial winding window')
            side_boxes=[(left-distance-bw,left-distance,1),(right+distance,right+distance+bw,-1)]
            for x0,x1,sign in side_boxes:
                env={'x0':x0,'x1':x1,'y0':lo,'y1':hi,'id':id,'limb':limb,'circuit':sec['circuit'],'turns':turns};envelopes.append(env)
                if mode=='2d':
                    if rep=='blocks':box(id+('_p' if sign==1 else '_n'),name+' · winding block','copper',x0,x1,lo,hi,winding=circuit['id'],polarity=sign,turns=turns)
                    else:
                        for j in range(turns):
                            layer,row=divmod(j,tpl);xx=x1-ins-w/2-layer*(w+2*ins) if sign==1 else x0+ins+w/2+layer*(w+2*ins);yy=(lo+hi-natural_height)/2+ins+h/2+row*(h+2*ins)
                            shape(f'{id}_{j}_{sign}',name+f' · turn {j+1}','copper',xx,yy,w,h,sec['conductor'] in ['round','litz'],winding=circuit['id'],polarity=sign,turns=1)
            if mode=='2d' and bobbin>0 and ((workflow is not None and not workflow.get('custom_sections') and (limb,sec['circuit']) not in seen_bobbins) or (workflow is None or workflow.get('custom_sections')) and limb not in [r.get('bobbin_limb') for r in p['regions']]):
                for sign,(x0,x1) in enumerate([(left-distance,left-distance+bobbin),(right+distance-bobbin,right+distance)] if workflow is not None and not workflow.get('custom_sections') else [(left-clearance-bobbin,left-clearance),(right+clearance,right+clearance+bobbin)]):box(f'bobbin_{limb}_{i}_{sign}' if workflow is not None and not workflow.get('custom_sections') else f'bobbin_{limb}_{sign}','Bobbin wall','insulation',x0,x1,pad+bottom+clearance,pad+bottom+window_height-clearance,bobbin_limb=limb)
            if mode=='3d':
                radius=distance+bw/2
                p['windings'].append({'id':id,'name':name,'circuit':sec['circuit'],'turns':turns,'current':circuit['current'],'window':{'x0':(left-radius)/1000,'x1':(right+radius)/1000,'y0':(pad-radius)/1000,'y1':(pad+depth+radius)/1000,'z0':lo/1000,'z1':hi/1000},'display_build_m':bw/1000})
            seen_bobbins.add((limb,sec['circuit']))
            lmt=2*((right-left)+depth+4*(distance+bw/2))
        fill=turns*cu/(bw*bh)
        sigma=finite(sec.get('conductivity_MSm',58),'Conductor conductivity',0,1000);rho=1/(sigma*1e6) if sigma>0 else None
        section_stats.append({'section':i+1,'circuit':sec['circuit'],'turns':turns,'layers':layers,'turns_per_layer':tpl,'last_layer_turns':turns-(layers-1)*tpl,'build_mm':bw,'height_mm':bh,'copper_area_per_turn_mm2':cu,'copper_fill_fraction':fill,'mean_turn_length_mm_estimate':lmt,'dc_resistance_ohm_estimate':rho*(lmt/1000)*turns/(cu*1e-6) if rho else None,'limb':limb})
        if family!='toroid':section_stats[-1].update(radial_inner_mm=distance,radial_outer_mm=distance+bw)
        if fill>1:notes.append(f'Section {i+1}: declared copper area exceeds block volume. This is allowed only as a homogenized source; check the winding design.')
    # Fit/collision checks in builder units before conversion. Blocks are checked
    # by envelope even in turn mode, retaining the requested insulation margin.
    if family!='toroid':
        for env in envelopes:
            if env['x0']<0 or env['x1']>p['domain']['width']:raise ValueError('Increase air padding to contain outer-limb windings')
            if any(shapes_overlap(env,r) for r in core_regions):raise ValueError('Winding envelope intersects a core limb; reduce radial build or increase window width')
        for j,a in enumerate(envelopes):
            for b in envelopes[j+1:]:
                if a['id']!=b['id'] and shapes_overlap(a,b):raise ValueError('Winding section envelopes overlap; change limb, build or layer order')
    else:
        copper=[r for r in p['regions'] if r.get('winding')]
        for i,a in enumerate(copper):
            if any(shapes_overlap(a,b) for b in core_regions):raise ValueError('Toroid conductor crosses the annular core')
            if any(shapes_overlap(a,b) for b in copper[i+1:]):raise ValueError('Toroid conductors overlap; enlarge bore or reduce conductor size')
    if mode=='3d':
        if len(p['windings'])>32:raise ValueError('3D supports up to 32 separately meshed sheet sections; reduce layers or use 2D')
        for r in p['regions']:
            r['z0'],r['z1']=r.pop('y0')/1000,r.pop('y1')/1000;r['y0'],r['y1']=pad/1000,(pad+depth)/1000;r['x0']/=1000;r['x1']/=1000
        p['domain']={'width':(width+2*pad)/1000,'height':(depth+2*pad)/1000,'depth':(height+2*pad)/1000,'nx':mesh,'ny':mesh,'nz':mesh,'budget':s.get('mesh_budget','standard')}
        if p['domain']['budget'] not in ['standard','extended']:raise ValueError('Choose standard or extended mesh budget')
        if p['domain']['budget']=='extended':notes.append('Extended 3D budget selected: up to 120,000 tetrahedra / 24,000 nodes. Solves and a full multiwinding matrix can take substantially longer and require more memory.')
        notes.append('3D winding sections are closed ideal rectangular sheets at the mean radius. Copper thickness affects their placement and display envelope; no individual 3D turns are solved.')
    else:
        for r in p['regions']:
            for key in ['x0','x1','y0','y1']:r[key]=round(r[key]/1000,12)
            if r.get('polygon'):r['polygon']=[[round(x/1000,12),round(y/1000,12)] for x,y in r['polygon']]
        for key in ['width','height','depth']:p['domain'][key]/=1000
    for key in ['frequency','voltage','current','power']:
        np=s.get('nameplate',{});lo=finite(np.get(key+'_min_'+{'frequency':'Hz','voltage':'V','current':'A','power':'W'}[key],0),key+' minimum',0,1e9);hi=finite(np.get(key+'_max_'+{'frequency':'Hz','voltage':'V','current':'A','power':'W'}[key],0),key+' maximum',0,1e9)
        if lo>hi:raise ValueError(key+' minimum exceeds maximum')
    leakage=None
    # Window-energy estimate from the actual ordered MMF ramps, restricted to
    # two-circuit concentric radial sections on one limb with equal height.
    if family!='toroid' and orientation=='radial' and len(circuits)==2 and len({t['limb'] for t in section_stats})==1 and max(t['height_mm'] for t in section_stats)-min(t['height_mm'] for t in section_stats)<1e-8:
        a,b=list(circuits.values());current={a['name']:1,b['name']:-a['turns']/b['turns']};mmf=integral=0
        for j,t in enumerate(section_stats):
            end=mmf+t['turns']*current[t['circuit']];integral+=(t['build_mm']/1000)*(mmf*mmf+mmf*end+end*end)/3;mmf=end
            if j<len(section_stats)-1:integral+=max(0,section_stats[j+1]['radial_inner_mm']-t['radial_outer_mm'])/1000*mmf*mmf
        leakage=4*math.pi*1e-7*(sum(t['mean_turn_length_mm_estimate'] for t in section_stats)/len(section_stats))/(section_stats[0]['height_mm'])*integral
    palette=['#e9ad6b','#d98072','#80b6c9','#b498d3','#94be89','#e1c86c','#82bab4','#c793a9']
    circuit_colors={c['id']:palette[i] for i,c in enumerate(circuits.values())}
    for r in p['regions']:
        if r.get('winding'):r['display_color']=circuit_colors[r['winding']]
    for w in p['windings']:
        if w.get('circuit'):w['display_color']=palette[list(circuits).index(w['circuit'])]
    summary={'sections':section_stats,'circuits':list(circuits.values()),'core_type':family,'part_number':s.get('part_number',''),'notes':notes,'analytic_leakage_H':leakage,'analytic_leakage_note':'Balanced ampere-turn, one-dimensional window-energy estimate for the first circuit. Uniform common winding height; no fringing/end effects. Compare with FEM short-circuit inductance.'}
    if workflow is not None:
        p['builder']=workflow;p['circuit_definitions']=copy.deepcopy(workflow['circuits'])
        by_name={sec['circuit']:sec for sec in sections}
        for w in p['windings']:
            sec=by_name.get(w.get('circuit',w['name']))
            if sec:
                w.update(series_group=sec['series_group'],logical_circuit_id=sec['logical_circuit_id'],logical_circuit_name=sec['logical_circuit_name'],electrical_winding_id=sec['electrical_winding_id'],electrical_winding_name=sec['electrical_winding_name'])
                if p['mode']=='2d':w['name']=sec['display_group_name']
        for group in summary['circuits']:
            sec=by_name.get(group['name'])
            if sec:group['name']=sec['display_group_name']
        for row,sec in zip(summary['sections'],sections):row.update(circuit=sec['display_group_name'],logical_circuit_id=sec['logical_circuit_id'],electrical_winding_id=sec['electrical_winding_id'])
        summary['electrical_windings']=copy.deepcopy(summary['circuits'])
        summary['circuit_definitions']=copy.deepcopy(workflow['circuits'])
        summary['excitation_mode']=workflow.get('excitation_mode','instantaneous')
        summary['notes'].append('Named circuits contain independently excited windings. Only sections of the same electrical winding are connected in series; primary and secondary currents remain independent.')
        if workflow.get('excitation_mode')=='sinusoidal_snapshot':summary['notes'].append('Currents are a prescribed sinusoidal snapshot I_peak*cos(snapshot_angle+phase); no AC eddy-current, voltage-driven circuit or time-domain solve is implied.')
    if mode=='3d':
        from .mesh import axis_grid
        objects=p['regions']+[w['window'] for w in p['windings']]
        grids=[axis_grid(p['domain'][size],p['domain']['n'+axis],[o[axis+end] for o in objects for end in ['0','1']]) for axis,size in zip('xyz',['width','height','depth'])]
        estimated=6*math.prod(len(g)-1 for g in grids);limit=120000 if p['domain'].get('budget')=='extended' else 44000
        summary['mesh_estimate']={'nodes':math.prod(len(g) for g in grids),'tetrahedra':estimated,'selected_element_budget':limit,'within_budget':estimated<=limit and math.prod(len(g) for g in grids)<=(24000 if limit==120000 else 10000)}
    p['builder_summary']=summary
    p=validate(p)
    return {'project':p,'summary':summary}
