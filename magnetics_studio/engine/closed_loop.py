"""Finite annular DC loop and nonsingular free-space Biot-Savart probes."""
import copy  #: Preserve an independent exact snapshot of the caller's SI source request.
import math  #: Evaluate circular geometry and finite-conductor analytical references.

from .current_flux import reconstruct_current  #: Enforce shared-face continuity and explicit cut circulation.
from .dc_conduction import solve_tagged_dc  #: Reuse the qualified homogeneous P1 Ohmic conduction kernel.
from .mesh import build_mesh, tetra_geometry  #: Reuse conforming tetrahedral topology and physical cell volumes.
from .project import number  #: Reject nonfinite and out-of-range SI inputs.
from .sparse import check_cancel  #: Cooperate with source-job cancellation during assembly and integration.


def solve_loop(spec, cancel=None):  #: Solve a complete finite annulus with a voltage jump on a coincident cut.
    keys = {'inner_radius_m', 'outer_radius_m', 'thickness_m', 'conductivity_S_m', 'voltage_V', 'cells', 'probes_m'}  #: Keep this benchmark request separate from Studio project and circuit schemas.
    if not isinstance(spec, dict) or set(spec) != keys:  #: Require explicit dimensions, drive, discretisation and probes.
        raise ValueError('Provide exactly the finite-loop dimensions, conductivity, voltage, cells and probes_m')  #: Reject silent defaults or unrelated project fields.
    spec = copy.deepcopy(spec)  #: Detach every nested probe and mesh list before creating saved source or field provenance.
    inner = number(spec['inner_radius_m'], 'Inner radius [m]', 1e-5, 10)  #: Bound the hole radius away from zero.
    outer = number(spec['outer_radius_m'], 'Outer radius [m]', inner+1e-5, 10)  #: Require finite radial conductor width.
    thickness = number(spec['thickness_m'], 'Thickness [m]', 1e-5, 10)  #: Specify the complete axial copper thickness.
    sigma = number(spec['conductivity_S_m'], 'Conductivity [S/m]', 1e-3, 1e9)  #: Use one homogeneous isotropic DC conductivity.
    voltage = number(spec['voltage_V'], 'Cut voltage [V]', -1e4, 1e4)  #: Retain signed circulation, including zero drive.
    counts = spec['cells']  #: Read angular, radial and axial subdivisions in that order.
    if (not isinstance(counts, list) or len(counts) != 3 or any(type(n) is not int or not 1 <= n <= 128 for n in counts)
            or counts[0] < 8 or 6*math.prod(counts) > 90000):  #: Bound geometric faceting, topology and reconstruction memory before meshing.
        raise ValueError('Loop cells require 8..128 angular cells, 1..128 radial/axial cells and at most 90000 tetrahedra')  #: Reject unsupported mesh requests early.
    probes = spec['probes_m']  #: Evaluate only requested free-space field samples.
    if not isinstance(probes, list) or not 1 <= len(probes) <= 64:  #: Limit the direct volume-quadrature cost.
        raise ValueError('Supply 1..64 free-space probes_m')  #: Require at least one observable for this source-to-field operation.
    for p in probes:  #: Validate probe geometry before doing the scalar solve.
        if not isinstance(p, list) or len(p) != 3:  #: Require three explicit SI coordinates per probe.
            raise ValueError('Each probe requires three coordinates [m]')  #: Refuse ambiguous dimensions.
        for x in p:  #: Apply the shared finite-number and boolean guards.
            number(x, 'Probe coordinate [m]', -100, 100)  #: Bound every requested coordinate.
        r = math.hypot(p[0], p[1])  #: Compute distance from the loop axis.
        clearance = max(inner*math.cos(math.pi/counts[0])-r, r-outer, abs(p[2])-thickness/2)  #: Lower-bound distance from the faceted annular conductor.
        if clearance <= .1*max(outer-inner, thickness):  #: Exclude near and in-copper singular integration from this quadrature path.
            raise ValueError('Probes must be separated from copper by more than 10% of its largest cross-section dimension')  #: Keep the supported nonsingular sampling scope explicit.
    check_cancel(cancel)  #: Stop promptly before constructing the reference topology.
    nx, ny, nz = counts  #: Match the reference grid coordinates to angle, radius and thickness.
    grid = build_mesh({'mode': '3d', 'domain': dict(width=1., height=1., depth=1., nx=nx, ny=ny, nz=nz, budget='extended')}, cancel=cancel)  #: Build six conforming tetrahedra per reference hexahedron.
    nodes = []  #: Retain distinct seam identities despite coincident physical coordinates.
    for x, y, z in grid['nodes']:  #: Map the whole cube around the complete physical copper loop.
        theta = 0. if x == 1. else 2*math.pi*x  #: Snap the final seam geometrically to the first one.
        radius = inner+(outer-inner)*y  #: Preserve the declared finite radial conductor width.
        nodes.append((radius*math.cos(theta), radius*math.sin(theta), thickness*(z-.5)))  #: Centre the loop axially at z=0 in metres.
    high = {i for i, p in enumerate(grid['nodes']) if p[0] == 0.}  #: Identify the first side of the excitation cut.
    low = {i for i, p in enumerate(grid['nodes']) if p[0] == 1.}  #: Identify the coincident second side of that same cut.
    low_by_yz = {(grid['nodes'][i][1], grid['nodes'][i][2]): i for i in low}  #: Pair exact reference-grid nodes rather than approximate spatial neighbours.
    pairs = [[i, low_by_yz[tuple(grid['nodes'][i][1:])]] for i in sorted(high)]  #: Declare the complete conforming periodic seam.
    source = solve_tagged_dc(nodes, grid['elements'], high, low, sigma, voltage,
                             lift=[1-p[0] for p in grid['nodes']], cancel=cancel, linear_solver='scipy-direct')  #: Solve the cut-domain potential and its independent reaction/power checks.
    recovered = reconstruct_current(source, cancel, periodic_pairs=pairs)  #: Close every seam flux while retaining the solved total circulation.
    source['conservative_current'] = recovered  #: Store the exact volume-current source used in field integration.
    field, integrals = _integrate(source, probes, cancel)  #: Integrate the full physical loop and its source diagnostics without remeshing.
    coefficient = sigma*voltage/(2*math.pi)  #: Analytical smooth-annulus J_theta=C/r coefficient in A/m.
    exact_r = 2*math.pi/(sigma*thickness*math.log(outer/inner))  #: Analytical full-loop Ohmic resistance in ohms.
    exact_center = 4*math.pi*1e-7*coefficient*(math.asinh(thickness/(2*inner))-math.asinh(thickness/(2*outer)))  #: Exact finite-thickness centre Bz in tesla.
    return {**source, 'format': 'magnetics-studio.closed-loop-field/1', 'input': copy.deepcopy(spec),  #: Detach saved source provenance from later caller edits.
            'excitation': 'Impressed voltage jump across a coincident cut; complete physical annular return',
            'magnetic_model': 'Free-space mu0 Biot-Savart volume integral; no magnetic core or eddy-current feedback',
            'magnetic_field': field, 'source_integrals': integrals, 'analytic_resistance_ohm': exact_r,  #: Record actual closure and magnetic-moment integrals beside the sampled fields.
            'analytic_cut_current_A': voltage/exact_r, 'analytic_center_Bz_T': exact_center}  #: Return source, closure and fields with explicit model scope and independent smooth-geometry values.


