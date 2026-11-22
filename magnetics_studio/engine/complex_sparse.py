"""Restarted complex GMRES with sparse plus low-rank operators; no installation."""
import math  #: Compute real vector norms and complex-rotation magnitudes.
import os  #: Respect the existing forced-standard-library execution option.
import time  #: Report measured solve time.
from .sparse import check_cancel  #: Reuse the application's cancellation contract.


def inner(a, b):  #: Define the Hermitian inner product needed by complex Arnoldi iteration.
    return sum(x.conjugate() * y for x, y in zip(a, b))  #: Conjugate the first argument, unlike the real magnetostatic dot product.


def norm(a):  #: Return a nonnegative Euclidean norm for complex vectors.
    return math.sqrt(sum(abs(x) ** 2 for x in a))  #: Magnitude squared includes both real and imaginary parts.


def rotation(a, b):  #: Construct a unitary complex Givens rotation eliminating b.
    if b == 0:  #: An already triangular column needs no rotation.
        return 1., 0j  #: Use the identity transformation.
    if a == 0:  #: Avoid division by zero in the general phase formula.
        return 0., b.conjugate() / abs(b)  #: Rotate b into the first entry with a real positive magnitude.
    length = math.hypot(abs(a), abs(b))  #: Stable norm of the two complex entries.
    return abs(a) / length, (a / abs(a)) * b.conjugate() / length  #: The rotation is [[c,s],[-conj(s),c]].


