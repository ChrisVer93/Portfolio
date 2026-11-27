'use strict'; // #: Keep the additive native-backend interface explicit and error-visible.
const nativeBaseLeft = renderLeft; // #: Preserve every existing builder, material, AC and reference-solver control.
const nativeBaseMetrics = renderMetrics; // #: Preserve existing result metrics for other solver modes.
const nativeBaseBottom = renderBottom; // #: Retain the existing studies/matrix/log result views.
let nativePackages = null; // #: Treat backend availability as unknown until the actual server environment is inspected.
let nativeCoreResult = null; // #: Keep independent component screening separate from the active FEM field result.
let nativeImageURL = null; // #: Revoke preview blob URLs when replacing a CAD projection.

renderLeft = function () { // #: Extend the existing Analysis panel without replacing its workflow.
    nativeBaseLeft(); // #: Render all original controls first.
    if (S.tab !== 'setup') return; // #: Keep optional-backend actions in the Analysis tab.
    const section = document.createElement('section'); // #: Attach handlers only to the new subtree.
    const available = nativePackages?.ngsolve === true; // #: Enable FEM actions only when the tested packages are actually present.
    const controls = S.p.native_settings || {maxh_m: .015, max_passes: 2}; // #: Retain native mesh controls in the shared project JSON.
    section.innerHTML = '<div class="section-label">Netgen / NGSolve · linear 2D and 3D</div>'; // #: Identify the actual external mesh/FEM backend and physical scope.
    section.innerHTML += '<p class="hint">Unstructured triangles or tetrahedra; native local refinement. Linear magnetostatics only. 3D sources remain ideal closed current sheets. For nonlinear 2D and AC, use the existing dedicated controls below.</p>'; // #: Expose applicability before the user starts a solve.
    section.innerHTML += input('Maximum element size · mm', controls.maxh_m*1000, 'nativeSize'); // #: Request real native element size independently of the reference mesh subdivisions.
    section.innerHTML += input('Maximum mesh passes · 1–4', controls.max_passes, 'nativePasses'); // #: Bound complete native solve/estimate/refine passes.
    if(S.p.mode==='3d')section.innerHTML+='<label>Native HCurl order <select data-edit="nativeOrder">'+[0,2,3].map(n=>'<option value="'+n+'"'+(n===(controls.hcurl_order||0)?' selected':'')+'>'+n+(n===0?' · original lowest order':' · single pass')+'</option>').join('')+'</select></label><p class="hint">Orders2/3 require1mesh pass. Higher-order fields vary inside cells; plots/exports use centroid samples. Direct probes and energy use the actual native field.</p>'; // #: Expose native polynomial-order selection with explicit pass, display and qualification limits.
    section.innerHTML += '<button id="nativeRun" class="block-button" '+(available ? '' : 'disabled')+'>Solve with Netgen / NGSolve</button>'; // #: Route this action to the established backend explicitly.
    section.innerHTML += '<p class="hint">'+(available ? 'Tested package versions detected. Recovery indicators are not certified error bounds; inspect stopping status and integral convergence.' : 'Native backend unavailable or not yet checked. Start Studio in the documented optional development environment; the reference solver remains available.')+'</p>'; // #: Report actual environment availability rather than pretending dependencies are bundled.
    section.innerHTML += '<button id="nativeCheck">Check backend availability</button>'; // #: Allow a fresh environment diagnostic without installing anything.
    const core = S.p.openmagnetics_request || {format: 'magnetics-studio.openmagnetics-core/1', shape: 'E 42/21/15', material: 'N97', bobbin: 'Bobbin E42/15', wire: 'Round 0.5 - Grade 1', gap_m: .001, turns: 24, frequency_Hz: 100000, temperature_C: 25, primary_current_rms_A: .001, reluctance_model: 'CLASSIC'}; // #: Keep the supported component-screening request separate from the current FEM geometry.
    section.innerHTML += '<div class="section-label">OpenMagnetics · component/core CAD</div><p class="hint">Separate catalogue core screening. It does not replace the current FEM model or generate winding solids. Core CAD includes MVB’s extra 5 µm mating gap.</p>'; // #: Prevent screening estimates and CAD from being mistaken for matched solved FEM geometry.
    for (const [key, label] of [['shape','Core shape catalogue name'], ['material','Core material catalogue name'], ['bobbin','Bobbin catalogue name'], ['wire','Wire catalogue name']]) { // #: Expose the actual external catalogue identifiers.
        section.innerHTML += input(label, core[key], 'om_'+key, {type:'text'}); // #: Let the native library validate actual catalogue names.
    } // #: End editable catalogue identity controls.
    section.innerHTML += input('Central material removal · mm', core.gap_m*1000, 'om_gap'); // #: Keep requested gap removal distinct from the measured CAD mating separation.
    section.innerHTML += input('Equal primary / secondary turns', core.turns, 'om_turns'); // #: State the limited two-winding screening example explicitly.
    section.innerHTML += '<button id="nativeCore" class="block-button" '+(nativePackages?.openmagnetics ? '' : 'disabled')+'>Calculate and generate core CAD</button><div id="nativeCoreOutput"></div>'; // #: Offer real component calculations only when the qualified packages are detected.
    const readOptions = () => ({maxh_m: Number(section.querySelector('[data-edit="nativeSize"]').value)/1000, max_passes: Number(section.querySelector('[data-edit="nativePasses"]').value),hcurl_order:S.p.mode==='3d'?Number(section.querySelector('[data-edit="nativeOrder"]').value):0}); // #: Convert visible mesh inputs to explicit SI run options.
    section.querySelector('#nativeRun').onclick = () => start('ngsolve', {options: readOptions(), matrix: $('matrixOption').checked}); // #: Reuse existing asynchronous jobs, cancellation, result provenance and 3D volume rendering.
    section.querySelector('#nativeCheck').onclick = async () => {try {nativePackages = await api('/api/backends'); renderLeft();} catch (error) {toast(error.message);}}; // #: Refresh only metadata and preserve actionable failures.
    for (const key of ['nativeSize', 'nativePasses', ...(S.p.mode==='3d'?['nativeOrder']:[])]) { // #: Save native run settings using the normal project persistence path.
        section.querySelector('[data-edit="'+key+'"]').onchange = () => {S.p.native_settings = readOptions(); changed();}; // #: Invalidate old fields when actual native mesh settings change.
    } // #: End native mesh setting persistence.
    section.querySelector('#nativeCore').onclick = async () => { // #: Use a separate completion handler because this result is not a FEM field.
        if (S.busy) return toast('An analysis is already running'); // #: Preserve the shared single-job constraint.
        const get = key => section.querySelector('[data-edit="om_'+key+'"]').value; // #: Read catalogue names and dimensions from the current visible controls.
        const request = {...core, shape:get('shape'), material:get('material'), bobbin:get('bobbin'), wire:get('wire'), gap_m:Number(get('gap'))/1000, turns:Number(get('turns'))}; // #: Preserve explicit physical conventions and convert gap units once.
        try { // #: Keep native/schema failures actionable without altering existing solved fields.
            setBusy(true, 'openmagnetics'); // #: Show actual running state and expose cancellation.
            const job = await api('/api/run', {action:'openmagnetics', project:S.p, core_request:request}); // #: Submit the real optional component/core-CAD worker.
            S.job = job.job_id; // #: Tie polling to this exact job identity.
            while (S.busy) { // #: Wait only while this particular operation remains active.
                await new Promise(resolve => setTimeout(resolve, 450)); // #: Poll asynchronously without blocking browser interaction.
                const status = await api('/api/status'); // #: Read the actual server job state.
                if (status.id !== job.job_id) throw Error('The active native job changed'); // #: Reject another tab's unrelated result.
                S.logs = status.log || []; renderBottom(); // #: Show actual native diagnostics in the standard log pane.
                if (status.status === 'running') continue; // #: Do not read partial native output.
                if (status.status === 'cancelled') {setBusy(false); return toast('Core calculation cancelled');} // #: Preserve a real cancellation result.
                if (status.status === 'error') throw Error(status.error); // #: Report actual worker errors without substituted estimates.
                const envelope = await api('/api/result'); // #: Retrieve the completed checked native result.
                if (envelope.job_id !== job.job_id || envelope.result.kind !== 'openmagnetics_core_screening') throw Error('Unexpected component result'); // #: Keep component and FEM result contracts separate.
                nativeCoreResult = envelope.result; // #: Retain the exact component inputs, CAD and numerical evidence.
                S.p.openmagnetics_request = request; autosave(); // #: Persist the explicit independent screening request with the project.
                setBusy(false); renderLeft(); // #: Restore the standard controls and show the completed component result.
                return; // #: Complete this operation without replacing the current FEM fields or mesh.
            } // #: End asynchronous component polling.
        } catch (error) {setBusy(false); toast(error.message);} // #: Restore usability after an actual input, connection or native failure.
    }; // #: End component job handler.
    $('leftContent').prepend(section); // #: Preserve original control handlers while adding the new backend subtree.
    if (nativeCoreResult) { // #: Render only actual completed component/CAD output.
        const out = section.querySelector('#nativeCoreOutput'); // #: Keep component results inside their clearly labelled section.
        out.innerHTML = '<p>Lm: '+fmt(nativeCoreResult.values.magnetizing_inductance_H*1e6)+' µH · wire DC: '+fmt(nativeCoreResult.values.wire_dc_resistance_ohm_per_m)+' Ω/m</p><p>Core only · '+nativeCoreResult.cad.solid_count+' valid solids · measured centre separation '+fmt(nativeCoreResult.cad.measured_central_face_separation_m === undefined ? nativeCoreResult.cad.expected_central_face_separation_m*1000 : nativeCoreResult.cad.measured_central_face_separation_m*1000)+' mm</p><img alt="Isometric projection of the actual generated core STEP" class="native-core-image"><button id="omSave">Save calculation JSON</button>'; // #: Show model-based metrics and actual core geometry with no field-solve claim.
        if (nativeImageURL) URL.revokeObjectURL(nativeImageURL); // #: Release the previous preview's browser storage.
        nativeImageURL = URL.createObjectURL(new Blob([nativeCoreResult.cad_svg], {type:'image/svg+xml'})); // #: Display a generated CAD projection through the existing image CSP allowance.
        out.querySelector('img').src = nativeImageURL; // #: Use the checked native STEP projection rather than a geometry illustration.
        out.querySelector('#omSave').onclick = () => download(JSON.stringify(nativeCoreResult,null,2), 'openmagnetics_core_result.json'); // #: Preserve exact model and native-calculation provenance.
        for (const [name, encoded] of Object.entries(nativeCoreResult.cad_files || {})) { // #: Offer only the checked fixed-name CAD bytes returned by the worker.
            const button = document.createElement('button'); button.textContent = 'Save '+name; // #: Avoid injecting filenames as HTML.
            button.onclick = () => download(Uint8Array.from(atob(encoded), ch => ch.charCodeAt(0)), name, 'application/octet-stream'); // #: Download actual STEP/STL bytes without an arbitrary server file path.
            out.appendChild(button); // #: Keep neutral CAD exchange inside the separate component section.
        } // #: End checked CAD download actions.
    } // #: End actual component result display.
}; // #: Complete the additive Analysis panel.

