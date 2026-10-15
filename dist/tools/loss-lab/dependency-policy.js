// An ignored dependency uses one explicitly selected measured reference slice.
const cache=new WeakMap();
export function dependencySlice(curve,notes=[]){
 const disabled=Object.entries(curve?.dependencyPolicy||{}).filter(([,v])=>v.enabled===false);
 if(!disabled.length)return curve;
 for(const [key,v] of disabled){if(!Number.isFinite(v.reference))throw Error('Choose a numeric reference for ignored dependency '+key);notes.push(`Dependency ${key} ignored by explicit assumption; reference ${v.reference} used`);}
 const signature=JSON.stringify([disabled,curve.iterations.length]);const hit=cache.get(curve);if(hit?.signature===signature)return hit.curve;
 const selected=curve.iterations.filter(it=>disabled.every(([k,v])=>it.deps?.[k]===v.reference));
 if(!selected.length)throw Error('No recorded iteration matches the selected dependency reference combination');
 const result={...curve,temperatureIndependent:disabled.some(([k])=>k==='Tj')?false:curve.temperatureIndependent,voltageScaling:disabled.some(([k])=>k==='Vds')?false:curve.voltageScaling,iterations:selected.map(it=>({...it,deps:Object.fromEntries(Object.entries(it.deps||{}).filter(([k])=>!disabled.some(([d])=>d===k)))}))};
 cache.set(curve,{signature,curve:result});return result;
}
