"""Interface-fitted Cartesian triangle/tetrahedron meshes for boxes.

    Every geometry and winding coordinate is a mesh plane. Each 3D hexahedron
    is split into six Freudenthal tetrahedra with globally matching faces.
"""
import itertools
import math
from .sparse import check_cancel


def dot(a, b):
    return sum(x*y for x, y in zip(a, b))


def sub(a, b):
    return tuple(x-y for x, y in zip(a, b))


def cross(a, b):
    return (a[1]*b[2]-a[2]*b[1], a[2]*b[0]-a[0]*b[2], a[0]*b[1]-a[1]*b[0])


def inside(box, point):
    return all(box[axis+'0']-1e-13 <= point[i] <= box[axis+'1']+1e-13
               for i, axis in enumerate('xyz'[:len(point)]))


def axis_grid(size, target, cuts):
    pts = sorted(set([0., size] + [float(x) for x in cuts]))
    result = [0.]
    for a, b in zip(pts, pts[1:]):
        if b-a < size*1e-8:
            raise ValueError('Two geometry planes are too close; simplify the geometry')
        n = max(1, math.ceil((b-a)/size*target - 1e-10))
        result.extend(a + (b-a)*i/n for i in range(1, n+1))
    return result


def build_mesh(project, progress=None, cancel=None, *, interval_factor=1):  #: Keep ordinary meshes unchanged and allow explicit bounded subdivision of every fitted base interval.
    if type(interval_factor) is not int or interval_factor not in (1,2,4):raise ValueError('Interval factor must be1,2or4')  #: Require dyadic factors for genuine nested reference study levels; reject booleans and rounded values.
    if project['mode']=='2d' and any(r.get('polygon') for r in project.get('regions', [])):
        if interval_factor!=1:raise ValueError('Interval refinement requires rectangular reference geometry')  #: Do not silently apply Cartesian refinement semantics to the separate polygon mesher.
        from .polygon_mesh import build_polygon_mesh
        return build_polygon_mesh(project,progress,cancel)
    dim = 3 if project['mode'] == '3d' else 2
    domain = project['domain']
    objects = list(project.get('regions', []))
    if dim == 3:
        objects += [w['window'] for w in project.get('windings', [])]
    grids = []
    for axis, size_key in zip('xyz'[:dim], ['width', 'height', 'depth']):
        cuts = [o[axis+end] for o in objects for end in ('0', '1')]
        grids.append(axis_grid(domain[size_key], domain['n'+axis], cuts))
    count = math.prod((len(g)-1)*interval_factor+1 for g in grids)  #: Predict refined node allocation before constructing new coordinates or elements.
    cells = math.prod((len(g)-1)*interval_factor for g in grids)  #: Account for every refined physical and exterior-air interval before the original memory guard.
    max_nodes, max_elements = (24000, 46000) if dim == 2 else (24000, 120000) if domain.get('budget')=='extended' else (10000, 44000)
    if count > max_nodes or cells*(2 if dim == 2 else 6) > max_elements:
        raise ValueError('Mesh exceeds the selected memory budget; lower subdivisions/simplify sections, or explicitly select the extended 3D budget in Builder → Dimensions')
    if interval_factor!=1:  #: Retain the exact ordinary mesh path when refinement is not explicitly requested.
        check_cancel(cancel)  #: Allow study cancellation before allocating the bounded finer Cartesian grids.
        grids=[[a+(b-a)*i/interval_factor for a,b in zip(g,g[1:]) for i in range(interval_factor)]+[g[-1]] for g in grids]  #: Preserve every fitted plane exactly and halve or quarter all base intervals without changing geometry.
    if dim == 2:
        xs, ys = grids
        nodes = [(x, y) for y in ys for x in xs]
        nx = len(xs)
        elements = []
        for j in range(len(ys)-1):
            for i in range(nx-1):
                a = j*nx+i; b = a+1; c = a+nx; d = c+1
                elements.extend([(a,b,d),(a,d,c)])
    else:
        xs, ys, zs = grids
        nodes = [(x,y,z) for z in zs for y in ys for x in xs]
        nx, ny = len(xs), len(ys)
        def index(p):
            return p[0] + nx*(p[1]+ny*p[2])
        elements = []
        for k in range(len(zs)-1):
            check_cancel(cancel)
            for j in range(ny-1):
                for i in range(nx-1):
                    for perm in itertools.permutations(range(3)):
                        p = [i,j,k]; tet = [index(p)]
                        for axis in perm:
                            p[axis] += 1
                            tet.append(index(p))
                        elements.append(tuple(tet))
    tags = []
    for e in elements:
        c = tuple(sum(nodes[n][i] for n in e)/len(e) for i in range(dim))
        tag = -1
        for i, reg in enumerate(project.get('regions', [])):
            if inside(reg, c):
                tag = i
        tags.append(tag)
    boundary = set()
    sizes = [domain[k] for k in ['width','height','depth'][:dim]]
    for n, p in enumerate(nodes):
        if any(abs(x) < 1e-13 or abs(x-size) < 1e-13 for x, size in zip(p, sizes)):
            boundary.add(n)
    if progress:
        progress(f'Mesh: {len(nodes)} nodes, {len(elements)} '+('triangles' if dim == 2 else 'tetrahedra'))
    steps = [[b-a for a,b in zip(g,g[1:])] for g in grids]
    aspect = max(max(a)/min(b) for i,a in enumerate(steps) for j,b in enumerate(steps) if i != j)
    quality = {'smallest_axis_interval_m': min(min(g) for g in steps),
               'largest_cell_axis_aspect_ratio': aspect}
    if dim == 2:
        quality['minimum_triangle_angle_deg'] = math.degrees(math.atan(1/aspect))
    return {'dimension': dim, 'nodes': nodes, 'elements': elements,
            'tags': tags, 'boundary': boundary, 'grids': grids,'quality':quality}


def triangle_geometry(points):
    (x0,y0),(x1,y1),(x2,y2) = points
    det = (x1-x0)*(y2-y0)-(x2-x0)*(y1-y0)
    if det <= 0:
        raise ValueError('Invalid triangle')
    grads = [((y1-y2)/det,(x2-x1)/det),
             ((y2-y0)/det,(x0-x2)/det),
             ((y0-y1)/det,(x1-x0)/det)]
    return det/2, grads


def tetra_geometry(points):
    p0,p1,p2,p3 = points
    u,v,w = sub(p1,p0),sub(p2,p0),sub(p3,p0)
    det = dot(u,cross(v,w))
    if abs(det) < 1e-30:
        raise ValueError('Degenerate tetrahedron')
    g1 = tuple(x/det for x in cross(v,w))
    g2 = tuple(x/det for x in cross(w,u))
    g3 = tuple(x/det for x in cross(u,v))
    g0 = tuple(-g1[i]-g2[i]-g3[i] for i in range(3))
    return abs(det)/6, [g0,g1,g2,g3]
