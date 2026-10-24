import {matlabStateToProject,hydrateProject} from './io.js?v=2.5.5';
import {assertImportFileType} from './import-formats.js?v=2.5.7';
import {checkProject} from './preflight.js?v=2.5.5';
import {runProject} from './engine.js?v=2.5.6';
import {screenProject} from './projection-screen.js?v=2.5.5';
import {runSensitivity} from './sensitivity.js?v=2.5.5';
self.onmessage=async e=>{try{if(e.data.task==='import-project'){self.postMessage({stage:'Parsing project'});assertImportFileType(e.data.name,'project');const raw=JSON.parse(new TextDecoder().decode(e.data.buffer));self.postMessage({stage:'Loading waveforms and component data'});const q=raw.schemaVersion===1?raw:matlabStateToProject(raw);if(!Array.isArray(q.instances)||!Array.isArray(q.waveforms)||!q.operating)throw Error('Invalid project schema');const project=hydrateProject(q);self.postMessage({stage:'Checking inputs'});const checks=checkProject(project);self.postMessage({project,checks});}else if(e.data.task==='screen'){self.postMessage({screen:screenProject(e.data.project,p=>self.postMessage({progress:p}))});}else if(e.data.task==='sensitivity'){const sensitivity=runSensitivity(e.data.project,e.data.config,p=>self.postMessage({progress:p}));self.postMessage({sensitivity});}else{const result=runProject(e.data,p=>self.postMessage({progress:p}));self.postMessage({result});}}catch(err){self.postMessage({error:err.message});}};