renderMetrics = function () { // #: Avoid the old generic converged label on a native pass/budget stop.
    nativeBaseMetrics(); // #: Retain ordinary solver and AC metrics.
    if (!S.result?.native_refinement) return; // #: Change metrics only for actual native field results.
    const r = S.result, s = r.stats, h = r.native_refinement.history.at(-1); // #: Read accepted solve evidence and final stopping criteria.
    $('metrics').innerHTML = '<div><small>'+(s.native_hcurl_order?'PEAK CENTROID-SAMPLED B':'PEAK FLUX DENSITY')+'</small><strong>'+fmt(s.peak_B_T)+' <em>T</em></strong></div><div><small>MAGNETIC ENERGY</small><strong>'+fmt(s.energy_J)+' <em>J</em></strong></div><div><small>NETGEN ELEMENTS</small><strong>'+s.elements.toLocaleString()+'</strong></div><div><small>'+esc(r.native_refinement.stop_reason.toUpperCase())+'</small><strong class="status-text">Indicator '+fmt(h.relative_indicator)+'</strong></div>'; // #: Distinguish heuristic target completion, pass limit and resource stopping.
}; // #: Complete native metric labelling.
renderBottom = function () { // #: Show actual native refinement history in the existing Studies panel.
    if (S.bottom === 'studies' && !S.study && S.result?.native_refinement) { // #: Let a newer current/frequency/convergence study replace an earlier native field's refinement history.
        const r = S.result.native_refinement; // #: Read the saved accepted-pass history.
        $('bottomContent').innerHTML = '<p>Netgen / NGSolve · '+esc(r.stop_reason)+' · operating-point recovery indicator, not a certified error bound.</p>'+table(['Pass','Elements','DOFs','Energy J','Indicator','Energy change'],r.history.map(h=>[h.pass,h.elements,h.dofs,fmt(h.energy_J),fmt(h.relative_indicator),h.energy_change===null?'—':fmt(h.energy_change)])); // #: Expose actual meshes and integral changes rather than only the final residual.
        return; // #: Avoid replacing this history with an unrelated study renderer.
    } // #: End native history branch.
    nativeBaseBottom(); // #: Preserve all existing log, region, matrix and AC study views.
}; // #: Complete the additive result renderer.
api('/api/backends').then(status => {nativePackages=status; if (S.p) renderLeft();}).catch(() => {}); // #: Inspect native availability without disrupting normal startup if optional diagnostics are unavailable.
