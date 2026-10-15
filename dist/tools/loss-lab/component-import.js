import {makeInstance,makeCandidate,canonicalCurve,uid} from './io.js';
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
  c.curves=item.curves.map(value=>{const cr=canonicalCurve(structuredClone(value));if(!characteristicIds(type).includes(cr.sourceId))throw Error('Characteristic does not match '+type+': '+cr.sourceId);if(cr.constant===undefined&&(!cr.iterations?.length||cr.iterations.some(it=>!Array.isArray(it.x)||!Array.isArray(it.y)||it.x.length<2||it.x.length!==it.y.length||![...it.x,...it.y,...Object.values(it.deps||{})].every(Number.isFinite))))throw Error('Invalid curve iteration');if(cr.constant!==undefined&&(!Number.isFinite(cr.constant)||cr.constant<0))throw Error('Invalid constant resistance');const id=uid('curve');ids.set(value.id,id);return {...cr,id};});
  c.lossModels=Object.fromEntries(Object.entries(c.lossModels||{}).map(([k,v])=>{if(v==='none')return [k,v];if(!ids.has(v))throw Error('Active curve selection does not exist: '+k);return [k,ids.get(v)];}));return c;
 });return instance;
}
