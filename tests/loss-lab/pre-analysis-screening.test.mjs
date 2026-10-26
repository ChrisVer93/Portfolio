import test from 'node:test';
import assert from 'node:assert/strict';
import {emptyProject,makeInstance,makeCandidate} from '../../dist/tools/loss-lab/io.js';
import {checkProject} from '../../dist/tools/loss-lab/preflight.js';
import {screenProject} from '../../dist/tools/loss-lab/projection-screen.js';
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
 let navigate,selected=[];
 const node=id=>{
  if(!nodes.has(id))nodes.set(id,{value:'',textContent:'',innerHTML:'',hidden:false,disabled:false,open:false,
   classList:{toggle(){},add(){},remove(){}},remove(){},focus(){},setAttribute(){},
   showModal(){this.open=true;},close(){this.open=false;},querySelectorAll(){return []}});
  return nodes.get(id);
 };
 globalThis.document={querySelector:node,querySelectorAll:q=>q==='[data-screen-zero]:checked'?selected:[],activeElement:null};
 globalThis.window={addEventListener:(event,fn)=>{if(event==='hashchange')navigate=fn;}};
 let currentHash=hash;globalThis.location={get hash(){return currentHash;},set hash(v){currentHash='#'+v.replace(/^#/,'');}};
 globalThis.localStorage={getItem:()=>JSON.stringify(project),setItem(){}};
 globalThis.Worker=class {constructor(){workers.push(this);this.terminated=false;}postMessage(message){this.message=message;}terminate(){this.terminated=true;}};
 globalThis.setTimeout=()=>0;
 try{
  await import('../../dist/tools/loss-lab/app.js?'+tag);
  await body({node,workers,navigate,selectZero:()=>{selected=[{dataset:{screenZero:'0'}}];}});
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
