"""Planar P1 triangular FEM, linear and reversible nonlinear B-H laws."""
import math
from .materials import MU0, h_and_energy, reluctivity
from .mesh import triangle_geometry, dot
from .sparse import pcg, check_cancel


def differential_nu(material, b):
    curve = material.get('bh')
    if not curve:
        return 1/(MU0*material.get('mu_r', 1.))
    for (b0,h0),(b1,h1) in zip(curve,curve[1:]):
        if b <= b1:
            return (h1-h0)/(b1-b0)
    return 1/MU0


class PlanarSystem:
    def __init__(self, project, mesh, progress=None, cancel=None):
        self.project, self.mesh = project, mesh
        self.progress, self.cancel = progress, cancel
        self.fixed = mesh['boundary']
        self.n = len(mesh['nodes'])
        self.depth = project['domain']['depth']
        mats = {m['id']:m for m in project['materials']}
        self.data = []
        self.bases = [[0.]*self.n for _ in project['windings']]
        # Use effective cross sections after last-box-wins material assignment.
        areas = {}
        for e,tag in zip(mesh['elements'],mesh['tags']):
            area, grads = triangle_geometry([mesh['nodes'][i] for i in e])
            reg = project['regions'][tag] if tag >= 0 else {}
            mat = mats[reg.get('material','air')]
            curls = [(g[1],-g[0]) for g in grads]
            self.data.append((e,area,curls,mat,reg))
            if reg.get('winding'):
                key = reg['id'] if 'turns' in reg else (reg['winding'],reg['polarity'])
                areas[key] = areas.get(key,0.) + area
        ids = {w['id']:i for i,w in enumerate(project['windings'])}
        for w in project['windings']:
            if any(not any(areas.get(r['id'] if 'turns' in r else (w['id'],s),0.)>0 for r in project['regions'] if r.get('winding')==w['id'] and r.get('polarity')==s) for s in [-1,1]):
                raise ValueError(f"Winding {w['name']} needs nonempty + and − conductor sections")
        for e,area,curls,mat,reg in self.data:
            if reg.get('winding'):
                i = ids[reg['winding']]
                w = project['windings'][i]
                key = reg['id'] if 'turns' in reg else (w['id'],reg['polarity'])
                if areas.get(key,0.)<=0:raise ValueError('A conductor section has zero effective area')
                j = reg['polarity']*reg.get('turns',w['turns'])/areas[key]
                for n in e:
                    self.bases[i][n] += j*area/3
        self.nonlinear = any(mat.get('bh') for _,_,_,mat,_ in self.data)

    def field(self, e, curls, a):
        return tuple(sum(a[n]*c[k] for n,c in zip(e,curls)) for k in range(2))

    def assemble(self, a=None, tangent=False):
        rows = [{} for _ in range(self.n)]
        internal = [0.]*self.n
        energy = 0.
        for count,(e,area,curls,mat,reg) in enumerate(self.data):
            if count % 1000 == 0:
                check_cancel(self.cancel)
            bvec = self.field(e,curls,a) if a is not None else (0.,0.)
            b = math.hypot(*bvec)
            nu = reluctivity(mat,b)
            delta = (differential_nu(mat,b)-nu)/(b*b) if tangent and b > 1e-14 else 0.
            energy += area*h_and_energy(mat,b)[1]
            for i,ni in enumerate(e):
                bc = dot(bvec,curls[i])
                internal[ni] += area*nu*bc
                row = rows[ni]
                for j,nj in enumerate(e):
                    value = area*(nu*dot(curls[i],curls[j])+delta*bc*dot(bvec,curls[j]))
                    row[nj] = row.get(nj,0.)+value
        return rows,internal,energy

    def energy(self, a):
        return sum(area*h_and_energy(mat, math.hypot(*self.field(e,curls,a)))[1]
                   for e,area,curls,mat,reg in self.data)

    def solve(self, rhs):
        if not self.nonlinear:
            if not hasattr(self,'rows'):
                self.rows,_,_ = self.assemble()
            a, info = pcg(self.rows,rhs,self.fixed,progress=self.progress,cancel=self.cancel)
            info['nonlinear_iterations'] = 0
            return a,info
        a = [0.]*self.n
        normf = math.sqrt(sum(v*v for i,v in enumerate(rhs) if i not in self.fixed))
        history = []
        if normf == 0:
            return a, {'iterations':0,'residual':0.,'nonlinear_iterations':0,'history':[],'backend':'Python'}
        total = 0
        for step in range(1,61):
            check_cancel(self.cancel)
            rows,internal,energy = self.assemble(a,tangent=True)
            residual = [rhs[i]-internal[i] if i not in self.fixed else 0. for i in range(self.n)]
            rel = math.sqrt(sum(v*v for v in residual))/normf
            history.append({'step':step-1,'residual':rel})
            if self.progress:
                self.progress(f'Nonlinear Newton {step-1}: residual {rel:.3g}')
            if rel < 1e-7:
                return a, {'iterations':total,'residual':rel,'nonlinear_iterations':step-1,
                           'history':history,'backend':info['backend'] if step>1 else 'Python'}
            da,info = pcg(rows,residual,self.fixed,tol=1e-10,progress=self.progress,cancel=self.cancel)
            total += info['iterations']
            objective = energy-dot(rhs,a)
            descent = dot(residual,da)
            alpha = 1.
            accepted = False
            for _ in range(24):
                candidate = [v+alpha*d for v,d in zip(a,da)]
                trial = self.energy(candidate)-dot(rhs,candidate)
                if trial <= objective-1e-4*alpha*descent+abs(objective)*1e-14:
                    a = candidate
                    accepted = True
                    break
                alpha *= .5
            if not accepted:
                raise RuntimeError('Nonlinear line search failed; inspect material data and mesh')
        raise RuntimeError(f'Nonlinear solve did not converge (residual {rel:.3g}); no result accepted')

    def post(self, a):
        fields, hfields, measures = [],[],[]
        energy = 0.
        for e,area,curls,mat,reg in self.data:
            vec = self.field(e,curls,a)
            mag = math.hypot(*vec)
            nu = reluctivity(mat,mag)
            fields.append([*vec,0.])
            hfields.append([vec[0]*nu,vec[1]*nu,0.])
            measures.append(area*self.depth)
            energy += area*self.depth*h_and_energy(mat,mag)[1]
        return {'B':fields,'H':hfields,'measures':measures,'energy_J':energy,'Az':a}

    def linkage(self, basis, a):
        return dot(basis,a)*self.depth
