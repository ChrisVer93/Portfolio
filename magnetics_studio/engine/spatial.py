"""3D first-family, lowest-order Nedelec tetrahedral magnetostatics.

Edge degrees of freedom are line integrals of A. A boundary-collapsed spanning
tree fixes the gradient nullspace; boundary tangential A is homogeneous. Coil
sources use J=curl(T), with Tz=NI/h in a fitted rectangular winding window.
This models ideal rectangular current sheets, not solid conductors.
"""
import itertools
import math
from collections import deque
from .mesh import tetra_geometry, cross, dot, inside
from .materials import MU0
from .sparse import pcg, check_cancel

LOCAL_EDGES = list(itertools.combinations(range(4),2))


class SpatialSystem:
    def __init__(self, project, mesh, progress=None, cancel=None, source=None):
        self.project,self.mesh = project,mesh
        self.progress,self.cancel = progress,cancel
        self.nonlinear = False
        edges = {}
        self.data = []
        mats = {m['id']:m for m in project['materials']}
        for count,(tet,tag) in enumerate(zip(mesh['elements'],mesh['tags'])):
            if count % 500 == 0:
                check_cancel(cancel)
            pts = [mesh['nodes'][i] for i in tet]
            vol,grads = tetra_geometry(pts)
            mat = mats[project['regions'][tag]['material']] if tag >= 0 else mats['air']
            if mat.get('bh'):
                raise ValueError('3D currently supports linear isotropic materials only')
            nu = 1/(MU0*mat.get('mu_r',1.))
            ids,curls,pairs = [],[],[]
            for i,j in LOCAL_EDGES:
                if tet[i] > tet[j]:
                    i,j = j,i
                key = (tet[i],tet[j])
                if key not in edges:
                    edges[key] = len(edges)
                ids.append(edges[key])
                curls.append(tuple(2*v for v in cross(grads[i],grads[j])))
                pairs.append((i,j))
            self.data.append((tet,vol,nu,ids,curls,grads,pairs))
        self.edges = list(edges)
        self.n = len(edges)
        self.rows = [{} for _ in self.edges]
        self.bases = [[0.]*self.n for _ in project['windings']]
        self.source = [0.]*self.n
        for count,(tet,vol,nu,ids,curls,grads,pairs) in enumerate(self.data):
            if count % 500 == 0:
                check_cancel(cancel)
            center = tuple(sum(mesh['nodes'][n][k] for n in tet)/4 for k in range(3))
            for i,ni in enumerate(ids):
                row = self.rows[ni]
                for j,nj in enumerate(ids):
                    value = vol*nu*dot(curls[i],curls[j])
                    if value:
                        row[nj] = row.get(nj,0.)+value
            for basis,w in zip(self.bases,project['windings']):
                if inside(w['window'],center):
                    tz = w['turns']/(w['window']['z1']-w['window']['z0'])
                    for n,c in zip(ids,curls):
                        basis[n] += vol*tz*c[2]
            if source:
                # Degree-two four-point tetrahedral rule for test sources.
                q1,q2 = .5854101966249685,.1381966011250105
                for vertex in range(4):
                    lambdas = [q1 if k == vertex else q2 for k in range(4)]
                    point = tuple(sum(lambdas[k]*mesh['nodes'][tet[k]][d] for k in range(4)) for d in range(3))
                    jvec = source(*point)
                    for n,(i,j) in zip(ids,pairs):
                        basisvec = [lambdas[i]*grads[j][d]-lambdas[j]*grads[i][d] for d in range(3)]
                        self.source[n] += vol*.25*dot(jvec,basisvec)
        self.fixed,self.tree = self.gauge()
        if progress:
            progress(f'3D: {self.n} edges; {len(self.fixed)} boundary/gauge constraints')

    def gauge(self):
        """Contract boundary vertices, then eliminate a spanning-tree gradient.

        A connected rectangular domain has one gradient null mode per interior
        vertex with zero Dirichlet scalar trace. The tree removes precisely
        that many DOFs, in addition to tangential boundary edges.
        """
        nodes = self.mesh['nodes']
        d = self.project['domain']
        sizes = [d['width'],d['height'],d['depth']]
        boundary = self.mesh['boundary']
        fixed = set()
        adjacency = [[] for _ in nodes]
        for e,(i,j) in enumerate(self.edges):
            pi,pj = nodes[i],nodes[j]
            if any((abs(pi[k])<1e-13 and abs(pj[k])<1e-13) or
                   (abs(pi[k]-sizes[k])<1e-13 and abs(pj[k]-sizes[k])<1e-13) for k in range(3)):
                fixed.add(e)
            adjacency[i].append((j,e))
            adjacency[j].append((i,e))
        seen = set(boundary)
        queue = deque(sorted(boundary))
        tree = set()
        while queue:
            n = queue.popleft()
            for other,edge in adjacency[n]:
                if other not in seen:
                    seen.add(other)
                    queue.append(other)
                    tree.add(edge)
        if len(seen) != len(nodes) or len(tree) != len(nodes)-len(boundary):
            raise ValueError('Gauge construction failed on disconnected mesh')
        return fixed|tree,tree

    def solve(self, rhs):
        a,info = pcg(self.rows,rhs,self.fixed,tol=1e-9,progress=self.progress,cancel=self.cancel)
        info['nonlinear_iterations'] = 0
        # A physically compatible load must satisfy the omitted gauge equations.
        residual = [sum(v*a[j] for j,v in self.rows[i].items())-rhs[i] for i in self.tree]
        norm = math.sqrt(sum(v*v for v in rhs))
        gauge_residual = math.sqrt(sum(v*v for v in residual))/norm if norm else 0.
        info['gauge_residual'] = gauge_residual
        if gauge_residual > 1e-6:
            raise RuntimeError(f'Incompatible 3D source or inaccurate solve (gauge residual {gauge_residual:.3g})')
        return a,info

    def post(self, a):
        fields,hfields,measures = [],[],[]
        energy = 0.
        for tet,vol,nu,ids,curls,grads,pairs in self.data:
            b = [sum(a[n]*c[k] for n,c in zip(ids,curls)) for k in range(3)]
            fields.append(b)
            hfields.append([nu*v for v in b])
            measures.append(vol)
            energy += .5*vol*nu*dot(b,b)
        return {'B':fields,'H':hfields,'measures':measures,'energy_J':energy}

    def linkage(self, basis, a):
        return dot(basis,a)
