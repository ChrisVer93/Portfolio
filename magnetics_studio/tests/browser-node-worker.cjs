'use strict'; // #: QA-only Node transport for the exact delivered browser worker and actual pinned WebAssembly Python.
const {parentPort,workerData}=require('worker_threads'),fs=require('fs'),vm=require('vm'),path=require('path'); // #: Provide real thread cancellation and inspect only the generated trusted static packet.
global.self=global;global.importScripts=()=>{global.loadPyodide=require('pyodide').loadPyodide;}; // #: Substitute local loading of the identical pinned Pyodide runtime, not a fake Python interpreter.
global.fetch=async()=>({json:async()=>JSON.parse(fs.readFileSync(path.join(workerData.site,'magnetics-core.json'),'utf8'))}); // #: Supply the exact published source/input packet to the original worker code.
global.postMessage=value=>parentPort.postMessage(value);vm.runInThisContext(fs.readFileSync(path.join(workerData.site,'browser-worker.js'),'utf8'),{filename:'browser-worker.js'}); // #: Execute the genuine shipped worker logic unchanged.
parentPort.on('message',data=>self.onmessage({data})); // #: Keep browser-style request/response identity on real worker threads.