def _integrate(source, probes, cancel):  #: Integrate only the closed current created and checked by solve_loop.
    import numpy as np  #: Use bounded vectorised nonsingular tetrahedral quadrature.
    mesh = source['mesh']  #: Retain the exact source geometry, with no remeshing or interpolation.
    recovered = source['conservative_current']  #: Consume the RT0 field rather than the discontinuous P1 gradient.
    points = np.asarray(mesh['nodes_m'])[mesh['tetrahedra']]  #: Gather physical vertices for each tetrahedron.
    centers = points.mean(axis=1)  #: Locate the RT0 stored current values.
    volumes = np.asarray([tetra_geometry(p)[0] for p in points])  #: Compute independent physical integration measures.
    current = np.asarray(recovered['current_density_at_cell_centroid_A_m2'])  #: Read the conservative centroid vectors in A/m².
    divergence = np.asarray(recovered['divergence_A_m3'])  #: Retain the affine RT0 term even at roundoff-sized divergence.
    alpha, beta = (5+3*math.sqrt(5))/20, (5-math.sqrt(5))/20  #: Use the symmetric four-point tetrahedron rule exact through degree two.
    barycentric = np.full((4,4), beta)  #: Start with equal off-diagonal barycentric coordinates.
    np.fill_diagonal(barycentric, alpha)  #: Place one dominant barycentric coordinate at each quadrature point.
    quadrature_points = np.einsum('qi,tij->tqj', barycentric, points)  #: Map the quadrature points into each physical tetrahedron.
    quadrature_current = current[:,None,:]+divergence[:,None,None]*(quadrature_points-centers[:,None,:])/3  #: Evaluate the full recovered RT0 field at all integration points.
    fields = []  #: Retain exact requested probe order and independent quadrature diagnostics.
    for probe in probes:  #: Evaluate direct source-to-probe integration without a magnetic air-boundary approximation.
        check_cancel(cancel)  #: Allow interruption between bounded probe operations.
        delta = np.asarray(probe)-quadrature_points  #: Point source-to-observer vectors in metres.
        terms = np.cross(quadrature_current, delta)/np.linalg.norm(delta, axis=2)[:,:,None]**3  #: Apply the Biot-Savart current-density kernel.
        contributions = 1e-7*np.sum(terms*volumes[:,None,None]/4, axis=1)  #: Include mu0/(4pi) and the physical tetrahedron weights in each cell contribution.
        field = np.sum(contributions, axis=0)  #: Sum all copper, including the complementary physical return half.
        return_field = np.sum(contributions[centers[:,1] < 0], axis=0)  #: Expose the lower-half return contribution as an audit of full-loop coverage.
        central_delta = np.asarray(probe)-centers  #: Build a separate centroid-only quadrature comparison.
        central = 1e-7*np.sum(np.cross(current, central_delta)*volumes[:,None]/np.linalg.norm(central_delta,axis=1)[:,None]**3, axis=0)  #: Integrate the same source with the degree-one rule.
        if not np.all(np.isfinite(field)) or not np.all(np.isfinite(central)):  #: Refuse a nonfinite field even after geometric preflight.
            raise RuntimeError('Nonfinite Biot-Savart field')  #: Never publish failed kernel evaluations.
        fields.append({'point_m': probe, 'B_T': field.tolist(), 'return_half_B_T': return_field.tolist(), 'centroid_quadrature_B_T': central.tolist(),  #: Keep the explicit physical return contribution reviewable.
                       'quadrature_difference_T': float(np.linalg.norm(field-central))})  #: Record a rule difference, not an asserted accuracy bound.
    integrated_j = np.sum(current*volumes[:,None], axis=0)  #: A fully closed conservative source has zero volume-integrated vector current in A m.
    moment = .5*np.sum(np.cross(quadrature_points, quadrature_current)*volumes[:,None,None]/4, axis=(0,1))  #: Integrate the finite-conductor magnetic dipole moment in A m² with degree-two exactness.
    integrals = {'volume_integral_J_A_m': integrated_j.tolist(), 'magnetic_moment_A_m2': moment.tolist()}  #: Preserve independent global source-closure and moment observables.
    return fields, integrals  #: Preserve finite-copper samples, actual quadrature diagnostics and source integrals.
