'use strict'; // #: Keep accidental global assignments and invalid JavaScript behaviour visible.
const adaptiveBaseLeft = renderLeft; // #: Retain the existing analysis panel and all its controls.
const adaptiveBaseBottom = renderBottom; // #: Retain the existing log, matrix, region and study renderers.
const adaptiveBaseMetrics = renderMetrics; // #: Preserve the original field metrics before adding adaptive status.
let adaptiveLastResult = null; // #: Detect a newly completed adaptive result without repeatedly replacing the user's selected tab.

renderLeft = function () { // #: Extend the existing panel rather than duplicating the application workflow.
    adaptiveBaseLeft(); // #: Build and wire the original controls first.
    if (S.tab !== 'setup') return; // #: Adaptive controls belong only to the Analysis panel.
    const section = document.createElement('section'); // #: Use a new subtree so existing button handlers remain attached.
    section.innerHTML = '<div class="section-label">Adaptive mesh · linear 2D</div>'; // #: State the implemented dimensional and material scope.
    if (S.p.mode !== '2d' || S.p.materials.some(m => m.bh)) { // #: Match the server's linear-planar restriction.
        section.innerHTML += '<p class="hint">Adaptive solving currently requires a linear 2D model. Ordinary 3D and nonlinear 2D solves remain available.</p>'; // #: Explain the restriction without changing the selected problem.
    } else { // #: Offer controls only for supported physics.
        section.innerHTML += input('Maximum passes', 4, 'adaptivePasses'); // #: Bound the number of complete solve–estimate passes.
        section.innerHTML += input('Relative indicator target', 0.15, 'adaptiveIndicator'); // #: This is an uncalibrated indicator ratio, not a certified error percentage.
        section.innerHTML += input('Relative energy-change target', 0.01, 'adaptiveEnergy'); // #: Require an inter-pass integral check as well as the spatial indicator.
        section.innerHTML += input('Squared-indicator fraction to mark', 0.5, 'adaptiveMarking'); // #: Control how much residual mass selects new local refinement.
        section.innerHTML += '<button id="adaptiveButton" class="block-button">Solve with local adaptive refinement</button>'; // #: Start a real adaptive server job from the standard application.
        section.innerHTML += '<p class="hint">Local conforming triangle subdivision. Nonzero winding current required. Targets may remain unmet at pass/memory limits. Matrix accuracy needs separate unit-excitation checks. No smoothing/coarsening yet.</p>'; // #: Expose operating-point and stopping limitations before solving.
        section.querySelector('#adaptiveButton').onclick = () => { // #: Read the current visible controls when the user actually starts the job.
            const value = key => Number(section.querySelector('[data-edit="' + key + '"]').value); // #: Convert each numeric text field for server-side strict validation.
            const options = {max_passes: value('adaptivePasses'), indicator_target: value('adaptiveIndicator'), energy_target: value('adaptiveEnergy'), marking_fraction: value('adaptiveMarking')}; // #: Send named controls with the result's reproducible settings.
            return start('adaptive', {options, matrix: $('matrixOption').checked}); // #: Use existing asynchronous polling, cancellation and final-field handling; return completion for integration tests.
        }; // #: End the job-start handler.
    } // #: End the supported/unsupported analysis branch.
    $('leftContent').prepend(section); // #: Keep adaptive controls visible above the original analysis sections.
}; // #: Complete the additive analysis-panel extension.

renderBottom = function () { // #: Display adaptive evidence in the existing Studies area.
    if (S.result?.adaptive && adaptiveLastResult !== S.result) { // #: React once to each newly completed adaptive field result.
        adaptiveLastResult = S.result; // #: Remember this exact result object.
        S.study = {kind: 'adaptive', ...S.result.adaptive}; // #: Reuse the existing Save study JSON export with the full accepted-pass history.
        S.bottom = 'studies'; // #: Show the stopping evidence immediately after the adaptive job completes.
    } // #: Later tab clicks retain the user's selection.
    if (S.bottom !== 'studies' || S.study?.kind !== 'adaptive') return adaptiveBaseBottom(); // #: Delegate every unrelated view to the existing renderer.
    document.querySelectorAll('[data-bottom]').forEach(b => b.classList.toggle('active', b.dataset.bottom === S.bottom)); // #: Keep the active Studies tab styling consistent.
    const study = S.study; // #: Read the same data that study JSON export will save.
    const rows = study.rows.map(r => [r.pass_number, r.elements, fmt(r.energy_J), fmt(r.relative_indicator), r.energy_change === null ? '—' : fmt(r.energy_change), r.marked_elements]); // #: Show accepted mesh size, energy, residual indicator, energy change and proposed marking.
    $('bottomContent').innerHTML = '<p><strong>Adaptive status: ' + esc(study.status) + '</strong></p>' + table(['Pass', 'Triangles', 'Energy · J', 'Indicator ratio', 'Energy-change ratio', 'Cells selected'], rows) + '<p class="hint">' + esc(study.note) + '</p>'; // #: Escape all explanatory text and retain raw dimensionless ratios in the table.
}; // #: Complete the adaptive evidence renderer.

renderMetrics = function () { // #: Separate algebraic convergence from adaptive-target completion.
    adaptiveBaseMetrics(); // #: Render the existing physical quantities and solver residual.
    if (!S.result?.adaptive) return; // #: Ordinary solve metrics retain their previous behaviour.
    const label = $('metrics').querySelector('div:last-child small'); // #: Locate the solve-status heading without changing the physical values.
    if (label) label.textContent = S.result.adaptive.targets_met ? 'ADAPTIVE TARGETS MET' : 'ADAPTIVE TARGETS NOT MET'; // #: Never call a pass-limited adaptive run converged merely because its linear equations solved.
}; // #: Complete the status-label correction.
