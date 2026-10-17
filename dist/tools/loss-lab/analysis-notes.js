import {characteristicName,QUANTITIES} from './characteristics.js?v=1.10.0';
import {INTERPOLATION_METHODS} from './curve-methods.js?v=1.10.0';
import {operatingPointLabel} from './result-view.js?v=1.10.0';
const esc=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const curveLabel=c=>c.sourceId?characteristicName(c.sourceId).split(' — ')[0]:`${QUANTITIES[c.yName]?.[0]||c.yName} vs ${QUANTITIES[c.xName]?.[0]||c.xName}`;
export function noteKind(message){
 if(/negative extrapolated.*clamped to zero/i.test(message))return 'Invalid voltage projection replaced with zero';
 if(/duplicate axis value/i.test(message))return 'Duplicate curve points';
 if(/single-point characteristic/i.test(message))return 'Single-point curve used as a constant';
 if(/nearest reference used/i.test(message))return 'Nearest reference used';
 if(/clamped to (?:sampled range|domain)/i.test(message))return 'Value limited to available data';
 if(/fixed at reference/i.test(message))return 'Reference condition differs from operating condition';
 if(/uses fixed reference Vds; enable/i.test(message))return 'Voltage scaling needs review';
 if(/Dependency .*outside/i.test(message))return 'Dependency outside available reference conditions';
 // Ordinary 1D projection is expected. Keep it in the detailed diagnostics/JSON.
 if(/Curve query extrapolated|simplex extrapolation/i.test(message))return null;
 return null;
}
export function collectAnalysisNotes(rows,project){
 const warnings=new Map(),assumptions=new Map(),models=new Map();
 const add=(device,characteristic,kind,detail,row,severity='warning')=>{const key=[device,characteristic,kind].join('|');let entry=warnings.get(key);if(!entry){entry={device,characteristic,kind,severity,details:new Set()};warnings.set(key,entry);}entry.details.add(`${operatingPointLabel(row)}: ${detail}`);};
 for(const row of rows){
  const deviceErrors=new Set((row.devices||[]).filter(d=>!d.valid).map(d=>`${d.instanceName} / ${d.part}: ${d.error}`));
  for(const reason of row.reasons||[])if(!deviceErrors.has(reason))add('Operating point','Output / study', 'Calculation incomplete',reason,row,'error');
  for(const device of row.devices||[]){const name=[device.instanceName,device.part].filter(Boolean).join(' / '),candidate=project?.instances.flatMap(i=>i.candidates).find(c=>c.id===device.candidateId),curves=candidate?.curves||[];
   if(device.valid===false){add(name,'Device model','Calculation failed',device.error,row,'error');continue;}
   const described=new Set();for(const d of device.diagnostics||[]){described.add(`${d.characteristic}: ${d.message}`);const kind=noteKind(d.message);if(!kind)continue;const curve=curves.find(c=>c.id===d.curveId),label=curve?curveLabel(curve):characteristicName(d.characteristic).split(' — ')[0];add(name,label,kind,d.message,row);}
   for(const note of device.notes||[]){if(described.has(note)&&noteKind(note))continue;const kind=noteKind(note);if(kind){const curve=curves.find(c=>note.startsWith((c.sourceId||c.yName+' vs '+c.xName)+':'));add(name,curve?curveLabel(curve):'Device model',kind,note,row);continue;}
    if(/Curve query extrapolated|Iteration .*extrapolated|simplex extrapolation|Forward-family interpolation|Weighted average:/i.test(note))continue;
    let clean=curves.filter(c=>c.sourceId).reduce((text,c)=>text.split(c.sourceId).join(curveLabel(c)),note.replace(/ \[[^\]]+\]$/,''));if(/Sparse dependency family: normalised simplex/.test(note))clean='Incomplete reference grid: linear interpolation between neighbouring reference conditions.';if(/Recovery detected/.test(note))clean='Recovery events inferred from forward diode current ending with blocking voltage; inspect the event trace.';if(/MATLAB inverse interpolation/.test(note))clean='MATLAB inverse lookup sorts curve points without rejecting nonmonotonic branches.';if(/^Active /i.test(note)){models.set(name+'|'+clean,{device:name,text:clean});continue;}
    if(/User-selected zero floor|Capacitor mean-current loss|assumed temperature-independent|Switching energy assumed|ignored by explicit assumption|Reverse gate-on conduction|scaled linearly|voltage scaling explicitly disabled|Recovery detected|Recovery energy approximated|Frequency-dependent resistance|Core estimate|Thermal model:|MATLAB inverse interpolation|Sparse dependency family: normalised simplex/i.test(note)){const stable=/Thermal model:/.test(note)?'Thermal model: '+(candidate?.thermal?.scope==='bank'?'entire-bank':'per-device')+' thermal resistance; converged (iteration counts and residuals retained in full results).':clean;assumptions.set(name+'|'+stable,{device:name,text:stable});}
   }
   if(candidate){for(const curve of curves.filter(c=>(c.originPolicy==='zero'||c.negativeOutputPolicy==='zero'||c.voltageScaling===false||c.temperatureIndependent||Object.values(c.dependencyPolicy||{}).some(v=>v.enabled===false)))){if(!models.size&&!device.notes?.length)continue;const active=(device.queries||[]).some(q=>q.curveId===curve.id)||(device.notes||[]).some(n=>n.includes('['+curve.id+']'));if(!active)continue;const nameCurve=curveLabel(curve);if(curve.originPolicy==='zero')assumptions.set(name+'|origin|'+curve.id,{device:name,text:nameCurve+': zero-current voltage/energy is explicitly set to zero; stored samples are retained.'});if(curve.negativeOutputPolicy==='zero')assumptions.set(name+'|zero|'+curve.id,{device:name,text:nameCurve+': negative physical projections use a user-selected zero floor; loss may be underestimated.'});if(curve.voltageScaling===false&&['Eon','Eoff'].some(k=>[curve.xName,curve.yName].includes(k)))assumptions.set(name+'|voltage|'+curve.id,{device:name,text:nameCurve+': voltage scaling disabled by user.'});}}
  }
 }
 const operating=project?.operating||{};const settings=[`Interpolation: ${INTERPOLATION_METHODS[operating.interpolationMethod||'reference-first']||operating.interpolationMethod}.`,`Out-of-domain policy: ${operating.domainPolicy||'error'}.`];
 if(rows.some(r=>(r.devices||[]).some(d=>(d.trace||[]).some(e=>['on','off'].includes(e.category)))))settings.push('Switching model: Eon and Eoff are zero at zero current; negative event current is treated as zero. Separate no-load / output-capacitance energy is not added.');
 return {warnings:[...warnings.values()].map(w=>({...w,details:[...w.details]})),assumptions:[...assumptions.values()],models:[...models.values()],settings};
}
export function analysisNotesHTML(rows,project){const data=collectAnalysisNotes(rows,project);const warnings=data.warnings.length?data.warnings.map(w=>`<details class="analysis-warning"><summary><b>${esc(w.device)}</b> · ${esc(w.characteristic)} — ${esc(w.kind)}</summary><ul>${w.details.map(d=>`<li class="caption">${esc(d)}</li>`).join('')}</ul></details>`).join(''):'<p>No warnings requiring review.</p>';return `<h3>Warnings requiring review</h3>${warnings}<h3>Assumptions & calculation summary</h3><ul>${data.settings.map(s=>`<li>${esc(s)}</li>`).join('')}${data.assumptions.map(a=>`<li><b>${esc(a.device)}</b>: ${esc(a.text)}</li>`).join('')}</ul><details><summary>Active model details</summary><ul>${data.models.map(a=>`<li><b>${esc(a.device)}</b>: ${esc(a.text)}</li>`).join('')}</ul></details>`;}
