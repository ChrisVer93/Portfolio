'use strict'; // #: Keep the additive AC interface in strict JavaScript mode.
const acBaseLeft = renderLeft; // #: Retain all existing builder, material and adaptive controls.
const acBaseBottom = renderBottom; // #: Preserve the existing static/adaptive result views.
const acBaseMetrics = renderMetrics; // #: Retain ordinary metrics for non-AC results.
let acLastResult = null; // #: Detect a newly completed AC field without overriding later user tab selections.
const acComplex = z => fmt(z[0]) + (z[1] < 0 ? ' − j' : ' + j') + fmt(Math.abs(z[1])); // #: Display the stored real/imaginary RMS convention explicitly.

renderLeft = function () { // #: Extend the common Analysis panel with real AC controls.
    acBaseLeft(); // #: Render the original controls before adding the AC subtree.
    if (S.tab !== 'setup') return; // #: Keep this interface confined to Analysis.
    const section = document.createElement('section'); // #: Preserve event handlers on existing panel subtrees.
    section.innerHTML = '<div class="section-label">AC / eddy currents · linear 2D</div>'; // #: State the available solver scope before presenting inputs.
    if (S.p.mode !== '2d' || S.p.materials.some(m => m.bh)) { // #: Match the server's current physics restrictions.
        section.innerHTML += '<p class="hint">AC solving requires a linear 2D model. Nonlinear and 3D AC are not implemented.</p>'; // #: Do not silently convert an unsupported problem.
    } else { // #: Expose controls for a supported linear planar project.
        const settings = S.p.ac_settings || {frequency_Hz: 10000, phase_deg: 0}; // #: Use saved analysis controls when available.
        section.innerHTML += input('Frequency · Hz', settings.frequency_Hz, 'acFrequency'); // #: Frequency changes the diffusion operator, not merely a display label.
        section.innerHTML += input('Displayed snapshot phase · degrees', settings.phase_deg, 'acObservation'); // #: This phase reconstructs an instant from the solved RMS phasors.
        section.innerHTML += '<p class="hint">AC current entries are RMS amperes. Source phase is separate from displayed phase. Existing winding regions are stranded uniform-J sources: no resolved copper/litz loss.</p>'; // #: Avoid peak/RMS and winding-loss ambiguities.
        for (const winding of S.p.windings) { // #: Keep each electrical winding's excitation independent.
            const amplitude = 'ac_current_A' in winding ? (winding.ac_current_A ?? '') : (S.p.builder?.excitation_mode === 'sinusoidal_snapshot' ? '' : winding.current); // #: Never prefill an evaluated builder snapshot as though it were an RMS amplitude.
            section.innerHTML += '<label class="form-field">' + esc(winding.name) + ' · RMS AC current A<input type="number" step="any" data-ac-winding="' + esc(winding.id) + '" data-ac-key="ac_current_A" value="' + esc(amplitude) + '"></label>'; // #: Allow an independent explicit AC amplitude without changing the stored static excitation.
            section.innerHTML += '<label class="form-field">' + esc(winding.name) + ' · AC phase °<input type="number" step="any" data-ac-winding="' + esc(winding.id) + '" data-ac-key="ac_phase_deg" value="' + esc(winding.ac_phase_deg === undefined ? 0 : (winding.ac_phase_deg ?? '')) + '"></label>'; // #: Phase names do not implicitly impose electrical phase.
        } // #: Finish the per-winding source controls.
        section.innerHTML += '<button id="addAcSolid" class="block-button">Assign selected region as solid conductor</button>'; // #: Add an explicit resolved-conductor constraint from selected geometry.
        section.innerHTML += '<p class="hint">Select a non-winding region first. Each solid group has one axial driving gradient and prescribed net current. Use opposite currents for a return path; zero net current permits induced circulating currents.</p>'; // #: Describe the physical constraint rather than calling it a general circuit solver.
        for (const conductor of S.p.ac_conductors || []) { // #: Show every explicitly conducting group and its source assumptions.
            section.innerHTML += '<div class="section-label">Solid · ' + esc(conductor.name || conductor.id) + '</div>'; // #: Resolve labels without merging group identities.
            for (const [key, label, fallback] of [['conductivity_Spm', 'Conductivity · S/m', 58e6], ['current_A', 'Net RMS current · A', 0], ['phase_deg', 'Current phase · degrees', 0]]) { // #: Keep conductivity, imposed current and electrical phase distinct.
                section.innerHTML += '<label class="form-field">' + label + '<input type="number" step="any" data-ac-solid="' + esc(conductor.id) + '" data-ac-key="' + key + '" value="' + esc(conductor[key] ?? fallback) + '"></label>'; // #: Store SI conductivity explicitly instead of interpreting material metadata silently.
            } // #: End the editable source/constraint quantities.
            section.innerHTML += '<button data-ac-remove="' + esc(conductor.id) + '">Remove solid assignment</button>'; // #: Allow reversible removal of the declared conducting model.
        } // #: End the solid-group list.
        section.innerHTML += '<button id="acRun" class="block-button">Solve AC fields and ohmic losses</button>'; // #: Start the actual complex field solver.
        section.innerHTML += input('Sweep frequencies · Hz', '1000, 10000, 100000', 'acFrequencies', {type: 'text'}); // #: Request independently solved frequencies rather than a static phase sweep.
        section.innerHTML += '<button id="acSweep" class="block-button">Run AC frequency sweep</button>'; // #: Launch the bounded multi-frequency study.
        section.innerHTML += '<p class="hint">No AC adaptive refinement yet. Check skin-depth and mesh convergence. Solid V/I ratios apply to the present simultaneous excitation; no full impedance matrix or voltage-driven network is inferred.</p>'; // #: Keep the first AC release's limits visible before solving.
        const controls = () => ({frequency_Hz: Number(section.querySelector('[data-edit="acFrequency"]').value), phase_deg: Number(section.querySelector('[data-edit="acObservation"]').value)}); // #: Read the current visible values for each requested run.
        for (const key of ['acFrequency', 'acObservation']) { // #: Save frequency/observation controls with the project.
            section.querySelector('[data-edit="' + key + '"]').onchange = () => {S.p.ac_settings = controls(); changed();}; // #: Invalidate old fields when run settings are edited.
        } // #: Finish analysis-setting persistence.
        section.querySelector('#acRun').onclick = () => start('ac', {options: controls()}); // #: Reuse standard job polling, cancellation and export handling.
        section.querySelector('#acSweep').onclick = () => start('ac_sweep', {options: controls(), frequencies: section.querySelector('[data-edit="acFrequencies"]').value.split(',').map(v => Number(v.trim()))}); // #: Send all frequency points for strict server-side validation before solving.
        section.querySelector('#addAcSolid').onclick = () => { // #: Convert only an explicitly selected unexcited geometric region.
            const region = getSel(); // #: Read the current shared CAD/geometry selection.
            if (S.sel?.kind !== 'regions' || !region) return toast('Select a geometric region first'); // #: Never assign an entire model accidentally.
            if (region.winding || region.ac_conductor) return toast('Choose a region with no existing winding/solid assignment'); // #: Prevent double-counted sources or overwritten conductor constraints.
            const id = uid('solid'); // #: Give this independent axial-gradient constraint a stable unique identifier.
            S.p.ac_conductors ||= []; // #: Initialise the optional solid-group collection only when needed.
            S.p.ac_conductors.push({id, name: region.name, conductivity_Spm: 58e6, current_A: 0, phase_deg: 0}); // #: Start as a passive group with an explicit editable illustrative copper conductivity.
            region.ac_conductor = id; // #: Link the selected physical region to its declared constraint.
            changed(); // #: Preserve ordinary undo/autosave/invalidation behaviour.
        }; // #: Complete explicit solid assignment.
        section.querySelectorAll('[data-ac-winding]').forEach(el => el.onchange = () => {S.p.windings.find(w => w.id === el.dataset.acWinding)[el.dataset.acKey] = el.value.trim() ? Number(el.value) : null; changed();}); // #: Edit only the selected winding's explicit AC amplitude or phase; blank entries remain invalid rather than becoming zero silently.
        section.querySelectorAll('[data-ac-solid]').forEach(el => el.onchange = () => {S.p.ac_conductors.find(g => g.id === el.dataset.acSolid)[el.dataset.acKey] = Number(el.value); changed();}); // #: Edit the chosen solid constraint and let the server reject invalid SI values.
        section.querySelectorAll('[data-ac-remove]').forEach(el => el.onclick = () => {const id = el.dataset.acRemove; S.p.ac_conductors = S.p.ac_conductors.filter(g => g.id !== id); for (const region of S.p.regions) if (region.ac_conductor === id) delete region.ac_conductor; changed();}); // #: Remove both group and region references so no dangling constraint is saved.
    } // #: End the supported-physics branch.
    $('leftContent').prepend(section); // #: Place AC controls above the retained static/adaptive controls.
}; // #: Complete the Analysis-panel extension.

