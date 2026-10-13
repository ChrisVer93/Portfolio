import {runProject} from './engine.js';
self.onmessage=e=>{try{let result=runProject(e.data,p=>self.postMessage({progress:p}));self.postMessage({result});}catch(err){self.postMessage({error:err.message});}};
