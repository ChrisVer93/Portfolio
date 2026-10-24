import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';

const root=new URL('../../dist/tools/loss-lab/',import.meta.url);
const read=file=>readFileSync(new URL(file,root),'utf8');

test('native file inputs open synchronously from all upload buttons',()=>{
 const app=read('app.js');
 assert.match(app,/function openImportPicker\(selector\)\{[\s\S]*?input\.value='';\s*input\.click\(\)/);
 for(const id of ['waveFiles','projectFile','componentFile','curveFiles']){
  assert.ok(app.includes("openImportPicker('#"+id+"')"),id);
 }
 assert.doesNotMatch(app,/showOpenFilePicker|new DataTransfer\(\)|dispatchEvent\(new Event\('change'/);
});
test('file inputs use restricted accept hints and application enforces types',()=>{
 const html=read('index.html'),app=read('app.js'),worker=read('worker.js');
 for(const [id,hint] of [['waveFiles','.csv,.txt'],['projectFile','.json'],['componentFile','.json'],['curveFiles','.json']]){
  assert.match(html,new RegExp('id="'+id+'"[^>]*accept="'+hint.replaceAll('.','\\.')+'"'));
 }
 assert.match(app,/assertImportFileType\(file\.name,'waveform'\)/);
 assert.match(app,/assertImportFileType\(file\.name,'project'\)/);
 assert.match(app,/assertImportFileType\(file\.name,'alternative'\)/);
 assert.match(worker,/assertImportFileType\(e\.data\.name,'project'\)/);
 assert.match(app,/el\.ondrop=e=>\{e\.preventDefault\(\);importWaves\(\[\.\.\.e\.dataTransfer\.files\]\)/);
});