renderMetrics = function () { // #: Give AC results physically correct RMS/average labels.
    acBaseMetrics(); // #: Preserve ordinary static and adaptive behaviour when no AC result is selected.
    if (!S.result?.ac) return; // #: Stop before applying AC labels to a magnetostatic result.
    const result = S.result; // #: Read the accepted complex-field result.
    const values = [['MAX ELEMENT RMS |B|', fmt(result.stats.peak_B_rms_T) + ' T'], ['MEAN MAGNETIC ENERGY', fmt(result.ac.mean_magnetic_energy_J) + ' J'], ['RESOLVED OHMIC LOSS', fmt(result.ac.ohmic_loss_W) + ' W'], ['AC POWER-BALANCE RATIO', fmt(result.ac.complex_power_balance)]]; // #: Distinguish cycle-mean energy and ohmic loss from the displayed instantaneous fields.
    $('metrics').innerHTML = values.map(([label, value]) => '<div><small>' + esc(label) + '</small><strong>' + esc(value) + '</strong></div>').join(''); // #: Escape all metric text before inserting it into the existing layout.
}; // #: Complete the AC metric presentation.

renderBottom = function () { // #: Present RMS complex field ports and frequency-study evidence.
    if (S.result?.ac && acLastResult !== S.result) { // #: Handle each newly completed AC result exactly once.
        acLastResult = S.result; // #: Retain object identity so later user tab changes persist.
        S.study = null; // #: Do not present a preceding static study as the latest AC study.
        S.bottom = 'matrix'; // #: Open the relevant complex field-port table after solving.
        S.logs = S.logs.filter(line => !line.startsWith('Energy consistency:') && !line.startsWith('Matrix reciprocity:')); // #: Remove inherited static-only diagnostic labels from the common polling path.
        S.logs.push('AC complex-power balance: ' + fmt(S.result.ac.complex_power_balance), 'Fields display an instantaneous snapshot at ' + fmt(S.result.ac.settings.phase_deg) + '°; source and exported complex quantities use RMS phasors.'); // #: Record the applicable AC physical check and display convention.
        $('statusLine').textContent = 'Completed AC solve · ' + fmt(S.result.ac.settings.frequency_Hz) + ' Hz · snapshot ' + fmt(S.result.ac.settings.phase_deg) + '°'; // #: Correct the generic polling path's magnetostatic completion label.
    } // #: Leave later log/study/table navigation under user control.
    if (S.bottom === 'matrix' && S.result?.ac) { // #: The matrix tab becomes an explicitly labelled operating-point field-port view for AC.
        document.querySelectorAll('[data-bottom]').forEach(b => b.classList.toggle('active', b.dataset.bottom === S.bottom)); // #: Keep the common active-tab styling consistent.
        const rows = S.result.ac.ports.map(p => [p.name, acComplex(p.current_A), acComplex(p.voltage_V), p.impedance_ohm ? acComplex(p.impedance_ohm) : '—']); // #: Show real and imaginary RMS quantities without dropping phase.
        $('bottomContent').innerHTML = '<p>RMS field ports · present simultaneous excitation. V/I is not an extracted self/multiport impedance matrix.</p>' + table(['Port', 'Current · A', 'Voltage · V', 'V/I · Ω'], rows); // #: Avoid presenting these ratios as a validated inductance matrix.
        return; // #: Do not run the static matrix renderer on an AC result.
    } // #: End the AC port-table branch.
    if (S.bottom === 'studies' && S.study?.kind === 'ac_sweep') { // #: Show each independently solved AC frequency as a study row.
        document.querySelectorAll('[data-bottom]').forEach(b => b.classList.toggle('active', b.dataset.bottom === S.bottom)); // #: Retain active-tab styling for frequency studies.
        const rows = S.study.rows.map(r => [fmt(r.frequency_Hz), fmt(r.ohmic_loss_W), fmt(r.mean_magnetic_energy_J), fmt(r.complex_power_balance)]); // #: Compare actual recomputed loss, mean energy and physical balance.
        $('bottomContent').innerHTML = table(['Frequency · Hz', 'Ohmic loss · W', 'Mean magnetic energy · J', 'Power-balance ratio'], rows) + '<p class="hint">' + esc(S.study.note) + '</p>'; // #: Keep mesh and operating-point qualifications attached to the study.
        return; // #: Do not interpret a frequency sweep as a current sweep.
    } // #: End the AC frequency-study branch.
    acBaseBottom(); // #: Preserve every existing non-AC result/log/adaptive view.
}; // #: Complete the additive AC result interface.
