import {runProject} from './engine.js';
import {runSensitivity} from './sensitivity.js';
self.onmessage=e=>{try{if(e.data.task==='sensitivity'){const sensitivity=runSensitivity(e.data.project,e.data.config,p=>self.postMessage({progress:p}));self.postMessage({sensitivity});}else{const result=runProject(e.data,p=>self.postMessage({progress:p}));self.postMessage({result});}}catch(err){self.postMessage({error:err.message});}};
