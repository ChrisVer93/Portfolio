// Regression tests added after an independent numerical review of the Loss Lab engine.
// Every expected value below is derived analytically (see the comment above each test).
import test from 'node:test';import assert from 'node:assert/strict';
import {computeDevice,sliceWaveform,spectrum,spectrumPlan,mergeSpectrumLines,rmsTime,runProject,selectAnalysisWindow,queryCurve,setCurveScale,recoveryEvents} from '../../dist/tools/loss-lab/engine.js';
import {makeInstance,emptyProject} from '../../dist/tools/loss-lab/io.js';

const op={...emptyProject().operating,window:1,domainPolicy:'error',outputPairs:[{v:'Vo',i:'Io',polarity:1}]};
const setup=(type,map)=>{const i=makeInstance(type);i.mapping=map??{current:'I',voltage:'V',gate:'G'};return {i,c:i.candidates[0]};};
const curve=(id,xName,yName,xs,ys,deps={})=>({id,xName,yName,canonicalSI:true,iterations:[{x:xs,y:ys,deps}]});
const near=(got,want,rel,label)=>assert.ok(Math.abs(got-want)<=rel*Math.abs(want),`${label}: got ${got}, expected ${want} (±${rel*100}%)`);
const triangle=(t,f,pk)=>t.map(x=>{const ph=(x*f)%1;return pk*(ph<.5?4*ph-1:3-4*ph);});
const noteMatching=(r,re)=>r.notes.some(n=>re.test(n));
const dropLast=w=>({...w,columns:Object.fromEntries(Object.entries(w.columns).map(([k,a])=>[k,a.slice(0,-1)]))});

// ---------- 1. Frequency-dependent ESR must not alias switching ripple ----------
// Triangle, peak 10 A: odd harmonics with amplitude 80/(π²k²), Irms_k² = amp²/2. R(f)=10 mΩ + 2 µΩ/Hz.
const R=f=>0.01+2e-6*f;
function esrCase(fsw,span,n,fftSize){
  const {i,c}=setup('Inductor',{current:'I',voltage:'V'});c.dcResistance=R(0);
  c.curves=[curve('R','f','ESR',[0,1e8],[R(0),R(1e8)],{T:100})];
  const t=Array.from({length:n+1},(_,k)=>k*span/n);
  const w={id:'w',name:'w',time:'t',columns:{t,I:triangle(t,fsw,10),V:t.map(()=>0)}};
  let want=0;for(let k=1;k<4000;k+=2){const a=80/(Math.PI**2*k*k);want+=a*a/2*R(k*fsw);}
  return {got:computeDevice(w,i,c,{...op,window:span,fftSize}),want};
}
test('ESR loss: 100 kHz ripple on a 20 ms window is not aliased (was −93% with 1024 points)',()=>{const {got,want}=esrCase(1e5,.02,400000,1024);near(got.total,want,.005,'ESR total');});
test('ESR loss: result does not depend on the requested FFT size',()=>{const a=esrCase(1e5,.02,400000,1024),b=esrCase(1e5,.02,400000,4096);near(a.got.total,b.got.total,1e-6,'fft size independence');});
test('ESR loss: short windows with whole periods stay exact',()=>{const {got,want}=esrCase(1e5,2e-4,20000,1024);near(got.total,want,.005,'ESR total');});
test('flat ESR(f) equals Irms² × R (Parseval)',()=>{const {i,c}=setup('Inductor',{current:'I',voltage:'V'});c.dcResistance=.05;c.curves=[curve('R','f','ESR',[0,1e7],[.05,.05],{T:100})];const t=Array.from({length:20001},(_,k)=>k*1e-3/20000),I=triangle(t,1e5,10);const r=computeDevice({id:'w',name:'w',time:'t',columns:{t,I,V:t.map(()=>0)}},i,c,{...op,window:1e-3});near(r.total,rmsTime(t,I)**2*.05,.005,'Parseval');});
test('non-periodic current window raises a leakage warning, whole periods do not',()=>{const a=esrCase(1e5,7.3e-5,7300,1024).got,b=esrCase(1e5,2e-4,20000,1024).got;assert.ok(noteMatching(a,/discontinuity at the window boundary/),'expected warning');assert.ok(!noteMatching(b,/discontinuity at the window boundary/),'unexpected warning');});
test('spectrumPlan resolves the finest sample step and reports its band limit',()=>{const t=Array.from({length:4001},(_,k)=>k*5e-6);const p=spectrumPlan(t,1024);assert.ok(p.n>=4001&&(p.n&(p.n-1))===0);assert.ok(p.nyquist>=1/(2*5e-6)*.99);assert.equal(p.capped,false);});
test('merging dense spectral lines preserves total power and DC',()=>{const lines=Array.from({length:20000},(_,k)=>({f:k*10,i2:1+(k%7)}));const merged=mergeSpectrumLines(lines,3000,1.005);const sum=a=>a.reduce((s,h)=>s+h.i2,0);assert.ok(merged.length<lines.length);near(sum(merged),sum(lines),1e-12,'power');assert.equal(merged[0].f,0);});
test('spectrum() reproduces amplitude of a sine (Irms² = A²/2)',()=>{const t=Array.from({length:4097},(_,k)=>k/4096),x=t.map(v=>3*Math.sin(2*Math.PI*8*v));const s=spectrum(t,x,4096);near(s[8].i2,4.5,1e-6,'sine power');});

