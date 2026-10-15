import {CURVE_IDS,calibrationValue,si} from './engine.js?v=1.5.1';
export const QUANTITIES={Id:['Drain current','A'],If:['Forward current','A'],Vds:['Drain–source voltage','V'],Vsd:['Source–drain voltage','V'],Vf:['Forward voltage','V'],Rds:['On-state resistance','Ohm'],ESR:['Equivalent series resistance','Ohm'],Rds_normalised:['Normalised on-state resistance','-'],ESR_normalised:['Normalised ESR','-'],Eon:['Turn-on energy','J'],Eoff:['Turn-off energy','J'],Err:['Reverse-recovery energy','J'],Qrr:['Reverse-recovery charge','C'],di_dt:['Current slew rate','A/s'],Tj:['Junction temperature','degC'],T:['Temperature','degC'],Vgs:['Gate–source voltage','V'],Rg:['Gate resistance','Ohm'],f:['Frequency','Hz'],B:['Flux density','T'],Pv:['Core loss density','W/m^3'],Constant:['Constant','-']};
export function dependencies(id){if(id.includes('normalised')&&id.includes('ESR'))return [];if(id.includes('Rds_normalised'))return ['Vgs','Id'];if(/^(Vds_|Id_Vds|Rds_|Id_Rds|Vsd_|Id_Vsd)/.test(id))return ['Tj','Vgs'];if(id.includes('Qrr'))return ['Tj','If'];if(id.includes('Err')||id.includes('Vf'))return ['Tj'];if(id.includes('Eon')||id.includes('Eoff'))return ['Vds','Rg','Tj'];if(id==='Constant_ESR')return [];if(id==='ESR_f_f_T'||id==='f_ESR_f_T')return ['T'];if(id==='ESR_T_f_f'||id==='T_ESR_f_f')return ['f'];if(id==='Pv_B_f_f_T'||id==='B_Pv_f_f_T')return ['f','T'];if(id==='Pv_f_f_B_T'||id==='f_Pv_f_B_T')return ['B','T'];return [];}
export function characteristicName(id){if(id==='Constant_ESR')return 'Constant equivalent series resistance';const axes=CURVE_IDS[id];if(!axes)return id;const [x,y]=axes;let d=dependencies(id);return `${QUANTITIES[y]?.[0]||y} vs ${QUANTITIES[x]?.[0]||x}${d.length?' — at specified '+d.map(k=>QUANTITIES[k][0].toLowerCase()).join(', '):''}`;}
export function allowNegative(id){return /Vsd|Qrr|Err/.test(id);}
export function validateAxes(s){for(const k of ['xmin','xmax','ymin','ymax'])if(!Number.isFinite(s[k]))throw Error('Axis limits must be finite numbers');if(!(s.xmax>s.xmin&&s.ymax>s.ymin))throw Error('Each axis maximum must exceed its minimum');if(s.xscale==='log'&&s.xmin<=0)throw Error('Logarithmic X limits must be positive');if(s.yscale==='log'&&s.ymin<=0)throw Error('Logarithmic Y limits must be positive');return true;}
export function samplePoint(point,cal,s){validateAxes(s);if(cal.length!==3)throw Error('Calibrate three reference points first');let x=calibrationValue(point[0],cal[0][0],cal[1][0],s.xmin,s.xmax,s.xscale),y=calibrationValue(point[1],cal[0][1],cal[2][1],s.ymin,s.ymax,s.yscale),tol=1e-10*Math.max(1,Math.abs(s.xmax),Math.abs(s.ymax));if(x<s.xmin-tol||x>s.xmax+tol||y<s.ymin-tol||y>s.ymax+tol)throw Error('Sample is outside the rectangle defined by the axis limits');if(!allowNegative(s.curveId)&&(x<0||y<0))throw Error('Negative samples are not allowed for this characteristic');if(allowNegative(s.curveId)){x=Math.abs(x);y=Math.abs(y);}const [xn,yn]=CURVE_IDS[s.curveId];if((xn==='ESR_normalised'||yn==='ESR_normalised')&&(!Number.isFinite(s.rbase)||s.rbase<=0))throw Error('Rbase must be positive');return [xn==='ESR_normalised'?x*s.rbase:si(x,s.xunit,xn),yn==='ESR_normalised'?y*s.rbase:si(y,s.yunit,yn)];}

// MATLAB digitiser zero-start policy. Raw samples remain available separately.
export function originSamples(samples,id){
 const forced=['Err_If_f_Tj','If_Err_f_Tj','Eon_Id_f_Vds_Rg_Tj','Id_Eon_f_Vds_Rg_Tj','Eoff_Id_f_Vds_Rg_Tj','Id_Eoff_f_Vds_Rg_Tj'].includes(id);
 let points=samples.filter(p=>p.every(Number.isFinite)).map(p=>forced?p.map(Math.abs):[...p]).sort((a,b)=>a[0]-b[0]);
 let origin=null,policy=forced?'forced-zero':'linear-zero-start';
 if(!points.length)return {points,origin,policy};
 if(points.some((p,j)=>j&&p[0]===points[j-1][0]))throw Error('Duplicate X points: remove a sample or choose a single branch');
 const zero=points.find(p=>Math.abs(p[0])<1e-12);
 if(zero){if(forced){zero[0]=0;zero[1]=0;}else zero[1]=Math.max(zero[1],0);}
 else if(forced){origin=[0,0];points.unshift(origin);}
 else if(points[0][0]>0){const [a,b]=points;origin=[0,Math.max(b?a[1]-a[0]*(b[1]-a[1])/(b[0]-a[0]):a[1],0)];points.unshift(origin);}
 else if(points.at(-1)[0]>0){const j=points.findIndex(p=>p[0]>0),a=points[j-1],b=points[j];origin=[0,Math.max(a[1]-a[0]*(b[1]-a[1])/(b[0]-a[0]),0)];points.splice(j,0,origin);}
 points=points.map(([x,y])=>[x,y<0&&Math.abs(y)<1e-12?0:y]);
 return {points,origin,policy};
}