def gmres(rows, rhs, fixed=(), low_rank=(), tol=1e-8, restart=36, maxiter=6000, progress=None, cancel=None):  #: Solve a constrained nonsymmetric complex linear system.
    started = time.perf_counter()  #: Include reduction and preconditioner construction in reported time.
    check_cancel(cancel)  #: Respect a cancellation request before allocating Krylov vectors.
    blocked = set(fixed)  #: Homogeneous fixed values are eliminated rather than replaced by asymmetric rows.
    free = [i for i in range(len(rows)) if i not in blocked]  #: Retain only unconstrained unknowns.
    index = {n: i for i, n in enumerate(free)}  #: Map global node indices to reduced positions.
    sparse = [[(index[j], complex(v)) for j, v in rows[n].items() if j in index] for n in free]  #: Reduce the ordinary sparse matrix once.
    ranks = [(complex(weight), [(index[j], value) for j, value in vector.items() if j in index]) for weight, vector in low_rank]  #: Keep conductor constraints as low-rank corrections instead of dense matrices.
    b = [complex(rhs[n]) for n in free]  #: Preserve the RMS source phasor on every free degree of freedom.
    bn = norm(b)  #: Use the original unpreconditioned right-hand-side norm for acceptance.
    result = [0j] * len(rows)  #: Boundary values stay exactly zero.
    if not free or bn == 0:  #: A homogeneous reduced problem has the zero solution.
        return result, dict(iterations=0, residual=0., backend='Python complex GMRES', seconds=time.perf_counter()-started)  #: Do not fabricate iterations for a zero source.
    diagonal = [complex(rows[n].get(n, 0)) for n in free]  #: Start with the sparse operator's diagonal.
    for weight, vector in ranks:  #: Include every low-rank correction in the Jacobi preconditioner.
        for j, value in vector:  #: A rank-one outer product contributes weight times value squared on the diagonal.
            diagonal[j] += weight * value * value  #: These conductor vectors are real, so this is not a Hermitian outer product.
    if any(abs(v) == 0 or not math.isfinite(abs(v)) for v in diagonal):  #: Division by zero or a nonfinite preconditioner cannot be accepted.
        raise ValueError('Invalid complex operator diagonal')  #: Fail before entering the iterative solve.
    backend = 'Python complex GMRES'  #: Standard-library execution is always available.
    try:  #: Accelerate only when the optional existing numerical packages are already installed.
        if os.environ.get('MAGNETICS_PURE_PYTHON') == '1':  #: Honour the explicit fallback-test mode.
            raise ImportError('Forced standard-library mode')  #: Reuse the same fallback branch as a missing optional package.
        import numpy as np  #: Use installed array conversion for an optional sparse matvec.
        from scipy.sparse import csr_matrix  #: Use installed sparse storage, never a downloaded dependency.
        offsets = [0]  #: Construct compressed-sparse-row offsets.
        for row in sparse:  #: Each reduced row contributes its stored entries.
            offsets.append(offsets[-1] + len(row))  #: Record the end position of this row.
        matrix = csr_matrix(([v for row in sparse for _, v in row], [j for row in sparse for j, _ in row], offsets), shape=(len(free), len(free)))  #: Preserve the exact complex sparse coefficients.
        def sparse_mv(x):  #: Adapt the optional backend to the same list-based solver interface.
            return matrix.dot(np.asarray(x, dtype=complex)).tolist()  #: Perform only the sparse product in SciPy.
        backend = 'Complex GMRES / installed SciPy matvec'  #: Record which optional acceleration actually ran.
    except ImportError:  #: A restricted laptop can run without NumPy or SciPy.
        def sparse_mv(x):  #: Define the equivalent standard-library sparse product.
            return [sum(value * x[j] for j, value in row) for row in sparse]  #: Accumulate each row without constructing a dense matrix.
    def apply(x):  #: Apply the complete reduced AC operator.
        y = sparse_mv(x)  #: Evaluate stiffness plus conductive mass first.
        for weight, vector in ranks:  #: Apply conductor mean-potential corrections separately.
            projection = sum(value * x[j] for j, value in vector)  #: Compute the nonconjugated c-transpose-x required by the PDE elimination.
            for j, value in vector:  #: Scatter the rank-one correction only to its nonzero support.
                y[j] += weight * value * projection  #: Add weight times c times c-transpose-x.
        return y  #: Return the actual operator product before preconditioning.
    x, iterations = [0j] * len(free), 0  #: Start from zero with a reproducible iteration count.
    while iterations < maxiter:  #: Restart until the true residual passes or the hard limit is reached.
        check_cancel(cancel)  #: Keep every restart interruptible.
        residual = [bb - aa for bb, aa in zip(b, apply(x))]  #: Recompute the unpreconditioned residual rather than trusting recurrences.
        relative = norm(residual) / bn  #: This is the reported and accepted algebraic residual.
        if relative <= tol:  #: Acceptance always refers to the original constrained equations.
            for n, value in zip(free, x):  #: Restore free values to their global node locations.
                result[n] = value  #: Leave all constrained entries at zero.
            return result, dict(iterations=iterations, residual=relative, backend=backend, seconds=time.perf_counter()-started)  #: Return only a verified solution.
        z = [value / dd for value, dd in zip(residual, diagonal)]  #: Left-precondition the restart residual.
        beta = norm(z)  #: Scale the initial Arnoldi vector to unit Euclidean norm.
        vectors = [[value / beta for value in z]]  #: Store the first vector of the new Krylov basis.
        width = min(restart, maxiter - iterations, len(free))  #: Do not exceed iteration, restart or vector-space limits.
        h = [[0j] * width for _ in range(width + 1)]  #: Allocate the small Hessenberg least-squares system.
        g = [complex(beta)] + [0j] * width  #: The transformed least-squares right-hand side begins with the residual norm.
        rotations = []  #: Retain unitary rotations for subsequent Arnoldi columns.
        count = 0  #: Track the number of usable Krylov columns in this restart.
        for j in range(width):  #: Expand the preconditioned Krylov space one vector at a time.
            check_cancel(cancel)  #: Allow cancellation even during a long restart cycle.
            w = [value / dd for value, dd in zip(apply(vectors[j]), diagonal)]  #: Apply the left-preconditioned operator to the current vector.
            for _ in range(2):  #: Reorthogonalise to reduce loss of orthogonality in finite precision.
                for i in range(j + 1):  #: Remove projections onto every existing basis vector.
                    value = inner(vectors[i], w)  #: Use the complex Hermitian projection coefficient.
                    h[i][j] += value  #: Accumulate both Gram–Schmidt passes into the same Hessenberg entry.
                    w = [a - value * v for a, v in zip(w, vectors[i])]  #: Subtract the projected component.
            length = norm(w)  #: The remaining component defines the next Arnoldi direction.
            h[j + 1][j] = length  #: Store the subdiagonal before QR elimination.
            if length > 1e-14:  #: Do not normalise an exhausted or numerically vanishing direction.
                vectors.append([value / length for value in w])  #: Extend the orthonormal basis.
            for i, (c, s) in enumerate(rotations):  #: Apply previous QR rotations to this new Hessenberg column.
                first, second = h[i][j], h[i + 1][j]  #: Preserve both entries during the in-place rotation.
                h[i][j], h[i + 1][j] = c * first + s * second, -s.conjugate() * first + c * second  #: Maintain a triangular transformed system.
            c, s = rotation(h[j][j], h[j + 1][j])  #: Eliminate the new subdiagonal entry with a unitary rotation.
            rotations.append((c, s))  #: Reuse this rotation on later columns.
            h[j][j] = c * h[j][j] + s * h[j + 1][j]  #: Retain the transformed diagonal entry.
            h[j + 1][j] = 0j  #: The eliminated subdiagonal is exactly zero in the small QR system.
            g[j], g[j + 1] = c * g[j], -s.conjugate() * g[j]  #: Apply the same rotation to the least-squares right-hand side.
            iterations, count = iterations + 1, j + 1  #: Count this actual operator expansion.
            if length <= 1e-14 or abs(g[j + 1]) <= tol * beta:  #: Finish on Krylov exhaustion or a promising preconditioned residual.
                break  #: The outer loop will verify the original residual before accepting anything.
        coefficients = [0j] * count  #: Allocate the small triangular solution.
        for i in range(count - 1, -1, -1):  #: Solve the QR upper triangle by back substitution.
            if abs(h[i][i]) < 1e-30:  #: A singular small system cannot yield a valid correction.
                raise RuntimeError('Complex GMRES Arnoldi breakdown')  #: Fail rather than emit a division artefact.
            coefficients[i] = (g[i] - sum(h[i][j] * coefficients[j] for j in range(i + 1, count))) / h[i][i]  #: Recover this Krylov expansion coefficient.
        x = [value + sum(coefficients[j] * vectors[j][i] for j in range(count)) for i, value in enumerate(x)]  #: Add the restart correction to the current solution.
        if progress:  #: Avoid logging for direct numerical callers that do not request it.
            progress(f'Complex GMRES {iterations}: previous true residual {relative:.3g}')  #: Clearly label the residual as the value before this correction.
    relative = norm([bb - aa for bb, aa in zip(b, apply(x))]) / bn  #: Check once more if the final allowed correction converged.
    if relative <= tol:  #: A last-iteration success must not be discarded.
        for n, value in zip(free, x):  #: Restore the verified final reduced solution.
            result[n] = value  #: Keep homogeneous boundary entries unchanged.
        return result, dict(iterations=iterations, residual=relative, backend=backend, seconds=time.perf_counter()-started)  #: Report genuine convergence at the iteration limit.
    raise RuntimeError(f'Complex GMRES did not converge in {maxiter} iterations (residual {relative:.3g})')  #: No unconverged field is published.
