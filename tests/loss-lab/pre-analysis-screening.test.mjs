import test from 'node:test';
import assert from 'node:assert/strict';
import {emptyProject,makeInstance,makeCandidate} from '../../dist/tools/loss-lab/io.js';
import {checkProject} from '../../dist/tools/loss-lab/preflight.js';
import {screenProject} from '../../dist/tools/loss-lab/projection-screen.js';

test('Check Inputs screens a negative interpolated value before any full analysis is requested',async()=>{
 const project=emptyProject(),instance=makeInstance('MOSFET'),candidate=makeCandidate('MOSFET');
 instance.name='Example MOSFET';
 instance.mapping={current:'I',voltage:'V',gate:'G'};
 candidate.part='Example characteristic';
 candidate.enabled=['conduction'];
 candidate.thermal={mode:'fixed',temperature:25};
 candidate.vgsOn=15;
 candidate.curves=[{
  id:'negative-example',xName:'Id',yName:'Vds',canonicalSI:true,
  iterations:[{x:[1,2],y:[0,1],deps:{Vgs:15,Tj:25}}]
 }];
 instance.candidates=[candidate];
 project.instances=[instance];
 project.waveforms=[{
  id:'w',name:'Example operating point',time:'t',
  columns:{t:[0,.5,1],I:[.1,.1,.1],V:[10,10,10],G:[1,1,1]}
 }];
 project.operating={...project.operating,window:1,domainPolicy:'extrapolate',outputPairs:[{v:'V',i:'I',polarity:1}]};
 assert.equal(checkProject(project).errors.length,0);
 const screen=screenProject(project);
 assert.equal(screen.issues.length,1);
 assert.ok(Math.abs(screen.issues[0].minRaw+.9)<1e-10);

 const keys=['document','window','location','localStorage','Worker','setTimeout'];
 const original=Object.fromEntries(keys.map(k=>[k,globalThis[k]]));
 const nodes=new Map(),workers=[];
 const node=id=>{
  if(!nodes.has(id)){
   nodes.set(id,{value:'',textContent:'',innerHTML:'',hidden:false,disabled:false,
    classList:{toggle(){},add(){},remove(){}},remove(){},focus(){},setAttribute(){},
    querySelectorAll(){return []}});
  }
  return nodes.get(id);
 };
 globalThis.document={querySelector:node,querySelectorAll:()=>[],activeElement:null};
 globalThis.window={addEventListener(){}};
 globalThis.location={hash:'#checks'};
 globalThis.localStorage={getItem:()=>JSON.stringify(project),setItem(){}};
 globalThis.Worker=class {
  constructor(){workers.push(this);this.terminated=false;}
  postMessage(message){this.message=message;}
  terminate(){this.terminated=true;}
 };
 globalThis.setTimeout=()=>0;
 try{
  await import('../../dist/tools/loss-lab/app.js?pre-analysis-projection-regression');
  assert.equal(workers.length,1,'Check Inputs should schedule a screening worker automatically');
  assert.equal(workers[0].message?.task,'screen');
  assert.match(node('#page').innerHTML,/Interpolation and physical-value screening/);
  assert.doesNotMatch(node('#page').innerHTML,/Negative interpolated value/);
  workers[0].onmessage({data:{screen}});
  assert.match(node('#page').innerHTML,/Negative interpolated value/);
  assert.match(node('#page').innerHTML,/negative-example/);
  assert.match(node('#page').innerHTML,/data-check-projection="0"/);
  assert.match(node('#page').innerHTML,/analysis not started|before running the analysis/i);
  node('#run').onclick();
  assert.equal(workers.length,1,'Run must not bypass a failed pre-analysis screening');
  assert.equal(globalThis.location.hash,'#checks');
 }finally{
  for(const [k,v] of Object.entries(original)){if(v===undefined)delete globalThis[k];else globalThis[k]=v;}
 }
});
