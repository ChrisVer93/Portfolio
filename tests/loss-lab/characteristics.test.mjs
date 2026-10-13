import test from 'node:test';import assert from 'node:assert/strict';
import {dependencies,characteristicName,samplePoint,validateAxes} from '../../dist/tools/loss-lab/characteristics.js';
const s={curveId:'Rds_Id_f_Vgs_Tj',xmin:0,xmax:10,ymin:0,ymax:1,xscale:'linear',yscale:'linear',xunit:'A',yunit:'Ohm'};const cal=[[0,100],[100,100],[0,0]];
test('names are engineering labels and dependency lists follow chosen characteristic',()=>{assert.match(characteristicName('Eon_Id_f_Vds_Rg_Tj'),/Turn-on energy/);assert.deepEqual(dependencies('Eon_Id_f_Vds_Rg_Tj'),['Vds','Rg','Tj']);assert.deepEqual(dependencies('Qrr_di_dt_f_Tj_If'),['Tj','If']);assert.deepEqual(dependencies('Pv_B_f_f_T'),['f','T']);});
test('sampling rejects clicks outside axis rectangle',()=>{assert.throws(()=>samplePoint([110,50],cal,s),/outside/);assert.deepEqual(samplePoint([50,50],cal,s),[5,.5]);});
test('ordinary characteristics reject negative samples',()=>{assert.throws(()=>samplePoint([50,50],cal,{...s,xmin:-10,xmax:-1}),/Negative/);});
test('MATLAB body-diode negative samples are accepted then converted to magnitudes',()=>{let r=samplePoint([50,50],cal,{...s,curveId:'Vsd_Id_f_Vgs_Tj',xmin:-10,xmax:0,ymin:-2,ymax:0,yunit:'V'});assert.deepEqual(r,[5,1]);});
test('finite axis ordering and log positive limits enforced',()=>{assert.throws(()=>validateAxes({...s,xmax:0}),/maximum/);assert.throws(()=>validateAxes({...s,xscale:'log'}),/positive/);assert.throws(()=>validateAxes({...s,ymax:Infinity}),/finite/);});

const {originSamples}=await import('../../dist/tools/loss-lab/characteristics.js');
test('ordinary samples extrapolate to zero without changing raw input',()=>{const raw=[[2,4],[4,6]];assert.deepEqual(originSamples(raw,'Rds_Id_f_Vgs_Tj').points,[[0,2],[2,4],[4,6]]);assert.deepEqual(raw,[[2,4],[4,6]]);});
test('negative extrapolated origin is clamped to zero',()=>{assert.deepEqual(originSamples([[2,1],[4,4]],'Rds_Id_f_Vgs_Tj').origin,[0,0]);});
test('all MATLAB energy characteristics force the origin',()=>{for(const id of ['Err_If_f_Tj','If_Err_f_Tj','Eon_Id_f_Vds_Rg_Tj','Id_Eon_f_Vds_Rg_Tj','Eoff_Id_f_Vds_Rg_Tj','Id_Eoff_f_Vds_Rg_Tj']){assert.deepEqual(originSamples([[2,4],[4,6]],id).origin,[0,0]);assert.deepEqual(originSamples([[0,4],[4,6]],id).points[0],[0,0]);}});
test('existing ordinary origin retained and crossing origin interpolated',()=>{assert.deepEqual(originSamples([[0,3],[2,4]],'Rds_Id_f_Vgs_Tj').points,[[0,3],[2,4]]);assert.deepEqual(originSamples([[-2,1],[2,3]],'Rds_Id_f_Vgs_Tj').origin,[0,2]);});
test('origin generation handles empty input and refuses ambiguous branches',()=>{assert.deepEqual(originSamples([],'Eon_Id_f_Vds_Rg_Tj').points,[]);assert.throws(()=>originSamples([[2,1],[2,3]],'Eon_Id_f_Vds_Rg_Tj'),/Duplicate X/);});