// ---------- 2. Switching energy ----------
// Ideal switch, 100 kHz, on for half a period, current 8→12 A, Eon=10 µJ/A, Eoff=5 µJ/A, ref 400 V.
const F=1e5;
function switching(N,periods,{late=0,vds=400}={}){const dt=1/F/N,t=[],I=[],V=[],G=[];for(let k=0;k<=periods*N;k++){const s=k%N,on=s<N/2;t.push(k*dt);G.push(on?1:0);I.push(on&&s>=late?8+4*s/(N/2):0);V.push(on?0:vds);}return {id:'w',name:'w',time:'t',columns:{t,I,V,G}};}
function mosfet(){const {i,c}=setup('MOSFET');c.enabled=['on','off'];c.thermal.temperature=100;c.curves=[curve('eon','Id','Eon',[0,20],[0,200e-6],{Vds:400,Rg:2,Tj:100}),curve('eoff','Id','Eoff',[0,20],[0,100e-6],{Vds:400,Rg:2,Tj:100})];return {i,c};}
const steady=(N)=>F*(10e-6*8+5e-6*(8+4*(N/2-1)/(N/2)));
test('switching loss is exact for a whole number of periods and independent of step size',()=>{for(const N of [100,1000]){const {i,c}=mosfet(),w=sliceWaveform(switching(N,40),{window:10/F});near(computeDevice(w,i,c,op).total,steady(N),1e-9,'N='+N);}});
test('switching loss scales linearly with bus voltage relative to the reference voltage',()=>{const {i,c}=mosfet(),w=sliceWaveform(switching(1000,40,{vds:800}),{window:10/F});near(computeDevice(w,i,c,op).total,2*steady(1000),1e-9,'800 V');});
test('direct single-device call with a partial switching period raises a warning',()=>{const {i,c}=mosfet(),w=switching(1000,40);const bad=computeDevice(sliceWaveform(w,{window:2.5/F}),i,c,op),good=computeDevice(sliceWaveform(w,{window:10/F}),i,c,op);assert.ok(noteMatching(bad,/switching periods/),'expected warning');assert.ok(!noteMatching(good,/switching periods/),'unexpected warning');});
test('late current logging: a sharp current step just after the gate edge is used for Eon (aligned logs unchanged)',()=>{const run=late=>{const {i,c}=mosfet();return computeDevice(dropLast(sliceWaveform(switching(1000,40,{late}),{window:8/F})),i,c,op);};const aligned=run(0),late=run(3);assert.ok(!noteMatching(aligned,/gate edge for/),'aligned log must not be adjusted');assert.ok(noteMatching(late,/current taken after the gate edge/),'late log should be adjusted');near(late.total,aligned.total,.01,'late vs aligned');});
test('current logged long after the gate edge raises a warning; a larger look-around window fixes it',()=>{const mk=lookaround=>{const {i,c}=mosfet();if(lookaround)c.eventLookahead=lookaround;return computeDevice(dropLast(sliceWaveform(switching(1000,40,{late:40}),{window:8/F})),i,c,op);};const bad=mk(0),good=mk(1e-6);assert.ok(noteMatching(bad,/current is ≈0 at the gate edge/),'expected warning');assert.ok(!noteMatching(good,/current is ≈0 at the gate edge/),'warning should clear');assert.ok(bad.total<.6*good.total,'unadjusted result is badly low');});

