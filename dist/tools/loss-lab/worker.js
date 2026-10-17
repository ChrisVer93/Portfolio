import {runProject} from './engine.js?v=1.8.1';
import {screenProject} from './projection-screen.js?v=1.8.1';
import {runSensitivity} from './sensitivity.js?v=1.8.1';
self.onmessage=e=>{try{if(e.data.task==='screen'){self.postMessage({screen:screenProject(e.data.project,p=>self.postMessage({progress:p}))});}else if(e.data.task==='sensitivity'){const sensitivity=runSensitivity(e.data.project,e.data.config,p=>self.postMessage({progress:p}));self.postMessage({sensitivity});}else{const result=runProject(e.data,p=>self.postMessage({progress:p}));self.postMessage({result});}}catch(err){self.postMessage({error:err.message});}};
