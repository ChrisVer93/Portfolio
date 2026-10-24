import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';

const root=new URL('../../dist/tools/loss-lab/',import.meta.url);
const read=file=>readFileSync(new URL(file,root),'utf8');

test('Open Project directly activates a native file input through an associated label',()=>{
 const html=read('index.html'),css=read('style.css');
 assert.match(html,/<label[^>]*id="openProject"[^>]*for="projectFile"[^>]*>Open project<\/label>/);
 assert.match(html,/<input type="file" id="projectFile" accept="\.json" class="file-input-offscreen">/);
 assert.doesNotMatch(html,/<input hidden type="file" id="projectFile"/);
 assert.match(css,/\.file-input-offscreen\{[^}]*opacity:0/);
 assert.doesNotMatch(css,/\.file-input-offscreen\{[^}]*display:none/);
});
test('all upload actions use native labels rather than JavaScript file-click handlers',()=>{
 const app=read('app.js'),ui=read('loss-model-ui.js');
 assert.match(app,/<label[^>]*id="importWave"[^>]*for="waveFiles"/);
 assert.match(app,/<label[^>]*id="importComponent"[^>]*for="componentFile"/);
 assert.match(app,/<label[^>]*id="importAlternative"[^>]*for="componentFile"/);
 assert.match(ui,/<label[^>]*id="importCurves"[^>]*for="curveFiles"/);
 assert.match(app,/<label class="dropzone" id="waveDrop" for="waveFiles"/);
 assert.doesNotMatch(app,/function openImportPicker|\$\('#openProject'\)\.onclick/);
 assert.doesNotMatch(app,/showOpenFilePicker|new DataTransfer\(\)|dispatchEvent\(new Event\('change'/);
 assert.match(app,/document\.querySelectorAll\('\[data-file-trigger\]'\)\.forEach/);
});
test('pickers filter allowed types and all handlers reject disallowed extensions',()=>{
 const html=read('index.html'),app=read('app.js'),worker=read('worker.js');
 for(const [id,accept] of [['waveFiles','.csv,.txt'],['projectFile','.json'],['componentFile','.json'],['curveFiles','.json']]){
  assert.ok(html.includes('id="'+id+'" '+(id==='waveFiles'||id==='curveFiles'?'multiple ':'')+'accept="'+accept+'"'),id);
 }
 assert.match(app,/assertImportFileType\(file\.name,'waveform'\)/);
 assert.match(app,/assertImportFileType\(file\.name,'project'\)/);
 assert.match(app,/assertImportFileType\(file\.name,'alternative'\)/);
 assert.match(worker,/assertImportFileType\(e\.data\.name,'project'\)/);
 assert.match(app,/el\.ondrop=e=>\{e\.preventDefault\(\);importWaves\(\[\.\.\.e\.dataTransfer\.files\]\)/);
});