// ---------- 3. Conduction, scaling, magnetics, thermal ----------
test('Rds conduction with a sinusoidal current equals Irms² × Rds',()=>{const {i,c}=setup('MOSFET');c.enabled=['conduction'];c.curves=[curve('r','Id','Rds',[0,100],[.01,.01],{Tj:100,Vgs:15})];const t=Array.from({length:2001},(_,k)=>k/2000);const w={id:'w',name:'w',time:'t',columns:{t,I:t.map(x=>50*Math.sin(2*Math.PI*10*x)),V:t.map(()=>400),G:t.map(()=>1)}};near(computeDevice(w,i,c,op).total,12.5,1e-3,'12.5 W');});
test('two parallel devices share current: total = I²R/2',()=>{const {i,c}=setup('MOSFET');c.enabled=['conduction'];c.parallel=2;c.totalCount=2;c.curves=[curve('r','Id','Rds',[0,100],[.01,.01],{Tj:100,Vgs:15})];const w={id:'w',name:'w',time:'t',columns:{t:[0,.5,1],I:[40,40,40],V:[400,400,400],G:[1,1,1]}};near(computeDevice(w,i,c,op).total,8,1e-9,'8 W');});
test('core loss: flux swing is ΔB/2 = Vpk/(2π f N Ae) and Pv is read at that flux (guards a factor-2 error)',()=>{const f=1e5,N=10,Ae=1e-4,Vc=1e-5,Bpk=.1,Vpk=2*Math.PI*f*N*Ae*Bpk,n=20000,span=20/f,t=Array.from({length:n+1},(_,k)=>k*span/n);const Bs=[.02,.03,.04,.05,.07,.1,.13,.16,.2,.25,.3,.35,.4],Pv=B=>3e5*(B/.1)**2.6;const {i,c}=setup('Inductor',{current:'I',voltage:'V'});c.enabled=['core'];c.N=N;c.Ae=Ae;c.Vcore=Vc;c.coreApproxConfirmed=true;c.coreFrequency=f;c.curves=[curve('pv','B','Pv',Bs,Bs.map(Pv),{f,T:100})];const w={id:'w',name:'w',time:'t',columns:{t,I:t.map(()=>0),V:t.map(x=>Vpk*Math.sin(2*Math.PI*f*x))}};const r=computeDevice(w,i,c,op);near(r.trace.at(-1).Bpeak_T,Bpk,1e-3,'Bpk');near(r.total,Pv(Bpk)*Vc,1e-3,'core loss');});
test('iterative thermal solution matches the closed-form fixed point',()=>{const {i,c}=setup('MOSFET');c.enabled=['conduction'];c.thermal={mode:'iterative',temperature:25,Rth:.5,scope:'device',maxTemperature:175};c.curves=[curve('r','Id','Rds',[0,100],[.01,.01],{Vgs:15}),curve('tn','Tj','Rds_normalised',[25,150],[1,1.5],{Vgs:15,Id:50})];const w={id:'w',name:'w',time:'t',columns:{t:[0,.5,1],I:[50,50,50],V:[400,400,400],G:[1,1,1]}};const x=12.5/(1-.05),r=computeDevice(w,i,c,op);near(r.temperature,25+x,.002,'Tj');near(r.total,25*(1+.004*x),.001,'loss');});
test('invalid inputs are rejected instead of producing numbers',()=>{const {i,c}=setup('Inductor',{current:'I',voltage:'V'});c.curves=[{id:'R',xName:'Constant',yName:'ESR',constant:.01,canonicalSI:true,iterations:[]}];const bad=cols=>()=>computeDevice({id:'w',name:'w',time:'t',columns:cols},i,c,op);assert.throws(bad({t:[0,1,2],I:[1,NaN,1],V:[0,0,0]}));assert.throws(bad({t:[0,1,1],I:[1,1,1],V:[0,0,0]}));});

