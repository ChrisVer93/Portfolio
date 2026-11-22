'use strict'; // #: Execute the original Python reference engine in a dedicated WebAssembly worker.
importScripts('https://cdn.jsdelivr.net/pyodide/v0.27.7/full/pyodide.js'); // #: Pin the Python/WebAssembly runtime rather than use a floating development build.
const ready=(async()=>{ // #: Load exact trusted source/data once for this worker lifetime.
    const py=await loadPyodide(),bundle=await (await fetch('magnetics-core.json')).json(); // #: Initialise actual Python and retrieve the source-bound published engine packet.
    for(const [name,text] of Object.entries(bundle.files)){const path='/studio/'+name;py.FS.mkdirTree(path.slice(0,path.lastIndexOf('/')));py.FS.writeFile(path,text);} // #: Preserve original relative module/data/example paths inside the virtual filesystem.
    py.runPython("import sys,os\nsys.path.insert(0,'/studio')\nos.environ['MAGNETICS_PURE_PYTHON']='1'\nfrom engine import browser_bridge as bridge\nimport json"); // #: Explicitly select unchanged standard-library reference kernels without pretending native packages exist.
    return py; // #: Reuse the real loaded engine for metadata and accepted solves.
})(); // #: Start source initialisation before the first interface request arrives.
self.onmessage=async event=>{ // #: Accept only bounded adapter operations, never caller-supplied Python code.
    const {id,operation,payload}=event.data; // #: Retain exact request/response identity across asynchronous worker messages.
    try{const py=await ready;py.globals.set('_browser_payload',JSON.stringify(payload));py.globals.set('_browser_operation',operation); // #: Transport finite caller data through JSON rather than executable string interpolation.
        const text=py.runPython("_p=json.loads(_browser_payload)\nif _browser_operation=='rpc':\n _r=bridge.rpc(_p['path'],_p.get('data'))\nelif _browser_operation=='preflight':\n _r=bridge.preflight(_p)\nelif _browser_operation=='run':\n _r=bridge.run(_p,lambda message:None)\nelif _browser_operation=='export':\n _r=bridge.export(_p['result'],_p['kind'])\nelse:\n raise ValueError('Unknown browser worker operation')\njson.dumps(_r,allow_nan=False)"); // #: Run only the exact original adapter and require complete finite JSON output.
        self.postMessage({id,value:JSON.parse(text)}); // #: Publish one completed actual response with its original identity.
    }catch(error){self.postMessage({id,error:error.message});} // #: Preserve real initialization/physical/numerical failures rather than invent a result.
}; // #: Keep long numerical work isolated from the original DOM and cancellation controls.
