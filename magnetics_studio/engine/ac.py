"""Linear planar RMS phasor magnetodynamics with explicit solid-current constraints.

Convention: physical x(t)=sqrt(2)*Re(x_rms*exp(+j*omega*t)).
Solid groups share a uniform axial driving gradient E0 and a prescribed total
current. Stranded winding regions retain uniform impressed J and have no
resolved copper resistance, skin/proximity loss or homogenised litz loss.
"""
from .connections import check_series_currents  #: Validate actual RMS section phasors as well as the saved static source values.
import cmath  #: Construct source and observation-phase phasors.
import copy  #: Keep input definitions unchanged during frequency sweeps.
from .inductance import ac_series_equivalent  #: Add signed series-equivalent inductance to the existing frequency-study port responses.
import math  #: Use SI angular frequency, energy norms and skin-depth diagnostics.
import time  #: Measure the complete AC analysis.
from .analysis import mesh_public  #: Preserve the application's solved-mesh export schema.
from .complex_sparse import gmres  #: Solve the actual complex-valued constrained diffusion problem.
from .materials import MU0  #: Convert linear relative permeability to SI reluctivity.
from .mesh import build_mesh  #: Start from the existing interface-fitted triangular mesh.
from .planar import PlanarSystem  #: Reuse verified P1 stiffness and stranded source assembly.
from .project import validate, number  #: Apply strict existing geometry/material validation.
from .sparse import check_cancel  #: Honour cancellation throughout assembly and postprocessing.


def pair(value):  #: Encode a complex phasor using only standard JSON numbers.
    return [value.real, value.imag]  #: The order is always real, imaginary.


def phasor(magnitude, angle):  #: Interpret signed current magnitudes and electrical phase consistently.
    return magnitude * cmath.exp(1j * math.radians(angle))  #: A negative signed magnitude reverses orientation by 180 degrees.


def ac_settings(project, options):  #: Resolve reproducible AC controls before allocating a mesh.
    defaults = dict(frequency_Hz=10000., phase_deg=0.)  #: Frequency is positive; observation phase selects only the displayed instant.
    stored = project.get('ac_settings', {})  #: Projects may save their preferred frequency and display phase.
    if not isinstance(stored, dict) or options is not None and not isinstance(options, dict):  #: Controls must be named objects, not arrays or scalars.
        raise ValueError('AC settings/options must be objects')  #: Reject malformed input instead of silently replacing it.
    if (set(stored) | set(options or {})) - set(defaults):  #: Reject misspelled or unsupported controls.
        raise ValueError('Unknown AC option')  #: No nonlinear, displacement-current or transient option is silently ignored.
    settings = dict(defaults, **stored)  #: Start from the stored model's controls.
    settings.update(options or {})  #: Explicit run controls override stored preferences.
    number(settings['frequency_Hz'], 'AC frequency (Hz)', 0.001, 1e7)  #: Bound the positive frequency used in the quasistatic formulation.
    number(settings['phase_deg'], 'Display phase (degrees)', -1e6, 1e6)  #: Allow wrapped observation phases while rejecting nonfinite data.
    return settings  #: Include these exact controls in the solved result.


