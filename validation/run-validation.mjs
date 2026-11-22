// Compares Loss Lab results with reference values (measurements, manufacturer tools, hand calculations).
// Usage:  node validation/run-validation.mjs [folder ...]      (default: validation/measurements and validation/examples)
// Each case is a JSON file:
//   { "name": "...", "project": <saved Loss Lab project JSON>, "expected": { "totalLoss_W": 12.5, "tolerancePercent": 3,
//     "source": "calorimetric measurement | vendor calculator | analytic", "combination": 1 } }
// "combination" selects the alternative combination (1-based) and the first operating point is compared.
// Exit code 1 when a case is outside its tolerance, so it can run in CI.
import fs from 'node:fs';import path from 'node:path';import url from 'node:url';
import {runProject} from '../dist/tools/loss-lab/engine.js';import {hydrateProject} from '../dist/tools/loss-lab/io.js';
const here=path.dirname(url.fileURLToPath(import.meta.url));
const folders=process.argv.length>2?process.argv.slice(2):[path.join(here,'measurements'),path.join(here,'examples')];
let failed=0,count=0;const rows=[];
for(const folder of folders){if(!fs.existsSync(folder))continue;for(const file of fs.readdirSync(folder).filter(f=>f.endsWith('.json')&&!/^TEMPLATE/i.test(f)).sort()){
  const spec=JSON.parse(fs.readFileSync(path.join(folder,file),'utf8'));count++;
  try{const result=runProject(hydrateProject(spec.project)),wanted=spec.expected.combination??1,row=result.rows.find(r=>r.combination===wanted)??result.rows[0];
   const got=row.totalLoss,want=spec.expected.totalLoss_W,tol=spec.expected.tolerancePercent??5,err=100*(got-want)/want,ok=Number.isFinite(got)&&Math.abs(err)<=tol;if(!ok)failed++;
   rows.push({case:spec.name??file,source:spec.expected.source??'?',expected_W:want,tool_W:+got.toFixed(4),error_percent:+err.toFixed(2),tolerance_percent:tol,result:ok?'PASS':'FAIL'});}
  catch(e){failed++;rows.push({case:spec.name??file,source:spec.expected?.source??'?',expected_W:spec.expected?.totalLoss_W,tool_W:null,error_percent:null,tolerance_percent:spec.expected?.tolerancePercent??5,result:'ERROR: '+e.message.slice(0,80)});}}}
if(!count){console.log('No validation cases found. Add JSON files to validation/measurements (see validation/README.md).');process.exit(0);}
console.table(rows);if(failed){console.error(failed+' case(s) outside tolerance');process.exit(1);}console.log('All '+count+' case(s) within tolerance.');
