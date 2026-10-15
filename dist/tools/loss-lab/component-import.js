import {makeInstance,makeCandidate,canonicalCurve,uid} from './io.js';
import {CURVE_IDS} from './engine.js';
import {characteristicIds} from './workflow.js';
export function importComponent(raw,fallbackType){
 if(raw.schemaVersion&&raw.instances)throw Error('This is a project file. Use Open project.');
 const type=raw.componentType||raw.type||fallbackType;
 if(!['MOSFET','Diode','Capacitor','Inductor'].includes(type))throw Error('Select a component type for this legacy candidate JSON.');
 const source=raw.candidate?[raw.candidate]:raw.candidates||[raw];
 if(!Array.isArray(source)||!source.length)throw Error('No candidates found');
 const instance=makeInstance(type);instance.name=raw.name||source[0].part||type;
 instance.candidates=source.map(item=>{
  if(!Array.isArray(item.curves)||!Array.isArray(item.enabled))throw Error('Component JSON requires curves and enabled loss categories');
  const allowed=type==='MOSFET'?['conduction','body','on','off','recovery']:type==='Diode'?['conduction','recovery']:type==='Inductor'?['copper','core']:['copper'];
  if(item.enabled.some(k=>!allowed.includes(k)))throw Error('Loss categories do not match '+type);
  const c={...makeCandidate(type),...structuredClone(item),id:uid('candidate')},ids=new Map();
  c.curves=item.curves.map(value=>{const cr=canonicalCurve(structuredClone(value));cr.sourceId??=characteristicIds(type).find(id=>CURVE_IDS[id][0]===cr.xName&&CURVE_IDS[id][1]===cr.yName);if(!characteristicIds(type).includes(cr.sourceId))throw Error('Characteristic does not match '+type+': '+cr.sourceId);if(cr.constant===undefined&&(!cr.iterations?.length||cr.iterations.some(it=>!Array.isArray(it.x)||!Array.isArray(it.y)||it.x.length<2||it.x.length!==it.y.length||![...it.x,...it.y,...Object.values(it.deps||{})].every(Number.isFinite))))throw Error('Invalid curve iteration');if(cr.constant!==undefined&&(!Number.isFinite(cr.constant)||cr.constant<0))throw Error('Invalid constant resistance');const id=uid('curve');ids.set(value.id,id);return {...cr,id};});
  c.lossModels=Object.fromEntries(Object.entries(c.lossModels||{}).map(([k,v])=>{if(v==='none')return [k,v];if(!ids.has(v))throw Error('Active curve selection does not exist: '+k);return [k,ids.get(v)];}));return c;
 });return instance;
}

// Reuse selected part characteristics without copying installation settings.
export function importAlternative(raw,type,sourceIndex=0,curveIndices=[]){
 const declared=raw.componentType||raw.type;if(declared&&declared!==type)throw Error('Uploaded part type does not match '+type);
 if(raw.schemaVersion&&raw.instances)throw Error('Use an exported alternative JSON, not a project file');
 const source=raw.candidate?[raw.candidate]:raw.candidates||[raw],part=source[sourceIndex];
 if(!part||!Array.isArray(part.curves))throw Error('No alternative characteristics found');
 if(!curveIndices.length)throw Error('Select at least one characteristic');
 if(curveIndices.some(j=>!Number.isInteger(j)||!part.curves[j])||new Set(curveIndices).size!==curveIndices.length)throw Error('Invalid characteristic selection');
 const curves=curveIndices.map(j=>part.curves[j]);
 const validated=importComponent({componentType:type,candidate:{part:part.part,enabled:[],curves,lossModels:{}}}).candidates[0];
 return {part:String(part.part||''),curves:validated.curves};
}
