import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {assertImportFileType, IMPORT_FORMATS} from '../../dist/tools/loss-lab/import-formats.js';
const root=new URL('../../dist/tools/loss-lab/',import.meta.url);
const read=f=>readFileSync(new URL(f,root),'utf8');

test('waveform upload only accepts CSV/TXT, case-insensitively',()=>{
 assert.deepEqual([...IMPORT_FORMATS.waveform],['csv','txt']);
 for(const f of ['trace.csv','trace.TXT','oscilloscope.Txt'])assert.equal(assertImportFileType(f,'waveform'),true);
 for(const f of ['trace.json','trace.mat','trace.xlsx','trace.csv.exe','trace',''])assert.throws(()=>assertImportFileType(f,'waveform'),/Waveform import accepts only/);
});
test('project, alternative and curve upload only accepts JSON',()=>{
 for(const kind of ['project','alternative']){
  assert.equal(assertImportFileType('study.JSON',kind),true);
  for(const f of ['study.mat','curve.csv','curve.txt','curve.json.txt','study'])assert.throws(()=>assertImportFileType(f,kind),/accepts only/);
 }
});
test('UI handlers, drop zone and project worker validate extensions',()=>{
 const app=read('app.js'),worker=read('worker.js'),html=read('index.html');
 assert.match(html,/id="waveFiles" multiple accept="\.csv,\.txt"/);
 assert.match(html,/id="projectFile" accept="\.json"/);
 assert.match(html,/id="curveFiles" multiple accept="\.json"/);
 assert.match(html,/id="componentFile" accept="\.json"/);
 assert.match(app,/async function importWaves\(files\)[\s\S]{0,130}assertImportFileType\(file\.name,'waveform'\)/);
 assert.match(app,/async function readImportJSON\(file\)\{assertImportFileType\(file\.name,'alternative'\)/);
 assert.match(app,/\$\('#projectFile'\)\.onchange=[\s\S]{0,160}assertImportFileType\(file\.name,'project'\)/);
 assert.match(app,/\$\('#componentFile'\)\.onchange=[\s\S]{0,160}assertImportFileType\(file\.name,'alternative'\)/);
 assert.match(worker,/assertImportFileType\(e\.data\.name,'project'\)/);
 assert.match(app,/el\.ondrop=e=>\{e\.preventDefault\(\);importWaves\(\[\.\.\.e\.dataTransfer\.files\]\)/);
 assert.doesNotMatch(app,/async function readJSONorMAT/);
});
