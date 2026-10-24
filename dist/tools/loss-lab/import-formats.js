/** Import format policy. The picker is only a UI hint; validate every file path. */
export const IMPORT_FORMATS=Object.freeze({
 waveform: Object.freeze(['csv','txt']),
 project: Object.freeze(['json']),
 alternative: Object.freeze(['json'])
});
export function assertImportFileType(filename,kind){
 const allowed=IMPORT_FORMATS[kind];
 if(!allowed)throw Error('Unknown import category: '+kind);
 const extension=String(filename||'').match(/\.([A-Za-z0-9]+)$/)?.[1]?.toLowerCase();
 if(!allowed.includes(extension))throw Error((kind==='waveform'?'Waveform':kind==='project'?'Project':'Alternative/characteristic')+' import accepts only '+allowed.map(e=>'.'+e).join(' or ')+' files.');
 return true;
}