def solve_ac(project, options=None, progress=None, cancel=None):  #: Solve one genuine frequency-domain operating point.
    started = time.perf_counter()  #: Include validation, assembly and postprocessing in the measured runtime.
    check_cancel(cancel)  #: Permit cancellation before work begins.
    p = validate(project)  #: Work on a detached validated copy of the geometry and winding model.
    if p['mode'] != '2d' or any(m.get('bh') for m in p['materials']):  #: This first AC solver is linear, isotropic and planar.
        raise ValueError('AC currently supports linear 2D models only; nonlinear/3D AC is not implemented')  #: Never reinterpret unsupported physics as a static or linear surrogate.
    settings = ac_settings(p, options)  #: Validate frequency and snapshot controls early.
    p['ac_settings'] = dict(settings)  #: Keep the returned project's saved controls consistent with the actual overridden run settings.
    omega = 2 * math.pi * settings['frequency_Hz']  #: Convert cyclic frequency to angular frequency in rad/s.
    groups = p.get('ac_conductors', [])  #: Only explicitly declared solid groups conduct eddy currents.
    if not isinstance(groups, list) or len(groups) > 32:  #: Bound the number of independent axial electric-gradient constraints.
        raise ValueError('Use at most 32 explicit AC solid-conductor groups')  #: Keep memory and field-port semantics inspectable.
    ids = [g.get('id') for g in groups if isinstance(g, dict)]  #: Collect conductor identities without trusting malformed entries.
    if len(ids) != len(groups) or any(not isinstance(i, str) or not i or len(i) > 80 for i in ids) or len(set(ids)) != len(ids):  #: Every source needs a unique stable identifier.
        raise ValueError('AC solid conductors need unique nonempty string ids')  #: Prevent accidental merging of independent electric gradients.
    conductors = {g['id']: g for g in groups}  #: Resolve each region assignment to its declared source/constraint.
    currents = {}  #: Store the complex RMS imposed current of each solid group.
    for g in groups:  #: Validate all solid definitions, including unexcited passive conductors.
        number(g.get('conductivity_Spm'), 'Solid conductivity (S/m)', 1., 1e9)  #: Conductivity is explicit SI data, independent of metadata-only catalogue fields.
        number(g.get('current_A', 0.), 'Solid RMS current (A)', -1e6, 1e6)  #: A zero current imposes an isolated net-zero-current conductor.
        number(g.get('phase_deg', 0.), 'Solid current phase (degrees)', -1e6, 1e6)  #: Electrical source phase differs from observation phase.
        currents[g['id']] = phasor(g.get('current_A', 0.), g.get('phase_deg', 0.))  #: Construct the imposed net-current phasor.
    for region in p['regions']:  #: Check assignments before mesh generation.
        if region.get('ac_conductor') not in [None, ''] and region['ac_conductor'] not in conductors:  #: Reject references to absent constraints.
            raise ValueError('Unknown AC conductor in region ' + region['id'])  #: Do not silently treat a misspelled solid as an insulator.
        if region.get('ac_conductor') and region.get('winding'):  #: A cell cannot be both a resolved solid and a uniform stranded source.
            raise ValueError('A region cannot be both an AC solid conductor and a stranded winding')  #: Avoid double-counting current and applying an invalid bulk winding loss model.
    winding_currents = []  #: Keep every independent electrical winding's RMS excitation separate.
    for winding in p['windings']:  #: Use the existing electrical-winding identities and turn weights.
        if p.get('builder', {}).get('excitation_mode') == 'sinusoidal_snapshot' and 'ac_current_A' not in winding:  #: A builder's evaluated instantaneous current cannot silently become an RMS amplitude.
            raise ValueError('Set explicit RMS ac_current_A for each winding; builder sinusoidal snapshot currents are instantaneous')  #: Require a deliberate AC source definition for this ambiguous import case.
        amplitude = number(winding.get('ac_current_A', winding['current']), 'Stranded RMS current (A)', -1e6, 1e6)  #: Explicit AC currents can coexist with the original static excitation without overwriting it.
        angle = number(winding.get('ac_phase_deg', 0.), 'Stranded AC phase (degrees)', -1e6, 1e6)  #: AC phases are explicit rather than inferred from phase names or static snapshot metadata.
        winding_currents.append(phasor(amplitude, angle))  #: Use the explicit RMS override or the documented ordinary-current RMS convention.
    check_series_currents(p, winding_currents)  #: Same-current sections must retain matching actual AC excitation; container windings stay independent.
    mesh = build_mesh(p, progress, cancel)  #: All material/source interfaces remain fitted to the initial triangles.
    if len(mesh['nodes']) > 8000 or len(mesh['elements']) > 16000:  #: Use a smaller explicit budget for the list-based complex Krylov backend.
        raise ValueError('AC mesh budget is 8000 nodes / 16000 triangles; reduce initial subdivisions')  #: Reject excessive jobs without changing the mesh silently.
    system = PlanarSystem(p, mesh, progress, cancel)  #: Reuse real stiffness, geometry and stranded ampere-turn bases.
    stiffness, _, _ = system.assemble()  #: Obtain K from the verified linear magnetostatic assembly.
    rows = [{j: complex(value) for j, value in row.items()} for row in stiffness]  #: Complex storage will hold K+jωM.
    rhs = [sum(b[i] * current for b, current in zip(system.bases, winding_currents)) for i in range(system.n)]  #: Assemble prescribed uniform stranded J phasors.
    data = {g['id']: dict(s=0., c={}, area=0., h_over_delta=0.) for g in groups}  #: Accumulate each solid group's conductivity integral, vector and resolution evidence.
    source_areas = {}  #: Cache exact stranded normalisation areas once instead of rescanning all cells during postprocessing.
    cells = []  #: Retain conductor/material properties for independent field/loss integration.
    for index, (triangle, area, curls, material, region) in enumerate(system.data):  #: Assemble every physical triangle once.
        if index % 1000 == 0:  #: Avoid excessive cancellation callback overhead.
            check_cancel(cancel)  #: Do not return a partially assembled field.
        gid = region.get('ac_conductor')  #: Unassigned material regions have no conductive diffusion term.
        sigma = conductors[gid]['conductivity_Spm'] if gid else 0.  #: Catalogue conductivity metadata does not activate eddy currents automatically.
        nu = 1 / (MU0 * material.get('mu_r', 1.))  #: Only real, frequency-independent permeability is supported here.
        cells.append((gid, sigma, nu))  #: Reuse exact solved element properties in postprocessing.
        if region.get('winding'):  #: Track the existing explicit-section or legacy polarity-side normalisation.
            key = region['id'] if 'turns' in region else (region['winding'], region['polarity'])  #: Explicit section turn counts and aggregate winding sides use different area keys.
            source_areas[key] = source_areas.get(key, 0.) + area  #: Integrate only effective tagged source area.
        if gid:  #: Add conductive mass only to explicitly resolved solids.
            group = data[gid]  #: Resolve this cell's shared axial-gradient constraint.
            group['s'] += sigma * area  #: s=∫σ dS has units siemens times metres.
            group['area'] += area  #: Store effective area after overlap priority is applied.
            delta = math.sqrt(2 * nu / (omega * sigma))  #: Classical skin depth for this linear μ and σ.
            points = [mesh['nodes'][n] for n in triangle]  #: Obtain physical side lengths for a mesh-resolution diagnostic.
            h = max(math.dist(points[k], points[(k + 1) % 3]) for k in range(3))  #: Use the longest triangle side as a conservative size measure.
            group['h_over_delta'] = max(group['h_over_delta'], h / delta)  #: Large ratios warn that skin depth may be under-resolved.
            for i, ni in enumerate(triangle):  #: Assemble the conductivity-weighted P1 vector and mass matrix.
                group['c'][ni] = group['c'].get(ni, 0.) + sigma * area / 3  #: c_i=∫σNi dS.
                for j, nj in enumerate(triangle):  #: Linear triangle mass integration is exact for NiNj.
                    value = 1j * omega * sigma * area * (2 if i == j else 1) / 12  #: Add jωσ|T|/12 times the standard diagonal/off-diagonal mass factors.
                    rows[ni][nj] = rows[ni].get(nj, 0j) + value  #: Retain sparse stiffness and conductive mass in one operator.
    low_rank = []  #: Keep conductor-constraint elimination sparse plus rank one per group.
    for gid, group in data.items():  #: Apply each prescribed total-current constraint.
        if group['area'] <= 0:  #: An entirely overwritten or unassigned solid has no valid current path.
            raise ValueError('AC conductor has zero effective area: ' + gid)  #: Reject invisible constraints instead of dividing by zero.
        low_rank.append((-1j * omega / group['s'], group['c']))  #: Eliminate E0 to obtain −jω ccᵀ/s in the field operator.
        for node, value in group['c'].items():  #: Add this solid group's imposed-current contribution.
            rhs[node] += value * currents[gid] / group['s']  #: The source vector is c I/s, preserving the exact net-current constraint.
    if progress:  #: Identify the physics being solved in the application's job log.
        progress(f'AC diffusion: {settings["frequency_Hz"]:g} Hz, RMS phasors, {len(groups)} solid constraints')  #: Do not call this a static phase snapshot.
    if groups:  #: Conductive diffusion requires the complex constrained operator.
        potential, info = gmres(rows, rhs, mesh['boundary'], low_rank, progress=progress, cancel=cancel)  #: Solve the eliminated complex magnetodynamic equations.
    else:  #: With no resolved solids the harmonic field operator is the existing real stiffness.
        real, first = system.solve([value.real for value in rhs])  #: Reuse verified PCG for the real impressed-source component.
        imag, second = system.solve([value.imag for value in rhs])  #: Solve the imaginary impressed-source component independently.
        potential = [complex(a, b) for a, b in zip(real, imag)]  #: Restore the complete RMS complex field; the induced voltage still depends on frequency.
        info = dict(iterations=first['iterations']+second['iterations'], residual=max(first['residual'], second['residual']), backend='AC two-component '+first['backend'])  #: Report actual solves rather than claiming eddy-current redistribution in stranded-only models.
    gradients = {gid: (currents[gid] + 1j * omega * sum(value * potential[n] for n, value in group['c'].items())) / group['s'] for gid, group in data.items()}  #: Recover E0=(I+jω cᵀa)/s for each solid.
    phase = cmath.exp(1j * math.radians(settings['phase_deg']))  #: Select an observation time without changing the solved RMS phasors.
    bfields, hfields, jfields, loss_density, measures = [], [], [], [], []  #: Keep complex field data separate from the real viewer snapshot.
    mean_energy, loss = 0., 0.  #: Accumulate cycle-mean magnetic energy and time-average ohmic loss.
    integrated = {gid: 0j for gid in conductors}  #: Independently integrate each solid's recovered J over its triangles.
    winding_indices = {w['id']: i for i, w in enumerate(p['windings'])}  #: Resolve source identity without a per-element winding search.
    quadrature = [(2/3, 1/6, 1/6), (1/6, 2/3, 1/6), (1/6, 1/6, 2/3)]  #: Three-point degree-two quadrature integrates |J|² exactly for linear A.
    for index, ((triangle, area, curls, material, region), (gid, sigma, nu)) in enumerate(zip(system.data, cells)):  #: Postprocess directly from the accepted complex solution.
        if index % 1000 == 0:  #: Keep loss integration interruptible on larger meshes.
            check_cancel(cancel)  #: Never publish partly integrated power results.
        b = [sum(potential[n] * curl[k] for n, curl in zip(triangle, curls)) for k in range(2)] + [0j]  #: Recover B=curl(Az ez) on each element.
        h = [nu * value for value in b]  #: Recover the linear H phasor from the same material law.
        j, density = 0j, 0.  #: Nonconducting and source-free cells have no resolved solid J or ohmic density.
        if gid:  #: Recover resolved solid current, including its skin/proximity redistribution.
            samples = [sigma * (gradients[gid] - 1j * omega * sum(weight * potential[n] for weight, n in zip(weights, triangle))) for weights in quadrature]  #: Evaluate J=σ(E0−jωA) at exact loss-integration points.
            j = sum(samples) / 3  #: The cell-average J also integrates net current exactly.
            density = sum(abs(value) ** 2 for value in samples) / (3 * sigma)  #: RMS phasors give average Joule density |J|²/σ without an extra half factor.
            integrated[gid] += area * j  #: Check the imposed current independently from the eliminated algebraic equation.
        elif region.get('winding'):  #: Keep impressed stranded current visible without inventing resolved copper loss.
            winding_index = winding_indices[region['winding']]  #: Find this source's RMS excitation in constant time.
            j = winding_currents[winding_index] * region['polarity'] * region.get('turns', p['windings'][winding_index]['turns'])  #: Form the section ampere-turn phasor before area normalisation.
            key = region['id'] if 'turns' in region else (region['winding'], region['polarity'])  #: Match explicit-section versus aggregate-side normalisation.
            j /= source_areas[key]  #: Preserve total ampere-turns using the cached effective tagged area.
        volume = area * system.depth  #: Convert planar areas to the selected effective stack volumes.
        mean_energy += .5 * volume * nu * sum(abs(value) ** 2 for value in b)  #: Cycle-mean magnetic energy uses RMS B with the usual one-half constitutive factor.
        loss += volume * density  #: Integrate time-average resolved ohmic loss in watts.
        bfields.append(b)  #: Retain all complex magnetic flux-density components.
        hfields.append(h)  #: Retain all complex magnetic field-intensity components.
        jfields.append(j)  #: Store the element-average axial current phasor.
        loss_density.append(density)  #: Store exactly integrated element-average loss density, not |average J|²/σ.
        measures.append(volume)  #: Preserve the application's region-integration convention.
    linkages = [system.depth * sum(value * a for value, a in zip(basis, potential)) for basis in system.bases]  #: Flux linkage is linear in the complex vector potential, without conjugating the basis.
    voltages = [1j * omega * value for value in linkages]  #: Stranded source voltage is the induced jωλ; copper resistance is not included.
    source_power = sum(v * i.conjugate() for v, i in zip(voltages, winding_currents))  #: Sum RMS complex power from all impressed stranded sources.
    source_power += sum(system.depth * gradients[gid] * currents[gid].conjugate() for gid in conductors)  #: Include the solid axial-gradient field ports.
    expected_power = complex(loss, 2 * omega * mean_energy)  #: For real μ, input power equals ohmic loss plus jω∫ν|B|²dV.
    balance = abs(source_power - expected_power) / max(abs(source_power), abs(expected_power), 1e-30)  #: Normalise the independent integrated complex-power check.
    if balance > 2e-5:  #: A converged linear system alone cannot excuse inconsistent physical postprocessing.
        raise RuntimeError(f'AC complex-power balance failed ({balance:.3g})')  #: Reject results with an unacceptable current/field/loss inconsistency.
    ports = []  #: Report actual simultaneously excited field ports, not an uncomputed impedance matrix.
    for gid, group in data.items():  #: Include driven and passive solid constraints.
        current, voltage = currents[gid], system.depth * gradients[gid]  #: Axial voltage-gradient port uses the selected stack length.
        error = abs(integrated[gid] - current) / max(abs(current), sum(abs(jfields[i]) * system.data[i][1] for i, cell in enumerate(cells) if cell[0] == gid), 1e-30)  #: Scale net-zero-conductor checks by circulating-current magnitude.
        if error > 2e-7:  #: Integrated recovered J must satisfy each imposed constraint.
            raise RuntimeError('AC integrated conductor-current check failed: ' + gid)  #: Do not publish a conductor with an inconsistent return/current condition.
        ports.append(dict(id=gid, name=conductors[gid].get('name', gid), current_A=pair(current), voltage_V=pair(voltage), impedance_ohm=pair(voltage/current) if current else None, integrated_current_A=pair(integrated[gid]), current_balance=error, h_over_skin_depth=group['h_over_delta']))  #: The V/I ratio applies only to the present simultaneous excitation and boundary reference.
    for winding, current, voltage, linkage in zip(p['windings'], winding_currents, voltages, linkages):  #: Expose stranded electrical winding ports in the same complex convention.
        ports.append(dict(id=winding['id'], name=winding['name'], current_A=pair(current), voltage_V=pair(voltage), linkage_Wb_turn=pair(linkage), impedance_ohm=pair(voltage/current) if current else None, stranded=True))  #: Do not invent a self-impedance when other driven windings are active.
    snapshot_b = [[math.sqrt(2) * (value * phase).real for value in b] for b in bfields]  #: Feed existing 2D field rendering with an explicitly labelled instantaneous snapshot.
    snapshot_h = [[math.sqrt(2) * (value * phase).real for value in h] for h in hfields]  #: Apply exactly the same observation phase to H.
    snapshot_a = [math.sqrt(2) * (value * phase).real for value in potential]  #: Flux contours use this same instantaneous Az, not phasor magnitude.
    snapshot_energy = sum(.5 * volume * cell[2] * sum(value * value for value in b) for volume, cell, b in zip(measures, cells, snapshot_b))  #: Keep the generic viewer's snapshot energy internally consistent.
    rms_b = [math.sqrt(sum(abs(value) ** 2 for value in b)) for b in bfields]  #: RMS vector norm is distinct from any particular instantaneous magnitude.
    post = dict(B=snapshot_b, H=snapshot_h, Az=snapshot_a, measures=measures, energy_J=snapshot_energy)  #: Preserve existing 2D field/contour rendering and export compatibility.
    post['phasor'] = dict(B_real=[[v.real for v in b] for b in bfields], B_imag=[[v.imag for v in b] for b in bfields], H_real=[[v.real for v in h] for h in hfields], H_imag=[[v.imag for v in h] for h in hfields], Az_real=[v.real for v in potential], Az_imag=[v.imag for v in potential], Jz_real=[v.real for v in jfields], Jz_imag=[v.imag for v in jfields], B_rms_magnitude_T=rms_b, ohmic_loss_density_Wpm3=loss_density)  #: Preserve complete complex data rather than discarding phase to fit a static schema.
    warnings = ['Linear 2D magnetoquasistatic RMS phasors, exp(+jωt). No displacement current, hysteresis/core-loss law, nonlinear/3D AC or end effects.', 'Displayed B/H/Az are instantaneous fields at the specified phase; phasor real/imaginary data and RMS norms are exported separately.', 'Only explicit AC solid groups have resolved conductivity/loss. Stranded winding blocks/turns have uniform impressed J and no solved copper or litz loss.', 'Solid groups share an axial electric driving gradient and a net-current constraint; they are not a general electrical circuit. Nonzero total axial current relies on the finite outer-boundary return reference.', 'Port V/I ratios describe the present simultaneous excitation, not an extracted multiport/self-impedance matrix. Check mesh, skin-depth and air-domain sensitivity.', 'Independent research implementation; external Maxwell/measurement correlation pending.']  #: Attach the exact formulation/port/data limitations to every exported result.
    if any(group['h_over_delta'] > .5 for group in data.values()):  #: A large triangle/skin-depth ratio warrants explicit mesh investigation.
        warnings.append('Some solid triangles exceed half a skin depth in longest-side length. Refine and compare losses/impedance; this diagnostic is not an accuracy bound.')  #: Do not call a converged algebraic solve skin-depth converged.
    stats = dict(mode='2d', analysis='ac', frequency_Hz=settings['frequency_Hz'], nodes=len(mesh['nodes']), elements=len(mesh['elements']), dofs=system.n-len(system.fixed), peak_B_T=max((math.sqrt(sum(v*v for v in b)) for b in snapshot_b), default=0.), peak_B_rms_T=max(rms_b, default=0.), energy_J=snapshot_energy, mean_magnetic_energy_J=mean_energy, ohmic_loss_W=loss, seconds=time.perf_counter()-started, solver=info, energy_consistency=None, reciprocity=None, nonlinear=False, mesh_quality=mesh['quality'], complex_power_balance=balance)  #: Distinguish AC physical checks from static energy/matrix checks.
    region_stats = []  #: Keep the generic region table consistent with the displayed instantaneous field.
    peaks = [math.sqrt(sum(v*v for v in b)) for b in snapshot_b]  #: Compute only instantaneous magnitudes for the existing region table.
    for tag, region in enumerate(p['regions']):  #: Report effective tagged volumes, excluding overwritten material.
        indices = [i for i, value in enumerate(mesh['tags']) if value == tag]  #: Resolve this region's actual solved triangles.
        volume = sum(measures[i] for i in indices)  #: Sum selected stack-volume measures.
        region_stats.append(dict(id=region['id'], name=region['name'], volume_m3=volume, mean_B_T=sum(peaks[i]*measures[i] for i in indices)/volume if volume else 0., peak_B_T=max((peaks[i] for i in indices), default=0.)))  #: Preserve the existing report table schema with explicit snapshot semantics.
    return dict(project=p, mesh=mesh_public(mesh), fields=post, stats=stats, windings=[dict(id=w['id'], name=w['name'], turns=w['turns'], current_A=math.sqrt(2)*(i*phase).real, linkage_Wb_turn=math.sqrt(2)*(l*phase).real) for w,i,l in zip(p['windings'],winding_currents,linkages)], inductance_H=None, circuits=None, regions=region_stats, warnings=warnings, ac=dict(settings=settings, convention='RMS; x(t)=sqrt(2) Re[x exp(+jωt)]', ports=ports, source_complex_power_VA=pair(source_power), mean_magnetic_energy_J=mean_energy, ohmic_loss_W=loss, complex_power_balance=balance))  #: Return actual solved phasors and a clearly defined compatible field snapshot.


