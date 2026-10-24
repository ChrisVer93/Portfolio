import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
test('the three import dialogs exclude All files where supported',()=>{
 const app=readFileSync(new URL('../../dist/tools/loss-lab/app.js',import.meta.url),'utf8');
 assert.match(app,/showOpenFilePicker\(\{/);
 assert.match(app,/excludeAcceptAllOption:true/);
 assert.match(app,/filteredImportPicker\('#waveFiles','waveform',true\)/);
 assert.match(app,/filteredImportPicker\('#projectFile','project'\)/);
 assert.match(app,/filteredImportPicker\('#componentFile','alternative'\)/);
 assert.match(app,/filteredImportPicker\('#curveFiles','alternative',true\)/);
 assert.match(app,/input\.dispatchEvent\(new Event\('change'/);
 assert.match(app,/assertImportFileType\(file\.name,kind\)/);
 assert.match(app,/typeof window\.showOpenFilePicker!=='function'/);
});
