"""Conforming 2D convex-polygon/box meshes, using only the standard library.

Cartesian cells are partitioned at material boundaries. All resulting edges
are split at shared collinear vertices before centroid-fan triangulation.
Circular conductors are explicitly faceted polygons, never centroid masks.
"""
import math
from collections import defaultdict
from .sparse import check_cancel


def area(poly):
    return .5*sum(p[0]*q[1]-q[0]*p[1] for p,q in zip(poly,poly[1:]+poly[:1]))


def vertices(region):
    return [tuple(p) for p in region.get('polygon', [])] or [
        (region['x0'],region['y0']),(region['x1'],region['y0']),
        (region['x1'],region['y1']),(region['x0'],region['y1'])]


def split(poly,a,b,tol):
    """Clip a convex polygon into left/right closed half planes."""
    left,right=[],[]
    dx,dy=b[0]-a[0],b[1]-a[1]
    def val(p):
        return dx*(p[1]-a[1])-dy*(p[0]-a[0])
    for p,q in zip(poly,poly[1:]+poly[:1]):
        u,v=val(p),val(q)
        if u>=-tol:left.append(p)
        if u<=tol:right.append(p)
        if u>tol and v < -tol or u < -tol and v > tol:
            t=u/(u-v);point=(p[0]+t*(q[0]-p[0]),p[1]+t*(q[1]-p[1]))
            left.append(point);right.append(point)
    return left,right


def build_polygon_mesh(project,progress=None,cancel=None):
    from .mesh import axis_grid,triangle_geometry
    d=project['domain'];regions=project['regions'];span=max(d['width'],d['height']);quantum=span*1e-11;tol=span*span*1e-15
    xs=axis_grid(d['width'],d['nx'],[round(r[k],12) for r in regions if not r.get('polygon') or r.get('winding') for k in ['x0','x1']])
    ys=axis_grid(d['height'],d['ny'],[round(r[k],12) for r in regions if not r.get('polygon') or r.get('winding') for k in ['y0','y1']])
    if len(xs)*len(ys)>24000:raise ValueError('Too many turn/geometry coordinates; reduce packing or mesh density')
    pieces=[]
    for y0,y1 in zip(ys,ys[1:]):
        check_cancel(cancel)
        for x0,x1 in zip(xs,xs[1:]):
            parts=[([(x0,y0),(x1,y0),(x1,y1),(x0,y1)],-1)]
            for tag,r in enumerate(regions):
                if x1<=r['x0']+quantum or x0>=r['x1']-quantum or y1<=r['y0']+quantum or y0>=r['y1']-quantum:continue
                if not r.get('polygon'):
                    parts=[(p,tag) for p,_ in parts];continue
                updated=[];clip=vertices(r)
                for poly,oldtag in parts:
                    inner=poly
                    for a,b in zip(clip,clip[1:]+clip[:1]):
                        inner,outer=split(inner,a,b,tol)
                        if len(outer)>2 and area(outer)>tol:updated.append((outer,oldtag))
                        if len(inner)<3 or area(inner)<=tol:inner=[];break
                    if inner:updated.append((inner,tag))
                parts=updated
            pieces.extend(parts)
            if len(pieces)>18000:raise ValueError('Polygon partition exceeds mesh budget; reduce turns or mesh density')
    nodes=[];lookup={}
    def node(p):
        key=tuple(round(x/quantum) for x in p)
        if key not in lookup:lookup[key]=len(nodes);nodes.append(tuple(p))
        return lookup[key]
    def line_key(a,b):
        dx,dy=b[0]-a[0],b[1]-a[1];length=math.hypot(dx,dy)
        if length<quantum:return None
        nx,ny=-dy/length,dx/length
        if nx < -1e-10 or abs(nx)<1e-10 and ny<0:nx,ny=-nx,-ny
        return (round(nx*1e8),round(ny*1e8),round((nx*a[0]+ny*a[1])/span*1e8))
    lines=defaultdict(set);polys=[]
    for poly,tag in pieces:
        ids=[]
        for p in poly:
            n=node(p)
            if not ids or n!=ids[-1]:ids.append(n)
        if ids and ids[-1]==ids[0]:ids.pop()
        if len(ids)<3:continue
        polys.append((ids,tag))
        for a,b in zip(ids,ids[1:]+ids[:1]):lines[line_key(nodes[a],nodes[b])].update([a,b])
    elements=[];tags=[];min_angle=180.
    for ids,tag in polys:
        border=[]
        for a,b in zip(ids,ids[1:]+ids[:1]):
            p,q=nodes[a],nodes[b];dx,dy=q[0]-p[0],q[1]-p[1];length2=dx*dx+dy*dy;along=[]
            for n in lines[line_key(p,q)]:
                r=nodes[n];t=((r[0]-p[0])*dx+(r[1]-p[1])*dy)/length2
                if -1e-9<=t<1-1e-9 and abs(dx*(r[1]-p[1])-dy*(r[0]-p[0]))<=quantum*math.sqrt(length2)*10:along.append((t,n))
            border.extend(n for _,n in sorted(along))
        center=node(tuple(sum(nodes[n][k] for n in ids)/len(ids) for k in [0,1]))
        for a,b in zip(border,border[1:]+border[:1]):
            pts=[nodes[a],nodes[b],nodes[center]]
            if abs(area(pts))<=span*span*1e-20:continue
            if area(pts)<0:a,b=b,a;pts=[nodes[a],nodes[b],nodes[center]]
            elements.append((a,b,center));tags.append(tag)
            for j in range(3):
                u=(pts[(j+1)%3][0]-pts[j][0],pts[(j+1)%3][1]-pts[j][1]);v=(pts[(j+2)%3][0]-pts[j][0],pts[(j+2)%3][1]-pts[j][1]);cos=sum(x*y for x,y in zip(u,v))/(math.hypot(*u)*math.hypot(*v));min_angle=min(min_angle,math.degrees(math.acos(max(-1.,min(1.,cos)))))
    if len(nodes)>24000 or len(elements)>46000:raise ValueError('Turn-resolved mesh exceeds 24,000 nodes / 46,000 triangles; reduce density or number of turns')
    boundary={i for i,p in enumerate(nodes) if min(abs(p[0]),abs(p[1]),abs(p[0]-d['width']),abs(p[1]-d['height']))<quantum*2}
    steps=[b-a for g in [xs,ys] for a,b in zip(g,g[1:])]
    quality={'smallest_axis_interval_m':min(steps),'largest_cell_axis_aspect_ratio':max(steps)/min(steps),'minimum_triangle_angle_deg':min_angle,'geometry':'Conforming convex polygons; circular conductors faceted'}
    if progress:progress(f'Polygon mesh: {len(nodes)} nodes, {len(elements)} fitted triangles')
    return {'dimension':2,'nodes':nodes,'elements':elements,'tags':tags,'boundary':boundary,'grids':[xs,ys],'quality':quality}