def frequency_sweep(project, frequencies, options=None, progress=None, cancel=None):  #: Recompute actual AC fields at each requested frequency.
    if not isinstance(frequencies, list) or not 2 <= len(frequencies) <= 12:  #: Bound the number of complete solves in a study.
        raise ValueError('Use 2–12 AC sweep frequencies')  #: Reject unbounded or malformed studies.
    for value in frequencies:  #: Validate all requested points before starting any expensive solve.
        number(value, 'Sweep frequency (Hz)', .001, 1e7)  #: Keep the same frequency limits as individual AC solves.
    rows = []  #: Record physical outputs for every accepted frequency.
    for frequency in frequencies:  #: Never infer AC loss curves from static interpolation.
        check_cancel(cancel)  #: Keep the study cancellable between operating points.
        controls = copy.deepcopy(options or {})  #: Avoid changing caller-owned settings.
        controls['frequency_Hz'] = frequency  #: Override only the point's actual frequency.
        result = solve_ac(project, controls, progress, cancel)  #: Assemble and solve the complex field at this frequency.
        rows.append(dict(frequency_Hz=frequency, ohmic_loss_W=result['ac']['ohmic_loss_W'], mean_magnetic_energy_J=result['ac']['mean_magnetic_energy_J'], complex_power_balance=result['ac']['complex_power_balance'], ports=[ac_series_equivalent(port, frequency) for port in result['ac']['ports']]))  #: Preserve actual phasors and derive Ls=Im(V/I)/(2pi f) for every defined port ratio.
    return dict(kind='ac_sweep', rows=rows, note='Each frequency is an independent linear 2D AC field solve on the same initial mesh; check skin-depth convergence at every frequency. Ls = Im(V/I)/(2 pi f) is a signed series equivalent at the present simultaneous excitation, not an isolated self/magnetising/leakage inductance or a full impedance matrix. Zero-current V/I is undefined.')  #: Keep physical interpretation and zero-current limits with the exported study.
