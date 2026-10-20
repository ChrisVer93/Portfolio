import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {HELP_ARTICLES,topicForField,articleHTML,helpPanelHTML} from '../../dist/tools/loss-lab/help-content.js';
import {demoProject} from '../../dist/tools/loss-lab/io.js';
import {queryCurve} from '../../dist/tools/loss-lab/engine.js';

const settings=['cand.series','cand.parallel','cand.totalCount','inst.currentPolarity','cand.gateType','cand.vgsOn','cand.vgsOff','cand.rgOn','cand.rgOff'];
const thermal=['cand.thermal.mode','cand.thermal.temperature','cand.thermal.Rth','cand.thermal.scope','cand.thermal.maxTemperature'];
test('each requested component and thermal field has distinct text-only guidance in the offline manual',()=>{
 const topics=new Set(),manual=readFileSync(new URL('../../dist/tools/loss-lab/manual.html',import.meta.url),'utf8');
 for(const path of [...settings,...thermal,'cand.gateOn','cand.gateOff']){const topic=topicForField(path),a=HELP_ARTICLES.find(a=>a.id===topic);assert.ok(topic.startsWith('component-'),path);topics.add(topic);assert.ok(!/<svg|<img/.test(articleHTML(a)));assert.ok(manual.includes(articleHTML(a)),path);}
 assert.equal(topics.size,settings.length+thermal.length+2);
});
test('quick field help omits illustrations while full documentation retains its existing figures',()=>{
 const a=HELP_ARTICLES.find(a=>a.id==='counts');assert.ok(articleHTML(a).includes('<svg'));assert.ok(!articleHTML(a,{quick:true}).includes('<svg'));
 const p=demoProject(),panel=helpPanelHTML({open:true,view:'manual',topic:'counts',quick:true},p,{issues:[],errors:[]},null);assert.ok(!/<svg|<img/.test(panel));assert.ok(panel.includes('Series and parallel'));
});
test('interpolation worked examples match the implemented engine',()=>{
 const family={xName:'Vds',yName:'Id',iterations:[{x:[0,4],y:[0,4],deps:{Vgs:10}},{x:[0,4],y:[0,16],deps:{Vgs:20}}]};
 assert.equal(queryCurve(family,1,'Id','Vds',{Vgs:15},'error',[],'reference-first'),.625);assert.equal(queryCurve(family,1,'Id','Vds',{Vgs:15},'error',[],'forward-first'),.4);
 const r={xName:'Id',yName:'Rds',iterations:[{x:[0,10],y:[.002,.002],deps:{Vgs:10}},{x:[0,10],y:[.012,.012],deps:{Vgs:20}}]};
 assert.ok(Math.abs(queryCurve(r,5,'Id','Rds',{Vgs:12.5},'error',[],'inverse-distance')-.003)<1e-12);
 assert.ok(Math.abs(queryCurve(r,5,'Id','Rds',{Vgs:12.5},'error',[],'reference-first')-.0045)<1e-12);
});
test('actual application places helpers beside labels and opens every requested field article',async()=>{
 const p=demoProject(),saved=JSON.stringify(p),keys=['document','window','location','localStorage','Worker'],original=Object.fromEntries(keys.map(k=>[k,globalThis[k]])),nodes=new Map();let elements=[],navigate,writes=0;
 const node=id=>{if(!nodes.has(id)){const n={value:'',textContent:'',hidden:false,disabled:false,classList:{toggle(){},add(){},remove(){}},focus(){},remove(){},querySelectorAll(){return [];},_html:''};Object.defineProperty(n,'innerHTML',{get(){return n._html;},set(html){n._html=html;if(id==='#page')elements=[...html.matchAll(/<button\b([^>]*)>/g)].map(m=>{const dataset=Object.fromEntries([...m[1].matchAll(/data-([\w-]+)="([^"]*)"/g)].map(a=>[a[1].replace(/-([a-z])/g,(_,x)=>x.toUpperCase()),a[2]]));return {dataset,focus(){}};});}});nodes.set(id,n);}return nodes.get(id);};
 globalThis.document={querySelector:node,querySelectorAll:s=>s==='[data-help-topic]'?elements.filter(e=>e.dataset.helpTopic):s==='[data-subtab]'?elements.filter(e=>e.dataset.subtab):[],activeElement:null};globalThis.window={addEventListener:(e,f)=>{if(e==='hashchange')navigate=f;}};globalThis.location={hash:'#overview'};globalThis.localStorage={getItem:()=>saved,setItem(){writes++;}};globalThis.Worker=class{postMessage(){}terminate(){}};
 const inspect=path=>{const html=node('#page').innerHTML,id='field-'+path.replace(/[^\w-]/g,'-'),button=elements.find(e=>e.dataset.helpField===path);assert.ok(button,path);assert.ok(html.includes(`<label for="${id}">`),path);assert.ok(html.indexOf(`data-help-field="${path}"`)<html.indexOf(`id="${id}"`),path);button.onclick({preventDefault(){}});assert.ok(node('#page').innerHTML.includes(`id="manual-${topicForField(path)}"`),path);assert.ok(!node('#page').innerHTML.match(/id="helpArticle">[\s\S]*?<svg/),path);node('#helpClose').onclick();};
 try{await import('../../dist/tools/loss-lab/app.js?v6-help-regression');const initialWrites=writes;assert.ok(!node('#page').innerHTML.includes('Use the ? beside each setting'));for(const field of ['op.mode','op.window','op.interpolationMethod','op.domainPolicy','op.fftSize','op.outputPairs.0.v','op.inputPairs.0.i'])inspect(field);
  location.hash='#waveforms';navigate();inspect('op.mode');location.hash='#devices';navigate();for(const field of settings)inspect(field);elements.find(e=>e.dataset.subtab==='thermal').onclick();for(const field of thermal)inspect(field);assert.equal(writes,initialWrites);
 }finally{for(const [k,v] of Object.entries(original)){if(v===undefined)delete globalThis[k];else globalThis[k]=v;}}
});
