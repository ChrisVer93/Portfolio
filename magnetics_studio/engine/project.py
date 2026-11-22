"""Strict project boundary: fail early instead of silently changing physics."""
import copy
import math


def number(value, name, lower=None, upper=None):
    if isinstance(value,bool) or not isinstance(value,(int,float)) or not math.isfinite(value):
        raise ValueError(f'{name} must be a finite number')
    if lower is not None and value < lower or upper is not None and value > upper:
        raise ValueError(f'{name} must be between {lower} and {upper}')
    return value


def validate(project):
    from .materials import validate_material
    p = copy.deepcopy(project)
    if not isinstance(p,dict) or p.get('mode') not in ['2d','3d']:
        raise ValueError('Project mode must be 2d or 3d; use the supplied current examples')
    p.setdefault('name','Untitled magnetic study')
    if not isinstance(p['name'],str) or len(p['name']) > 240:
        raise ValueError('Project name must be text of at most 240 characters')
    d = p['domain']
    for k in ['width','height','depth']:
        number(d[k],k,1e-6,100.)
    for k in ['nx','ny']+(['nz'] if p['mode']=='3d' else []):
        number(d[k],k,2,150 if p['mode']=='2d' else 32)
        if int(d[k]) != d[k]:
            raise ValueError('Mesh subdivisions must be integers')
        d[k] = int(d[k])
    p.setdefault('regions',[])
    p.setdefault('windings',[])
    if not isinstance(p['materials'],list) or len(p['materials'])>100 or not p['materials']:
        raise ValueError('Use 1–100 material definitions')
    if len(p['regions'])>(1200 if p['mode']=='2d' else 80) or len(p['windings'])>(32 if p['mode']=='3d' else 16):
        raise ValueError('This release supports at most 1200 2D regions (80 in 3D) and up to 16 electrical windings (32 3D sections)')
    for group in ['materials','regions','windings']:
        ids = [x.get('id') for x in p[group]]
        if any(not isinstance(s,str) or not s or len(s)>80 for s in ids) or len(set(ids)) != len(ids):
            raise ValueError(f'{group} must have unique, nonempty string ids')
    mats = {m['id']:m for m in p['materials']}
    if 'air' not in mats or mats['air'].get('mu_r',1.) != 1 or mats['air'].get('bh'):
        raise ValueError('An air material with mu_r=1 and no B-H curve is required')
    for m in p['materials']:
        validate_material(m)
    windings = {w['id']:w for w in p['windings']}
    for w in p['windings']:
        w.setdefault('name',w['id'])
        number(w['turns'],'Turns',.001,1e6)
        number(w['current'],'Current (A)',-1e6,1e6)
    if d.get('budget','standard') not in ['standard','extended']:raise ValueError('Unknown mesh memory budget')
    axes = list(zip('xyz',['width','height','depth']))[:3 if p['mode']=='3d' else 2]
    boxes = p['regions'][:]
    if p['mode']=='3d':
        boxes += [w['window'] for w in p['windings']]
    for box in boxes:
        for axis,size in axes:
            a = number(box[axis+'0'],axis+'0',0.,d[size])
            b = number(box[axis+'1'],axis+'1',0.,d[size])
            if b-a < d[size]*1e-7:
                raise ValueError('Box dimensions must be positive and resolvable')
    for r in p['regions']:
        if r.get('polygon'):
            if p['mode']!='2d':raise ValueError('Polygon regions require 2D')
            from .polygon_mesh import area
            poly=r['polygon']
            if not isinstance(poly,list) or not 3<=len(poly)<=128:raise ValueError('Convex polygons require 3–128 vertices')
            for point in poly:
                if len(point)!=2:raise ValueError('Polygon points need x,y')
                for i,key in enumerate(['width','height']):number(point[i],'Polygon coordinate',0,d[key])
            if area(poly)<=0:raise ValueError('Polygon vertices must be counterclockwise')
            for a,b,c in zip(poly,poly[1:]+poly[:1],poly[2:]+poly[:2]):
                if (b[0]-a[0])*(c[1]-b[1])-(b[1]-a[1])*(c[0]-b[0]) < -1e-14:raise ValueError('Polygon must be convex')
            for k,axis in enumerate('xy'):
                if abs(min(v[k] for v in poly)-r[axis+'0'])>1e-10 or abs(max(v[k] for v in poly)-r[axis+'1'])>1e-10:raise ValueError('Polygon bounds must match its vertices')
        r.setdefault('name',r['id'])
        if r.get('material') not in mats:
            raise ValueError(f"Unknown material in {r['name']}")
        if p['mode']=='3d' and mats[r['material']].get('bh'):
            raise ValueError('Use linear materials for 3D in this release; nonlinear B-H is available in 2D')
        if r.get('winding'):
            if p['mode'] != '2d' or r['winding'] not in windings or r.get('polarity') not in [-1,1]:
                raise ValueError('2D coil boxes require a known winding and polarity +1 or −1')
    for w in p['windings']:
        assigned=[r for r in p['regions'] if r.get('winding')==w['id']]
        if any('turns' in r for r in assigned):
            if not all('turns' in r for r in assigned):raise ValueError('Do not mix explicit and implicit conductor turn counts')
            for r in assigned:number(r['turns'],'Section turns',.001,1e6)
            for sign in [-1,1]:
                if abs(sum(r['turns'] for r in assigned if r['polarity']==sign)-w['turns'])>max(1,w['turns'])*1e-9:raise ValueError('Section turns on each polarity must sum to circuit turns')
    from .connections import normalise_series  #: Reuse one canonical electrical-series interpretation in every validated project.
    normalise_series(p)  #: Migrate legacy connections on the detached copy and reject ambiguous/inconsistent section currents.
    return p