// ---------- 4. Whole-period window alignment through the full project run ----------
function project(wave,windowPeriods,instance){const n=wave.columns.t.length,cols={...wave.columns,Vi:Array(n).fill(400),Ii:Array(n).fill(5),Vo:Array(n).fill(400),Io:Array(n).fill(4)};return {...emptyProject(),operating:{...emptyProject().operating,snapWindow:true,window:windowPeriods/F,inputPairs:[{v:'Vi',i:'Ii',polarity:1}],outputPairs:[{v:'Vo',i:'Io',polarity:1}]},instances:[instance],waveforms:[{...wave,columns:cols}]};}
function projectDevice(late,periods){const {i,c}=mosfet();const res=runProject(project(switching(1000,40,{late}),periods,{...i,candidates:[c]}));return (res.rows?.[0]??res.results?.[0]).devices[0];}
test('runProject aligns any analysis window to whole switching periods (exact for 10, 10.5, 2.5 and 1.5 periods)',()=>{for(const n of [10,10.5,2.5,1.5])near(projectDevice(0,n).total,steady(1000),1e-9,'window '+n+'T');assert.ok(noteMatching(projectDevice(0,10.5),/whole switching periods/),'expected adjustment note');});
test('runProject with late current logging stays within 1 % after alignment and timing correction',()=>{near(projectDevice(3,10.5).total,steady(1000),.01,'late=3 samples');near(projectDevice(8,10).total,steady(1000),.01,'late=8 samples');});

// ---------- 5. Power-law (log-log) interpolation ----------
test('power-law interpolation is exact between sparse power-law points; linear overestimates',()=>{const Pv=B=>3e5*(B/.1)**2.6,Bs=[.05,.1,.2,.4],cc=curve('pv','B','Pv',Bs,Bs.map(Pv),{f:1e5,T:100});try{setCurveScale('power-law');near(queryCurve(cc,.14,'B','Pv',{f:1e5,T:100}),Pv(.14),1e-9,'power-law');setCurveScale('linear');assert.ok(queryCurve(cc,.14,'B','Pv',{f:1e5,T:100})>1.2*Pv(.14),'linear should overestimate by >20 %');}finally{setCurveScale('linear');}});
test('power-law interpolation passes through the origin for energy curves and leaves temperature axes linear',()=>{const E=I=>20e-6*(I/10)**1.8,xs=[0,10,20,40],ce=curve('e','Id','Eon',xs,xs.map(E),{Vds:400,Rg:2,Tj:100}),ct=curve('n','Tj','Rds_normalised',[25,150],[1,1.5],{Vgs:15,Id:50});try{setCurveScale('power-law');for(const I of [5,15,30])near(queryCurve(ce,I,'Id','Eon',{Vds:400,Rg:2,Tj:100}),E(I),1e-9,'Eon '+I);near(queryCurve(ct,87.5,'Tj','Rds_normalised',{Vgs:15,Id:50}),1.25,1e-12,'temperature axis stays linear');}finally{setCurveScale('linear');}});
test('a project saved without curveScale keeps the legacy linear behaviour',()=>{const {i,c}=mosfet();const w=sliceWaveform(switching(1000,40),{window:10/F});const legacy=computeDevice(w,i,c,{...op,curveScale:undefined}),linear=computeDevice(w,i,c,{...op,curveScale:'linear'});near(legacy.total,linear.total,1e-12,'legacy');});

