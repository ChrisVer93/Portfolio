// Presentation helpers: retain full precision and source provenance in results.
const number=v=>Number.isFinite(v)?Number(v.toPrecision(7)).toString():'—';
export function operatingPointLabel(r){return `Vin=${number(r.vin)} V · Vout=${number(r.vout)} V · Pout=${number(r.outputPower)} W`;}
export function compareOperatingPoints(a,b){for(const key of ['vin','vout','outputPower','combination']){const x=Number.isFinite(a[key])?a[key]:Infinity,y=Number.isFinite(b[key])?b[key]:Infinity;if(x!==y)return x<y?-1:1;}return 0;}
export function orderedOperatingPoints(rows){return [...rows].sort(compareOperatingPoints);}
export function orderedCombinations(rows){return [...rows].sort((a,b)=>a.combination-b.combination);}
