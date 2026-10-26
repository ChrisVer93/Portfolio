import {checkCharacteristic} from './preflight.js?v=2.5.15';
import {QUANTITIES} from './characteristics.js?v=2.5.15';
const sorted=o=>Object.fromEntries(Object.entries(o||{}).sort(([a],[b])=>a.localeCompare(b)));
const n=v=>Number.isFinite(v)?Number(v.toPrecision(8)).toString():'unavailable';
const unit=k=>QUANTITIES[k]?.[1]||k;
// Compare calculation inputs, excluding labels/provenance and explicit enabled defaults.
export function curveFingerprint(c){return JSON.stringify({xName:c.xName,yName:c.yName,constant:c.constant,
 iterations:(c.iterations||[]).map(it=>({x:it.x,y:it.y,deps:sorted(it.deps)})),
 originPolicy:c.originPolicy||'measured',negativeOutputPolicy:c.negativeOutputPolicy||'reject',
 dependencyPolicy:sorted(Object.fromEntries(Object.entries(c.dependencyPolicy||{}).filter(([,v])=>v.enabled===false))),
 temperatureIndependent:!!c.temperatureIndependent,
 voltageScaling:[c.xName,c.yName].some(k=>['Eon','Eoff'].includes(k))?c.voltageScaling!==false:undefined});}
export function characteristicFeedback(curve,{screen=null,instanceId,candidateId,...options}={}){
 const issues=checkCharacteristic(curve,options),projections=[],failedQueries=[];
 const recorded=screen?.curveInputs?.find(v=>v.instanceId===instanceId&&v.candidateId===candidateId&&v.curveId===curve.id);
 const screened=!!recorded&&recorded.fingerprint===curveFingerprint(curve),stale=!!recorded&&!screened;
 if(stale)issues.push({code:'screen-stale',severity:'warning',curveId:curve.id,message:'This characteristic has changed. Recheck interpolated values before analysis; the previous projection markers no longer describe these points.'});
 if(screened){
  const failures=new Map();
  for(const row of screen.result.rows)for(const device of row.devices){
   if(device.instanceId!==instanceId||device.candidateId!==candidateId)continue;
   for(const problem of device.projectionProblems||[])if(problem.curveId===curve.id)projections.push({...problem,operatingPoint:row.waveform,waveformId:row.waveformId});
   for(const q of device.queries||[])if(q.curveId===curve.id&&q.error){
    const key=[q.given,q.wanted,q.error].join(':'),point=row.waveformId;
    let group=failures.get(key);
    if(!group){group={...q,inputRange:[q.input,q.input],dependencyRanges:{},operatingPoints:new Set()};failures.set(key,group);}
    group.inputRange=[Math.min(group.inputRange[0],q.input),Math.max(group.inputRange[1],q.input)];group.operatingPoints.add(point);
    for(const [k,v] of Object.entries(q.deps||{})){const range=group.dependencyRanges[k]||[v,v];group.dependencyRanges[k]=[Math.min(range[0],v),Math.max(range[1],v)];}
   }
  }
  if(projections.length){const worst=projections.reduce((a,b)=>a.minRaw<b.minRaw?a:b),q=worst.query,accepted=projections.every(v=>v.accepted);
   issues.push({code:'projection',severity:accepted?'warning':'error',curveId:curve.id,
    message:`${accepted?'Explicit zero floor applied to':'Negative interpolated value:'} ${n(worst.minRaw)} ${unit(q.wanted)} at ${n(q.input)} ${unit(q.given)}. ${new Set(projections.map(v=>v.waveformId)).size} affected operating point(s). ${accepted?'Raw negative values remain shown on the graph.':'Edit this characteristic or explicitly choose a zero floor, then recheck before analysis.'}`});
  }
  const rangeText=([lo,hi])=>lo===hi?n(lo):n(lo)+' to '+n(hi);
  for(const group of failures.values()){
   const q={...group,operatingPoints:[...group.operatingPoints]};failedQueries.push(q);
   issues.push({code:'query',severity:'error',curveId:curve.id,message:`Interpolation failed at ${rangeText(q.inputRange)} ${unit(q.given)}${Object.keys(q.dependencyRanges).length?' ('+Object.entries(q.dependencyRanges).map(([k,v])=>`${k}=${rangeText(v)}`).join(', ')+')':''}: ${q.error}. ${q.operatingPoints.length} affected operating point(s).`});
  }
 }
 return {issues,projections,failedQueries,screened,stale};
}
