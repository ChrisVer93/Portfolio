import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {HELP_ARTICLES,topicForField,articleHTML} from '../../dist/tools/loss-lab/help-content.js';
import {demoProject} from '../../dist/tools/loss-lab/io.js';
import {runProject,outputPower,sliceWaveform} from '../../dist/tools/loss-lab/engine.js';

test('every study field resolves to specific guidance also present in the offline manual',()=>{
 const fields=['mode','window','interpolationMethod','domainPolicy','fftSize','balancedOutput','balancedInput'].map(k=>'op.'+k);
 for(const side of ['inputPairs','outputPairs'])for(const index of [0,4])for(const field of ['v','i','polarity'])fields.push(`op.${side}.${index}.${field}`);
 const manual=readFileSync(new URL('../../dist/tools/loss-lab/manual.html',import.meta.url),'utf8');
 for(const path of fields){const topic=topicForField(path),article=HELP_ARTICLES.find(a=>a.id===topic);assert.ok(topic.startsWith('study-'),path);assert.ok(article,path);assert.ok(manual.includes(articleHTML(article)),path);}
 assert.equal(new Set(HELP_ARTICLES.map(a=>a.id)).size,HELP_ARTICLES.length);
});

test('actual overview help buttons open the correct field article without modifying study or results',async()=>{
 const p=demoProject(),saved=JSON.stringify(p),globals=['document','window','location','localStorage','Worker'],original=Object.fromEntries(globals.map(k=>[k,globalThis[k]])),nodes=new Map();let helpButtons=[],storageWrites=0;
 const node=id=>{if(!nodes.has(id)){const n={value:'',textContent:'',hidden:false,disabled:false,classList:{toggle(){},add(){},remove(){}},remove(){},focus(){},querySelectorAll(){return [];},_html:''};Object.defineProperty(n,'innerHTML',{get(){return n._html;},set(html){n._html=html;if(id==='#page')helpButtons=[...html.matchAll(/<button[^>]*data-help-topic="([^"]+)"[^>]*>/g)].map(m=>({dataset:{helpTopic:m[1]},focus(){}}));}});nodes.set(id,n);}return nodes.get(id);};
 globalThis.document={querySelector:node,querySelectorAll:s=>s==='[data-help-topic]'?helpButtons:[],activeElement:null};globalThis.window={addEventListener(){}};globalThis.location={hash:'#overview'};globalThis.localStorage={getItem:()=>saved,setItem(){storageWrites++;}};globalThis.Worker=class{postMessage(){}terminate(){}};
 try{await import('../../dist/tools/loss-lab/app.js?study-help-regression');const initial=node('#page').innerHTML,writesBefore=storageWrites;assert.ok(!initial.includes('How interpolation and domain policies work'));
  const topics=['study-mode','study-window','study-interpolation','study-domain','study-spectrum','study-balanced-output','study-balanced-input','study-output-voltage','study-output-current','study-input-voltage','study-input-current','study-polarity'];
  for(const topic of topics){const button=helpButtons.find(b=>b.dataset.helpTopic===topic);assert.ok(button,topic);button.onclick({preventDefault(){}});const article=HELP_ARTICLES.find(a=>a.id===topic);assert.ok(node('#page').innerHTML.includes(articleHTML(article)),topic);assert.ok(node('#page').innerHTML.includes('Inputs changed')===false);node('#helpClose').onclick();}
  assert.equal(storageWrites,writesBefore);assert.equal(JSON.stringify(p),saved);
 }finally{for(const [k,v] of Object.entries(original)){if(v===undefined)delete globalThis[k];else globalThis[k]=v;}}
});

test('documented mode and three-phase effects agree with numerical engine',()=>{
 const p=demoProject(),dc=runProject(p);p.operating.mode='AC/AC';const ac=runProject(p);
 for(let j=0;j<dc.rows.length;j++){assert.equal(dc.rows[j].totalLoss,ac.rows[j].totalLoss);assert.equal(dc.rows[j].outputPower,ac.rows[j].outputPower);assert.equal(dc.rows[j].efficiency,ac.rows[j].efficiency);}
 const w=sliceWaveform(p.waveforms[0],p.operating),single=outputPower(w,{...p.operating,balancedOutput:false});assert.equal(outputPower(w,{...p.operating,balancedOutput:true}),3*single);
 assert.throws(()=>outputPower(w,{...p.operating,balancedOutput:true,outputPairs:[...p.operating.outputPairs,...p.operating.outputPairs]}),/exactly one phase pair/);
});