// ---------- 6. iGSE core loss ----------
const K=2e-3,AL=1.4,BE=2.6,PvS=(B,f)=>K*f**AL*B**BE,BsS=[.02,.03,.04,.05,.07,.1,.13,.16,.2,.25,.3];
function core(shape,freqs,{f=1e5,model='igse'}={}){const N=10,Ae=1e-4,Vc=1e-5,Bpk=.1,n=40000,span=20/f,t=Array.from({length:n+1},(_,k)=>k*span/n);const v=shape==='sine'?t.map(x=>2*Math.PI*f*N*Ae*Bpk*Math.sin(2*Math.PI*f*x)):t.map(x=>((x*f)%1)<.5?4*f*N*Ae*Bpk:-4*f*N*Ae*Bpk);const {i,c}=setup('Inductor',{current:'I',voltage:'V'});c.enabled=['core'];c.N=N;c.Ae=Ae;c.Vcore=Vc;c.coreFrequency=f;c.coreModel=model;c.coreApproxConfirmed=true;c.curves=[{id:'pv',xName:'B',yName:'Pv',canonicalSI:true,iterations:freqs.map(fr=>({x:BsS,y:BsS.map(B=>PvS(B,fr)),deps:{f:fr,T:100}}))}];return computeDevice({id:'w',name:'w',time:'t',columns:{t,I:t.map(()=>0),V:v}},i,c,{...op,curveScale:'power-law'});}
test('iGSE reproduces the Steinmetz datasheet value for a sinusoidal flux (also between frequency curves)',()=>{near(core('sine',[5e4,1e5,2e5]).total,PvS(.1,1e5)*1e-5,1e-4,'at 100 kHz');near(core('sine',[5e4,1e5,2e5],{f:7e4}).total,PvS(.1,7e4)*1e-5,1e-4,'at 70 kHz');const tr=core('sine',[5e4,1e5,2e5]).trace.at(-1);near(tr.alpha,AL,1e-6,'alpha');near(tr.beta,BE,1e-6,'beta');});
test('iGSE for a triangular flux matches the closed-form iGSE expression and differs from the sinusoidal-equivalent value',()=>{const a=AL,b=BE;let I=0;const M=200000;for(let m=0;m<M;m++){const th=(m+.5)*2*Math.PI/M;I+=Math.abs(Math.cos(th))**a*2*Math.PI/M;}const k=PvS(.1,1e5)/(1e5**a*.1**b),ki=k/((2*Math.PI)**(a-1)*I*2**(b-a)),exact=ki*(4*1e5*.1)**a*.2**(b-a)*1e-5;const r=core('tri',[5e4,1e5,2e5]);near(r.total,exact,.005,'closed form');assert.ok(Math.abs(r.total/(PvS(.1,1e5)*1e-5)-1)>.03,'should differ from sinusoidal-equivalent');});
test('iGSE needs frequency-dependent data and refuses to guess; the legacy sinusoidal path is unchanged',()=>{assert.throws(()=>core('sine',[1e5]),/two or more frequencies/);near(core('tri',[1e5],{model:'sinusoidal'}).total,PvS(.1,1e5)*1e-5,.01,'sinusoidal-equivalent');});

// ---------- 7. Recovery energy ----------
function diodeRecovery(vblock,extra={}){const {i,c}=setup('Diode',{current:'I',voltage:'V'});c.enabled=['recovery'];c.recoveryConfirmed=true;c.thermal.temperature=100;Object.assign(c,extra);c.curves=[curve('e','If','Err',[0,50],[0,50e-6],{Vds:400,Tj:100})];const N=100,t=[],I=[],V=[];for(let k=0;k<=N*10;k++){const s=k%N;t.push(k*1e-7);I.push(s<50?10:0);V.push(s<50?0:-vblock);}return computeDevice({id:'w',name:'w',time:'t',columns:{t,I,V}},i,c,op);}
test('Err is scaled with blocking voltage relative to the reference voltage',()=>{const base=diodeRecovery(400),dbl=diodeRecovery(800);near(dbl.total,2*base.total,1e-9,'800 V vs 400 V');assert.ok(noteMatching(dbl,/Err scaled linearly/),'expected note');});
test('recovery detection window is configurable',()=>{const I=[10,0,0,0,0,0,0,0,0],Vb=[0,0,0,0,0,0,0,300,300];assert.equal(recoveryEvents(I,Vb).length,0);assert.equal(recoveryEvents(I,Vb,8).length,1);});

test('adaptive FFT planning caps extreme sample spacing without overflowing', () => {
  const plan = spectrumPlan([0, 1e-12, .02]);
  assert.equal(plan.n, 2 ** 19);
  assert.equal(plan.capped, true);
});

test('window snapping is opt-in and keeps the requested interval by default', () => {
  const {i} = mosfet();
  const p = project(switching(1000, 40), 10.5, i);
  p.operating.snapWindow = false;
  const t = selectAnalysisWindow(p.waveforms[0], p).columns.t;
  near(t.at(-1) - t[0], p.operating.window, 1e-12, 'requested interval');
});
