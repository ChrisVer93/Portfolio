"""Small symmetric sparse solver; no installed packages are required."""
import math
import os
import time


class Cancelled(RuntimeError):
    pass


def check_cancel(cancel):
    if cancel and cancel():
        raise Cancelled('Analysis cancelled')


def matvec(rows, x):
    return [sum(v * x[j] for j, v in row.items()) for row in rows]


def dot(x, y):
    return math.fsum(a * b for a, b in zip(x, y))


def pcg(rows, rhs, fixed=(), tol=1e-9, maxiter=32000, progress=None, cancel=None):
    """Homogeneous constraints, Jacobi PCG; report true Euclidean residual.

    Reduce the constrained matrix once, rather than applying asymmetric row
    replacement. An optional SciPy sparse matvec accelerates the SAME PCG
    algorithm when SciPy is already installed; it is never downloaded.
    """
    fixed = set(fixed)
    free = [i for i in range(len(rows)) if i not in fixed]
    index = {n: i for i, n in enumerate(free)}
    rr = [[(index[j], v) for j, v in rows[n].items() if j in index] for n in free]
    b = [rhs[n] for n in free]
    bn = math.sqrt(dot(b, b))
    result = [0.0] * len(rows)
    if not free or bn == 0:
        return result, {'iterations': 0, 'residual': 0., 'backend': 'Python PCG'}
    d = [rows[n].get(n, 0.) for n in free]
    if any(v <= 0 or not math.isfinite(v) for v in d):
        raise ValueError('Nonpositive stiffness diagonal; check geometry/materials')
    backend = 'Python PCG'
    try:
        if os.environ.get('MAGNETICS_PURE_PYTHON') == '1':
            raise ImportError('Explicit standard-library mode')
        import numpy as np
        from scipy.sparse import csr_matrix
        indices = [j for row in rr for j, _ in row]
        values = [v for row in rr for _, v in row]
        offsets = [0]
        for row in rr:
            offsets.append(offsets[-1] + len(row))
        matrix = csr_matrix((values, indices, offsets), shape=(len(free), len(free)))
        def mv(x):
            return matrix.dot(np.asarray(x)).tolist()
        backend = 'PCG / installed SciPy matvec'
    except ImportError:
        def mv(x):
            return [sum(v * x[j] for j, v in row) for row in rr]
    x = [0.] * len(free)
    r = b[:]
    z = [v / dd for v, dd in zip(r, d)]
    p = z[:]
    rz = dot(r, z)
    started = time.perf_counter()
    for it in range(1, maxiter + 1):
        if it % 20 == 1:
            check_cancel(cancel)
        ap = mv(p)
        den = dot(p, ap)
        if den <= 0 or not math.isfinite(den):
            raise RuntimeError('PCG lost positive definiteness')
        alpha = rz / den
        x = [xx + alpha * pp for xx, pp in zip(x, p)]
        r = [v - alpha * av for v, av in zip(r, ap)]
        rel = math.sqrt(dot(r, r)) / bn
        if it % 100 == 0 and progress:
            progress(f'PCG {it}: residual {rel:.3g}')
        if rel < tol:
            # Recompute to detect accumulated recurrence drift.
            true_r = [bb - aa for bb, aa in zip(b, mv(x))]
            rel = math.sqrt(dot(true_r, true_r)) / bn
            if rel <= max(10 * tol, 1e-12):
                for i, n in enumerate(free):
                    result[n] = x[i]
                return result, {'iterations': it, 'residual': rel,
                                'backend': backend, 'seconds': time.perf_counter() - started}
            r = true_r
            z = [v / dd for v, dd in zip(r, d)]
            p = z[:]
            rz = dot(r, z)
            continue
        z = [v / dd for v, dd in zip(r, d)]
        new = dot(r, z)
        beta = new / rz
        p = [zz + beta * pp for zz, pp in zip(z, p)]
        rz = new
    raise RuntimeError(f'PCG did not converge in {maxiter} iterations (residual {rel:.3g})')
