'use strict'; // #: Extend study presentation without changing existing field solvers or project editing.
const inductanceBaseBottom=renderBottom; // #: Preserve native/adaptive/AC/log/matrix renderers for unrelated views.
let inductancePortChoice=null; // #: Retain the selected AC measurement port while navigating its result.
renderBottom=function () { // #: Give the latest sweep precedence over a retained earlier native field's refinement history.
    const study=S.study; // #: Read the same accepted result object used by Save study JSON.
    if (S.bottom!=='studies' || !['sweep','ac_sweep'].includes(study?.kind)) return inductanceBaseBottom(); // #: Delegate every unrelated field, study and tab unchanged.
    document.querySelectorAll('[data-bottom]').forEach(b=>b.classList.toggle('active',b.dataset.bottom===S.bottom)); // #: Keep the visible Studies tab highlighted after native or reference studies.
    const el=$('bottomContent'), chart=MagneticsStudyCharts.chart; // #: Use the existing result area and the independently verified SVG renderer.
    if (study.kind==='sweep') { // #: Plot the defined current-dependent measurement rather than only magnetic energy.
        if (!study.inductance_intervals) return inductanceBaseBottom(); // #: Preserve compatibility with previously saved older sweep records.
        el.innerHTML='<p><strong>'+esc(study.selected_winding_name||study.winding_id)+' · current-dependent inductance</strong></p><p class="hint">'+esc(study.solver_scope)+'</p>'; // #: Identify the measured electrical winding and the actual reference-solver study backend.
        el.innerHTML+=table(['Current · A','Flux linkage · Wb turn','Chord L · µH','Energy · J','Peak |B| · T'],study.rows.map(r=>[fmt(r.current_A),fmt(r.selected_linkage_Wb_turn),r.chord_inductance_H===null?'—':fmt(r.chord_inductance_H*1e6),fmt(r.energy_J),fmt(r.peak_B_T)])); // #: Display actual linkage and inductance while preserving the earlier energy and peak-field outputs.
        el.innerHTML+=chart([{name:'Chord: [λ(I) − λ(0)] / I',points:study.rows.map(r=>[r.current_A,r.chord_inductance_H===null?null:r.chord_inductance_H*1e6])},{name:'Finite-interval slope: Δλ / ΔI at midpoint',points:study.inductance_intervals.map(r=>[r.current_mid_A,r.slope_inductance_H*1e6])}],'Current · A','Inductance · µH'); // #: Distinguish a chord curve from finite-interval slopes without claiming a computed small-signal tangent.
        el.innerHTML+='<p class="hint">'+esc(study.inductance_note)+'</p>'; // #: Keep fixed-bias, zero-current, mesh and nonlinear interpretation limits visible.
        el.innerHTML+=chart([{name:'Solved series-port flux linkage',points:study.rows.map(r=>[r.current_A,r.selected_linkage_Wb_turn*1e3])}],'Current · A','Flux linkage · mWb turn'); // #: Let the user inspect the actual nonlinear flux/current characteristic behind the inductance curves.
        el.innerHTML+=chart([{name:'Solved physical magnetic energy',points:study.rows.map(r=>[r.current_A,r.energy_J])}],'Current · A','Energy · J'); // #: Preserve the useful original energy-versus-current chart.
        return; // #: Do not let an earlier native field result overwrite the accepted sweep.
    } // #: End magnetostatic current-study presentation.
    inductanceBaseBottom(); // #: Retain the original actual AC loss, mean-energy and power-balance study table.
    const ports=study.rows[0]?.ports||[]; // #: Derive selectable measurement identities from actual accepted AC port data.
    if (!ports.length) return; // #: A model without electrical ports cannot define a port inductance curve.
    const chosen=ports.find(p=>p.id===inductancePortChoice)||ports.find(p=>p.impedance_ohm!==null)||ports[0]; // #: Prefer a driven port when first showing the study while preserving later user selection.
    inductancePortChoice=chosen.id; // #: Keep the exact independent source identity through re-rendering.
    el.innerHTML+=input('AC port for equivalent inductance',chosen.id,'inductanceAcPort',{choices:ports.map(p=>[p.id,p.name])}); // #: Avoid cluttering or combining unrelated winding/conductor port curves.
    const samples=study.rows.map(r=>({frequency:r.frequency_Hz,port:r.ports.find(p=>p.id===chosen.id)})); // #: Match each frequency by port identity rather than by accidental row position.
    const value=(sample,key)=>Number.isFinite(sample.port?.[key])?sample.port[key]:null; // #: Treat undefined zero-current or older measurements as missing, never as zero inductance.
    el.innerHTML+=table(['Frequency · Hz','Series-equivalent Ls · µH','Re(V/I) · Ω'],samples.map(s=>[fmt(s.frequency),value(s,'series_equivalent_inductance_H')===null?'—':fmt(s.port.series_equivalent_inductance_H*1e6),fmt(s.port.series_resistance_ohm)])); // #: Present signed per-port quantities with explicit physical units.
    el.innerHTML+=chart([{name:chosen.name+' · Ls = Im(V/I)/(2πf)',points:samples.map(s=>[s.frequency,value(s,'series_equivalent_inductance_H')===null?null:s.port.series_equivalent_inductance_H*1e6])}],'Frequency · Hz','Series-equivalent Ls · µH',true); // #: Plot actual frequency-dependent reactance-derived inductance using a logarithmic frequency axis.
    el.innerHTML+=chart([{name:chosen.name+' · Re(V/I)',points:samples.map(s=>[s.frequency,value(s,'series_resistance_ohm')])}],'Frequency · Hz','Operating-point resistance · Ω',true); // #: Preserve the distinction between dissipative and reactive port responses.
    el.querySelector('[data-edit="inductanceAcPort"]').onchange=event=>{inductancePortChoice=event.target.value;renderBottom();}; // #: Attach the real port-selector handler after all result HTML is constructed.
}; // #: Complete the additive study interface.
