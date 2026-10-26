import test from 'node:test';
import assert from 'node:assert/strict';
import {emptyProject,makeInstance,makeCandidate} from '../../dist/tools/loss-lab/io.js';
import {checkProject} from '../../dist/tools/loss-lab/preflight.js';
import {screenProject} from '../../dist/tools/loss-lab/projection-screen.js';
import {characteristicFeedback,curveFingerprint} from '../../dist/tools/loss-lab/curve-feedback.js';
import {readinessBanner} from '../../dist/tools/loss-lab/preflight-ui.js';

function fixture(){
 const project=emptyProject(),instance=makeInstance('MOSFET'),candidate=makeCandidate('MOSFET');
 instance.name='Example MOSFET';instance.mapping={current:'I',voltage:'V',gate:'G'};
 candidate.part='Example characteristic';candidate.enabled=['conduction'];
 candidate.thermal={mode:'fixed',temperature:25};candidate.vgsOn=15;
 candidate.curves=[{id:'negative-example',xName:'Id',yName:'Vds',canonicalSI:true,
  iterations:[{x:[1,2],y:[0,1],deps:{Vgs:15,Tj:25}}]}];
 instance.candidates=[candidate];project.instances=[instance];
 project.waveforms=[{id:'w',name:'Example operating point',time:'t',
  columns:{t:[0,.5,1],I:[.1,.1,.1],V:[10,10,10],G:[1,1,1]}}];
 project.operating={...project.operating,window:1,domainPolicy:'extrapolate',outputPairs:[{v:'V',i:'I',polarity:1}]};
 return project;
}
async function withApp(project,tag,body,hash='#overview'){
 const keys=['document','window','location','localStorage','Worker','setTimeout'];
 const original=Object.fromEntries(keys.map(k=>[k,globalThis[k]])),nodes=new Map(),workers=[];
 let navigate,selected=[];const subtabs=['settings','curves','thermal'].map(subtab=>({dataset:{subtab}}));
 const node=id=>{
  if(!nodes.has(id))nodes.set(id,{value:'',textContent:'',innerHTML:'',hidden:false,disabled:false,open:false,
   classList:{toggle(){},add(){},remove(){}},remove(){},focus(){},setAttribute(){},
   showModal(){this.open=true;},close(){this.open=false;},querySelectorAll(){return []}});
  return nodes.get(id);
 };
 globalThis.document={querySelector:node,querySelectorAll:q=>q==='[data-screen-zero]:checked'?selected:q==='[data-subtab]'?subtabs:[],activeElement:null};
 globalThis.window={addEventListener:(event,fn)=>{if(event==='hashchange')navigate=fn;}};
 let currentHash=hash;globalThis.location={get hash(){return currentHash;},set hash(v){currentHash='#'+v.replace(/^#/,'');}};
 globalThis.localStorage={getItem:()=>JSON.stringify(project),setItem(){}};
 globalThis.Worker=class {constructor(){workers.push(this);this.terminated=false;}postMessage(message){this.message=message;}terminate(){this.terminated=true;}};
 globalThis.setTimeout=()=>0;
 try{
  await import('../../dist/tools/loss-lab/app.js?'+tag);
  await body({node,workers,navigate,subtabs,selectZero:()=>{selected=[{dataset:{screenZero:'0'}}];}});
 }finally{for(const [k,v] of Object.entries(original)){if(v===undefined)delete globalThis[k];else globalThis[k]=v;}}
}

test('Check Inputs screens actual negative values and keeps review, consent and debug reachable',async()=>{
 const project=fixture(),screen=screenProject(project);
 assert.equal(checkProject(project).errors.length,0);assert.equal(screen.issues.length,1);
 assert.ok(Math.abs(screen.issues[0].minRaw+.9)<1e-10);
 await withApp(project,'checks-review',({node,workers,selectZero})=>{
  assert.equal(workers.length,1);assert.equal(workers[0].message.task,'screen');
  workers[0].onmessage({data:{screen}});
  assert.match(node('#page').innerHTML,/Negative interpolated value/);
  assert.match(node('#page').innerHTML,/negative-example/);
  assert.match(node('#page').innerHTML,/id="reviewProjections"/);
  node('#reviewProjections').onclick();
  assert.equal(workers.length,1,'opening cached review must not repeat screening');
  assert.equal(node('#modal').open,true);
  assert.match(node('#modalContent').innerHTML,/Apply a zero floor/);
  assert.match(node('#modalContent').innerHTML,/id="screenDebug"/);
  assert.equal(screen.result.rows[0].valid,true,'debug presentation must not mutate screening evidence');
  selectZero();node('#screenAccept').onclick();
  assert.equal(workers.length,2);assert.equal(workers[1].message.task,'screen');
  assert.equal(workers[1].message.project.instances[0].candidates[0].curves[0].negativeOutputPolicy,'zero');
  const accepted=screenProject(workers[1].message.project);assert.equal(accepted.issues.length,0);
  workers[1].onmessage({data:{screen:accepted}});
  assert.equal(workers.length,2,'saving a correction rechecks without starting analysis');
  node('#run').onclick();node('#confirmStudyRun').onclick();
  assert.equal(workers.length,3);assert.equal(workers[2].message.task,undefined);
  assert.equal(workers[2].message.operating.projectionScreen,false);
 },'#checks');
});

test('Run restores immediate prechecks before summary and cannot bypass negative projections',async()=>{
 const project=fixture();
 await withApp(project,'run-negative',({node,workers})=>{
  assert.match(node('#page').innerHTML,/Interpolation checks pending/);
  node('#run').onclick({type:'click'});
  assert.equal(workers.length,1);assert.equal(workers[0].message.task,'screen');
  assert.equal(node('#modal').open,false,'no confirmation hides the initial precheck');
  workers[0].onmessage({data:{screen:screenProject(project)}});
  assert.equal(location.hash,'#checks');assert.equal(node('#modal').open,true);
  assert.match(node('#modalContent').innerHTML,/Review characteristic projections/);
  assert.match(node('#page').innerHTML,/characteristic issue needs review/);
  node('#modal').close();node('#run').onclick();
  assert.equal(workers.length,1);assert.equal(node('#modal').open,true);
 });
});

test('passing screening offers analysis confirmation and input edits invalidate the cached check',async()=>{
 const project=fixture();project.instances[0].candidates[0].curves[0].iterations[0].y=[1,2];
 await withApp(project,'run-pass',({node,workers})=>{
  node('#run').onclick();workers[0].onmessage({data:{screen:screenProject(project)}});
  assert.equal(workers.length,1,'full analysis waits for study confirmation');
  assert.match(node('#page').innerHTML,/Input and interpolation checks passed/);
  assert.match(node('#modalContent').innerHTML,/Confirm & run analysis/);
  node('#confirmStudyRun').onclick();
  assert.equal(workers.length,2);assert.equal(workers[1].message.operating.projectionScreen,false);
  node('#cancelRun').onclick();node('#projectName').onchange({target:{value:'Edited study'}});
  assert.match(node('#page').innerHTML,/Interpolation checks pending/);
  node('#run').onclick();assert.equal(workers.length,3);assert.equal(workers[2].message.task,'screen');
 });
});

test('screening errors remain visible and a new Run retries screening before analysis',async()=>{
 await withApp(fixture(),'screen-retry',({node,workers})=>{
  node('#run').onclick();workers[0].onmessage({data:{error:'Example worker failure'}});
  assert.match(node('#page').innerHTML,/Characteristic screening could not finish/);
  assert.match(node('#status').textContent,/analysis not started/);
  node('#run').onclick();assert.equal(workers.length,2);assert.equal(workers[1].message.task,'screen');
 });
});

test('duplicate stored axes block the actual Run path before any screening or analysis worker',async()=>{
 const project=fixture();project.instances[0].candidates[0].curves[0].iterations[0]={x:[1,1,2],y:[0,.5,1],deps:{Vgs:15,Tj:25}};
 await withApp(project,'run-duplicate',({node,workers})=>{
  node('#run').onclick();assert.equal(workers.length,0);assert.equal(location.hash,'#checks');
  assert.match(node('#page').innerHTML,/repeated on rows 1, 2/);
  assert.match(node('#page').innerHTML,/data-fix-issue/);
 });
});

test('readiness never labels unscreened or failed interpolation as ready for analysis',()=>{
 const report=checkProject(fixture());
 assert.match(readinessBanner(report),/Interpolation checks pending/);
 assert.match(readinessBanner(report,{screen:{issues:[],failures:[{}]}}),/characteristic issue needs review/);
 assert.doesNotMatch(readinessBanner(report,{error:'failed'}),/Ready for analysis/);
 assert.match(readinessBanner(report,{screen:{issues:[],failures:[]}}),/Input and interpolation checks passed/);
});


test('screened errors mark the selected characteristic Needs review and overlay its original graph',async()=>{
 const project=fixture();
 await withApp(project,'inline-characteristic',({node,workers,navigate,subtabs})=>{
  workers[0].onmessage({data:{screen:screenProject(project)}});
  location.hash='#devices';navigate();subtabs.find(v=>v.dataset.subtab==='curves').onclick();
  const html=node('#page').innerHTML;
  assert.match(html,/loss-model-status review">Needs review/);
  assert.doesNotMatch(html,/loss-model-status ready">Ready/);
  const inline=html.split('data-characteristic-feedback="negative-example"')[1].split('</section>')[0];
  assert.match(inline,/Negative interpolated value: -0.9 V at 0.1 A/);
  assert.match(inline,/Negative interpolated values/);
  assert.match(inline,/Evaluated family/);
  assert.match(inline,/#ff6565/);
  assert.equal((inline.match(/<svg /g)||[]).length,1,'bad projections must be on the characteristic graph, not a separate error-only plot');
  assert.doesNotMatch(inline,/Curve points pass|checks passed|values passed/);
 },'#checks');
});

test('curve feedback retains exact recorded raw values and respects component/alternative identity',()=>{
 const p=fixture(),i=p.instances[0],c=i.candidates[0],curve=c.curves[0],screen=screenProject(p),before=JSON.stringify(screen);
 const feedback=characteristicFeedback(curve,{screen,instanceId:i.id,candidateId:c.id,policy:'extrapolate'});
 assert.equal(feedback.screened,true);assert.equal(feedback.projections[0].minRaw,-.9);
 assert.equal(feedback.issues.find(v=>v.code==='projection').severity,'error');
 for(const scope of [{instanceId:'other',candidateId:c.id},{instanceId:i.id,candidateId:'other'}]){
  const unrelated=characteristicFeedback(curve,{screen,...scope,policy:'extrapolate'});
  assert.equal(unrelated.screened,false);assert.equal(unrelated.projections.length,0);
 }
 assert.equal(JSON.stringify(screen),before);
});

test('editing a characteristic removes obsolete error markers and requires a new interpolation check',()=>{
 const p=fixture(),i=p.instances[0],c=i.candidates[0],curve=c.curves[0],screen=screenProject(p),draft=structuredClone(curve);
 draft.iterations[0].y=[1,2];
 const feedback=characteristicFeedback(draft,{screen,instanceId:i.id,candidateId:c.id,policy:'extrapolate'});
 assert.equal(feedback.stale,true);assert.equal(feedback.screened,false);assert.equal(feedback.projections.length,0);
 assert.ok(feedback.issues.some(v=>v.code==='screen-stale'));
 assert.ok(!feedback.issues.some(v=>v.code==='projection'));
 const equivalent={...curve,originPolicy:'measured',negativeOutputPolicy:'reject',dependencyPolicy:{Tj:{enabled:true,reference:25}}};
 assert.equal(curveFingerprint(equivalent),curveFingerprint(curve),'editor defaults must not invalidate unchanged calculation data');
});

test('a rejected out-of-domain query is shown on its characteristic with its actual input',()=>{
 const p=fixture();p.operating.domainPolicy='error';const i=p.instances[0],c=i.candidates[0];
 const feedback=characteristicFeedback(c.curves[0],{screen:screenProject(p),instanceId:i.id,candidateId:c.id});
 assert.equal(feedback.screened,true);assert.equal(feedback.projections.length,0);
 assert.ok(feedback.issues.some(v=>v.code==='query'&&v.severity==='error'&&v.message.includes('0.1 A')));
 assert.equal(feedback.failedQueries[0].output,null,'failed queries must not invent a plotted output');
});

test('accepted zero floors keep raw negative graph evidence and a visible assumption',()=>{
 const p=fixture(),i=p.instances[0],c=i.candidates[0],curve=c.curves[0];curve.negativeOutputPolicy='zero';
 const feedback=characteristicFeedback(curve,{screen:screenProject(p),instanceId:i.id,candidateId:c.id,policy:'extrapolate'});
 assert.equal(feedback.projections[0].minRaw,-.9);assert.equal(feedback.projections[0].query.output,0);
 assert.equal(feedback.issues.find(v=>v.code==='projection').severity,'warning');
 assert.match(feedback.issues.find(v=>v.code==='projection').message,/Explicit zero floor/);
});


test('repeated interpolation failures are grouped on the characteristic with the input range',()=>{
 const p=fixture(),i=p.instances[0],c=i.candidates[0];p.operating.domainPolicy='error';
 const screen=screenProject(p),device=screen.result.rows[0].devices[0],first=device.queries[0];
 device.queries=[first,{...first,input:.2},{...first,input:.3}];
 const feedback=characteristicFeedback(c.curves[0],{screen,instanceId:i.id,candidateId:c.id});
 assert.equal(feedback.failedQueries.length,1);assert.equal(feedback.issues.filter(v=>v.code==='query').length,1);
 assert.deepEqual(feedback.failedQueries[0].inputRange,[.1,.3]);
 assert.match(feedback.issues.find(v=>v.code==='query').message,/0.1 to 0.3 A/);
});
